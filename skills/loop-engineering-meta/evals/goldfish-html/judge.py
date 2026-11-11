#!/usr/bin/env python3
"""Offline holdout evaluator for html-design-lab worker checkouts.

Static/stdlib only. Browser/runtime claims require separate Playwright evidence.
Usage: python judge.py /path/to/worker/repo F01-release-shell
Never make this evaluator available to the coding worker during the trial.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

CASES = {"F01-release-shell", "R01-source-fidelity", "G01-offline-code-color"}
QA_MARKERS = ('class="v45qa"', 'id="v45-qa"',
              'guanshi-v45-compat-check', 'V4.5 · 本地浏览器兼容性自检')
PAYLOAD = "SELECT '-- <script>alert(1)</script>' AS text;\n-- <img src=x onerror=alert(1)>"
USER_TEXT = '测试报告和 V4.5 是用户正文，应予保留。'


def run(repo: Path, case_id: str) -> dict:
    root = repo / 'skills/html-design-lab'
    generator = root / 'scripts/generate.py'
    template_path = root / 'assets/v55-renderer.html'
    checks = {}
    if not generator.is_file() or not template_path.is_file():
        return {'case': case_id, 'passed': False, 'checks': {'source_files': 'FAIL: missing'}, 'browser_verified': False}
    try:
        spec = importlib.util.spec_from_file_location('holdout_html_generator', generator)
        if not spec or not spec.loader:
            raise RuntimeError('module unavailable')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        template = template_path.read_text(encoding='utf-8')
        fence = chr(96) * 3
        src = '# 演示\n\n## 真实代码\n\n' + USER_TEXT + '\n\n' + fence + 'sql\n' + PAYLOAD + '\n' + fence
        doc = mod.parse_text(src, kind='tutorial', docid='ab-holdout')
        output = mod.render(doc, 'terminal', template)
        matches = re.findall(r'<script\s+type="application/json"\s+id="document-spec-data">(.*?)</script>', output, re.S)
        assert len(matches) == 1, 'missing or duplicate embedded spec'
        exported = json.loads(matches[0])[0]
        blocks = [b for ch in exported['chapters'] for b in ch['blocks']]
        checks['embedded-data-roundtrip'] = any(b.get('type') == 'code' and b.get('code') == PAYLOAD for b in blocks)
        checks['user-test-words-preserved'] = USER_TEXT in json.dumps(exported, ensure_ascii=False)
        checks['hostile-input-inert'] = (PAYLOAD not in output and 'code.innerHTML' not in output)
        checks['no-legacy-qa-shell'] = all(token not in output for token in QA_MARKERS)
        checks['offline-highlight-present'] = ('function highlightCode(' in output
            and 'highlightCode(code,block.code,block.language)' in output
            and output.count('id="code-syntax-theme"') == 1
            and 'span.textContent=t' in output)
        checks['thirty-styles'] = len(set(mod.get_style_ids(template))) == 30
        existing = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
                                  cwd=root, capture_output=True, text=True, timeout=120)
        checks['existing-suite'] = existing.returncode == 0
        log_tail = (existing.stdout + '\n' + existing.stderr)[-2500:]
    except Exception as exc:
        return {'case': case_id, 'passed': False, 'checks': checks,
                'error': f'{type(exc).__name__}: {exc}', 'browser_verified': False}
    required = {
       'F01-release-shell': ('no-legacy-qa-shell', 'user-test-words-preserved', 'existing-suite', 'thirty-styles'),
       'R01-source-fidelity': ('embedded-data-roundtrip', 'hostile-input-inert', 'existing-suite', 'thirty-styles'),
       'G01-offline-code-color': ('offline-highlight-present', 'embedded-data-roundtrip', 'hostile-input-inert', 'existing-suite', 'thirty-styles')
    }[case_id]
    return {'case': case_id, 'passed': all(checks.get(k) for k in required), 'required': required,
            'checks': checks, 'existing_suite_log_tail': log_tail, 'browser_verified': False,
            'limitation': 'Static/stdlib acceptance only; Playwright user-facing behavior not verified.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('checkout', type=Path)
    ap.add_argument('case', choices=sorted(CASES))
    args = ap.parse_args()
    result = run(args.checkout, args.case)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
