#!/usr/bin/env python3
"""Transport-only source gate: fetch exactly caller-specified URLs, verify bytes, write receipts.
No data analysis. Exit nonzero unless all files are locally available from these URLs.
"""
import argparse, concurrent.futures, hashlib, html, json, pathlib, sys, tempfile, urllib.request
from datetime import datetime, timezone


# Transport implementations follow; no analytics occur in this module.

# Same-file GitHub recovery: REST Contents resolves path/ref to a Git blob;
# REST Git Blobs returns the full encoded bytes. Both hash and size are verified.
def _verified_github_blob(entry, dest, timeout):
    """Resolve the exact repository file and stream its original bytes.

    Metadata and web previews are not source bytes. Require metadata SHA/size
    and verify the downloaded bytes against both before accepting any result.
    """
    import re
    import urllib.parse
    parsed = urllib.parse.urlsplit(entry["url"])
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.netloc != "raw.githubusercontent.com" or len(parts) < 4:
        raise ValueError("GITHUB_RAW_URL_REQUIRED")
    owner, repo = parts[:2]
    ref = entry.get("github_ref", parts[2])
    path = entry.get("github_path", "/".join(parts[3:]))
    if "/".join(parts[2:]) != ref + "/" + path or ".." in parts or not path:
        raise ValueError("GITHUB_REF_PATH_AMBIGUOUS")
    quote = urllib.parse.quote
    root = f"https://api.github.com/repos/{owner}/{repo}"
    metadata_url = (root + "/contents/" + quote(path, safe="/")
                    + "?ref=" + quote(ref, safe=""))
    req = urllib.request.Request(metadata_url, headers={
        "User-Agent": "ontology-source-gate/4.0",
        "Accept": "application/vnd.github.object+json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as response:
        metadata = json.load(response)
    sha, size = metadata.get("sha"), metadata.get("size")
    if (metadata.get("type") != "file" or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or type(size) is not int or size < 1):
        raise ValueError("GITHUB_METADATA_INVALID")
    if entry.get("git_blob_sha") and entry["git_blob_sha"] != sha:
        raise ValueError("GITHUB_REF_CHANGED")
    if entry.get("expected_bytes") is not None and entry["expected_bytes"] != size:
        raise ValueError("GITHUB_SIZE_CHANGED")
    blob_url = root + "/git/blobs/" + sha
    file_url = ("https://github.com/" + owner + "/" + repo + "/raw/"
                + quote(ref, safe="/") + "/" + quote(path, safe="/"))
    attempts = []
    for transport, endpoint, accept in (
        ("github_git_blob_raw", blob_url, "application/vnd.github.raw+json"),
        ("github_file_raw", file_url, "application/octet-stream"),
    ):
        partial = None
        try:
            request = urllib.request.Request(endpoint, headers={
                "User-Agent": "ontology-source-gate/4.0",
                "Accept": accept, "Accept-Encoding": "identity",
            })
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise IOError(f"HTTP {response.status}")
                with tempfile.NamedTemporaryFile("wb", dir=dest, delete=False,
                                                 prefix=".githubblob_") as stream:
                    partial = pathlib.Path(stream.name)
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        stream.write(chunk)
            actual_size = partial.stat().st_size
            if actual_size != size:
                raise IOError(f"GITHUB_SIZE_MISMATCH: {actual_size}/{size}")
            git = hashlib.sha1(f"blob {actual_size}\0".encode())
            digest = hashlib.sha256()
            with partial.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    git.update(chunk)
                    digest.update(chunk)
            if git.hexdigest() != sha:
                raise IOError("GITHUB_GIT_BLOB_SHA_MISMATCH")
            if entry.get("sha256") and digest.hexdigest() != entry["sha256"]:
                raise IOError("SOURCE_SHA256_MISMATCH")
            target = dest / entry["name"]
            partial.replace(target)
            partial = None
            return {
                "name": entry["name"], "url": entry["url"],
                "status": "BYTES_VERIFIED", "bytes": actual_size,
                "sha256": digest.hexdigest(), "git_blob_sha": git.hexdigest(),
                "transport": transport, "transport_url": endpoint,
                "github_metadata_url": metadata_url,
                "local_path": str(target), "transport_fallback_errors": attempts,
            }
        except Exception as exc:
            attempts.append({"transport": transport, "endpoint": endpoint,
                             "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if partial is not None:
                partial.unlink(missing_ok=True)
    raise IOError("GITHUB_SAME_BLOB_TRANSFER_FAILED: "
                  + json.dumps(attempts, ensure_ascii=False))


def _fetch_raw_resumable(entry, dest, timeout):
    """Resume only a byte range validated by an unchanged HTTP ETag."""
    import re
    name, url = entry["name"], entry["url"]
    partial = dest / ("." + name + ".raw.partial")
    sidecar = dest / ("." + name + ".raw.etag.json")
    status = {"name": name, "url": url, "status": "SOURCE_BYTES_UNAVAILABLE"}
    try:
        meta = json.loads(sidecar.read_text("utf-8")) if sidecar.exists() else {}
        offset = partial.stat().st_size if partial.exists() and meta.get("url") == url and meta.get("etag") else 0
        if not offset:
            partial.unlink(missing_ok=True)
            sidecar.unlink(missing_ok=True)
        headers = {"User-Agent": "ontology-source-gate/3.0", "Accept-Encoding": "identity"}
        if offset:
            headers["Range"] = f"bytes={offset}-"
            headers["If-Range"] = meta["etag"]
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            etag = response.headers.get("ETag")
            if response.status == 206:
                m = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", ""))
                if not offset or not m or int(m.group(1)) != offset or int(m.group(2)) < offset:
                    raise IOError("Unsafe HTTP 206 Content-Range; resumed bytes rejected")
                if etag and etag != meta["etag"]:
                    raise IOError("HTTP ETag changed across partial transfer")
                expected = int(m.group(3))
                mode = "ab"
            elif response.status == 200:
                expected = int(response.headers["Content-Length"]) if response.headers.get("Content-Length") else None
                mode = "wb"
            else:
                raise IOError(f"Unexpected raw HTTP status: {response.status}")
            if etag:
                sidecar.write_text(json.dumps({"url": url, "etag": etag}), "utf-8")
            else:
                sidecar.unlink(missing_ok=True)
            with partial.open(mode) as stream:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    stream.write(chunk)
        size = partial.stat().st_size
        if not size or (expected is not None and size != expected):
            raise IOError(f"Incomplete transfer: {size}/{expected} bytes")
        if expected is None and not (entry.get("sha256") or entry.get("git_blob_sha")):
            raise IOError("UNVERIFIABLE_LENGTH: pin a hash or require Content-Length")
        if entry.get("expected_bytes") is not None and size != entry["expected_bytes"]:
            raise IOError(f"PINNED_LENGTH_MISMATCH: {size}/{entry['expected_bytes']} bytes")
        sha = hashlib.sha256()
        git = hashlib.sha1()
        git.update(f"blob {size}\0".encode())
        with partial.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                sha.update(chunk)
                git.update(chunk)
        if entry.get("sha256") and sha.hexdigest() != entry["sha256"]:
            raise ValueError("SOURCE_SHA256_MISMATCH")
        if entry.get("git_blob_sha") and git.hexdigest() != entry["git_blob_sha"]:
            raise ValueError("SOURCE_GIT_BLOB_SHA_MISMATCH")
        partial.replace(dest / name)
        sidecar.unlink(missing_ok=True)
        return {"name": name, "url": url, "status": "BYTES_VERIFIED",
                "bytes": size, "sha256": sha.hexdigest(), "git_blob_sha": git.hexdigest(),
                "local_path": str(dest / name), "resumed_from_bytes": offset}
    except Exception as exc:
        status["error"] = type(exc).__name__ + ": " + str(exc)
        status["partial_bytes_untrusted"] = partial.stat().st_size if partial.exists() else 0
        return status


def fetch_one(entry,dest,timeout):
    import os,time
    attempts=[]
    if os.getenv("ONTOLOGY_SOURCE_PREFER_GITHUB_BLOB")!="1":
        for attempt in range(3):
            result=_fetch_raw_resumable(entry,dest,timeout)
            attempts.append({"attempt":attempt+1,"transport":"raw_url","status":result["status"],
                             "error":result.get("error")})
            if result["status"]=="BYTES_VERIFIED":
                if entry.get("sha256") and result["sha256"]!=entry["sha256"]:
                    return {"name":entry["name"],"url":entry["url"],"status":"INTEGRITY_FAILED",
                            "error":"Source SHA-256 differs from pinned SHA-256","attempts":attempts}
                result["transport"]="raw_url"
                result["attempts"]=attempts
                return result
            if "MISMATCH" in result.get("error", ""):
                # A corrupt raw transfer may be repaired by fetching the same
                # pinned Git blob. Never accept either source without hashes.
                break
            if attempt<2:
                time.sleep(min(2**attempt,4))
    try:
        result=_verified_github_blob(entry,dest,timeout)
        attempts.append({"transport":"github_git_blob_api","status":"BYTES_VERIFIED"})
        result["attempts"]=attempts
        return result
    except Exception as exc:
        attempts.append({"transport":"github_same_blob_fallback","status":"FAILED",
                         "error":type(exc).__name__+": "+str(exc)})
        integrity_failed = any("MISMATCH" in a.get("error", "")
                               or "GITHUB_REF_CHANGED" in a.get("error", "")
                               for a in attempts)
        return {"name":entry["name"],"url":entry["url"],
                "status":"INTEGRITY_FAILED" if integrity_failed else "SOURCE_BYTES_UNAVAILABLE",
                "error":" | ".join(a.get("error","") for a in attempts if a.get("error")),
                "attempts":attempts}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',required=True); p.add_argument('--out',required=True); p.add_argument('--timeout',type=float,default=30); p.add_argument('--prefer-github-blob',action='store_true')
    a=p.parse_args();
    if a.prefer_github_blob:
        import os
        os.environ['ONTOLOGY_SOURCE_PREFER_GITHUB_BLOB']='1'
    manifest=json.loads(pathlib.Path(a.manifest).read_text()); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
    entries=manifest['files']
    if not isinstance(entries,list): raise SystemExit('files must be a list')
    if any(not isinstance(e,dict) or not isinstance(e.get('name'),str) or not isinstance(e.get('url'),str) or pathlib.PurePath(e['name']).name != e['name'] or e['name'] in ('.','..') for e in entries):
        raise SystemExit('Invalid manifest name or URL')
    if len({e['url'] for e in entries})!=len(entries) or len({e['name'] for e in entries})!=len(entries):
        raise SystemExit('Duplicate URL or destination name')
    if entries:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(5,len(entries))) as pool:
            results=list(pool.map(lambda entry: fetch_one(entry,out,a.timeout),entries))
    else:
        results=[]
    ready=bool(results) and all(r['status']=='BYTES_VERIFIED' for r in results)
    receipt={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'complete':ready,'results':results}
    (out/'source_gate_receipt.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False), encoding='utf-8')
    if not ready:
        lines = [
            '# Source Gate 阻塞审计报告', '',
            '**状态：SOURCE_BYTES_UNAVAILABLE / INTEGRITY_FAILED，业务分析未执行。**', '',
            f'检查时间（UTC）：{receipt["checked_at_utc"]}', '',
            '| 指定 URL | 状态 | 本地字节 | 实际错误 |', '|---|---|---:|---|'
        ]
        for r in results:
            safe=lambda x:str(x).replace('|',r'\|').replace('\n',' ')
            lines.append(f'| {safe(r["url"])} | {safe(r["status"])} | {r.get("bytes", "未取得")} | {safe(r.get("error", "无"))} |')
        lines += [
            '', '## 已验证与未执行', '',
            '已验证：指定 URL 的本次请求状态；仅当单个文件标为 BYTES_VERIFIED 时，其字节数和哈希可用于证明本地字节完整性。',
            '未执行：缺失文件的格式解析、有效记录数和数据质量、DuckDB SQL、本体、指标、Signal、Finding、Dashboard。',
            '', '## 复跑', '',
            '```bash',
            'python scripts/source_gate.py --manifest <原始URL清单.json> --out <输出目录>',
            '```', '',
            '恢复条件：所有指定 URL 的原始字节都成功进入当前运行环境并通过完整性检查，然后使用 DuckDB 解析和分析。',
            '', '此报告仅说明来源阻塞。报告已交付，不表示业务分析已完成。'
        ]
        md='\n'.join(lines)+'\n'
        (out/'source_gate_blocked.md').write_text(md, encoding='utf-8')
        rows=''.join('<tr><td>'+html.escape(r['url'])+'</td><td>'+html.escape(r['status'])+'</td><td>'+str(r.get('bytes','未取得'))+'</td><td>'+html.escape(str(r.get('error','')))+'</td></tr>' for r in results)
        page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Source Gate 阻塞审计</title><style>body{font:16px/1.6 system-ui;margin:4vw auto;max-width:1100px;padding:0 16px;color:#182538}table{border-collapse:collapse;width:100%;font-size:13px;table-layout:fixed;overflow-wrap:anywhere}td,th{border:1px solid #d7dce2;padding:9px;text-align:left}th{background:#f2f4f8}code{background:#eef1f4;padding:2px 5px}</style><h1>Source Gate 阻塞审计</h1><p><strong>阻塞，未完成业务分析</strong>。检查时间：'+html.escape(receipt['checked_at_utc'])+'</p><table><thead><tr><th>URL</th><th>状态</th><th>字节</th><th>实际错误</th></tr></thead><tbody>'+rows+'</tbody></table><h2>执行边界</h2><p>未取得完整指定源字节时，不解析缺失的指定源文件，不执行 DuckDB SQL，不生成本体、Finding 或 Dashboard。</p><h2>恢复条件</h2><p>全部指定 URL 原始字节进入环境并校验后，才能继续 DuckDB 分析。报告已交付 ≠ 业务分析已完成。</p></html>'
        (out/'source_gate_blocked.html').write_text(page,encoding='utf-8')
    else:
        for f in ('source_gate_blocked.md','source_gate_blocked.html'):
            (out/f).unlink(missing_ok=True)
    for r in results:print(r['name'], r['status'], r.get('error',''))
    print('SOURCE_GATE:', 'PASS' if ready else 'BLOCKED')
    return 0 if ready else 2

if __name__=='__main__': sys.exit(main())
