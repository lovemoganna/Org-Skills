const test = require('node:test');
const assert = require('node:assert/strict');
const { githubCommitAdapter } = require('../github_commit_adapter');
const grant = { repository_full_name: 'owner/repo', branch: 'isolation', path: 'x.js',
  expected_head: 'a'.repeat(40), operation_id: 'trial', content: '1' };
const req = { target: 'github.commit_file', args: grant };
test('grant pins branch, operation and exact bytes', async () => {
  const adapter = githubCommitAdapter({}, grant, { readTree: () => '' });
  assert.equal(await adapter.authorizeWrite(req), true);
  for (const property of ['repository_full_name', 'branch', 'path', 'expected_head', 'operation_id', 'content']) {
    const args = { ...grant, [property]: 'other' };
    assert.equal(await adapter.authorizeWrite({ ...req, args }), false);
    await assert.rejects(adapter.tools.mcp__legion__github_commit_file(args), /OUTSIDE_GRANT/);
  }
});
test('different observed head with a different commit message blocks before staging', async () => {
  const provider = { mcp__codex_apps__github_fetch_commit: async () =>
    ({ structuredContent: { commit: { sha: 'b'.repeat(40), message: 'other job' } } }) };
  const adapter = githubCommitAdapter(provider, grant, { readTree: () => { throw Error('unexpected'); } });
  await assert.rejects(adapter.tools.mcp__legion__github_commit_file(grant), /HEAD_CONFLICT/);
});
const { githubScopedEditAdapter } = require('../github_commit_adapter');
const {content, ...coordinates} = grant;
const scope = { ...coordinates, allowGeneratedContent:true, maxBytes:4 };
const provider = {mcp__codex_apps__github_fetch_file: async args => {
  assert.deepEqual(args,{repository_full_name:'owner/repo',path:'x.js',ref:grant.expected_head});
  return {structuredContent:{content:'old',sha:'c'.repeat(40),encoding:'utf-8'}};
}};
test('scope is host-only; exact immutable coordinates, UTF-8 size, changed bytes and closed schema', async () => {
  const adapter = await githubScopedEditAdapter(provider,scope,{readTree:()=>''});
  assert.equal(adapter.details.original.content,'old');
  assert.equal(await adapter.authorizeWrite({...req,args:{...grant,content:'😊'}}),true);
  for (const patch of [{content:'old'},{content:'😊a'},{content:'\uD800'},{path:'unapproved'},{branch:'main'},
                       {operation_id:'x'},{repository_full_name:'other/repo'},{expected_head:'e'.repeat(40)},{extra:1}]) {
    const args = {...grant,...patch};
    assert.equal(await adapter.authorizeWrite({...req,args}),false);
    await assert.rejects(adapter.tools.mcp__legion__github_commit_file(args),/OUTSIDE_GRANT/);
  }
});
test('missing opt-in, unbounded grants, main and unavailable originals fail before writes',async () => {
  for (const patch of [{allowGeneratedContent:false},{maxBytes:0},{maxBytes:10000000},{branch:'main'},{content:'x'}])
    await assert.rejects(githubScopedEditAdapter(provider,{...scope,...patch},{readTree:()=>''}),/bounded/);
  await assert.rejects(githubScopedEditAdapter({mcp__codex_apps__github_fetch_file:async()=>({isError:true})},
    scope,{readTree:()=>''}),/UTF-8/);
});
