# Changelog

## 0.1.1 — 2026-10-12
- 真实 `org-notes` 冒烟测试发现索引与日志的裸文件名要求不符合发布器 UUID 路径契约；改为现有发布契约优先，记录实际索引与日志 WIKI_ID。
- 新增 T13 路径兼容和 T14 幂等回归用例，保留真实 Commit、Actions 部署回执及未覆盖风险。
- 真实站点的两篇 SQL 笔记互引和两篇维护页已通过发布验证；完整 LLM Wiki 能力仍需后续测试。

## 0.1.0 — 2026-10-12
- 新建 Org-native LLM Wiki 知识维护编排 Skill。
- 明确 Ingest、Answer、Audit、Synthesize 四种模式、授权边界、Claim 级证据与冲突保留。
- 新增十二项回归场景与 G0–G6 验证门禁。
- 不修改既有 Org Museum 发布器、收录入口及 note-reforge。
