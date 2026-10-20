# Ink & Signal v17 — 新配置回归（2026-10-20）

## 基线
- 上传文件：`plantuml-style (1).puml`，723 行，版本标识 v17。
- 旧仓库基线：Ink & Signal v7；保留原有 `examples/01..09`。
- 本报告仅记录新增案例与自动检查设计。实际 CI 结论请以对应 Actions run 为准。

## 五个测试用例
| Fixture | 类型 | 核查重点 |
| --- | --- | --- |
| 01_activity_light.puml | Activity | 浅色主题、双层条件、风险语义色、退出条件 |
| 02_sequence_dark.puml | Sequence | 深色主题、参与者、分组与 alt 分支 |
| 03_component_ortho.puml | Component | 正交连线、模块分组、四级语义构造型 |
| 04_state_compact.puml | State | `$STATE_COMPACT`、状态转换、开始/结束标记 |
| 05_gantt_compat.puml | Gantt | 专属定界符、工期与前后置依赖 |

## 验收规则
1. 使用固定的 PlantUML v1.2026.8（Jar SHA-256 验证）在 GitHub Actions 执行 `-checkonly` 与 SVG 渲染。
2. 五个新增用例与九个原有示例总计十四张图，全部必须产生可解析 SVG，且无明确错误信息。
3. 运行既有 `test_encode_url.py` 单元测试，防止包括本地 `!include` 和敏感信息门禁在内的功能回退。
4. 仅构建成功：`RENDER_VALIDATED / VISUAL_UNVERIFIED`；须实际查看 SVG 的文字、对齐、间距、色彩后才可标记 `VISUALLY_REVIEWED`。
5. 发生失败时依据 GitHub Actions 日志定位，不得填写虚构的通过状态。

Actions: https://github.com/lovemoganna/Org-Skills/actions/workflows/plantuml-style-v17.yml

## 渲染发现与修复
- 初次运行五个新例均可解析，但 SVG 显示全局 `skinparam padding` 废弃提示；浅色活动图使用旧着色语法时还出现警告与文本串行。
- 原有 `examples/02_activity.puml` 在 PlantUML v1.2026.8 的原提前停止分支中触发 `Cannot find if`；已重排条件分支，保留敏感数据只允许本地渲染的语义。
- v17.1 移除全局废弃 padding 并将活动图填色改为现代语法；后续以工作流实际验收结果为准。

## 已完成的真实验收（2026-10-20）

- **成功的 GitHub Actions 运行**：https://github.com/lovemoganna/Org-Skills/actions/runs/39405660663
- **运行对应代码**：`d1d1bca45eb5a7d2f064498843e74880fc70e096`。
- **PlantUML 引擎**：v1.2026.8，JAR SHA-256 为 `5e1ecfa8ecd32c90b03bbf3b1eb6f020943f98ab0fcf4032be31a0002ee2c462`。
- **渲染**：5/5 个新案例 + 9/9 个原有示例，共 14/14 张有效 SVG，14/14 张 PNG，`-checkonly` 无错误；检查无已知废弃警告文案。
- **现有功能单元测试**：29/29 通过，包括私有内容保护、CJK 编码往返和 `!include` 内联。
- **人工查看预览（新增五图）**：Activity、Sequence、Component、State、Gantt 均能显示中文和语义颜色；发现组件图箭头文本拥挤后使用 `skinparam ranksep 140` 扩大间距，并在该成功运行中完成复验。结论限制为上述五张实际预览，不外推到未经测试的其他图型或终端。
- **回归问题**：旧活动图原有分支结构曾触发 `Cannot find if`，现代化活动图填色语法及分支调整后解除；旧 `skinparam padding` 曾显示废弃警告，已从 v17.1 基线移除。

最终状态：`14/14 RENDER_VALIDATED`；新增五图 `VISUALLY_REVIEWED`（已检查文字和明显重叠，未进行跨设备无障碍专项审计）。
