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
