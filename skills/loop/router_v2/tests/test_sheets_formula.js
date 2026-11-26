const assert = require('node:assert/strict');
const test = require('node:test');
const {sheetsFormulaAdapter} = require('../sheets_formula');
const args = {spreadsheet_id:'book',sheetId:1,title:'Totals',row:1,column:2,
  before:'=A2+B2',after:'=A2*B2',markerId:17};

test('rejects unsafe coordinate, operation ID and formula before any provider call', async () => {
  let calls = 0;
  const fail = () => {calls++; throw Error('unexpected provider call');};
  const adapter = sheetsFormulaAdapter({mcp__codex_apps__google_drive_batch_update_spreadsheet:fail,
    mcp__codex_apps__google_drive_get_spreadsheet_cells:fail},{exclusiveWorkbookIds:['book']});
  for (const override of [{row:-1},{markerId:1},
    {after:'=IMPORTXML(A2,B2)'},{after:'=A2+B2'}]) {
    await assert.rejects(adapter.bindings.mcp__Legion__replace_formula({...args,...override}), /invalid single-cell/);
  }
  assert.equal(calls,0);
});

test('changed formula precondition prevents every write', async () => {
  let writes = 0;
  const adapter = sheetsFormulaAdapter({
    mcp__codex_apps__google_drive_batch_update_spreadsheet:() => {writes++;},
    mcp__codex_apps__google_drive_get_spreadsheet_cells:() => ({structuredContent:{
      spreadsheetId:'book',sheets:[{properties:{sheetId:1,title:'Totals'},data:[{rowData:[
        {values:[{userEnteredValue:{formulaValue:'=B2'}}]}]}]}]}})
  },{exclusiveWorkbookIds:['book']});
  await assert.rejects(adapter.bindings.mcp__Legion__replace_formula(args), /precondition mismatch/);
  assert.equal(writes,0);
});

test('exclusive resource scope comes only from trusted host configuration', async () => {
  assert.throws(() => sheetsFormulaAdapter({}), /exclusive workbook IDs/);
  const fail = () => {throw Error('unexpected provider call');};
  const adapter = sheetsFormulaAdapter({mcp__codex_apps__google_drive_get_spreadsheet_cells:fail,
    mcp__codex_apps__google_drive_batch_update_spreadsheet:fail},{exclusiveWorkbookIds:['book']});
  await assert.rejects(adapter.bindings.mcp__Legion__replace_formula({...args,
    spreadsheet_id:'shared',exclusiveWorkbookIds:['shared']}), /outside trusted exclusive scope/);
});

test('model-derived arithmetic repair stays within one pinned operation on one observed cell',async () => {
  let reads = 0;
  const adapter = sheetsFormulaAdapter({
    mcp__codex_apps__google_drive_batch_update_spreadsheet:() => {throw Error('unexpected write');},
    mcp__codex_apps__google_drive_get_spreadsheet_cells:() => {
      reads++;
      return {structuredContent:{spreadsheetId:'book',sheets:[{properties:{sheetId:1,title:'Totals'},
        data:[{rowData:[{values:[{userEnteredValue:{formulaValue:'=A2+B2'}}]}]}]}]}};
    }},{exclusiveWorkbookIds:['book']});
  const {before,after,...scope} = args;
  const target = 'sheets.replace_formula';
  const {details,authorizeWrite} = await adapter.prepareScope(scope,null);
  assert.equal(reads,1);
  assert.equal(details.before,before);
  assert.equal(JSON.stringify(details).includes(after),false);
  for (const change of [{title:'Other'},{column:3},{markerId:3},{before:'=1'},{after:'=IMPORTXML(A1,B1)'},
    {after:'=C2+A2'},{after:'=1 2'},{after:'=SUM'},{unexpected:true}]) {
    assert.equal(authorizeWrite({target,args:{...args,...change}}),false);
  }
  assert.equal(authorizeWrite({target,args}),true);
  assert.equal(authorizeWrite({target,args:{...args,after:'=A2/B2'}}),false);
  const state = {original_plan:{steps:[{kind:'tool',target,args}]}};
  const resumed = await adapter.prepareScope(scope,state);
  assert.equal(reads,1);
  assert.equal(resumed.authorizeWrite({target,args}),true);
  assert.equal(resumed.authorizeWrite({target,args:{...args,after:'=A2/B2'}}),false);
  await assert.rejects(adapter.prepareScope({...scope,column:3},state),/checkpoint outside/);
});
