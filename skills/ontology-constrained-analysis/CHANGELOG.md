# Changelog

## v16.2 — Browser fixed-URL SQL verification (2026-10-08)

- 修复测试覆盖缺口：此前 VFS 的 `read_xlsx('source.xlsx')` PASS 不能证明原始远程 `read_xlsx(URL)` 可执行。浏览器实际用原 URL 对四张授权 Sheet 分别执行 DuckDB-WASM SQL，并逐表与 VFS 行数比较。
- 实测结果：users 10、fiat_transactions 25、crypto_transactions 25、exchange_rates 8；四条远程 URL SQL PASS，VFS PASS。证据：GitHub Actions `Ontology Real Workbook Materialization` run `37760620994`（commit `c14d4e47d22b9d9577d04811a898fe6aa1ebb579`）。
- 明确 Range 能力判断：请求返回 200 且无有效 Content-Range 时，标 `NOT_CONFIRMED`，不得伪称 Range 206 已通过。
- 远程 SQL 结果、VFS 结果及 Range 状态独立记录；不能以其中一项成功代替其他项。此轮验证的是 CI 实际 HTTP Origin，不代表用户最终部署 Origin。
- 未验证：用户最终网页 Origin、部署环境的跨域限制、模型行为 Eval。未执行时不宣称通过。

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
