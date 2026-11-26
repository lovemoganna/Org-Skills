const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const vm = require('node:vm');
const base = '26b4049ee110e2860243c095e5bf1a76cf7f6ae5';
const path = 'skills/loop/router_v2/legion_host.js';
const source = execFileSync('git', ['show', base + ':' + path], {encoding:'utf8'});
const exported = {exports:{}};
vm.runInNewContext(source, {module:exported});
const host = exported.exports.legionHost({});
const plan = {id:'baseline',goal:'Check how a ready skill progresses',steps:[
  {id:'diagnose',kind:'skill',target:'causal-net-loop',args:{},depends_on:[]}
],acceptance:[{id:'analysis',evidence_from:['diagnose']}]};
(async () => {
  const first = await host.advance(host.init(plan));
  const second = await host.advance(JSON.parse(JSON.stringify(first.state)));
  assert.equal(first.summary.status, 'AWAITING_MODEL');
  assert.equal(second.summary.status, 'AWAITING_MODEL');
  assert.equal(second.summary.completed, 0);
  assert.equal(second.summary.pending_model[0].target, 'causal-net-loop');
  const toolPlan = {...plan,steps:[{...plan.steps[0],kind:'tool',target:'github.fetch_file'}]};
  const unavailable = await host.advance(host.init(toolPlan));
  assert.equal(unavailable.state.results.diagnose.error, 'CAPABILITY_UNAVAILABLE');
  assert.equal(unavailable.summary.status, 'BLOCKED');
  console.log(JSON.stringify({base,source:path,first,second,unavailable},null,2));
})().catch(e => {console.error(e);process.exitCode=1;});
