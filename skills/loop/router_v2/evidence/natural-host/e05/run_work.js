// Evaluate runWork in trusted Work code mode with real connectors. The caller
// supplies the pre-authorized immutable scope; task text cannot grant writes.
async function runWork(tools, checkout, session, grant, resume) {
  const base = 'skills/loop/router_v2/';
  const evidence = base + 'evidence/natural-host/e05/';
  const q = s => "'" + s.replaceAll("'", "'\\''") + "'";
  async function shell(cmd) {
    let r = await tools.exec_command({cmd, workdir:checkout, max_output_tokens:20000, yield_time_ms:500});
    let out = r.output || '';
    while (r.session_id && r.exit_code == null) {
      r = await tools.write_stdin({session_id:r.session_id, chars:'', max_output_tokens:20000});
      out += r.output || '';
    }
    if (r.exit_code !== 0) throw Error(out);
    return out;
  }
  async function save(file, value) {
    const data = JSON.stringify(value,null,2);
    for (let i = 0; i < data.length; i+=8192)
      await shell('printf %s ' + q(data.slice(i,i+8192)) + (i ? ' >> ' : ' > ') + q(evidence+file));
  }
  const task = (await shell('cat '+q(evidence+'task.txt'))).trimEnd();
  const work = Function(await shell('cat '+q(base+'work_legion.js'))+'\nreturn workLegion')();
  const calls = [];
  const tracked = new Proxy(tools, {get(object,key) {
    if (typeof key !== 'string' || !key.startsWith('mcp__codex_apps__github_')) return object[key];
    if (typeof object[key] !== 'function') return undefined;
    return async args => {
      const raw = await object[key](args);
      calls.push({tool:key,args,result:raw.structuredContent ?? raw});
      if (!resume && key.endsWith('_update_ref') && !raw.isError) throw Error('INJECTED_ACK_LOSS');
      return raw;
    };
  }});
  const verify = async ({acceptance}) => {
    const info = JSON.parse(await shell(['python3', base+'evidence/natural-host/e04/check_remote.py', grant.branch,
      grant.expected_head, evidence+'expected.mjs', 'e05'].map(q).join(' ')));
    const updates = calls.filter(r => r.tool.endsWith('_update_ref')).length;
    const before = JSON.parse(await shell('cat '+q(evidence+'fault-provider.json')));
    const previous = before.filter(r => r.tool.endsWith('_update_ref')).length;
    const checked = previous === 1 && updates === 0 && info.parents[0] === grant.expected_head && info.assertions === 4;
    return {checks:acceptance.map(a => ({id:a.id,passed:checked,evidence:{...info,updates_before_stop:previous,updates_after_restart:updates}}))};
  };
  const config = {checkout,session,id:'e05',githubGrant:grant,verify};
  if (!resume) config.observeCheckpoint = async state => {
    if (state.status === 'BLOCKED' && state.write_in_flight) throw Error('INJECTED_STOP_AFTER_DURABLE_BLOCK');
  };
  try {
    const result = await work(tracked,config).run(task);
    await save(resume?'recovered.json':'fault-result.json',result);
    return {status:result.status,verification:result.verification};
  } finally {
    await save(resume?'recovery-provider.json':'fault-provider.json',calls);
  }
}
