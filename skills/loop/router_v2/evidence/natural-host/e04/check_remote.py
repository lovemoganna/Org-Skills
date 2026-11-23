"""Verify one immutable business commit using a fresh remote fetch and executable tests."""
import json
import pathlib
import re
import subprocess
import sys
import tempfile

branch, expected_parent, expected_content_file, case = sys.argv[1:5]
pinned_commit = sys.argv[5] if len(sys.argv) == 6 else None
if pinned_commit and not re.fullmatch(r"[0-9a-f]{40}", pinned_commit):
    raise ValueError("invalid commit")
if not re.fullmatch(r'legion-e04-e05-[\w-]+', branch) or not re.fullmatch(r'[0-9a-f]{40}', expected_parent):
    raise ValueError('invalid test ref')
if case not in ('e04', 'e05'):
    raise ValueError('unknown case')
with tempfile.TemporaryDirectory() as tmp:
    path = pathlib.Path(tmp)
    def git(*args):
        return subprocess.check_output(['git', '-C', tmp, *args])
    git('init', '-q')
    git('fetch', '-q', 'https://github.com/lovemoganna/Org-Skills.git', 'refs/heads/' + branch)
    head = git('rev-parse', 'FETCH_HEAD').decode().strip()
    if pinned_commit:
        git('merge-base', '--is-ancestor', pinned_commit, head)
        head = pinned_commit
    parent = git('show', '-s', '--format=%P', head).decode().strip()
    assert parent == expected_parent, parent
    assert git('diff', '--name-only', parent, head) == b'legion-test/sum.mjs\n'
    content = git('show', head + ':legion-test/sum.mjs')
    assert content == pathlib.Path(expected_content_file).read_bytes()
    (path / 'sum.mjs').write_bytes(content)
    test = """import assert from 'node:assert/strict';
import * as api from './sum.mjs';
assert.equal(api.sum([]), 0);
assert.equal(api.sum([3,-1,5]), 7);
"""
    if case == 'e05':
        test += 'assert.equal(api.count([]),0); assert.equal(api.count([3,-1,5]),3);\n'
    subprocess.run(['node', '--input-type=module', '-e', test], cwd=path, check=True)
    print(json.dumps({'head': head, 'parents': [parent], 'changed': ['legion-test/sum.mjs'],
                      'bytes': len(content), 'assertions': 4 if case == 'e05' else 2}))
