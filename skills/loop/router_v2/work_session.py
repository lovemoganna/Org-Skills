"""Local state for the native Work entry. Run from the pinned checkout root."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

from engine import discover

def save(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, mode="wb", delete=False) as stream:
        name = stream.name
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.replace(name, path)
            fd = os.open(path.parent, os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            Path(name).unlink(missing_ok=True)

def main():
    action = sys.argv[1]
    root = Path("skills").resolve(strict=True)
    if action == "catalog":
        return [dict(item, path="skills/" + item["path"]) for item in discover(root)
                if item["path"] == f'{item["name"]}/SKILL.md']
    if action == "skill":
        path = Path(sys.argv[2]).resolve(strict=True)
        if path.name != "SKILL.md" or not path.is_relative_to(root):
            raise ValueError("unknown Skill path")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != sys.argv[3]:
            raise ValueError("Skill changed since discovery")
        return content.decode("utf-8")
    if action not in ("open", "save"):
        raise ValueError("unknown action")
    directory = Path(sys.argv[2])
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not directory.is_absolute() or directory.is_symlink() or directory.stat().st_mode & 0o077:
        raise ValueError("private absolute session directory required")
    path = directory / "session.json"
    with (directory / ".lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = json.loads(path.read_bytes()) if path.exists() else None
        if action == "open":
            task = json.load(sys.stdin)
            if record is None:
                record = {"task": task, "generation": 0, "state": None}
                save(path, json.dumps(record).encode())
            if task != record["task"]:
                raise ValueError("session belongs to another task")
            return record
        if record is None or record["generation"] != int(sys.argv[3]):
            raise ValueError("session changed; reload latest checkpoint")
        record["generation"] += 1
        record["state"] = json.load(sys.stdin)
        save(path, json.dumps(record, ensure_ascii=False).encode())
        return record["generation"]

if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
