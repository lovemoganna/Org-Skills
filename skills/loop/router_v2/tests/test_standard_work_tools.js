const {test} = require("node:test");
const assert = require("node:assert/strict");
const {legionHost} = require("../legion_host");
const {standardLegionTools} = require("../standard_tools");

test("radar creation requires a verified predecessor and uses a single scoped provider batch", async () => {
  const writes = [];
  const grant = {spreadsheet_id:"isolated",sheetId:42,title:"Test Radar",minRows:2,maxRows:2};
  const role = id => ({board:"exchange",title:"Analyst",location:"Hong Kong",
    url:"https://job-boards.greenhouse.io/exchange/jobs/"+id,duty_excerpt:"KYC due diligence"});
  const roles = [role(1),role(2)];
  const tools = {
    mcp__codex_apps__google_drive_get_spreadsheet_range:async()=>({}),
    mcp__codex_apps__google_drive_get_spreadsheet_metadata:async()=>({}),
    mcp__codex_apps__google_drive_batch_update_spreadsheet:async request=>{
      writes.push(request);
      return {spreadsheetId:"isolated",replies:[{addSheet:{properties:{sheetId:42}}}]};
    }
  };
  const bindings = await standardLegionTools(tools,{radarGrant:grant},async () => ({
    roles,attempts:[],checked_at:"2026-11-24T00:00:00Z"
  }));
  const target="ats.publish_radar";
  const host = legionHost(bindings.toolBindings,{approvedAdapters:bindings.adapters,
    checkpoint:async()=>{},authorizeWrite:bindings.writeGrants[target].authorizeWrite});
  const source={id:"official",kind:"tool",target:"ats.verify_greenhouse",args:{},depends_on:[]};
  const sink={id:"create",kind:"tool",target,args:{verification_step:"official"},depends_on:["official"]};
  const plan=steps=>({id:"radar",goal:"verify and save",steps,acceptance:[{id:"write",evidence_from:["create"]}]});
  const injected={...sink,args:{verification_step:"official",roles:[role(99)]}};
  assert.equal((await host.advance(host.init(plan([source,injected])))).summary.status,"BLOCKED");
  assert.equal(writes.length,0);
  assert.equal((await host.advance(host.init(plan([source,{...sink,depends_on:[]}])))).summary.status,"BLOCKED");
  assert.equal(writes.length,0);
  assert.equal((await host.advance(host.init(plan([source,sink])))).summary.status,"COMPLETED_UNVERIFIED");
  assert.equal(writes.length,1);
  assert.equal(writes[0].spreadsheet_id,"isolated");
  assert.equal(writes[0].requests[0].addSheet.properties.sheetId,42);
  assert.equal(writes[0].requests[1].updateCells.rows.length,3);
});
