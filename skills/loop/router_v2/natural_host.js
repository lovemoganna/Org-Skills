// Host capabilities are injected by trusted Work code, never by the task or Skill.
function naturalHost(legion, bindings) {
  const catalog = new Map();
  for (const item of bindings.catalog) {
    if (!item?.name || !item.path || catalog.has(item.name)) throw Error("invalid Skill catalog");
    catalog.set(item.name, item);
  }
  const clone = value => JSON.parse(JSON.stringify(value));
  const available = legion.capabilities().filter(tool => tool.available).map(tool => {
    const info = bindings.capabilityInfo?.[tool.id];
    return info === undefined ? tool : {...tool, details:clone(info)};
  });
  const registry = new Map(available.map(tool => [tool.id, tool]));
  function compile(task, selection, id) {
    if (!Array.isArray(selection?.actions) || !selection.actions.length || selection.actions.length > 12)
      throw Error("selection must contain 1..12 actions");
    const actions = selection.actions.map(action => ({
      id: action.id, kind: action.kind, target: action.target,
      args: action.args ?? {}, depends_on: action.depends_on ?? []
    }));
    const ids = new Set(actions.map(action => action.id));
    if (ids.size !== actions.length) throw Error("duplicate action id");
    for (const action of actions) {
      if (action.kind === "skill" && !catalog.has(action.target)) throw Error("unknown Skill: " + action.target);
      if (action.kind === "tool" && !registry.has(action.target)) throw Error("unavailable tool: " + action.target);
      if (!Array.isArray(action.depends_on) || action.depends_on.some(dep => !ids.has(dep))) throw Error("unknown dependency");
      if (action.kind === "tool" && registry.get(action.target).effect === "write" && !legion.hasCheckpoint())
        throw Error("writes require a durable host checkpoint");
    }
    const steps = [];
    const emitted = new Set();
    while (steps.length < actions.length) {
      const next = actions.find(action => !emitted.has(action.id) && action.depends_on.every(dep => emitted.has(dep)));
      if (!next) throw Error("cyclic dependencies");
      steps.push(next);
      emitted.add(next.id);
    }
    const acceptance = selection.acceptance;
    const state = legion.init({id, goal: task, steps, acceptance});
    // All actions must contribute, directly or transitively, to an acceptance check.
    const covered = new Set(acceptance.flatMap(check => check.evidence_from));
    for (const action of [...steps].reverse()) {
      if (covered.has(action.id)) for (const dep of action.depends_on) covered.add(dep);
    }
    if (covered.size !== steps.length) throw Error("unaccounted action");
    const skills = steps.filter(step => step.kind === "skill");
    state.natural_entry = 1;
    state.selected_skills = Object.fromEntries(skills.map(step => [step.target,clone(catalog.get(step.target))]));
    state.route = skills.length === 0 ? "direct" : skills.length === 1 ? "single_skill"
      : skills.every((skill, i) => !i || skill.depends_on.includes(skills[i-1].id)) ? "fixed_chain" : "dynamic_chain";
    return state;
  }
  function accepted(proof, criteria) {
    if (!Array.isArray(proof?.checks) || proof.checks.length !== criteria.length) return false;
    return criteria.every(criterion => proof.checks.some(check =>
      check?.id === criterion.id && check.passed === true && check.evidence &&
      typeof check.evidence === "object" && !Array.isArray(check.evidence) && Object.keys(check.evidence).length > 0));
  }
  function transientRead(state) {
    for (const step of state.plan.steps) {
      const result = state.results[step.id];
      if (registry.get(step.target)?.effect !== "read" || result?.status !== "FAILED" ||
          state.retry_counts?.[step.id]) continue;
      const rawError = result.raw?.error ?? result.raw?.structuredContent?.error;
      const http = result.http_status ?? rawError?.status ?? rawError?.statusCode ?? result.raw?.status;
      if ([408, 429, 500, 502, 503, 504].includes(http) ||
          /\b(ETIMEDOUT|ECONNRESET|EAI_AGAIN)\b/.test(result.error)) {
        // Defer to the provider when it requests a longer backoff.
        const delay = rawError?.retry_after ?? result.raw?.headers?.["retry-after"];
        if (delay != null && (!Number.isFinite(Number(delay)) || Number(delay) < 0 || Number(delay) > 60)) continue;
        return {step, delay:Number(delay ?? 0), reason: `transient read failure: ${http ?? result.error}`};
      }
    }
  }
  async function run(task, options = {}) {
    if (typeof task !== "string" || !task.trim()) throw Error("natural-language task required");
    let state = options.state;
    if (state) {
      if (state.natural_entry !== 1 || state.plan.goal !== task) throw Error("task does not match checkpoint");
    } else {
      const selection = await bindings.select({task, skills: [...catalog.values()], tools: available});
      if (selection?.blocked) return {status:"BLOCKED", reason: String(selection.blocked)};
      state = compile(task, selection, options.id ?? "legion");
      await legion.save(state);
    }
    let execution = await legion.advance(state);
    const reconciled = new Set();
    for (;;) {
      state = execution.state;
      if (state.status === "BLOCKED" && state.write_in_flight && !reconciled.has(state.write_in_flight) && legion.hasWriteVerifier()) {
        reconciled.add(state.write_in_flight);
        execution = await legion.reconcileWrite(state);
        continue;
      }
      if (["BLOCKED","FAILED"].includes(state.status) && !state.write_in_flight) {
        const retry = transientRead(state);
        if (retry) {
          if (retry.delay) await new Promise(resolve => setTimeout(resolve,retry.delay * 1000));
          execution = await legion.retryRead(state,retry.step.id,{},retry.reason);
          continue;
        }
      }
      if (state.status !== "AWAITING_MODEL") break;
      const ready = state.pending_model.slice(0,3);
      const answers = await Promise.all(ready.map(async step => {
        const skill = state.selected_skills?.[step.target] ?? catalog.get(step.target);
        if (!skill || !catalog.has(step.target)) throw Error("unavailable Skill in checkpoint");
        const instructions = await bindings.readSkill(skill);
        if (typeof instructions !== "string" || !instructions.trim()) throw Error("missing Skill instructions");
        const inputs = Object.fromEntries(step.depends_on.map(id => [id,clone(state.results[id])]));
        const answer = await bindings.analyze({task,skill,instructions,step:clone(step),inputs});
        if (answer?.blocked) return {blocked:String(answer.blocked)};
        if (typeof answer?.output !== "string" || !answer.output.trim() ||
            typeof answer.source !== "string" || !answer.source.trim() ||
            [instructions.trim(), step.target, task.trim()].includes(answer.output.trim())) throw Error("invalid native Skill result");
        const source = [skill.path,skill.source_sha256].filter(Boolean).join("@") + " | " + answer.source;
        return {id:step.id,output:answer.output,source};
      }));
      const blocked = answers.find(item => item.blocked);
      if (blocked) return {status:"BLOCKED",reason:blocked.blocked,route:state.route,state,summary:execution.summary};
      if (answers.length === 1) {
        const {id,output,source} = answers[0];
        execution = await legion.finishSkill(state,id,output,source);
      } else {
        execution = await legion.finishSkills(state,answers);
      }
    }
    const result = {state, route:state.route, summary:execution.summary, status:state.status};
    if (state.status !== "COMPLETED_UNVERIFIED") return result;
    if (typeof bindings.verify !== "function") return {...result, status:"NOT_VERIFIED"};
    const verification = await bindings.verify({task,state:clone(state),acceptance:clone(state.plan.acceptance)});
    return {...result, status:accepted(verification,state.plan.acceptance) ? "VERIFIED" : "NOT_VERIFIED", verification};
  }
  return {run};
}
if (typeof module !== "undefined") module.exports = {naturalHost};
