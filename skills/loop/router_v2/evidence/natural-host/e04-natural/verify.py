"""Fetch the isolated ref and execute the independently defined acceptance cases."""
import json
import pathlib
import subprocess
import tempfile

here = pathlib.Path(__file__).resolve().parent
baseline = json.loads((here / 'baseline.json').read_bytes())
with tempfile.TemporaryDirectory() as tmp:
    cwd = pathlib.Path(tmp)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=cwd)
    git('init', '-q')
    scope = baseline['scope']
    git('fetch', '-q', 'https://github.com/' + scope['repository_full_name'] + '.git', 'refs/heads/' + scope['branch'])
    head = git('rev-parse', 'FETCH_HEAD').decode().strip()
    assert git('show', '-s', '--format=%P', head).decode().strip() == baseline['base']
    assert git('diff', '--name-only', baseline['base'], head).decode().splitlines() == [scope['path']]
    content = git('show', head + ':' + scope['path'])
    assert content == (here / 'proposed.mjs').read_bytes()
    (cwd / 'remote.mjs').write_bytes(content)
    test = """import assert from 'node:assert/strict';
import {sum} from './remote.mjs';
assert.equal(sum([]),0);
assert.equal(sum([-3,2]),-1);
assert.equal(sum(['-2.5',' 3 ',1]),1.5);
for (const input of ['oops','',null,Infinity,NaN]) assert.throws(()=>sum([input]),TypeError);
"""
    subprocess.run(['node','--input-type=module','-e',test],cwd=cwd,check=True)
    print(json.dumps({'head':head,'parent':baseline['base'],'path':scope['path'],'bytes':len(content),'assertions':8}))
