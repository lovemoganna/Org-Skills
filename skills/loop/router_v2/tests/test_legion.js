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
 const success=await h.retryRead(failed.state,'s',{path:'correct'},'wrong file path');
 assert.equal(success.summary.status,'COMPLETED_UNVERIFIED');assert.equal(n,2);
 assert.equal(success.state.retry_history.s.status,'FAILED');
 await assert.rejects(()=>h.retryRead(success.state,'s',{path:'other'},'again'));
});
