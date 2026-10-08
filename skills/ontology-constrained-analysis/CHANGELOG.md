# Changelog

## v16.1 — Runtime / artifact regression repair (2026-10-08)

- 保持 SKILL.md 全部有效指令，压缩不影响 Markdown 语义的空行，使原有 180 行硬限制通过；未放宽验收标准。
- 明确原始 read_xlsx 读取、CSV 导出和四表一次物化不是同一验收阶段；新增真实 DuckDB 1.4.2 物化回归及独立 SQL Result 回执，不硬编码结果值。
- 新增统一 SQL 格式化、高亮、纯 SQL 复制资产；真实 Chromium HTTP Origin 与原生 Clipboard API 回归。
- 新增 Google XLSX 原 URL 直接下载、浏览器 CORS/HEAD/Range、DuckDB-WASM Excel 扩展和同源字节 VFS read_xlsx 回归；报告原 URL 与 VFS 文件路径差异。
- 原有 Source Gate 测试保持不变；结构与 Eval 定义检查纳入回归。模型行为 Eval、用户最终部署 Origin 均须单独验收。

## v16 — Source Gate / Fail-closed reporting

- 固定来源只可由同一 URL 的真实完整字节填充，不得因远端元数据存在即推进分析。
- 源 Gate 失败时自动交付 Markdown、HTML、JSON 审计文件。
- 阻塞不等于完成分析；禁止构造 SQL Result 或 Finding。
- Olist 特定执行器不属于通用 Skill。
- 保留 v15 的本体、Signal、关系执行、竞争解释和多表粒度约束。
- 新增源阻塞与通用性回归 Eval；Eval 定义验证不代表模型行为已验证。
