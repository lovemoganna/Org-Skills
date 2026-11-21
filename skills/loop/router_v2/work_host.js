// Evaluate this function in Work code mode and supply the current tools object.
// The current Work model handles Skill steps. Only listed reads are dispatched here.
function workHost(tools, checkout) {
  const reads = {
    "github.get_pr_info": "mcp__codex_apps__github_get_pr_info",
    "github.fetch_file": "mcp__codex_apps__github_fetch_file",
    "github.fetch_workflow_run_jobs": "mcp__codex_apps__github_fetch_workflow_run_jobs",
  };
  const quote = (value) => "'" + value.replaceAll("'", "'\\''") + "'";
  const shell = (cmd) => tools.exec_command({ cmd, workdir: checkout, max_output_tokens: 24000 });
  const save = async (path, value) => {
    const body = JSON.stringify(value, null, 2);
    const result = await shell("printf '%s\\n' " + quote(body) + " > " + quote(path));
    if (result.exit_code !== 0) throw new Error(result.output);
  };
  const bridge = async (command, session, args = []) => {
    const result = await shell(
      "python3 skills/loop/router_v2/host_bridge.py " +
      [command, "--session", session, ...args].map(quote).join(" ")
    );
    if (![0, 1].includes(result.exit_code)) throw new Error(result.output);
    return JSON.parse(result.output);
  };
  const record = async (session, request, entry) => {
    const report = session + "/" + request.step_id + "-" + (request.attempt ?? 1) + "-report.json";
    await save(report, {
      ...entry,
      step_id: request.step_id,
      request_sha256: request.request_sha256,
    });
    return bridge("record", session, ["--result", report]);
  };
  const init = (session, planPath) => bridge("init", session, [
    "--plan", planPath, "--skills-root", "skills", "--host-capabilities",
    Object.keys(reads).filter((name) => typeof tools[reads[name]] === "function").join(","),
  ]);
  const advance = async (session) => {
    let state = await bridge("next", session);
    while (state.pending_request?.kind === "tool") {
      const request = state.pending_request;
      const name = reads[request.target];
      if (!name || typeof tools[name] !== "function") return state;
      const receipt = request.step_id + "-" + (request.attempt ?? 1) + "-receipt.json";
      let response;
      let error;
      try {
        response = await tools[name](request.args);
        if (!response?.structuredContent || response.isError ||
            response.structuredContent.error || response.structuredContent.error_code) {
          error = response?.structuredContent?.error ?? response?.content ??
            "Connector did not return structured content";
        }
      } catch (failure) {
        error = String(failure);
      }
      await save(session + "/" + receipt, { tool: name, request, response, error });
      state = await record(session, request, {
        status: error === undefined ? "SUCCESS" : "FAILED",
        receipt_ref: receipt,
        artifact_ref: error === undefined ? receipt : null,
        error: error ?? null,
      });
    }
    return state;
  };
  const finishSkill = async (session, request, output, source) => {
    if (request.kind !== "skill" || typeof output !== "string" || !output.trim()) {
      throw new Error("A native Skill step needs a nonempty output from the Work model");
    }
    const pending = (await bridge("next", session)).pending_request;
    if (pending?.kind !== "skill" || pending.step_id !== request.step_id ||
        pending.request_sha256 !== request.request_sha256 || pending.target !== request.target) {
      throw new Error("Skill output does not match the pending request");
    }
    const filename = request.step_id + "-skill-output.json";
    await save(session + "/" + filename, {
      request, source, executor: "current Work model", output,
    });
    return record(session, request, {
      status: "SUCCESS", receipt_ref: filename, artifact_ref: filename,
    });
  };
  return {
    init, advance, finishSkill, save,
    retryRead: (session, step, path, reason) => bridge("retry-read", session,
      ["--step", step, "--path", path, "--reason", reason]),
  };
}
