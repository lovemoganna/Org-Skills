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
