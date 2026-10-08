# Changelog

## v16.3 — Audit-led consolidation (2026-10-08)

- 将 SKILL.md 中重复的源恢复、浏览器及 SQL UI 细则合并到已有 `references/runtime.md`；入口仅保留执行契约、四个 Gate、核心拒绝条件与按需读取。
- 将重复的专项检查压缩为 `references/validator.md` 的 Gate 检查；统一当前证据作用域、阶段复验、模型 Eval 与部署 Origin 的判定。
- 修复四表审计暴露的 Gate 1 漏洞：真实数据原子必须记录可核验来源；结构通过不等于语义通过。
- 明确禁止所有 SQL（含探索和概览）直接聚合不同单位；给无效 SUM 标注“不可汇总”仍必须删除。
- 明确批量授权与默认单阶段停止的优先级，并区分最终 Origin 端到端验证与内联 HTML/CI Origin 局部检查。
- 将本次复现的移动端 SQL 展开溢出归入原有浏览器响应式验收：代码容器内滚动，不撑宽整页。
- 未改变数据源、引擎、固定 SQL、同源恢复、阻塞交付、真实 SQL、Signal/Finding、四个 Gate 或 Dashboard 的原有硬约束。相关 Eval 文件和执行脚本保持原样。
- 规模（Git Blob 字节/文本行数）：SKILL.md 9,609 B/179 行 → 6,598 B/89 行；runtime.md 11,150 B/234 行 → 6,800 B/77 行；validator.md 14,593 B/635 行 → 8,501 B/76 行；ontology.md 3,925 B/132 行 → 4,152 B/132 行。上述四文件合计 39,277 B → 26,051 B（-33.7%），1,180 行 → 374 行（-68.3%）。


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
