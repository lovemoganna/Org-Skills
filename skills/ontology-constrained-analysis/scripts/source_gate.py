#!/usr/bin/env python3
"""Transport-only source gate: fetch exactly caller-specified URLs, verify bytes, write receipts.
No data analysis. Exit nonzero unless all files are locally available from these URLs.
"""
import argparse, concurrent.futures, hashlib, html, json, pathlib, sys, tempfile, urllib.request
from datetime import datetime, timezone


def fetch_one(entry, dest, timeout):
    url, name = entry['url'], entry['name']
    status = {'name': name, 'url': url, 'status': 'SOURCE_BYTES_UNAVAILABLE'}
    tmp = None
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'ontology-source-gate/1.0'}), timeout=timeout) as response:
            with tempfile.NamedTemporaryFile('wb', dir=dest, delete=False, prefix='.partial_') as f:
                tmp = pathlib.Path(f.name)
                for chunk in iter(lambda: response.read(1024 * 1024), b''):
                    f.write(chunk)
        data_sha = hashlib.sha256()
        blob_sha = hashlib.sha1()
        size = tmp.stat().st_size
        blob_sha.update(f'blob {size}\0'.encode())
        with tmp.open('rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                data_sha.update(chunk); blob_sha.update(chunk)
        expected_blob_sha = entry.get('git_blob_sha')
        if expected_blob_sha and blob_sha.hexdigest() != expected_blob_sha:
            status.update(status='INTEGRITY_FAILED', error='Git Blob SHA differs from expected', bytes=size, git_blob_sha=blob_sha.hexdigest())
            return status
        target = dest / name
        tmp.replace(target)
        tmp = None
        status.update(status='BYTES_VERIFIED', bytes=size, sha256=data_sha.hexdigest(), git_blob_sha=blob_sha.hexdigest(), local_path=str(target))
    except Exception as exc:
        status['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if tmp and tmp.exists(): tmp.unlink()
    return status



# Same-file GitHub recovery: REST Contents resolves path/ref to a Git blob;
# REST Git Blobs returns the full encoded bytes. Both hash and size are verified.
def _verified_github_blob(entry, dest, timeout):
    import base64, re, urllib.parse
    url=entry["url"]
    parsed=urllib.parse.urlsplit(url)
    parts=parsed.path.strip("/").split("/")
    if parsed.scheme!="https" or parsed.netloc!="raw.githubusercontent.com" or len(parts)<4:
        raise ValueError("GitHub fallback requires an exact raw.githubusercontent.com owner/repo/ref/path")
    owner,repo=parts[:2]
    ref=entry.get("github_ref",parts[2])
    path=entry.get("github_path","/".join(parts[3:]))
    if "/".join(parts[2:])!=ref+"/"+path or ".." in parts or not path:
        raise ValueError("GitHub fallback URL/ref/path ambiguity")
    base=f"https://api.github.com/repos/{owner}/{repo}"
    def api_json(endpoint):
        request=urllib.request.Request(endpoint,headers={"User-Agent":"ontology-source-gate/2.0","Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(request,timeout=timeout) as response:
            if response.status!=200:
                raise IOError(f"GitHub REST HTTP {response.status}")
            return json.load(response)
    metadata_url=base+"/contents/"+urllib.parse.quote(path,safe="/")+"?ref="+urllib.parse.quote(ref,safe="")
    metadata=api_json(metadata_url)
    sha=metadata.get("sha")
    if metadata.get("type")!="file" or not isinstance(sha,str) or not re.fullmatch(r"[0-9a-f]{40}",sha):
        raise ValueError("GitHub Contents metadata missing valid Git blob")
    if entry.get("git_blob_sha") and entry["git_blob_sha"]!=sha:
        raise ValueError("GitHub branch blob differs from pinned original")
    blob_url=base+"/git/blobs/"+sha
    blob=api_json(blob_url)
    if blob.get("sha")!=sha or blob.get("encoding")!="base64":
        raise ValueError("GitHub Git Blobs response inconsistent")
    payload=base64.b64decode(blob["content"])
    if len(payload)!=metadata["size"] or len(payload)!=blob["size"]:
        raise IOError("GitHub blob content length mismatch")
    target=dest/entry["name"]
    with tempfile.NamedTemporaryFile("wb",dir=dest,delete=False,prefix=".githubblob_") as stream:
        stream.write(payload)
        partial=pathlib.Path(stream.name)
    try:
        sha256=hashlib.sha256()
        git=hashlib.sha1()
        git.update(f"blob {len(payload)}\0".encode())
        with partial.open("rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):
                sha256.update(block)
                git.update(block)
        if git.hexdigest()!=sha:
            raise IOError("Git Blob SHA-1 mismatch after full decode")
        if entry.get("sha256") and sha256.hexdigest()!=entry["sha256"]:
            raise IOError("Expected SHA-256 mismatch")
        partial.replace(target)
        return {"name":entry["name"],"url":url,"status":"BYTES_VERIFIED",
                "bytes":len(payload),"sha256":sha256.hexdigest(),"git_blob_sha":git.hexdigest(),
                "transport":"github_git_blob_api","transport_url":blob_url,"local_path":str(target)}
    finally:
        partial.unlink(missing_ok=True)


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


_raw_fetch_one=fetch_one
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
            if attempt<2:
                time.sleep(min(2**attempt,4))
    try:
        result=_verified_github_blob(entry,dest,timeout)
        attempts.append({"transport":"github_git_blob_api","status":"BYTES_VERIFIED"})
        result["attempts"]=attempts
        return result
    except Exception as exc:
        attempts.append({"transport":"github_git_blob_api","status":"FAILED",
                         "error":type(exc).__name__+": "+str(exc)})
        return {"name":entry["name"],"url":entry["url"],"status":"SOURCE_BYTES_UNAVAILABLE",
                "error":attempts[-1]["error"],"attempts":attempts}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--manifest',required=True); p.add_argument('--out',required=True); p.add_argument('--timeout',type=float,default=30)
    a=p.parse_args(); manifest=json.loads(pathlib.Path(a.manifest).read_text()); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
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
