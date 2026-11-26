// Run inside Work code mode with the real tools object, a trusted checkout, and
// the loaded workLegion function. No provider responses are fixtures.
async function runPrSql({task, tools, checkout, session, workLegion}) {
  const calls = [];
  const quote = value => "'" + String(value).replace(/'/g, "'\\''") + "'";
  async function shell(command) {
    let result = await tools.exec_command({workdir: checkout, cmd: command, max_output_tokens: 10000});
    let output = result.output;
    while (result.session_id && result.exit_code == null) {
      result = await tools.write_stdin({session_id: result.session_id, chars: "", max_output_tokens: 10000});
      output += result.output;
    }
    if (result.exit_code !== 0) throw Error(output);
    return output;
  }
  const sqlName = "mcp__legion__query_rows";
  const githubName = "mcp__codex_apps__github_get_pr_info";
  const bindings = {
    [githubName]: async args => {
      const raw = await tools[githubName](args);
      calls.push({name: githubName, args, raw});
      return raw;
    },
    [sqlName]: async ({rows, sql}) => {
      const json = JSON.stringify({rows, sql});
      if (json.length > 60_000) throw Error("shell bridge payload exceeds 60000 characters");
      const command = "printf '%s' " + quote(json) + " | python3 skills/loop/router_v2/query_rows.py";
      const result = JSON.parse(await shell(command));
      calls.push({name: sqlName, args: {rows, sql}, result});
      return result;
    }
  };
  const adapters = {"sql.query_rows": {effect: "read", names: [sqlName],
    check: data => Array.isArray(data?.rows) && Array.isArray(data?.columns)}};
  const repo = task.match(/\b([\w.-]+\/[\w.-]+)\b/)?.[1];
  const nums = [...new Set(Array.from(task.matchAll(/#(\d+)\b/g), match => +match[1]))];
  const measure = /排名|排序/.test(task) ? "ranking" : /合计|汇总/.test(task) ? "totals" : null;
  if (!repo || !nums.length || !measure) throw Error("no independent verifier for task");
  const scope = {repo, nums, measure};
  // Independent read path: recompute metrics from immutable git objects using
  // Git's own numstat, without using the provider-reported numeric statistics.
  const originals = [];
  async function verify({acceptance}) {
    for (const number of scope.nums) {
      const info = calls.find(c => c.name === githubName && c.args.pr_number === number && c.args.repository_full_name === repo)?.raw?.structuredContent;
      if (!info || ![info.base_sha,info.head_sha].every(s => /^[0-9a-f]{40}$/.test(s))) throw Error("invalid commit provenance");
      const spec = info.base_sha + "..." + info.head_sha;
      const raw = await shell("git diff --no-ext-diff --numstat " + spec);
      const lines = raw.trimEnd().split("\n").filter(Boolean);
      let additions = 0, deletions = 0;
      for (const line of lines) {
        const [a,d] = line.split("\t");
        // Binary changes are included in changed_files and count as zero lines.
        if (a === "-" && d === "-") continue;
        if (!/^\d+$/.test(a) || !/^\d+$/.test(d)) throw Error("unexpected numstat");
        additions += +a;
        deletions += +d;
      }
      originals.push({number, spec, raw, additions, deletions, changed_files: lines.length});
    }
    const expected = scope.measure === "ranking" ? originals.map(r => ({
      number: r.number, churn: r.additions + r.deletions
    })).sort((a,b) => b.churn - a.churn || a.number - b.number) : [{
      pr_count: originals.length, file_appearances: originals.reduce((n,r) => n+r.changed_files,0),
      additions: originals.reduce((n,r) => n+r.additions,0), deletions: originals.reduce((n,r) => n+r.deletions,0)
    }];
    const actual = calls.find(c => c.name === sqlName)?.result?.rows;
    return {checks:[{id:acceptance[0].id,passed:acceptance.length === 1 && JSON.stringify(actual)===JSON.stringify(expected),
      evidence:{expected, actual, refs: originals.map(r=>r.spec)}}]};
  }
  const host = workLegion(tools, {checkout, session, extraTools: bindings,
    approvedAdapters: adapters, verify, capabilityInfo: {"sql.query_rows":
      "Read-only SQLite on ephemeral input_rows table. Args {rows:[{column:scalar}],sql:select}. Use dependency references {$from:stepId,path:['raw','structuredContent',field]}. Returns rows."}});
  const outcome = await host.run(task);
  return {task, scope, calls, independent_git_reads: originals, outcome};

}
if (typeof module !== "undefined") module.exports = {runPrSql};
