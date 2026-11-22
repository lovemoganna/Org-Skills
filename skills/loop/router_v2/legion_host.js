/* Legion candidate: native-host tool orchestration. No LLM API and no blanket permission.
 * Evaluate this file in Work code mode and call legionHost(tools, {checkpoint, authorizeWrite}).
 * The Work model supplies Plan and completes native Skill steps; this code does not invoke a model.
 */
function legionHost(tools, options = {}) {
  const MAX_STEPS = 12;
  const MAX_PARALLEL = 3;
  const REGISTRY = Object.freeze({
    "github.get_repo": { names: ["mcp__GitHub__get_repo"], effect: "read", check: d => !!d?.repository_full_name },
    "github.fetch_file": { names: ["mcp__GitHub__fetch_file", "mcp__codex_apps__github_fetch_file"], effect: "read", check: d => typeof d?.content === "string" },
    "github.get_pr_info": { names: ["mcp__GitHub__get_pr_info", "mcp__codex_apps__github_get_pr_info"], effect: "read", check: d => !!(d?.number || d?.pr_number) },
    "github.create_file": { names: ["mcp__GitHub__create_file"], effect: "write", check: d => typeof d?.commit_sha === "string" },
    "github.update_file": { names: ["mcp__GitHub__update_file"], effect: "write", check: d => typeof d?.commit_sha === "string" },
    "sheets.metadata": { names: ["mcp__Google_Drive__get_spreadsheet_metadata"], effect: "read", check: d => typeof d?.spreadsheetId === "string" },
    "sheets.range": { names: ["mcp__Google_Drive__get_spreadsheet_range"], effect: "read", check: d => Array.isArray(d?.values) },
    "sheets.batch_update": { names: ["mcp__Google_Drive__batch_update_spreadsheet"], effect: "write", check: d => !!(d && typeof d === "object" && (d.spreadsheetId || d.replies)) },
    "parallel.search": { names: ["mcp__Parallel__web_search"], effect: "read", check: d => Array.isArray(d?.results) },
  });
  const known = id => Object.prototype.hasOwnProperty.call(REGISTRY, id);
  const resolve = id => (REGISTRY[id]?.names || []).find(name => typeof tools[name] === "function");
  function validate(plan) {
    if (!plan || typeof plan.id !== "string" || !plan.id.trim() || typeof plan.goal !== "string" || !plan.goal.trim()) throw Error("id and goal required");
    if (!Array.isArray(plan.steps) || !plan.steps.length || plan.steps.length > MAX_STEPS) throw Error("1..12 steps required");
    if (!Array.isArray(plan.acceptance) || !plan.acceptance.length) throw Error("acceptance evidence required");
    const ids = new Set();
    for (const step of plan.steps) {
      if (!step || typeof step.id !== "string" || !/^[\w-]{1,80}$/.test(step.id) || ids.has(step.id)) throw Error("invalid/duplicate step id");
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
  function init(plan) { validate(plan); return { version: 1, plan: snapshot(plan), results: {}, trace: [], status: "PLANNED", trust: "HOST_REPORTED_NOT_INDEPENDENTLY_VERIFIED" }; }
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
  async function perform(step) {
    const conf = REGISTRY[step.target], name = resolve(step.target);
    if (!name) return receipt(step, "BLOCKED", { error: "CAPABILITY_UNAVAILABLE" });
    if (conf.effect === "write") {
      // Approval must be given by trusted host, never inferred from task text or JSON.
      const approved = typeof options.authorizeWrite === "function" ? await options.authorizeWrite({ id: step.id, target: step.target, args: snapshot(step.args) }) : false;
      if (approved !== true) return receipt(step, "BLOCKED", { error: "WRITE_AUTHORIZATION_REQUIRED" });
    }
    try {
      const raw = await tools[name](snapshot(step.args));
      const data = resultData(raw);
      if (raw?.isError || raw?.error || data?.error || !conf.check(data)) return receipt(step, "FAILED", { error: "PROVIDER_ERROR_OR_INVALID_RESPONSE", provider: name, raw });
      return receipt(step, "SUCCESS", { provider: name, raw });
    } catch (err) { return receipt(step, "FAILED", { error: String(err), provider: name }); }
  }
  async function advance(state) {
    if (!state || state.version !== 1) throw Error("invalid legion state");
    validate(state.plan);
    if (["FAILED", "BLOCKED", "COMPLETED_UNVERIFIED"].includes(state.status)) return { state, summary: summary(state) };
    while (true) {
      const next = ready(state);
      if (!next.length) {
        state.pending_model = [];
        state.status = state.plan.steps.every(s => state.results[s.id]?.status === "SUCCESS") ? "COMPLETED_UNVERIFIED" : "BLOCKED";
        await checkpoint(state);
        return { state, summary: summary(state) };
      }
      const toolSteps = next.filter(s => s.kind === "tool").slice(0, MAX_PARALLEL);
      if (toolSteps.length) {
        // Independent tool calls run concurrently; result storage is serialized to avoid lost updates.
        const responses = await Promise.all(toolSteps.map(perform));
        for (const r of responses) {
          state.results[r.id] = r;
          state.trace.push({ event: "EXECUTED", step: r.id, status: r.status, provider: r.provider ?? null });
          await checkpoint(state);
        }
        const halted = responses.find(r => r.status !== "SUCCESS");
        if (halted) {
          state.status = halted.status === "BLOCKED" ? "BLOCKED" : "FAILED";
          state.pending_model = [];
          await checkpoint(state);
          return { state, summary: summary(state) };
        }
        continue;
      }
      const model = next.filter(s => s.kind === "skill");
      state.status = "AWAITING_MODEL";
      state.pending_model = model.map(s => ({ id: s.id, target: s.target, args: s.args, depends_on: s.depends_on }));
      await checkpoint(state);
      return { state, summary: summary(state) };
    }
  }
  async function finishSkill(state, id, output, source) {
    if (state.status !== "AWAITING_MODEL" || !state.pending_model?.some(s => s.id === id)) throw Error("skill step is not pending");
    if (typeof output !== "string" || !output.trim() || typeof source !== "string" || !source.trim()) throw Error("nonempty model output and source required");
    const step = state.plan.steps.find(s => s.id === id);
    state.results[id] = receipt(step, "SUCCESS", { model_output: output, source, self_reported: true });
    state.trace.push({ event: "MODEL_STEP_RECORDED", step: id, status: "SUCCESS" });
    state.status = "RUNNING";
    state.pending_model = [];
    await checkpoint(state);
    return advance(state);
  }
  return { init, advance, finishSkill, capabilities, summary };
}
if (typeof module !== "undefined") module.exports = { legionHost };
