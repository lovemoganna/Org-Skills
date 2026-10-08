"""D23 acceptance record must stay bound to the unchanged D22 HTML bytes."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
report = ROOT / "artifacts" / "verified-d22-report.html"
record = ROOT / "tests" / "verified-d23-render-qa.json"
sha_path = ROOT / "tests" / "d10-fiat-direction-status.sql"


def git_blob_sha(data: bytes) -> str:
    prefix = b"blob " + str(len(data)).encode("ascii") + b"\\0"
    return hashlib.sha1(prefix + data).hexdigest()


def check(data: bytes, qa: dict) -> None:
    assert qa["stage"] == "D23" and qa["status"] == "PASS"
    assert hashlib.sha256(data).hexdigest() == qa["artifact_sha256"], "STALE_RENDER_QA"
    assert git_blob_sha(data) == qa["artifact_git_blob_sha"], "STALE_HTML_BLOB"
    assert qa["remote_render_run"] > 0 and qa["remote_render_artifact_id"] > 0
    assert qa["static_content_regression"] .startswith("PASS")
    assert qa["desktop"]["full_page_overflow"] == "PASS"
    assert qa["mobile"]["full_page_overflow"] == "PASS"
    assert qa["desktop"]["audit_accordions"] == "2/2 PASS"
    assert qa["mobile"]["audit_accordions"] == "2/2 PASS"
    assert qa["presentation"] == "PASS"


def main() -> None:
    data = report.read_bytes()
    qa = json.loads(record.read_text(encoding="utf-8"))
    check(data, qa)
    changed = data.replace(b"completed", b"COMPLETED", 1)
    assert changed != data
    try:
        check(changed, qa)
    except AssertionError:
        pass
    else:
        raise AssertionError("D23 must reject changed HTML bytes")
    print("PASS: D23 rendered QA evidence bound to exact unchanged HTML digest")


if __name__ == "__main__":
    main()
