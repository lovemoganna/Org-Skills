"""Independent remote inspection. The reference bytes come from the prewrite checkpoint."""
import json
import pathlib
import subprocess
import tempfile

here = pathlib.Path(__file__).resolve().parent
scope = json.loads((here / 'baseline.json').read_bytes())['scope']
state = json.loads((here / 'prewrite-checkpoint.json').read_bytes())
step = next(s for s in state['original_plan']['steps'] if s['id'] == state['write_in_flight'])
expected = step['args']['content'].encode()
assert len(expected) <= scope['maxBytes']
assert all(step['args'][k] == scope[k] for k in ['branch','path','repository_full_name','operation_id','expected_head'])
with tempfile.TemporaryDirectory() as tmp:
    cwd = pathlib.Path(tmp)
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=cwd)
    git('init', '-q')
    git('fetch', '-q', 'https://github.com/' + scope['repository_full_name'] + '.git', 'refs/heads/' + scope['branch'])
    head = git('rev-parse', 'FETCH_HEAD').decode().strip()
    parent = git('show', '-s', '--format=%P', head).decode().strip()
    assert parent == scope['expected_head']
    assert git('diff', '--name-only', parent, head).decode().splitlines() == [scope['path']]
    content = git('show', head + ':' + scope['path'])
    assert content == expected
    (cwd / 'remote.mjs').write_bytes(content)
    test = """import assert from 'node:assert/strict';
import {sum} from './remote.mjs';
assert.equal(sum([]),0);
assert.equal(sum([null,undefined]),0);
assert.equal(sum([null,-2,0,undefined,4]),2);
for (const input of ['3','oops',false,NaN,Infinity,-Infinity]) assert.throws(()=>sum([input]),TypeError);
"""
    subprocess.run(['node','--input-type=module','-e',test],cwd=cwd,check=True)
    print(json.dumps({'head':head,'parent':parent,'path':scope['path'],'pinned_bytes':len(content),'assertions':9}))
