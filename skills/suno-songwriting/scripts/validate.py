#!/usr/bin/env python3
"""Deterministic contract checks for a Suno song Markdown draft. Not an audio-quality eval."""
import argparse
import re
import sys
from pathlib import Path

HAN = re.compile(r'[\u4e00-\u9fff]')


def block_after(md: str, heading: str):
    m = re.search(r'^##\s+' + re.escape(heading) + r'\s*\n', md, re.M)
    if not m:
        return None
    section = md[m.end():]
    section = re.split(r'^##\s+', section, maxsplit=1, flags=re.M)[0]
    f = re.search(r'```text\s*\n(.*?)\n```', section, re.S)
    return f.group(1) if f else None


def validate_song(md: str, expected_title=None, mode="full-song"):
    errors = []
    if mode == 'style-only':
        style = block_after(md, 'Style of Music')
        if style is None:
            generic = re.findall(r'```(?:text)?\s*\n(.*?)\n```', md, re.S)
            style = generic[0] if len(generic) == 1 else md.strip() if '```' not in md else None
        if not style:
            errors.append('H4: missing Style text')
        elif len(style) > 1000:
            errors.append(f'H4: Style length {len(style)} > 1000')
        if re.search(r'^##\s+Lyrics\b|^\[(?:Verse|Chorus|Bridge|Outro)', md, re.M):
            errors.append('S2: style-only output must not include lyrics')
        return errors, {'mode': mode, 'style_chars': len(style) if style else None}
    title = re.search(r'^#\s+《([^》]+)》\s*·\s*(v\d+\.\d+)\s*$', md, re.M)
    if not title:
        errors.append('H1: missing title/version header')
    elif expected_title and title.group(1) != expected_title:
        errors.append('H1: user-specified title changed')

    intro_m = re.search(r'^##\s+创作简介\s*\n(.*?)(?=^##\s+|\Z)', md, re.M | re.S)
    intro = intro_m.group(1).strip() if intro_m else ''
    count = len(HAN.findall(intro))
    if not 100 <= count <= 150:
        errors.append(f'H2: intro Han count {count}, expected 100..150')

    for param in ['Genre', 'Mood', 'Tempo', 'Instrumentation', 'Vocal Style', 'Production']:
        if not re.search(r'^' + re.escape(param) + r':\s*\S+', md, re.M):
            errors.append(f'H3: missing {param}')

    style = block_after(md, 'Style of Music')
    if not style:
        errors.append('H4: missing Style of Music text block')
    elif len(style) > 1000:
        errors.append(f'H4: Style length {len(style)} > 1000')

    lyrics = block_after(md, 'Lyrics')
    if not lyrics:
        errors.append('H5: missing Lyrics text block')
    else:
        for tag in ['Verse 1', 'Pre-Chorus', 'Chorus', 'Verse 2', 'Bridge', 'Final Chorus', 'Outro']:
            if not re.search(r'^\[' + re.escape(tag) + r'\]$', lyrics, re.M):
                errors.append(f'H5: missing [{tag}]')
        if any(t in lyrics for t in ('歌词内容', '(注重韵脚', 'TODO')):
            errors.append('H5: contains template placeholder')
    return errors, {'title': title.group(1) if title else None,
                    'version': title.group(2) if title else None,
                    'intro_han': count, 'style_chars': len(style) if style else None,
                    'sections': re.findall(r'^\[([^\]]+)\]$', lyrics or '', re.M)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('song', type=Path)
    p.add_argument('--title')
    p.add_argument('--mode', choices=['full-song', 'style-only'], default='full-song')
    args = p.parse_args()
    errors, stats = validate_song(args.song.read_text(encoding='utf-8'), args.title, args.mode)
    print(stats)
    for error in errors:
        print('FAIL:', error)
    if errors:
        sys.exit(1)
    print('PASS: static format/length checks only; creative quality and actual audio UNVERIFIED')


if __name__ == '__main__':
    main()
