// Contract test with fixture responses; no connector or model is invoked.
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const { mkdtempSync, readFileSync, rmSync } = require("node:fs");
const { tmpdir } = require("node:os");
const { join } = require("node:path");
const { runInThisContext } = require("node:vm");

const driver = runInThisContext(
  readFileSync(join(__dirname, "work_host.js"), "utf8") + "\nworkHost;"
);
const root = join(__dirname, "../../..");
const shell = ({ cmd }) => {
  const result = spawnSync("bash", ["-c", cmd], { cwd: root, encoding: "utf8" });
  return { exit_code: result.status, output: result.stdout + result.stderr };
};

async function main() {
  const folder = mkdtempSync(join(tmpdir(), "router-work-contract-"));
  try {
    const tool = {
      id: "read", kind: "tool", target: "github.fetch_file",
      args: { repository_full_name: "owner/repo", path: "README.md", ref: "commit" },
    };
    const skill = { id: "apply", kind: "skill", target: "loop", args: {} };
    let response = { structuredContent: {} };
    const host = driver({
      exec_command: shell,
      mcp__codex_apps__github_fetch_file: async () => response,
    }, root);
    const run = async (name, step) => {
      const plan = join(folder, name + ".json");
      const session = join(folder, name);
      await host.save(plan, {
        id: name, goal: "contract", steps: [step],
        acceptance: [{ id: "observed", evidence_from: [step.id] }],
      });
      await host.init(session, plan);
      return [session, await host.advance(session)];
    };
    const [failed, state] = await run("empty", tool);
    assert.equal(state.status, "FAILED");
    assert.match(readFileSync(join(failed, "read-1-receipt.json"), "utf8"), /incomplete data/);
    response = { structuredContent: { content: "", sha: "1".repeat(40) } };
    assert.equal((await run("valid", tool))[1].status, "RECEIPTS_RECORDED_UNVERIFIED");

    const [session, { pending_request: request }] = await run("skill", skill);
    await assert.rejects(host.finishSkill(session, request, "generic output"), /versioned source/);
    const source = {
      path: "skills/loop/SKILL.md",
      blob: shell({ cmd: "git hash-object skills/loop/SKILL.md" }).output.trim(),
      ref: shell({ cmd: "git rev-parse HEAD" }).output.trim(),
    };
    await assert.rejects(host.finishSkill(session, request, "fixture", {
      ...source, blob: "2".repeat(40),
    }), /cataloged bytes/);
    assert.equal((await host.finishSkill(session, request, "fixture", source)).status,
                 "RECEIPTS_RECORDED_UNVERIFIED");
    await assert.rejects(host.finishSkill(session, request, "duplicate", source), /pending request/);
    console.log("PASS Work driver contracts: typed read result, source identity, stale Skill output");
  } finally {
    rmSync(folder, { recursive: true, force: true });
  }
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
