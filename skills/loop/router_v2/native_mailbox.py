"""Exchange native model work with trusted Work agents sharing a private run directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def publish(path, value):
    data = encode(value)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    try:
        try:
            os.link(tmp.name, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError("conflicting mailbox record")
    finally:
        os.unlink(tmp.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["request", "issue", "receive", "pending", "reply"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("argument", nargs="?")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    directory = args.directory
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if args.command == "pending":
        pending = [json.loads(p.read_text()) for p in sorted(directory.glob("*.request.json"))
                   if not p.with_name(p.name.replace(".request.", ".response.")).exists()]
        print(json.dumps(pending, ensure_ascii=False))
        return
    if args.command in ("receive", "reply"):
        if not re.fullmatch(r"[0-9a-f]{64}", args.argument or ""):
            parser.error("invalid request id")
        if not (directory / f"{args.argument}.request.json").is_file():
            parser.error("unknown request")
        if args.command == "reply":
            publish(directory / f"{args.argument}.response.json", json.load(sys.stdin))
            return
        receive(directory, args.argument, args.timeout)
        return
    if args.argument not in ("select", "analyze", "verify"):
        parser.error("unknown native role")
    envelope = {"kind": args.argument, "payload": json.load(sys.stdin)}
    # Acceptance must observe the current sink, including after a process restart.
    if args.argument == "verify":
        envelope["attempt"] = uuid.uuid4().hex
    request_id = hashlib.sha256(encode(envelope)).hexdigest()
    publish(directory / f"{request_id}.request.json", {"id": request_id, **envelope})
    if args.command == "issue":
        print(json.dumps({"id": request_id}))
        return
    receive(directory, request_id, args.timeout)


def receive(directory, request_id, timeout):
    response = directory / f"{request_id}.response.json"
    deadline = time.monotonic() + timeout
    while not response.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError(f"native response missing for {request_id}")
        time.sleep(0.25)
    print(response.read_text())


if __name__ == "__main__":
    main()
