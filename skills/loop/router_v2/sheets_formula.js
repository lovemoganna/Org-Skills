// The host must authorize the complete argument object and scope before using this adapter.
function sheetsFormulaAdapter(tools, {exclusiveWorkbookIds} = {}) {
  if (!Array.isArray(exclusiveWorkbookIds) || !exclusiveWorkbookIds.length ||
      exclusiveWorkbookIds.some(id => typeof id !== 'string' || !/^[\w-]+$/.test(id))) {
    throw Error('trusted exclusive workbook IDs required');
  }
  const allowed = new Set(exclusiveWorkbookIds);
  const batch = tools.mcp__codex_apps__google_drive_batch_update_spreadsheet;
  const cells = tools.mcp__codex_apps__google_drive_get_spreadsheet_cells;
  if (typeof batch !== 'function' || typeof cells !== 'function') throw Error('Sheets connectors unavailable');
  const providerData = r => {
    if (r?.isError || !r?.structuredContent) throw Error('invalid Sheets response');
    return r.structuredContent;
  };
  const arithmetic = /^=[A-Za-z0-9$()+*/. :,^-]+$/;
  function position(a) {
    const {spreadsheet_id, sheetId, title, row, column, markerId} = a;
    if (!allowed.has(spreadsheet_id)) throw Error('workbook outside trusted exclusive scope');
    if (typeof spreadsheet_id !== 'string' || !/^[\w-]+$/.test(spreadsheet_id) || !title || typeof title !== 'string' ||
        ![sheetId, row, column, markerId].every(n => Number.isSafeInteger(n) && n >= 0) ||
        markerId === sheetId || markerId > 2147483647 || sheetId > 2147483647 ||
        (row + 2) * (column + 1) > 1000000 || column >= 18278) {
      throw Error('invalid single-cell arithmetic formula request');
    }
    let col = '', n = column + 1;
    while (n) { n--; col = String.fromCharCode(65 + n % 26) + col; n = Math.floor(n / 26); }
    const cell = col + (row + 1), marker = 'LegionReceipt_' + markerId;
    const range = {sheetId, startRowIndex:row, endRowIndex:row+1, startColumnIndex:column, endColumnIndex:column+1};
    return {marker, cell, end:col+(row+2), range};
  }
  function spec(a) {
    const pos = position(a);
    if (![a.before,a.after].every(f => typeof f === 'string' && f.length < 4096 && arithmetic.test(f) &&
        !/[A-Z_][A-Z0-9_.]*\s*\(/i.test(f)) || a.before === a.after)
      throw Error('invalid single-cell arithmetic formula request');
    const signature = JSON.stringify([a.spreadsheet_id,a.sheetId,a.title,a.row,a.column,a.before,a.after,a.markerId]);
    return {...pos,signature};
  }
  const quote = title => "'" + title.replace(/'/g,"''") + "'";
  async function read(a, title, range) {
    const raw = await cells({spreadsheet_id:a.spreadsheet_id,ranges:[quote(title)+'!'+range],
      cell_fields:'userEnteredValue,effectiveValue'});
    const data = providerData(raw), sheet = data.sheets?.[0];
    if (data.spreadsheetId !== a.spreadsheet_id || sheet?.properties?.title !== title) throw Error('unexpected read target');
    return {raw, id:sheet.properties.sheetId, rows:sheet.data?.[0]?.rowData || []};
  }
  async function prepareScope(scope, savedState) {
    const keys = ['spreadsheet_id','sheetId','title','row','column','markerId'];
    const exactKeys = (obj, wanted) => obj && Object.keys(obj).length === wanted.length &&
      wanted.every(k => Object.hasOwn(obj,k));
    if (!exactKeys(scope,keys)) throw Error('invalid sheet scope keys');
    const pos = position(scope);
    const target = 'sheets.replace_formula';
    const sameScope = a => keys.every(k => a[k] === scope[k]);
    let baseline, pinned;
    if (savedState) {
      const writes = savedState.original_plan?.steps?.filter(s => s.kind === 'tool' && s.target === target);
      if (!writes || writes.length > 1) throw Error('ambiguous checkpoint formula grant');
      if (writes.length) {
        pinned = writes[0].args;
        if (!exactKeys(pinned,[...keys,'before','after']) || !sameScope(pinned)) throw Error('checkpoint outside sheet scope');
        spec(pinned);
        baseline = pinned.before;
      }
    } else {
      const current = await read(scope,scope.title,pos.cell);
      baseline = current.rows[0]?.values?.[0]?.userEnteredValue?.formulaValue;
      if (current.id !== scope.sheetId || typeof baseline !== 'string') throw Error('no scoped formula at provider');
    }
    // A scoped model-generated formula may contain only same-tab cell references,
    // constants and ordinary arithmetic. No functions, names, spills or sheet qualifiers.
    const validAfter = f => {
      if (typeof f !== 'string' || f.length > 4095 || !f.startsWith('=')) return false;
      const expr = f.slice(1);
      const tokens = expr.match(/\$?[A-Z]{1,3}\$?[1-9]\d*|\d+(?:\.\d+)?|[+*/^()-]| +/gi) || [];
      if (tokens.join('') !== expr) return false;
      const parts = tokens.filter(x => x.trim());
      if (parts.some(x=>x.replaceAll('$','').toUpperCase()===pos.cell)) return false;
      let operand = true, depth = 0;
      for (const x of parts) {
        if (operand) {
          if (x === '(') depth++;
          else if (!['+','-'].includes(x)) {
            if (!/^[A-Z0-9$]/i.test(x)) return false;
            operand = false;
          }
        } else if (x === ')') {
          if (--depth < 0) return false;
        } else {
          if (!['+','-','*','/','^'].includes(x)) return false;
          operand = true;
        }
      }
      return !operand && !depth;
    };
    return {details:{description:'Repair the scoped existing cell. Derive after from the task and the observed before formula, using simple same-sheet arithmetic.',scope:{...scope},before:baseline},
      authorizeWrite:request => {
        const a = request.args;
        if (request.target !== target || !exactKeys(a,[...keys,'before','after']) ||
            !sameScope(a) || a.before !== baseline || !validAfter(a.after) || (pinned && pinned.after !== a.after)) return false;
        try { spec(a); } catch { return false; }
        if (!pinned) pinned = {...a};
        return true;
      }};
  }
  async function inspect(a) {
    const s = spec(a);
    // Both checks are provider reads. The hidden sheet contains the pre-image and operation identity.
    const [audit, current] = await Promise.all([
      read(a,s.marker,s.cell+':'+s.end), read(a,a.title,s.cell)]);
    const cell = current.rows[0]?.values?.[0];
    const match = audit.id === a.markerId && current.id === a.sheetId &&
      audit.rows[0]?.values?.[0]?.userEnteredValue?.formulaValue === a.before &&
      audit.rows[1]?.values?.[0]?.userEnteredValue?.stringValue === s.signature &&
      cell?.userEnteredValue?.formulaValue === a.after && !!cell.effectiveValue && !cell.effectiveValue.errorValue;
    return {confirmed:match, receipt:{matched:match}, evidence:{audit:audit.raw,current:current.raw}};
  }
  async function replace(a) {
    const s = spec(a), initial = await read(a,a.title,s.cell);
    if (initial.id !== a.sheetId || initial.rows[0]?.values?.[0]?.userEnteredValue?.formulaValue !== a.before)
      throw Error('formula precondition mismatch');
    // Unique sheet creation fences replays. The provider captures the pre-image *inside* the batch.
    const requests = [
      {addSheet:{properties:{sheetId:a.markerId,title:s.marker,hidden:true,
        gridProperties:{rowCount:a.row+2,columnCount:a.column+1}}}},
      {copyPaste:{source:s.range,destination:{...s.range,sheetId:a.markerId},pasteType:'PASTE_FORMULA'}},
      {updateCells:{start:{sheetId:a.markerId,rowIndex:a.row+1,columnIndex:a.column},
        rows:[{values:[{userEnteredValue:{stringValue:s.signature}}]}],fields:'userEnteredValue'}},
      {findReplace:{range:s.range,find:a.before,replacement:a.after,matchCase:true,
        matchEntireCell:true,searchByRegex:false,includeFormulas:true}}
    ];
    const raw = await batch({spreadsheet_id:a.spreadsheet_id,requests});
    const res = providerData(raw), delta = res.replies?.[3]?.findReplace;
    if (res.spreadsheetId !== a.spreadsheet_id || delta?.formulasChanged !== 1 || delta?.occurrencesChanged !== 1)
      return {matched:false,error:'RECEIPT_CREATED_BUT_FORMULA_CHANGE_NOT_CONFIRMED',initial:initial.raw,requests,raw};
    const proof = await inspect(a);
    return {matched:proof.confirmed,initial:initial.raw,requests,raw,proof};
  }
  return {prepareScope, approvedAdapters:{'sheets.replace_formula':{names:['mcp__Legion__replace_formula'],
    effect:'write',sinkAtomic:true,check:x=>x?.matched===true}},
    bindings:{mcp__Legion__replace_formula:replace},
    verifyWrite:async request => {
      if (request.target !== 'sheets.replace_formula') throw Error('wrong verifier');
      return inspect(request.args);
    }};
}
if (typeof module !== 'undefined') module.exports = {sheetsFormulaAdapter};
