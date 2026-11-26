// Trusted capabilities for the standard Work entry. Resource grants are host configuration.
async function standardLegionTools(tools, config, call, shell) {
  const toolBindings = {}, adapters = {}, details = {};
  const writeGrants = {};
  function register(id, effect, dispatch, check, description) {
    const name = "mcp__legion__" + id.replaceAll(".", "_");
    toolBindings[name] = dispatch;
    adapters[id] = {effect,names:[name],check,...(effect === "write" && {sinkAtomic:true})};
    details[id] = description;
  }
  const data = raw => {
    if (raw?.isError || raw?.error) throw Error("spreadsheet provider error");
    return raw?.structuredContent ?? raw;
  };
  const exactKeys = (o, keys) => !!o && Object.keys(o).length === keys.length && keys.every(k => Object.hasOwn(o,k));
  const rawProof = (receipt,evidence) => ({confirmed:true,receipt,evidence});

  if (config.xlsxGrant) {
    const {source, destination} = config.xlsxGrant;
    if (![source,destination].every(p => typeof p === "string" && p.startsWith("/") && p.endsWith(".xlsx")) ||
        source === destination) throw Error("xlsxGrant requires distinct absolute input and output paths");
    if ((await shell("python3 -c 'import importlib.util; print(int(importlib.util.find_spec(\"openpyxl\") is not None))'")).trim() === "1") {
      const write = "xlsx.holdings";
      const allowed = args => exactKeys(args,["sheet","columns","window_minutes"]) &&
        typeof args.sheet === "string" && args.columns && typeof args.columns === "object" &&
        Number.isInteger(args.window_minutes) && args.window_minutes >= 1 && args.window_minutes <= 1440;
      writeGrants[write] = {
        authorizeWrite:({args}) => allowed(args),
        verifyWrite: async ({args}) => {
          try {
            const found = await call("xlsx_fifo.py",["report",source,destination],args);
            return rawProof(found,{file:destination,sha256:found.sha256,request_sha256:found.request_sha256});
          } catch { return {confirmed:false}; }
        }
      };
      const input = await call("xlsx_fifo.py",["inspect",source]);
      register(write,"write",args => {
        if (!allowed(args)) throw Error("invalid scoped XLSX request");
        return call("xlsx_fifo.py",["build",source,destination],args);
      }, d => d?.file === destination && d.charts === 1 && /^[a-f0-9]{64}$/.test(d.sha256),
      {description:"Create one Excel copy with native FIFO chart. Use actual source headers. Args {sheet, columns:{id,pair,time,side,quantity},window_minutes}. Only fixed grant paths are used.",input,destination});
    }
  }

  register("ats.verify_greenhouse","read",args => call("greenhouse_jobs.py",[],args),
    d => Array.isArray(d?.roles) && Array.isArray(d?.attempts),
    "Verify currently listed Greenhouse jobs against their own live application schema. Args {results:[{url}], titles:[substring], locations:[substring], responsibilities:[substring], limit:integer, exclude_titles?:[substring]}. Supply results from a completed search by predecessor reference. Exclude adjacent job families using exclude_titles when title phrases alone are ambiguous.");
  const scope = config.radarGrant;
  if (scope) {
    const {spreadsheet_id,sheetId,title,minRows,maxRows} = scope;
    if (!/^[\w-]+$/.test(spreadsheet_id ?? "") || !Number.isInteger(sheetId) || sheetId < 0 ||
        sheetId > 2147483647 || typeof title !== "string" || !/^[a-zA-Z0-9_ -]{1,70}$/.test(title) ||
        !Number.isInteger(minRows) || !Number.isInteger(maxRows) || minRows < 1 || maxRows < minRows || maxRows > 15)
      throw Error("invalid radarGrant");
    const range = {spreadsheet_id,sheet_name:title,range:"A1:F" + (maxRows+1),value_render_option:"UNFORMATTED_VALUE"};
    const sourceStep = (args,state) => {
      if (!state || !exactKeys(args,["verification_step"]) || typeof args.verification_step !== "string") return null;
      const step = state.plan.steps.find(s => s.id === args.verification_step);
      const result = state.results[args.verification_step];
      if (step?.target !== "ats.verify_greenhouse" || result?.status !== "SUCCESS" || !Array.isArray(result.raw?.roles))
        return null;
      return result.raw;
    };
    function rows(args,state) {
      const verified = sourceStep(args, state);
      if (!verified) return null;
      const unique = new Map(verified.roles.map(role => [role.url,role]));
      if (unique.size < minRows || unique.size > maxRows) return null;
      return [["Employer board","Role","Eligible locations","Official application","Responsibilities","Checked UTC"],
        ...Array.from(unique.values(),r => [r.board,r.title,r.location,r.url,r.duty_excerpt,verified.checked_at])];
    }
    const write = "ats.publish_radar";
    const authorized = (request,state) => !!state?.plan.steps.find(step => step.id === request.id)?.depends_on.includes(request.args.verification_step) && !!rows(request.args,state);
    const read = async () => data(await tools.mcp__codex_apps__google_drive_get_spreadsheet_range(range));
    if (typeof tools.mcp__codex_apps__google_drive_get_spreadsheet_range === "function" &&
        typeof tools.mcp__codex_apps__google_drive_batch_update_spreadsheet === "function" &&
        typeof tools.mcp__codex_apps__google_drive_get_spreadsheet_metadata === "function") {
      writeGrants[write] = {
        authorizeWrite:authorized,
        verifyWrite: async ({args},state) => {
          const expected = rows(args,state);
          if (!expected) return {confirmed:false};
          try {
            const observed = await read();
            if (JSON.stringify(observed.values) !== JSON.stringify(expected)) return {confirmed:false};
            const meta = data(await tools.mcp__codex_apps__google_drive_get_spreadsheet_metadata({spreadsheet_id}));
            if (!meta.sheets?.some(s=>s.properties?.sheetId===sheetId&&s.properties?.title===title))
              return {confirmed:false};
            const proof={spreadsheetId:spreadsheet_id,sheetId,values:observed.values};
            return rawProof(proof,proof);
          } catch { return {confirmed:false}; }
        }
      };
      register(write,"write",async (args,state) => {
        const values = rows(args,state);
        if (!values) throw Error("insufficient verified jobs");
        const requests = [
          {addSheet:{properties:{sheetId,title,gridProperties:{frozenRowCount:1}}}},
          {updateCells:{start:{sheetId,rowIndex:0,columnIndex:0},
            rows:values.map(row=>({values:row.map(v=>({userEnteredValue:{stringValue:v}}))})),fields:"userEnteredValue"}}
        ];
        const receipt = data(await tools.mcp__codex_apps__google_drive_batch_update_spreadsheet({spreadsheet_id,requests}));
        if (receipt.spreadsheetId !== spreadsheet_id || receipt.replies?.[0]?.addSheet?.properties?.sheetId !== sheetId)
          throw Error("sheet creation receipt is incomplete");
        return {spreadsheetId:spreadsheet_id,sheetId,values};
      },d => d?.spreadsheetId === spreadsheet_id && d.sheetId === sheetId && Array.isArray(d.values),
      {description:"Create only the authorized radar tab from actual ATS verification. Args {verification_step: step ID}. Declare that ATS tool as a direct dependency. Does not accept job rows from the model. Use sheets.range for an independent readback.",scope,readback:range});
      adapters[write].requiresState = true;
    }
  }
  return {toolBindings,adapters,details,writeGrants};
}
if (typeof module !== "undefined") module.exports = {standardLegionTools};
