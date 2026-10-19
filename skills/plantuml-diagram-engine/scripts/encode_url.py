#!/usr/bin/env python3
"""Generate shareable PlantUML PNG image URLs; optional public verification.

URL generation is offline. Checking URLs sends source to a public renderer.
"""
from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request
import zlib

ALPHABET = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_'
PLANTUML_BASE = 'https://www.plantuml.com/plantuml/png/'
KROKI_BASE = 'https://kroki.io/plantuml/png/'
PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
MAX_BYTES = 12_000_000


class RenderError(Exception):
    pass


class DiagramError(RenderError):
    pass


def plantuml_token(source: str) -> str:
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    raw = comp.compress(source.encode('utf-8')) + comp.flush()
    result = []
    for offset in range(0, len(raw), 3):
        a, b, c = (list(raw[offset:offset+3]) + [0, 0, 0])[:3]
        result.extend((ALPHABET[a >> 2], ALPHABET[((a & 3) << 4) | (b >> 4)],
                       ALPHABET[((b & 15) << 2) | (c >> 6)], ALPHABET[c & 63]))
    return ''.join(result)


def resolve_includes(source: str, base_dir: Path | None = None, depth: int = 0) -> str:
    """Preprocess local !include directives so public renderers receive inlined definitions."""
    if depth > 5:
        return source
    lines = []
    skill_root = Path(__file__).resolve().parent.parent
    for line in source.splitlines():
        stripped = line.strip()
        if (stripped.startswith('!include ') or stripped.startswith('!include_many ')
                or stripped.startswith('!include_once ')):
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2:
                target_str = parts[1].strip().strip('"\'')
                if target_str.startswith('http://') or target_str.startswith('https://'):
                    lines.append(line)
                    continue
                candidates = []
                if base_dir:
                    candidates.append((base_dir / target_str).resolve())
                candidates.append((skill_root / target_str).resolve())
                candidates.append((skill_root / 'styles' / target_str).resolve())
                candidates.append((skill_root / 'styles' / Path(target_str).name).resolve())
                target_file = next((c for c in candidates if c.is_file()), None)
                if target_file:
                    content = target_file.read_text(encoding='utf-8')
                    resolved_content = resolve_includes(content, base_dir=target_file.parent, depth=depth + 1)
                    lines.append(resolved_content)
                    continue
        lines.append(line)
    return '\n'.join(lines)


def kroki_token(source: str) -> str:
    return base64.urlsafe_b64encode(zlib.compress(source.encode('utf-8'), 9)).decode('ascii').rstrip('=')


def get_links(source: str, base_dir: Path | None = None) -> dict[str, str]:
    expanded = resolve_includes(source, base_dir=base_dir) if '!include' in source else source
    return {'plantuml': PLANTUML_BASE + plantuml_token(expanded),
            'kroki': KROKI_BASE + kroki_token(expanded)}


def validate_source(source: str) -> None:
    text = source.strip()
    pairs = [('@startuml', '@enduml'), ('@startwbs', '@endwbs'),
             ('@startmindmap', '@endmindmap'), ('@startgantt', '@endgantt')]
    valid = any(text.startswith(a) and text.endswith(b) and text.count(a) == 1
                and text.count(b) == 1 for a, b in pairs)
    if not valid:
        raise RenderError('SOURCE_INVALID: expected one complete PlantUML diagram')


def verify_online(url: str, timeout: int = 20) -> tuple[bytes, tuple[int, int]]:
    from PIL import Image  # Only required for online image checks, not URL generation.
    req = urllib.request.Request(url, headers={'Accept': 'image/png', 'User-Agent': 'plantuml-diagram-engine/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            if res.status != 200:
                raise RenderError(f'HTTP_{res.status}')
            headers = {k.lower(): v for k, v in res.headers.items()}
            if headers.get('x-plantuml-diagram-error') or headers.get('x-plantuml-error'):
                raise DiagramError('PLANTUML_SYNTAX_ERROR_HEADER')
            if '(error)' in headers.get('x-plantuml-diagram-description', '').lower():
                raise DiagramError('PLANTUML_ERROR_DIAGRAM')
            if headers.get('content-type', '').split(';')[0].lower() != 'image/png':
                raise RenderError('NOT_PNG_CONTENT_TYPE')
            data = res.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        if 400 <= e.code < 500:
            raise DiagramError(f'HTTP_{e.code}_POSSIBLE_SYNTAX_ERROR') from e
        raise RenderError(f'HTTP_{e.code}') from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise RenderError(f'NETWORK_ERROR: {e}') from e
    if len(data) > MAX_BYTES or not data.startswith(PNG_MAGIC):
        raise RenderError('INVALID_PNG_BYTES')
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != 'PNG':
                raise RenderError('INVALID_PNG_FORMAT')
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            if min(width, height) < 10 or width * height > 40_000_000:
                raise RenderError('INVALID_PNG_DIMENSIONS')
            image.load()
        return data, (width, height)
    except (OSError, ValueError) as e:
        raise RenderError(f'INVALID_PNG: {e}') from e


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Get online PNG links for PlantUML source')
    parser.add_argument('source', type=Path)
    parser.add_argument('--json', action='store_true', help='machine-readable output')
    parser.add_argument('--private', action='store_true', help='never generate publicly shareable URLs')
    parser.add_argument('--check-online', action='store_true', help='make GET request and check PNG')
    parser.add_argument('--public-ok', action='store_true', help='approve sending code to public service')
    parser.add_argument('--download', type=Path, help='explicitly save checked image')
    parser.add_argument('--timeout', type=int, default=20)
    args = parser.parse_args(argv)
    if args.private:
        raise RenderError('PRIVATE_SOURCE: public image URL disabled; use local renderer')
    if (args.check_online or args.download) and not args.public_ok:
        raise RenderError('PUBLIC_UPLOAD_DENIED: --public-ok required for network requests')
    source = args.source.read_text(encoding='utf-8')
    validate_source(source)
    links = get_links(source, base_dir=args.source.parent)
    status = 'URL_GENERATED / HTTP_UNVERIFIED'
    backend = None
    dimensions = None
    if args.check_online or args.download:
        errors = []
        for provider in ('plantuml', 'kroki'):
            try:
                image, dimensions = verify_online(links[provider], args.timeout)
                backend = provider
                status = 'PNG_VALIDATED / VISUAL_UNVERIFIED'
                break
            except DiagramError:
                raise  # Source / request problems are not fixed by switching servers.
            except (RenderError, ImportError) as e:
                errors.append(f'{provider}: {e}')
        else:
            status = 'URL_GENERATED / HTTP_UNVERIFIED; ' + '; '.join(errors)
        if args.download and backend is None:
            raise RenderError('DOWNLOAD_FAILED: neither renderer returned valid PNG')
        if backend and args.download:
            args.download.parent.mkdir(parents=True, exist_ok=True)
            args.download.write_bytes(image)
    if args.json:
        print(json.dumps({'urls': links, 'status': status, 'backend': backend,
                          'dimensions': dimensions}, ensure_ascii=False, indent=2))
    else:
        print('在线 PNG（PlantUML）：' + links['plantuml'])
        print('备用 PNG（Kroki）：' + links['kroki'])
        print('验证状态：' + status)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RenderError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
