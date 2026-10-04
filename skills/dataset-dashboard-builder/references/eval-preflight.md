# Evaluation Preflight

用于 Requirement / regression / eval 开始前的**最小能力检查**。

**Preflight 不是回归测试，不是产物，也不是停止点。**
它只决定“哪些步骤能执行、哪些具体 Case 受环境阻塞”。

只要 Canonical Fixture 可读，就必须继续实际运行 dataset-dashboard-builder，产出 SQL、分析结果和 HTML Dashboard。浏览器或其他单项能力缺失，不得提前终止整个回归。

## 1. Test Contract Discovery

先读取测试规范，并提取：

- required cases；
- conditional cases；
- canonical fixture path；
- mathematical anchors；
- required runtimes；
- rendered QA requirement；
- stop conditions。

禁止只读取锚点数字，不读取 Fixture / Case 条件。

## 2. Fixture Preflight

如果 Requirement 声明 Canonical Fixture：

1. 验证路径存在；
2. 验证所有 required tables / files 可读；
3. 检查 schema / row count / primary or candidate key；
4. 从原始行重算核心数学锚点；
5. 锚点只用于 compare，不得作为 input source。

状态：

- Fixture 可读且可重算 → 继续；
- Fixture 缺失 / 不可读 / 关键文件不全 → 对依赖真实数据的 Case 标记 `BLOCKED_FIXTURE`；
- 禁止把 Requirement 中的锚点硬编码进 Dashboard 冒充真实回归。

## 3. Environment Capability Preflight

快速记录：

```text
fixture_access
sql_runtime
javascript_runtime
html_runtime
browser_render
viewport_control
screenshot
keyboard_interaction
network_policy
```

能力不足时不要等到最后才披露。

## 3A. Continue-Execution Rule

Preflight 完成后必须进入实际执行。

- browser unavailable → 继续 SQL / Analysis / HTML；
- screenshot unavailable → 继续 HTML / interaction logic / static QA；
- optional renderer unavailable → 使用同语义 fallback；
- SQL runtime unavailable → 只将 SQL-execution 依赖项标记 BLOCKED_ENV，并继续能执行的分析与 HTML；不得声称 SQL 已执行；
- 只有 Fixture 本身不可读，才允许阻断依赖真实数据的主链路。

禁止输出“Preflight 完成”后直接结束。

## 4. Result Taxonomy

只允许：

- `PASS`：Case 已实际执行且证据满足 Requirement；
- `FAIL`：Case 已实际执行且违反 Requirement；
- `BLOCKED_FIXTURE`：缺必需 Fixture；
- `BLOCKED_ENV`：缺浏览器、SQL runtime、权限等执行能力；
- `NOT_APPLICABLE`：条件型 Case 本轮没有触发。

禁止：

- 把 BLOCKED 计入 PASS；
- 把 BLOCKED 当 Skill FAIL；
- 把 NOT_APPLICABLE 算进通过率分母；
- 用 `UNVERIFIED` 混合表达所有不同阻塞原因。

## 5. Runtime-Specific Blocking

若某 Case 依赖特定 runtime：

- 真实 SQL chain 要求 DuckDB，而环境没有 DuckDB → 该 SQL execution Case = `BLOCKED_ENV`；
- 可以用独立重算验证数学值，但不能因此声称 DuckDB SQL 已执行；
- Rendered QA 需要浏览器，而浏览器无法启动 / 截图 → Rendered Case = `BLOCKED_ENV`；
- Static QA 可以继续 PASS，但不能替代 Rendered QA。

## 6. Conditional Case Gate

Case 是否 required 由 Requirement 的 trigger 决定。

例如：

- Multi-Architecture / 5 dashboards：只有用户要求多方案时 required；
- Award-level visual gate：只有用户要求正式终稿 / 高奖项级视觉时 required；
- 静态导出任务不强制 Interaction Case；
- 没有稳定 entity key 时 drill-through 可以是 NOT_APPLICABLE 或 LIMITED，但必须说明原因。

禁止为了“全跑一遍”把未触发的条件型 Case 标成 FAIL / BLOCKED。

## 7. Layered Verdict

最终必须分开报告：

```text
Core Logic Verdict
Data / Fixture Verdict
Rendered / Environment Verdict
Overall Verdict
```

示例：

```text
Core Logic = PASS
Fixture = PASS
Rendered QA = BLOCKED_ENV
Overall = BLOCKED_ENV
```

如果 required Case 有 FAIL：

`Overall = FAIL`

如果没有 FAIL，但有 required BLOCKED：

`Overall = BLOCKED_FIXTURE / BLOCKED_ENV`

只有所有 required Gate 都实际 PASS：

`Overall = PASS`

## 8. Evidence Rule

每个 Case 至少记录：

```text
Case
Status
Trigger
Evidence
Runtime
Regression?
Owner: Requirement / Skill / Fixture / Environment
```

缺陷归属必须明确：

- Requirement：测试契约含糊、条件不清、Fixture 未指定；
- Skill：规则缺失或已有规则未正确执行；
- Fixture：数据缺失、损坏、schema 不符；
- Environment：runtime / browser / permission 不可用。

不得把基础设施问题错误修进分析 Skill。
