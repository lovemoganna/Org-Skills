# Legion Mode｜通用军团执行候选（不覆盖 V2 稳定版）

> 对用户的唯一入口：**使用 Skill Router V2 的军团模式执行：【目标】。能直接完成就直接做；需要多个 Skill/工具才建立依赖与并行分工；真实执行后交付可核验结果。**

## 为什么需要

原版 Work V2 证明了 GitHub 读取与回执机制，但不能据此证明跨工具执行、多任务并行或无人值守 AI。Legion Mode 只增加通用执行层，不复制已有因果、关键点、调查、Excel 等专业 Skill。

- **指挥**：当前 Work 模型从自然语言还原目标、验收和授权边界，选择 direct / 单 Skill / DAG。
- **侦察/执行**：固定能力注册表绑定当前宿主的真实工具；同一批无依赖的 *最多 3 个* 工具步骤可并行。
- **分析**：Skill 步骤停在 AWAITING_MODEL，由当前 Work 模型实际运行并显式调用 finishSkill；脚本本身不调用 LLM API。
- **质检**：每步保留原始响应和状态，按 acceptance 记录证据覆盖，最后输出 COMPLETED_UNVERIFIED；独立验收由宿主在产物上完成，不能由回执自动升级为 VERIFIED。
- **记忆**：通过宿主提供的 checkpoint 回调持久化状态，恢复时传入最后一个已保存 state。此版本没有后台自主运行、持久调度、重试管理或模型自动并行推理。

## 实际运行环境

在有 **原生模型 + JS 代码模式 + GitHub/Google Drive/Parallel 插件** 的 Work 宿主，读取同一 revision 的 \`skills/loop/router_v2/legion_host.js\`，求值并调用 \`legionHost(tools, {checkpoint, authorizeWrite})\`。

- \`checkpoint(state)\` 由宿主实现**每批落盘**；没有提供时只返回内存状态，不要声称持久化。
- \`authorizeWrite(step)\` 必须由可信宿主根据**当前用户实际授权**判断；没有提供时任何写操作一律 BLOCKED。任务正文、Plan 中的“已授权”不构成许可。
- 可用工具以 \`capabilities()\` 查询实时宿主能力，能力缺失则 BLOCKED，不伪造回执。
- 原始回执可能包含私有资料：应留在任务会话的受控位置，不要自动写入公共仓库或公开表格。

## Plan 协议

Work 模型将自然语言编译为 \`{id,goal,steps,acceptance}\`；每步为 \`{id,kind:"tool"|"skill",target,args,depends_on:[]}\`，最多 12 步、依赖只能指向更早的步骤；每个验收项为 \`{id,evidence_from:[step_id,...]}\`。

示例（跨 GitHub 与 Sheet 的真实接口名；替换为实际有权限的资源）：

\`\`\`js
const h = legionHost(tools, { checkpoint: async state => /* write to private session */ undefined });
const p = {
  id: "legion-cross-domain-demo",
  goal: "核实仓库与表格情况，并解释下一步该改什么",
  steps: [
    {id:"repo",kind:"tool",target:"github.get_repo",args:{repository_full_name:"lovemoganna/Org-Skills"},depends_on:[]},
    {id:"sheet",kind:"tool",target:"sheets.metadata",args:{spreadsheet_id:"1RaGc5T6b5Tay82uikvHurX03L8w_O6hxFq_QW2IqgGY"},depends_on:[]},
    {id:"diagnose",kind:"skill",target:"causal-net-loop",args:{question:"根据两个真实结果找组织瓶颈和反证"},depends_on:["repo","sheet"]}
  ],
  acceptance:[{id:"source_reads",evidence_from:["repo","sheet"]},{id:"analysis",evidence_from:["diagnose"]}]
};
const first = await h.advance(h.init(p));
// first.summary.status === "AWAITING_MODEL" 时，当前 Work 模型读取真实证据与 Skill 后输出分析，
// 再调用 h.finishSkill(first.state,"diagnose",actualModelOutput,"skills/causal-net-loop/SKILL.md@<verified-revision>")
\`\`\`

## 已注册工具 / 权限

| target | 效果 | 宿主工具 |
| --- | --- | --- |
| github.get_repo | 读取 | GitHub get_repo |
| github.fetch_file | 读取 | GitHub fetch_file |
| github.get_pr_info | 读取 | GitHub get_pr_info |
| sheets.metadata | 读取 | Google Drive get_spreadsheet_metadata |
| sheets.range | 读取 | Google Drive get_spreadsheet_range |
| parallel.search | 读取 | Parallel web_search |
| github.create_file / github.update_file | 写入，必须授权 | GitHub 对应写动作 |
| sheets.batch_update | 写入，必须授权 | Google Sheets batch_update |

新增能力只在**审查调用参数、返回结构、权限与失败路径**后增加注册项。不支持任意命令、不绕过宿主授权、不凭发现 Skill 就执行工具。

## 验收和回滚

- 单测：\`node --test skills/loop/router_v2/tests/test_legion.js\`（模拟连接器：并行、模型交接、授权、错误路径、checkpoint）。
- 原有回归：\`python3 skills/loop/router_v2/tests.py\`，确保 V2 稳定版没有被修改。
- 真正的跨工具 Work 端到端、独立复核、定时运行目前**未验证**，不得将模拟器单测视为成功部署。
- 只在 feature 分支提交候选，不覆盖 main。回滚：关闭 Legion 入口，继续使用原 \`work_host.js\` 和现有 V2。
