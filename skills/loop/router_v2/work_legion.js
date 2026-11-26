// Evaluate the trusted checkout's file in Work code mode. All authorizations and
// adapter functions are supplied by the host, outside the task and model output.
function workLegion(tools, config) {
  const {checkout, session} = config;
  if (![checkout, session].every(p => typeof p === "string" && p.startsWith("/"))) {
    throw Error("absolute checkout and private session paths required");
  }
  const base = "skills/loop/router_v2/";
  const quote = s => "'" + String(s).replaceAll("'", "'\\''") + "'";
  async function shell(command) {
    let r = await tools.exec_command({cmd:command, workdir:checkout, yield_time_ms:250, max_output_tokens:100000});
    let output = r.output || "";
    while (r.session_id && r.exit_code == null) {
      r = await tools.write_stdin({session_id:r.session_id, chars:"", yield_time_ms:1000, max_output_tokens:100000});
      output += r.output || "";
    }
    if (r.exit_code !== 0) throw Error(output.slice(-2000));
    return output;
  }
  async function call(script, args, input) {
    const command = ["python3", base + script, ...args].map(quote).join(" ");
    if (input === undefined) return JSON.parse(await shell(command));
    // Keep large receipts out of shell arguments and avoid ARG_MAX. Each caller
    // owns its input file; the shell removes it even if Python fails.
    const tmp = (await shell("mktemp")).trim();
    try {
      const bytes = JSON.stringify(input);
      for (let i = 0; i < bytes.length;) {
        let end = Math.min(i + 12000, bytes.length);
        if (end < bytes.length && /[\uD800-\uDBFF]/.test(bytes[end-1])) end--;
        await shell("printf %s " + quote(bytes.slice(i,end)) + " >> " + quote(tmp));
        i = end;
      }
      return JSON.parse(await shell(command + " < " + quote(tmp)));
    } finally {
      await shell("rm -f -- " + quote(tmp));
    }
  }
  async function load(file, name) {
    const source = await shell("cat -- " + quote(base + file));
    return Function(source + "\nreturn " + name)();
  }
  return {async run(task) {
    const [host, natural, catalog, saved] = await Promise.all([
      load("legion_host.js","legionHost"), load("natural_host.js","naturalHost"),
      call("work_session.py",["catalog"]), call("work_session.py",["open",session],task)
    ]);
    let generation = saved.generation;
    const checkpoint = async state => {
      generation = await call("work_session.py",["save",session,String(generation)],state);
      if (config.observeCheckpoint) await config.observeCheckpoint(state);
    };
    const extraTools = {...config.extraTools};
    const adapters = {...config.approvedAdapters};
    const info = {...config.capabilityInfo};
    const standard = await load("standard_tools.js","standardLegionTools");
    const standardBindings = await standard(tools,config,call,shell);
    for (const id of Object.keys(standardBindings.adapters)) {
      if (Object.hasOwn(adapters,id)) throw Error("standard adapter cannot be overridden: " + id);
    }
    Object.assign(extraTools,standardBindings.toolBindings);
    Object.assign(adapters,standardBindings.adapters);
    Object.assign(info,standardBindings.details);
    const grants = [];
    if (!Object.hasOwn(adapters,"sql.query_rows")) {
      const name = "mcp__legion__query_rows";
      extraTools[name] = args => call("query_rows.py",[],args);
      adapters["sql.query_rows"] = {effect:"read",names:[name],
        check:data => Array.isArray(data?.rows) && Array.isArray(data?.columns)};
      info["sql.query_rows"] = "Read-only SQLite SELECT over input_rows. Args {rows:[{column:scalar}],sql:string}.";
    }
    function register(adapter, target, details) {
      if (Object.hasOwn(adapters,target)) throw Error("duplicate adapter: " + target);
      Object.assign(extraTools,adapter.tools || adapter.bindings);
      Object.assign(adapters,adapter.approvedAdapters);
      info[target] = details;
      grants.push(adapter);
    }
    if (config.githubGrant || config.githubEditScope) {
      if (config.githubGrant && config.githubEditScope) throw Error("ambiguous GitHub grant");
      const readTree = async sha => {
        if (!/^[a-f0-9]{40}$/.test(sha)) throw Error("invalid Git object");
        return (await shell("git rev-parse --verify " + quote(sha+"^{tree}"))).trim();
      };
      if (config.githubEditScope) {
        const create = await load("github_commit_adapter.js","githubScopedEditAdapter");
        const adapter = await create(tools,config.githubEditScope,{readTree});
        register(adapter,"github.commit_file",adapter.details);
      } else {
        const create = await load("github_commit_adapter.js","githubCommitAdapter");
        register(create(tools,config.githubGrant,{readTree}),"github.commit_file",
          {description:"Commit exact authorized file on an isolated branch.",args:config.githubGrant});
      }
    }
    if (config.sheetGrant && config.sheetScope) throw Error("choose one Sheets grant");
    if (config.sheetGrant || config.sheetScope) {
      const create = await load("sheets_formula.js","sheetsFormulaAdapter");
      const adapter = create(tools,{exclusiveWorkbookIds:config.exclusiveWorkbookIds});
      let details;
      if (config.sheetScope) {
        const prepared = await adapter.prepareScope(config.sheetScope,saved.state);
        adapter.authorizeWrite = prepared.authorizeWrite;
        details = prepared.details;
      } else {
        const expected = Object.entries(config.sheetGrant);
        adapter.authorizeWrite = request => request.target === "sheets.replace_formula" &&
          Object.keys(request.args).length === expected.length &&
          expected.every(([key,value]) => Object.hasOwn(request.args,key) && request.args[key] === value);
        details = {description:"Conditional exact arithmetic formula replacement on an existing cell.",args:config.sheetGrant};
      }
      register(adapter,"sheets.replace_formula",details);
    }
    const runtimeTools = new Proxy(extraTools, {
      get:(local, key) => Object.hasOwn(local,key) ? local[key] : tools[key]
    });
    const authorizeWrite = async (request,state) => {
      if (Object.hasOwn(standardBindings.writeGrants,request.target))
        return standardBindings.writeGrants[request.target].authorizeWrite(request,state);
      const owned = grants.find(g => Object.hasOwn(g.approvedAdapters,request.target));
      if (owned) return owned.authorizeWrite(request);
      return config.authorizeWrite ? config.authorizeWrite(request) : false;
    };
    const verifyWrite = async (request,state) => {
      if (Object.hasOwn(standardBindings.writeGrants,request.target))
        return standardBindings.writeGrants[request.target].verifyWrite(request,state);
      const owned = grants.find(g => Object.hasOwn(g.approvedAdapters,request.target));
      if (owned && await owned.authorizeWrite(request)) return owned.verifyWrite(request);
      return config.verifyWrite ? config.verifyWrite(request) : {confirmed:false};
    };
    const legion = host(runtimeTools,{approvedAdapters:adapters,authorizeWrite,verifyWrite,checkpoint});
    const native = kind => async payload => {
      if (!config.onNativeRequest) return call("native_mailbox.py",["request",session,kind],payload);
      const {id} = await call("native_mailbox.py",["issue",session,kind],payload);
      await config.onNativeRequest({id,kind,session});
      return call("native_mailbox.py",["receive",session,id]);
    };
    return natural(legion,{
      catalog, select:config.select || native("select"),
      analyze:config.analyze || native("analyze"), verify:config.verify || native("verify"),
      readSkill:item => call("work_session.py",["skill",item.path,item.source_sha256]),
      capabilityInfo:info
    }).run(task,{state:saved.state || undefined,id:config.id});
  }};
}
if (typeof module !== "undefined") module.exports = {workLegion};
