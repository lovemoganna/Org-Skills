# Changelog

## v16.5 — Evidence and execution-gate repair (2026-10-08)

- 纠正 Gate 1 追认漏洞：只有本轮 Schema、类型、样本值、来源等中性勘察可先行；禁止业务聚合、JOIN、Signal 在两张本体表语义验收之前进行。新增独立时间顺序检查及原后置 Gate 1 负例回归。
- 本体证据来源必须指向当前授权表中的具体字段，不再接受仅写表名；保留真实 DuckDB DESCRIBE 检查和派生来源。
- 新增显式的关系类别值域必要条件检查（按本轮观测值集合，不内置币种/资产答案）；真实工作簿回归拒绝把混合法币与加密资产符号统一断言为“加密资产”。
- 对带数值的 Finding 增加 fact_verification 契约：模板及 bindings（变量映射到 query、row、column）必须从本轮 SQL Result 重建 facts；数据变化后不更新正文应报错。禁止报告生成器自写 PASS 代替独立核验。
- 保留原来源 URL、DuckDB/SQL、四 Gate、Lisp、Signal/Finding、SQL UI/浏览器和阻塞审计能力。未将临时执行脚本、数据库、HTML、截图、日志或 CI 产物提交为 Skill 代码。
- 资产核对：原 Skill 22 个受控文件、151,408 B；保留全部 22 个已引用或具独立测试作用的资产，无经证实冗余文件可删除。仅增加通用顺序检查脚本、独立回归文件和作用域内 .gitignore（25 文件；最终体积以 Git tree 统计为准）。未擅自清理其他 Skill 的文件；原失败执行产物在外部审计包和历史 GitHub Actions 中保留。
- 本次回归包括静态完整性、现有 Source Gate、原失败语义/执行顺序、合法反例、原真实四表 read_xlsx 及浏览器回归。CI 结果以本次提交实际运行记录为准；模型行为 Eval 与最终部署 Origin 不因 CI 成功自动通过。


## v16.4 — Canonical Gate 1 source-column regression (2026-10-08)

- 修复历史四表本体测试资产：`来源` 更名为规范列 `证据来源`，逐项保留原始表字段证据值；该数据专用资产保留在原测试分支。
- Gate 1 禁止报告生成时静默重命名后冒充本体验收；新增通用结构/来源检查脚本，以当前 DuckDB DESCRIBE 输出为依据核验允许表和字段，不预置数据集列名。
- 增加旧列名、禁用表、未知字段、合法/非法派生来源回归；该脚本只做结构和来源检查，不取代业务语义审查。
- 原先真实 SQL、读取契约、四 Gate、Lisp、Signal/Finding、Dashboard 判定及其他有效约束均保持不变。

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
