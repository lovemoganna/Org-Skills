const assert = require('node:assert/strict');
const { test } = require('node:test');
const { legionHost } = require('../legion_host.js');
const base = () => ({ id:'cross-domain', goal:'Use two independent sources', steps:[
 {id:'repo',kind:'tool',target:'github.get_repo',args:{repository_full_name:'example/demo'},depends_on:[]},
 {id:'sheet',kind:'tool',target:'sheets.metadata',args:{spreadsheet_id:'test'},depends_on:[]},
 {id:'think',kind:'skill',target:'causal-net-loop',args:{question:'compare'},depends_on:['repo','sheet']}], acceptance:[{id:'sources',evidence_from:['repo','sheet']},{id:'reasoning',evidence_from:['think']}] });
test('cross-domain real functions parallel, then native model handoff',async()=>{
 let active=0, peak=0;
 const tools={mcp__GitHub__get_repo:async()=>{active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,15));active--;return {result:{repository_full_name:'example/demo'}};},mcp__Google_Drive__get_spreadsheet_metadata:async()=>{active++;peak=Math.max(peak,active);await new Promise(r=>setTimeout(r,15));active--;return {result:{spreadsheetId:'test'}};}};
 const host=legionHost(tools), first=await host.advance(host.init(base()));
 assert.equal(peak,2);assert.equal(first.summary.status,'AWAITING_MODEL');assert.deepEqual(first.summary.pending_model.map(s=>s.id),['think']);
 const result=await host.finishSkill(first.state,'think','Mechanism candidate','skills/causal-net-loop/SKILL.md@rev');
 assert.equal(result.summary.status,'COMPLETED_UNVERIFIED');assert.equal(result.summary.acceptance[1].status,'EVIDENCE_RECORDED');assert.equal(result.summary.trust,'HOST_REPORTED_NOT_INDEPENDENTLY_VERIFIED');
});
test('missing capability blocks and does not invent success',async()=>{ const host=legionHost({});const r=await host.advance(host.init(base()));assert.equal(r.summary.status,'BLOCKED');assert.equal(r.summary.completed,0); });
test('write action requires trusted host authorization independent of plan',async()=>{
 let writes=0;const plan={id:'write',goal:'write with approval',steps:[{id:'w',kind:'tool',target:'github.create_file',args:{content:'secret'},depends_on:[]}],acceptance:[{id:'a',evidence_from:['w']}]};
 const tools={mcp__GitHub__create_file:async()=>{writes++;return {result:{commit_sha:'abc'}}}};
 const r=await legionHost(tools).advance(legionHost(tools).init(plan));assert.equal(r.summary.status,'BLOCKED');assert.equal(writes,0);
 const h=legionHost(tools,{authorizeWrite:async()=>true});const yes=await h.advance(h.init(plan));assert.equal(yes.summary.status,'COMPLETED_UNVERIFIED');assert.equal(writes,1);
});
test('reject unsafe targets, invalid dependencies, duplicate ids and missing acceptance',()=>{
 const h=legionHost({});for(const prop of ['target','dependency','duplicate','acceptance']){const p=base();if(prop==='target')p.steps[0].target='shell.exec';if(prop==='dependency')p.steps[0].depends_on=['think'];if(prop==='duplicate')p.steps[1].id='repo';if(prop==='acceptance')p.acceptance=[];assert.throws(()=>h.init(p));}
});
test('failed provider response halts, dependent Skills do not run',async()=>{
 const h=legionHost({mcp__GitHub__get_repo:async()=>({result:{error:'outage'}}),mcp__Google_Drive__get_spreadsheet_metadata:async()=>({result:{spreadsheetId:'test'}})});
 const r=await h.advance(h.init(base()));assert.equal(r.summary.status,'FAILED');assert.equal(r.state.results.think,undefined);
});
test('provider missing result cannot be promoted by raw success envelope',async()=>{
 const h=legionHost({mcp__GitHub__get_repo:async()=>({result:{}}),mcp__Google_Drive__get_spreadsheet_metadata:async()=>({result:{spreadsheetId:'test'}})});
 const r=await h.advance(h.init(base()));assert.equal(r.summary.status,'FAILED');
});
test('checkpoints are emitted per real result, not plans alone',async()=>{
 const stamps=[];const plan={id:'p',goal:'read',steps:[{id:'s',kind:'tool',target:'sheets.metadata',args:{spreadsheet_id:'id'},depends_on:[]}],acceptance:[{id:'a',evidence_from:['s']}]};
 const h=legionHost({mcp__Google_Drive__get_spreadsheet_metadata:async()=>({result:{spreadsheetId:'id'}})},{checkpoint:async s=>stamps.push(s.status)});
 const r=await h.advance(h.init(plan));assert.equal(r.summary.status,'COMPLETED_UNVERIFIED');assert.ok(stamps.length>=2);
});

test('host adapters generalize across providers but reject unreviewed overrides', async()=>{
 const p={id:'custom',goal:'read CRM',steps:[{id:'s',kind:'tool',target:'crm.fetch',args:{id:'1'},depends_on:[]}],acceptance:[{id:'e',evidence_from:['s']}]};
 const h=legionHost({mcp__CRM__fetch:async()=>({result:{itemId:'1'}})},{approvedAdapters:{'crm.fetch':{names:['mcp__CRM__fetch'],effect:'read',check:d=>d?.itemId==='1'}}});
 assert.equal((await h.advance(h.init(p))).summary.status,'COMPLETED_UNVERIFIED');
 assert.throws(()=>legionHost({}, {approvedAdapters:{'github.fetch_file':{names:['mcp__Bad__call'],effect:'read',check:()=>true}}}));
});
test('bounded read retry preserves first failure evidence and resource identity',async()=>{
 let n=0;
 const plan={id:'fix',goal:'read correct path',steps:[{id:'s',kind:'tool',target:'github.fetch_file',args:{repository_full_name:'x/y',path:'wrong'},depends_on:[]}],acceptance:[{id:'e',evidence_from:['s']}]};
 const h=legionHost({mcp__GitHub__fetch_file:async a=>{n++;return a.path==='correct'?{result:{content:'ok'}}:{result:{error:'not found'}}}});
 const failed=await h.advance(h.init(plan));assert.equal(failed.summary.status,'FAILED');
 await assert.rejects(()=>h.retryRead(failed.state,'s',{repository_full_name:'evil/repo'},'change repo'));
 await assert.rejects(()=>h.retryRead(failed.state,'s',{repo_full_name:'other/repo'},'add repo alias'));
 const success=await h.retryRead(failed.state,'s',{path:'correct'},'wrong file path');
 assert.equal(success.summary.status,'COMPLETED_UNVERIFIED');assert.equal(n,2);
 assert.equal(success.state.retry_history.s.status,'FAILED');
 await assert.rejects(()=>h.retryRead(success.state,'s',{path:'other'},'again'));
});

test('Work connector names resolve for a three-provider plan', async () => {
 const h = legionHost({
  mcp__codex_apps__github_fetch_file: async () => ({ structuredContent: { content: 'skill' } }),
  mcp__codex_apps__google_drive_get_spreadsheet_range: async () => ({ structuredContent: { values: [[1]] } }),
  mcp__codex_apps__parallel_web_search: async () => ({ structuredContent: { results: [{ url: 'https://example.com' }] } }),
 });
 const plan = base();
 plan.steps[0].target = 'github.fetch_file';
 plan.steps[1].target = 'sheets.range';
 plan.steps.splice(2, 0, { id: 'web', kind: 'tool', target: 'parallel.search', args: {}, depends_on: [] });
 plan.steps[3].depends_on.push('web');
 const run = await h.advance(h.init(plan));
 assert.equal(run.summary.completed, 3);
 assert.equal(run.summary.status, 'AWAITING_MODEL');
});

test('write receipt loss requires reconciliation after reload', async () => {
 const plan = {
  id: 'interrupted-write', goal: 'write a test file',
  steps: [
   { id: 'write', kind: 'tool', target: 'github.update_file', args: { branch: 'test/recovery' }, depends_on: [] },
   { id: 'readback', kind: 'tool', target: 'github.fetch_file', args: {}, depends_on: ['write'] },
  ],
  acceptance: [{ id: 'proof', evidence_from: ['write', 'readback'] }],
 };
 let writes = 0;
 let reads = 0;
 let saved;
 const tools = {
  mcp__codex_apps__github_update_file: async () => {
   writes++;
   return { structuredContent: { commit_sha: 'abc' } };
  },
  mcp__codex_apps__github_fetch_file: async () => {
   reads++;
   return { structuredContent: { content: 'test' } };
  },
 };
 const h = legionHost(tools, {
  authorizeWrite: async () => true,
  checkpoint: async state => {
   if (writes) throw Error('checkpoint store interrupted');
   saved = JSON.stringify(state);
  },
 });
 await assert.rejects(() => h.advance(h.init(plan)), /checkpoint store interrupted/);
 const resumedHost = legionHost(tools, { authorizeWrite: async () => true });
 const resumed = await resumedHost.advance(JSON.parse(saved));
 assert.equal(resumed.summary.status, 'BLOCKED');
 assert.equal(resumed.state.results.write.error, 'WRITE_OUTCOME_UNKNOWN');
 assert.equal(writes, 1);
 assert.equal(reads, 0);
 await assert.rejects(() => resumedHost.retryRead(resumed.state, 'write', {}, 'test retry'));
 await assert.rejects(() => resumedHost.reconcileWrite(resumed.state), /trusted write verifier/);
 const wrongProofHost = legionHost(tools, {
  verifyWrite: async () => ({ confirmed: true, receipt: { commit_sha: 'abc' } }),
 });
 assert.equal((await wrongProofHost.reconcileWrite(resumed.state)).summary.status, 'BLOCKED');
 const recoveredHost = legionHost(tools, {
  verifyWrite: async request => {
   assert.deepEqual(request, { id: 'write', target: 'github.update_file', args: { branch: 'test/recovery' } });
   return { confirmed: true, receipt: { commit_sha: 'abc' }, evidence: { readback: 'abc' } };
  },
 });
 const final = await recoveredHost.reconcileWrite(resumed.state);
 assert.equal(final.summary.status, 'COMPLETED_UNVERIFIED');
 assert.equal(final.state.results.write.reconciliation.prior.error, 'WRITE_OUTCOME_UNKNOWN');
 assert.equal(final.state.results.write.reconciliation.evidence.readback, 'abc');
 assert.equal(resumed.state.status, 'BLOCKED');
 assert.equal(writes, 1);
 assert.equal(reads, 1);
 await assert.rejects(() => recoveredHost.reconcileWrite(final.state), /no uncertain write/);
});

test('approval errors fail closed and record a checkpoint', async () => {
 const plan = {
  id: 'approval-error', goal: 'write a test file',
  steps: [{ id: 'write', kind: 'tool', target: 'github.update_file', args: {}, depends_on: [] }],
  acceptance: [{ id: 'proof', evidence_from: ['write'] }],
 };
 const h = legionHost({ mcp__codex_apps__github_update_file: async () => assert.fail('unauthorized write') }, {
  authorizeWrite: async () => { throw Error('approval unavailable'); },
 });
 const run = await h.advance(h.init(plan));
 assert.equal(run.summary.status, 'BLOCKED');
 assert.equal(run.state.results.write.error, 'WRITE_AUTHORIZATION_UNAVAILABLE');
 assert.equal(run.state.write_in_flight, undefined);
 await assert.rejects(() => h.reconcileWrite(run.state), /no uncertain write/);
});

test('provider response loss retains the failure and needs verification', async () => {
 const plan = {
  id: 'provider-response-loss', goal: 'write a test file',
  steps: [{ id: 'write', kind: 'tool', target: 'github.update_file', args: {}, depends_on: [] }],
  acceptance: [{ id: 'proof', evidence_from: ['write'] }],
 };
 const h = legionHost({ mcp__codex_apps__github_update_file: async () => { throw Error('response timeout'); } }, {
  authorizeWrite: async () => true,
  verifyWrite: async () => ({ confirmed: false }),
 });
 const run = await h.advance(h.init(plan));
 assert.equal(run.summary.status, 'BLOCKED');
 assert.match(run.state.results.write.prior.error, /response timeout/);
 assert.equal((await h.reconcileWrite(run.state)).summary.status, 'BLOCKED');
});
