/* Legion candidate: native-host tool orchestration. No LLM API and no blanket permission.
 * Evaluate in Work code mode with trusted checkpoint, authorizeWrite, and verifyWrite callbacks.
 * The Work model supplies Plan and completes native Skill steps; this code does not invoke a model.
 */
function legionHost(tools, options = {}) {
  const MAX_STEPS = 12;
  const MAX_PARALLEL = 3;
  const BUILTIN_REGISTRY = {
    "github.get_repo": { names: ["mcp__GitHub__get_repo", "mcp__codex_apps__github_get_repo"], effect: "read", check: d => !!(d?.repository_full_name || d?.full_name) },
    "github.fetch_file": { names: ["mcp__GitHub__fetch_file", "mcp__codex_apps__github_fetch_file"], effect: "read", check: d => typeof d?.content === "string" },
    "github.get_pr_info": { names: ["mcp__GitHub__get_pr_info", "mcp__codex_apps__github_get_pr_info"], effect: "read", check: d => !!(d?.number || d?.pr_number) },
    "github.create_file": { names: ["mcp__GitHub__create_file", "mcp__codex_apps__github_create_file"], effect: "write", check: d => typeof d?.commit_sha === "string" },
    "github.update_file": { names: ["mcp__GitHub__update_file", "mcp__codex_apps__github_update_file"], effect: "write", check: d => typeof d?.commit_sha === "string" },
    "sheets.metadata": { names: ["mcp__Google_Drive__get_spreadsheet_metadata", "mcp__codex_apps__google_drive_get_spreadsheet_metadata"], effect: "read", check: d => typeof d?.spreadsheetId === "string" },
    "sheets.range": { names: ["mcp__Google_Drive__get_spreadsheet_range", "mcp__codex_apps__google_drive_get_spreadsheet_range"], effect: "read", check: d => Array.isArray(d?.values) },
    "sheets.batch_update": { names: ["mcp__Google_Drive__batch_update_spreadsheet", "mcp__codex_apps__google_drive_batch_update_spreadsheet"], effect: "write", check: d => !!(d && typeof d === "object" && (d.spreadsheetId || d.replies)) },
    "parallel.search": { names: ["mcp__Parallel__web_search", "mcp__codex_apps__parallel_web_search"], effect: "read", check: d => Array.isArray(d?.results) },
  };
  // Only the trusted host may inject reviewed adapters; never use Plan/Skill text as a registry.
  const extra = options.approvedAdapters ?? {};
  if (!extra || typeof extra !== "object" || Array.isArray(extra)) throw Error("approvedAdapters must be a trusted host object");
  for (const [id, binding] of Object.entries(extra)) {
    if (!/^[a-z][a-z0-9_.-]{2,80}$/.test(id) || Object.prototype.hasOwnProperty.call(BUILTIN_REGISTRY,id) ||
        !binding || !["read","write"].includes(binding.effect) ||
        !Array.isArray(binding.names) || !binding.names.length ||
        !binding.names.every(n => typeof n === "string" && /^mcp__[a-zA-Z0-9_]+$/.test(n)) ||
        typeof binding.check !== "function") throw Error("unreviewed or invalid host adapter: " + id);
  }
  const REGISTRY = Object.freeze({ ...BUILTIN_REGISTRY, ...extra });
  const known = id => Object.prototype.hasOwnProperty.call(REGISTRY, id);
  const resolve = id => (REGISTRY[id]?.names || []).find(name => typeof tools[name] === "function");
  function validate(plan) {
    if (!plan || typeof plan.id !== "string" || !plan.id.trim() || typeof plan.goal !== "string" || !plan.goal.trim()) throw Error("id and goal required");
    if (!Array.isArray(plan.steps) || !plan.steps.length || plan.steps.length > MAX_STEPS) throw Error("1..12 steps required");
    if (!Array.isArray(plan.acceptance) || !plan.acceptance.length) throw Error("acceptance evidence required");
    const ids = new Set();
    for (const step of plan.steps) {
      if (!step || typeof step.id !== "string" || !/^[\w-]{1,80}$/.test(step.id) || Object.hasOwn(Object.prototype, step.id) || ids.has(step.id)) throw Error("invalid/duplicate step id");
      if (!["tool", "skill"].includes(step.kind) || typeof step.target !== "string" || !step.target || !step.args || typeof step.args !== "object" || Array.isArray(step.args)) throw Error("invalid step");
      if (!Array.isArray(step.depends_on) || step.depends_on.some(id => !ids.has(id)) || new Set(step.depends_on).size !== step.depends_on.length) throw Error("invalid dependency order");
      if (step.kind === "tool" && !known(step.target)) throw Error("tool not allowlisted: " + step.target);
      ids.add(step.id);
    }
    const checks = new Set();
    for (const check of plan.acceptance) {
      if (!check || typeof check.id !== "string" || !/^[\w-]{1,80}$/.test(check.id) || checks.has(check.id) || !Array.isArray(check.evidence_from) || !check.evidence_from.length || check.evidence_from.some(id => !ids.has(id))) throw Error("invalid acceptance");
      checks.add(check.id);
    }
    return plan;
  }
  const snapshot = obj => JSON.parse(JSON.stringify(obj));
  const resultData = response => response?.result ?? response?.structuredContent?.result ?? response?.structuredContent ?? response;
  const receipt = (step, status, detail) => ({ id: step.id, target: step.target, kind: step.kind, status, ...detail });
  function init(plan) { validate(plan); return { version: 1, plan: snapshot(plan), original_plan: snapshot(plan), results: {}, trace: [], status: "PLANNED", trust: "HOST_REPORTED_NOT_INDEPENDENTLY_VERIFIED" }; }
  const capabilities = () => Object.entries(REGISTRY).map(([id, config]) => ({ id, effect: config.effect, available: !!resolve(id) }));
  function ready(state) {
    return state.plan.steps.filter(s => !state.results[s.id] && s.depends_on.every(id => state.results[id]?.status === "SUCCESS"));
  }
  function summary(state) {
    const total = state.plan.steps.length;
    const success = Object.values(state.results).filter(r => r.status === "SUCCESS").length;
    const acceptance = state.plan.acceptance.map(a => ({ id: a.id, status: a.evidence_from.every(id => state.results[id]?.status === "SUCCESS") ? "EVIDENCE_RECORDED" : "NOT_MET", evidence_from: a.evidence_from }));
    return { task_id: state.plan.id, status: state.status, completed: success, total, acceptance, trust: state.trust, failed: Object.values(state.results).filter(r => r.status !== "SUCCESS").map(r => r.id), pending_model: state.pending_model ?? [] };
  }
  async function checkpoint(state) { if (typeof options.checkpoint === "function") await options.checkpoint(snapshot(state)); }
  // Pre-commit authorization/lease checks cannot fence a stale worker. Protect writes at the sink.
  // This conservative gate recognizes sink-side unique creation / conditional update shapes.
  function sinkAtomicWrite(step) {
    const args=step.args, conf=REGISTRY[step.target];
    if (conf.effect!=="write") return true;
    if (step.target==="github.create_file") return typeof args.path==="string" && !!args.path.trim() && typeof args.content==="string";
    if (step.target==="github.update_file") return typeof args.path==="string" && !!args.path.trim() &&
      typeof args.sha==="string" && !!args.sha.trim() && typeof args.content==="string";
    if (step.target==="sheets.batch_update") {
      const reqs=args.requests;
      if (!Array.isArray(reqs) || !reqs.length) return false;
      const props=reqs[0]?.addSheet?.properties;
      if (Object.keys(reqs[0]||{}).length!==1 || !props || !Number.isSafeInteger(props.sheetId) ||
          props.sheetId<0 || typeof props.title!=="string" || !props.title.trim()) return false;
      // The unique sheet and all its cells must be created by ONE atomic provider batch.
      // Updating/appending to an existing sheet, even after a successful lease check, is unsafe.
      return reqs.slice(1).every(r => Object.keys(r||{}).length===1 &&
        r?.updateCells && (r.updateCells.start?.sheetId===props.sheetId ||
          r.updateCells.range?.sheetId===props.sheetId) &&
        Array.isArray(r.updateCells.rows) && typeof r.updateCells.fields==="string");
    }
    // The host must independently review the provider's atomic semantics; task args cannot set this flag.
    return conf.sinkAtomic===true;
  }
  const writeRequest = step => ({ id: step.id, target: step.target, args: snapshot(step.args) });
  async function perform(step, beforeWrite) {
    const conf = REGISTRY[step.target], name = resolve(step.target);
    if (!name) return receipt(step, "BLOCKED", { error: "CAPABILITY_UNAVAILABLE" });
    if (conf.effect === "write") {
      // Approval must be given by trusted host, never inferred from task text or JSON.
      let approved = false;
      try {
        approved = typeof options.authorizeWrite === "function" &&
          await options.authorizeWrite(writeRequest(step));
      } catch {
        return receipt(step, "BLOCKED", { error: "WRITE_AUTHORIZATION_UNAVAILABLE" });
      }
      if (approved !== true) return receipt(step, "BLOCKED", { error: "WRITE_AUTHORIZATION_REQUIRED" });
      if (!sinkAtomicWrite(step)) return receipt(step, "BLOCKED", { error: "SINK_ATOMIC_WRITE_REQUIRED" });
      await beforeWrite();
    }
    try {
      const raw = await tools[name](snapshot(step.args));
      const data = resultData(raw);
      if (raw?.isError || raw?.error || data?.error || !conf.check(data)) return receipt(step, "FAILED", { error: "PROVIDER_ERROR_OR_INVALID_RESPONSE", provider: name, raw });
      return receipt(step, "SUCCESS", { provider: name, raw });
    } catch (err) { return receipt(step, "FAILED", { error: String(err), provider: name, ...(Number.isInteger(err?.status) && {http_status:err.status}) }); }
  }
  // Natural-entry DAGs can bind an argument to a successful predecessor's receipt.
  // Legacy plans retain their literal JSON semantics.
  function materialize(state, step) {
    if (state.natural_entry !== 1) return step;
    function resolveValue(value) {
      if (!value || typeof value !== "object") return value;
      if (Array.isArray(value)) return value.map(resolveValue);
      if (Object.hasOwn(value, "$from")) {
        if (Object.keys(value).length !== 2 || !Array.isArray(value.path) ||
            !step.depends_on.includes(value.$from) || state.results[value.$from]?.status !== "SUCCESS")
          throw Error("invalid predecessor reference");
        let result = state.results[value.$from];
        for (const key of value.path) {
          if ((typeof key !== "string" && !Number.isSafeInteger(key)) || !result ||
              typeof result !== "object" || !Object.hasOwn(result, key)) throw Error("missing receipt field");
          result = result[key];
        }
        return snapshot(result);
      }
      return Object.fromEntries(Object.entries(value).map(([key,item]) => [key, resolveValue(item)]));
    }
    return {...step, args:resolveValue(step.args)};
  }
  function pendingWrite(state) {
    const step = state.plan.steps.find(s => s.id === state.write_in_flight);
    if (!step || step.kind !== "tool" || REGISTRY[step.target].effect !== "write" ||
        !step.depends_on.every(id => state.results[id]?.status === "SUCCESS")) throw Error("invalid pending write");
    return materialize(state, step);
  }
  async function blockUncertainWrite(state, step, prior) {
    state.results[step.id] = receipt(step, "BLOCKED", { error: "WRITE_OUTCOME_UNKNOWN", ...(prior && { prior }) });
    state.trace.push({ event: "WRITE_RECONCILIATION_REQUIRED", step: step.id, status: "BLOCKED" });
    state.status = "BLOCKED";
    state.pending_model = [];
    await checkpoint(state);
    return { state, summary: summary(state) };
  }
  async function advance(state) {
    if (!state || state.version !== 1) throw Error("invalid legion state");
    validate(state.plan);
    if (["FAILED", "BLOCKED", "COMPLETED_UNVERIFIED"].includes(state.status)) return { state, summary: summary(state) };
    if (state.write_in_flight) {
      return blockUncertainWrite(state, pendingWrite(state));
    }
    while (true) {
      const next = ready(state);
      if (!next.length) {
        state.pending_model = [];
        state.status = state.plan.steps.every(s => state.results[s.id]?.status === "SUCCESS") ? "COMPLETED_UNVERIFIED" : "BLOCKED";
        await checkpoint(state);
        return { state, summary: summary(state) };
      }
      const readyTools = next.filter(s => s.kind === "tool");
      const reads = readyTools.filter(s => REGISTRY[s.target].effect === "read");
      const toolSteps = (reads.length ? reads.slice(0, MAX_PARALLEL) : readyTools.slice(0, 1));
      if (toolSteps.length) {
        const responses = await Promise.all(toolSteps.map(step => perform(materialize(state, step), async () => {
          state.write_in_flight = step.id;
          await checkpoint(state);
        })));
        for (const r of responses) {
          state.results[r.id] = r;
          state.trace.push({ event: "EXECUTED", step: r.id, status: r.status, provider: r.provider ?? null });
        }
        if (state.write_in_flight && responses[0].status === "FAILED") {
          return blockUncertainWrite(state, toolSteps[0], responses[0]);
        }
        delete state.write_in_flight;
        const halted = responses.find(r => r.status === "FAILED") ?? responses.find(r => r.status === "BLOCKED");
        if (halted) {
          state.status = halted.status === "BLOCKED" ? "BLOCKED" : "FAILED";
          state.pending_model = [];
        }
        await checkpoint(state);
        if (halted) return { state, summary: summary(state) };
        continue;
      }
      const model = next.filter(s => s.kind === "skill");
      state.status = "AWAITING_MODEL";
      state.pending_model = model.map(s => ({ id: s.id, target: s.target, args: s.args, depends_on: s.depends_on }));
      await checkpoint(state);
      return { state, summary: summary(state) };
    }
  }
  async function reconcileWrite(state) {
    if (!state || state.version !== 1 || !state.write_in_flight) throw Error("no uncertain write to reconcile");
    validate(state.plan);
    const step = pendingWrite(state);
    const prior = state.results[step.id];
    if (state.status !== "BLOCKED" || prior?.error !== "WRITE_OUTCOME_UNKNOWN") throw Error("advance the interrupted checkpoint before reconciliation");
    if (typeof options.verifyWrite !== "function") throw Error("trusted write verifier required");

    const proof = await options.verifyWrite(writeRequest(step));
    const observed = proof?.receipt;
    if (proof?.confirmed !== true || !proof.evidence || typeof proof.evidence !== "object" ||
        !Object.keys(proof.evidence).length || observed?.error || !REGISTRY[step.target].check(observed)) {
      return { state, summary: summary(state) };
    }
    const resumed = snapshot(state);
    resumed.results[step.id] = receipt(step, "SUCCESS", {
      reconciliation: snapshot({ receipt: observed, evidence: proof.evidence, prior }),
    });
    resumed.trace.push({ event: "WRITE_RECONCILED", step: step.id, status: "SUCCESS" });
    delete resumed.write_in_flight;
    resumed.status = "RUNNING";
    await checkpoint(resumed);
    return advance(resumed);
  }
  async function finishSkills(state, answers) {
    if (state.status !== "AWAITING_MODEL" || !Array.isArray(answers) || !answers.length ||
        new Set(answers.map(item => item.id)).size !== answers.length) throw Error("skill step is not pending");
    for (const {id, output, source} of answers) {
      if (!state.pending_model?.some(step => step.id === id)) throw Error("skill step is not pending");
      if (typeof output !== "string" || !output.trim() || typeof source !== "string" || !source.trim())
        throw Error("nonempty model output and source required");
    }
    for (const {id, output, source} of answers) {
      const step = state.plan.steps.find(item => item.id === id);
      state.results[id] = receipt(step, "SUCCESS", { model_output: output, source, self_reported: true });
      state.trace.push({ event: "MODEL_STEP_RECORDED", step: id, status: "SUCCESS" });
    }
    state.status = "RUNNING";
    state.pending_model = [];
    await checkpoint(state);
    return advance(state);
  }
  async function finishSkill(state, id, output, source) {
    return finishSkills(state, [{id, output, source}]);
  }
  async function retryRead(state, id, correctedArgs, reason) {
    if (!state || state.write_in_flight || !["FAILED", "BLOCKED"].includes(state.status)) throw Error("retry requires failed or blocked state without an uncertain write");
    const step = state.plan.steps.find(s => s.id === id);
    const prior = state.results[id];
    if (!step || step.kind !== "tool" || REGISTRY[step.target].effect !== "read" ||
        !prior || !["FAILED", "BLOCKED"].includes(prior.status) || state.retry_counts?.[id]) throw Error("only one retry of a failed read is allowed");
    if (!reason || typeof reason !== "string" || !reason.trim() ||
        !correctedArgs || typeof correctedArgs !== "object" || Array.isArray(correctedArgs)) throw Error("retry requires reason and corrected args object");
    const nextArgs = { ...step.args, ...snapshot(correctedArgs) };
    for (const key of ["repository_full_name", "repo_full_name", "repository_id", "repository_url", "spreadsheet_id", "spreadsheet_url"]) {
      if (nextArgs[key] !== step.args[key]) throw Error("retry cannot change resource identity: " + key);
    }
    state.retry_counts = { ...(state.retry_counts ?? {}), [id]: 1 };
    state.retry_history = { ...(state.retry_history ?? {}), [id]: prior };
    state.trace.push({ event: "READ_RETRY_REQUESTED", step: id, reason, prior_status: prior.status });
    step.args = nextArgs;
    delete state.results[id];
    state.status = "RUNNING";
    await checkpoint(state);
    return advance(state);
  }
  return { init, advance, retryRead, reconcileWrite, finishSkill, finishSkills, capabilities, summary, save: checkpoint,
    hasCheckpoint: () => typeof options.checkpoint === "function",
    hasWriteVerifier: () => typeof options.verifyWrite === "function" };
}
if (typeof module !== "undefined") module.exports = { legionHost };
