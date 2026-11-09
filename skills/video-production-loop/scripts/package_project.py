"""Package a video project outside its source tree; omit rebuildable caches."""
import argparse
import fnmatch
import os
from pathlib import Path
import tempfile
import zipfile

SKIP = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.remotion'}


def package(source, output, excludes=()):
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir():
        raise ValueError('Source must be an existing directory')
    if output == source or source in output.parents:
        raise ValueError('Output must be outside the source directory')
    if output.exists():
        raise ValueError('Refusing to overwrite existing output')
    files = []

    def excluded(path):
        rel = path.relative_to(source).as_posix()
        return any(fnmatch.fnmatchcase(rel, pattern) for pattern in excludes)

    for root, directories, names in os.walk(source, followlinks=False):
        parent = Path(root)
        directories[:] = sorted(d for d in directories
                                if d not in SKIP and not excluded(parent / d))
        for name in directories + sorted(names):
            path = parent / name
            if excluded(path):
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(source):
                raise ValueError(f'Linked paths are not packaged: {path}')
            if path.is_file():
                files.append(path)
    if not files:
        raise ValueError('No project files to package')
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.video-package-', suffix='.zip',
                                      dir=output.parent)
    os.close(fd)
    temporary = Path(temporary)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, (Path(source.name) / path.relative_to(source)).as_posix())
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP integrity check failed')
        # Exclusive creation also refuses an output created during packaging.
        with output.open('xb') as target, temporary.open('rb') as packed:
            import shutil
            shutil.copyfileobj(packed, target)
    finally:
        temporary.unlink(missing_ok=True)
    return {'output': str(output), 'files': len(files), 'bytes': output.stat().st_size}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--exclude', action='append', default=[],
                        help='Repeatable source-relative file/directory glob')
    args = parser.parse_args()
    try:
        import json
        print(json.dumps(package(args.source, args.output, args.exclude)))
    except (ValueError, OSError, zipfile.BadZipFile) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
