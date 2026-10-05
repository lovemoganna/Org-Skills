# Dashboard Audit Loop

目标：把 Dashboard 从“生成后靠用户肉眼指出问题”改成“生成前锁定问题，生成后自动审查并修正”。

本文件蒸馏自多套开源 Dashboard / UI Skills 的通用做法，重点借鉴：
- EnchStyle/ui-ux-audit-skill：Rendered Audit、Dashboard Profile、User Simulation、Token Consistency；
- data-goblin/power-bi-agentic-development：Decision Questions、One Page/One Intent、3-30-300、Design Gate；
- laviDrori0702/tableau-dashboard-creator-skill：Plan → Mock → Coverage Checklist → Spec、Simplest Primitive Guard；
- peixl/ifq-design-skills：高密度 Dashboard、Anti-AI-slop、真数据与交互三件套。

禁止整包照搬外部风格。只吸收可泛化的检查机制。

## 1. Decision Question Gate

渲染前，先写 2–5 个用户在默认视图中必须能回答的问题。

每个问题必须绑定：

- answer_type：level / change / comparison / composition / locate / evidence；
- primary_view：唯一主表达；
- source / metric；
- optional_support：只有新增信息时才允许存在；
- next_action：筛选 / 下钻 / 查看记录 / none。

硬规则：

- 每个 section 只能有一个主 job；
- 每个主组件必须服务至少一个 Decision Question；
- 不能说明自己回答哪个问题的组件，删除；
- 一个 Decision Question 默认只有一个 Primary View；
- 一个 section 同时承担 summary + exploration + evidence 三种角色时，必须拆分或降级。

## 1A. Reference Fit Gate

Mission / Decision Questions 与 Primary Analysis Model 明确后，读取 `dashboard-reference-catalog.md`，选择一个 Primary Archetype，并只读取对应的一个 Golden Blueprint。

记录 Primary Analysis Model、Archetype、Golden file、Why it fits、Primary question、Primary viewport composition、Required interaction、Removed unsupported slots。

如果最终 IA 与所选 reference 的 decision path 不一致，必须重新解释或换 reference。仅有相似颜色、卡片和图表类型不算 reference fit。

## 1B. Business KPI Eligibility Gate

Coverage Plan 之前检查所有候选 headline metric：是否有 comparator、delta/difference、decision polarity、合法 driver path、evidence path。不满足时降级为 context / diagnostic，不得占用 Primary KPI 位。

## 1C. Dashboard Surface Boundary Gate

Build 前预先拒绝 report-shaped IA：
- 不使用 WHAT / SO WHAT / WHY / PROVENANCE 等分析过程作为顶层 section；
- 不把 QA / SQL / Regression / Fixture 状态放入业务页面；
- 不通过长段文字串联页面；
- 不显示 Primary / Driver / Guardrail / Diagnostic / Context / Exploration 等内部角色或路由标签；
- 不为每个主图机械生成 So-What / Takeaway 文字卡；
- 1280×900 首屏必须完成 Primary Job，并给出下一步入口。

## 2. Dashboard Coverage Plan

渲染前生成 Coverage Plan：

| id | Decision Question | Role | Component | Measure / Grain | Interaction | Required |
|---|---|---|---|---|---|---|

Role 只能来自：

- primary；
- driver；
- guardrail；
- diagnostic；
- detail / evidence。

每个计划元素必须有稳定 id，例如：

- kpi-turnover
- trend-funds
- filter-date
- filter-direction
- table-entity
- queue-evidence

Coverage Plan 是生成与回归的共同契约。

## 3. Simplest Primitive Guard

每个问题默认使用“最简单且足够”的表达。

优先级：

plain number / text → KPI → table / bar-in-cell → simple chart → interactive chart → advanced custom visualization

升级到更复杂形式必须说明新增价值。

典型失败：

- 两个数字就画 donut；
- 单一排名同时画 bar + table；
- 一条业务时间序列为了金融感伪装成 K 线；
- 普通筛选能完成却引入 modal / drawer；
- Chart.js / Vela 只是为了“酷”而存在。

## 4. One Primary Answer per View

Dashboard 默认遵循：

**One Question → One Primary View**

辅助组件只有新增以下信息时才允许保留：

- time；
- segment；
- denominator；
- uncertainty；
- distribution；
- exact lookup；
- evidence；
- actionable context。

如果删除辅助组件后，用户没有失去独立判断能力，则删除。

## 5. Density & Hierarchy Gate

数据密集型 Dashboard 不以“更多留白”为默认优化方向。

要求：

- 高密度但可扫描；
- 第一屏有一个 dominant answer；
- chrome 比 data 更弱；
- KPI 数值同一基线；
- 同层级 panel 使用统一 gutter；
- 图表 plot area 与 panel 文本边缘对齐；
- 12–14px 数据字号可接受，低于 12px 默认复核；
- pointer-first 控件可使用 32–40px，但并列控件高度必须统一；
- 不使用巨大 hero、营销式空白、九宫格卡片堆满首页。

默认阅读优先级：

3 秒：最重要状态  
30 秒：变化 / 对比 / 重点对象  
300 秒：定位 / 证据 / 明细

## 6. Global Design System Gate

生成 HTML 前必须建立统一 token，不允许每个组件各自发明：

- type scale；
- spacing；
- gutter；
- radius；
- control height；
- border；
- surface hierarchy；
- status colors；
- focus / hover / selected / disabled；
- table row height；
- chart padding。

重复出现 2 次以上的视觉数值应优先抽成 token。

检查：

- 同行 input / select / button 高度一致；
- KPI value 在同一 baseline；
- section 左边界一致；
- 同级 card gap 一致；
- 深浅主题复用同一状态模型；
- 不能通过逐个 nudging 修对齐。

## 7. User Simulation Gate

至少模拟三种用户：

### A. Real User

按 Dashboard Mission 完整走一次：

打开页面 → 第一眼看什么 → 如何判断 → 第一次点击什么 → 是否得到预期结果 → 能否返回

### B. Constrained User

至少选一个：

- keyboard only；
- 200% zoom；
- 小屏；
- 深色模式；
- 色觉限制。

### C. Edge-data User

至少覆盖：

- empty；
- 1 row；
- long label；
- many categories；
- null；
- zero；
- extreme value。

UI 只在正常数据下正确不算完成。

## 8. Rendered Audit Gate

能实际渲染时，至少检查：

- 360px；
- 768px；
- 1280px。

必要时增加 1440px。

检查族：

1. overflow / clipping；
2. chart readable plot width：禁止为了消除整页 overflow 把长时间序列压缩到标签不可读；窄屏优先局部横向滚动、减少同时显示点数或调整粒度；
3. text wrap / widows；
4. card / KPI baseline；
5. control height；
6. repeated component size；
7. near-miss edges；
8. table header / alignment；
9. sticky region 占屏；
10. contrast / dark mode；
11. focus / hover / selected；
12. chart label collision；
13. empty / error states；
14. data values / visual agreement；
15. duplicate panels；
16. visible hierarchy；
17. Primary Viewport：1280×900 不滚动能否完成 Primary Job；
18. Dashboard / Report Boundary：是否出现过程型 section、开发状态或长篇报告式 narrative；
19. Reference Fit：实际构图是否仍符合所选 Archetype + Golden；
20. Analysis Model Fit：主要组件是否都能回指 Primary / Supporting Analysis Model；
21. UI Role Leakage：内部 Context / Guardrail / Exploration 等角色是否泄露；
22. Narrative Card Check：是否用固定 takeaway 卡替代比较、annotation 或 drill。

如果无法真实浏览器渲染：

- 执行 DOM / CSS / JS 静态检查；
- 普通生成任务明确“未完成 rendered visual check”；
- regression / eval 模式必须按 `eval-preflight.md` 标记 `BLOCKED_ENV`；
- 禁止把源码检查描述成视觉验收。

## 8A. Artifact Boundary Lint

HTML 生成后、最终 rendered audit 前运行：

`python tests/dashboard_surface_lint.py <dashboard.html>`

默认模式发现以下任一项即 Major：

- report_process_heading；
- internal_execution_state；
- internal_role_label。

用户明确要求审计视图时才允许 `--allow-audit`。Lint 只负责抓确定性边界错误，不能替代业务分析、Reference Fit 或 Rendered Audit。

## 9. Coverage Reconciliation Gate

生成后必须把 Coverage Plan 逐项对账。

示例：

- [x] kpi-turnover
- [x] trend-funds
- [x] filter-date
- [x] filter-direction
- [x] table-entity
- [x] queue-evidence

任何 required 项缺失 → Major。

任何实际组件不在 Coverage Plan 中：

- 如果回答新问题，回写 Plan；
- 如果不能证明新增价值，删除。

禁止出现“计划没有、AI 顺手加了”的孤儿组件。

## 10. Honesty Gate

必须检查：

- selector 是否真的改变 figure；
- KPI / chart / table 是否同口径；
- missing 不得画成 zero；
- truncated axis 不得误导；
- highlighted top / worst 必须真的是 extreme；
- callout 必须有数据证据；
- snapshot / estimate / reference 必须持续显式标记。

## 11. Audit Loop

最终闭环：

Decision Questions → Coverage Plan → Build → Coverage Reconciliation → User Simulation → Rendered Audit → Detect → Fix Root Cause → Re-render → Reconcile Again → Final

修复优先级：

- P0：数据/口径/误导/核心功能不可用；
- P1：主问题漏答、重复结构、交互断裂、响应式失败；
- P2：对齐、密度、状态可读性；
- P3：纯审美偏好。

P0/P1 未清零不得结束。

## 12. Durable Fix Rule

如果同类问题在两轮以上重复出现，不允许只修当前 HTML。

必须判断能否升级为：

- Skill rule；
- token；
- reusable component；
- regression case；
- static checker；
- rendered checker。

目标是让同类问题以后自动失败，而不是让用户再次指出。
