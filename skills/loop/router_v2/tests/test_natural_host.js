const {test} = require("node:test");
const assert = require("node:assert/strict");
const {legionHost} = require("../legion_host");
const {naturalHost} = require("../natural_host");

const item = {name:"diagnose",path:"skills/diagnose/SKILL.md",source_sha256:"sha-at-selection"};
const check = {id:"answer",evidence_from:["analysis"]};
function runtime(overrides) {
  const bindings = {
    catalog:[item],
    select:async () => ({actions:[{id:"analysis",kind:"skill",target:item.name}],acceptance:[check]}),
    readSkill:async () => "Inspect evidence.",
    analyze:async () => ({source:"native test role",output:"Observed three matching rows."}),
    ...overrides
  };
  return naturalHost(legionHost({}, {checkpoint:async () => {}}),bindings);
}
test("Skill execution requires native output and independent acceptance", async () => {
  const unverified = await runtime({}).run("inspect rows");
  assert.equal(unverified.status,"NOT_VERIFIED");
  assert.equal(unverified.state.results.analysis.model_output,"Observed three matching rows.");
  assert.match(unverified.state.results.analysis.source,/sha-at-selection/);
  for (const response of [item.name,"inspect rows","Inspect evidence."]) {
    await assert.rejects(runtime({analyze:async () => ({source:"model",output:response})}).run("inspect rows"),/invalid native/);
  }
  const failedProof = await runtime({verify:async () => ({checks:[{id:"wrong",passed:true,evidence:{count:3}}]})}).run("inspect rows");
  assert.equal(failedProof.status,"NOT_VERIFIED");
});
test("an interrupted model request retains the selected Skill revision and cannot resume another task", async () => {
  let saved;
  const delegate = legionHost({},{checkpoint:async state => {saved = state;}});
  const select = async () => ({actions:[{kind:"skill",id:"analysis",target:item.name}],acceptance:[check]});
  const driver = naturalHost(delegate,{catalog:[item],select,readSkill:async () => {throw Error("interrupted");}});
  await assert.rejects(driver.run("inspect rows"),/interrupted/);
  let actual;
  const changed = runtime({catalog:[{...item,source_sha256:"later"}],
    readSkill:async pin => {actual = pin.source_sha256; throw Error("different checkout");}});
  await assert.rejects(changed.run("other task",{state:saved}),/does not match/);
  await assert.rejects(changed.run("inspect rows",{state:saved}),/different checkout/);
  assert.equal(actual,item.source_sha256);
});
test("unknown capabilities, uncovered actions, and cyclic dependencies stop before dispatch", async () => {
  const action = {id:"analysis",kind:"skill",target:item.name};
  for (const [actions,reason] of [
    [[{...action,target:"invented"}],/unknown Skill/],
    [[{...action,kind:"tool",target:"delete.everything"}],/unavailable tool/],
    [[action,{...action,id:"orphan"}],/unaccounted/],
    [[{...action,depends_on:["analysis"]}],/cyclic/]
  ]) {
    await assert.rejects(runtime({select:async () => ({actions,acceptance:[check]})}).run("inspect rows"),reason);
  }
});
test("predecessor data is materialized before dispatch; transient read retries use the same resource", async () => {
  let firstCalls = 0;
  const observed = [];
  const host = legionHost({
    mcp__GitHub__get_repo:async () => {
      if (++firstCalls === 1) throw Object.assign(Error("temporarily unavailable"),{status:503});
      return {result:{full_name:"example/from-receipt"}};
    },
    mcp__GitHub__fetch_file:async args => {observed.push(args); return {result:{content:"three"}};}
  });
  const output = await naturalHost(host,{
    catalog:[],capabilityInfo:{"github.get_repo":{args:["repo_full_name"]}},
    select:async input => {
      assert.deepEqual(input.tools.find(t=>t.id==="github.get_repo").details.args,["repo_full_name"]);
      return {actions:[
        {id:"file",kind:"tool",target:"github.fetch_file",depends_on:["source"],
          args:{repository_full_name:{$from:"source",path:["raw","result","full_name"]},path:"count"}},
        {id:"source",kind:"tool",target:"github.get_repo",args:{repo_full_name:"example/from-receipt"}}
      ],acceptance:[{id:"read",evidence_from:["file"]}]};
    }
  }).run("read the count file");
  assert.equal(firstCalls,2);
  assert.deepEqual(observed,[{repository_full_name:"example/from-receipt",path:"count"}]);
  assert.equal(output.state.retry_history.source.http_status,503);
  assert.equal(output.state.results.file.raw.result.content,"three");
});
test("re-verifies the sink on completion and restart without repeating the tool", async () => {
  let reads=0, value="original";
  const host = legionHost({mcp__GitHub__get_repo:async () => {reads++;return {result:{full_name:"demo/repo"}};}});
  const runner = naturalHost(host,{
    catalog:[],select:async () => ({actions:[{kind:"tool",id:"repo",target:"github.get_repo"}],
      acceptance:[{id:"proof",evidence_from:["repo"]}]}),
    verify:async () => ({checks:[{id:"proof",passed:value==="original",evidence:{value}}]})
  });
  const first = await runner.run("read repository");
  value = "changed";
  assert.equal(first.status,"VERIFIED");
  assert.equal((await runner.run("read repository",{state:first.state})).status,"NOT_VERIFIED");
  assert.equal(reads,1);
});
