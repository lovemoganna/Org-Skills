"""D23 acceptance record must stay bound to the unchanged D22 HTML bytes."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
report = ROOT / "artifacts" / "verified-d22-report.html"
record = ROOT / "tests" / "verified-d23-render-qa.json"


def git_blob_sha(data: bytes) -> str:
    prefix = b"blob " + str(len(data)).encode("ascii") + bytes([0])
    return hashlib.sha1(prefix + data).hexdigest()


def check(data: bytes, qa: dict) -> None:
    assert qa["stage"] == "D23" and qa["status"] == "PASS"
    assert hashlib.sha256(data).hexdigest() == qa.get("artifact_sha256"), "STALE_RENDER_QA"
    assert git_blob_sha(data) == qa.get("artifact_git_blob_sha"), "STALE_HTML_BLOB"
    assert qa["remote_render_run"] > 0 and qa["remote_render_artifact_id"] > 0
    assert qa["static_content_regression"].startswith("PASS")
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
    # Historical failure: a missing SHA field must fail with a named evidence error,
    # not an unhelpful KeyError. The original file and verified record stay unchanged.
    missing_sha = dict(qa)
    missing_sha.pop("artifact_sha256", None)
    try:
        check(data, missing_sha)
    except AssertionError as exc:
        assert str(exc) == "STALE_RENDER_QA", exc
    else:
        raise AssertionError("D23 must reject missing artifact_sha256")
    missing_blob = dict(qa)
    missing_blob.pop("artifact_git_blob_sha", None)
    try:
        check(data, missing_blob)
    except AssertionError as exc:
        assert str(exc) == "STALE_HTML_BLOB", exc
    else:
        raise AssertionError("D23 must reject missing artifact_git_blob_sha")
    print("PASS: D23 exact HTML digests + missing-SHA and tamper regressions")


if __name__ == "__main__":
    main()
