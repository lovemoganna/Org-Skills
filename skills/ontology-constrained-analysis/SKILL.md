---
name: ontology-constrained-analysis
description: 对真实数据集或明确业务领域执行本体约束分析。先还原业务语义，建立本体原子知识库和本体识别规则库，再生成指标、问题、Signal、Finding 和 Dashboard。用于限制 AI 无效组合、要求真实数据验证、竞争解释、稳健性检查和全链路可追溯的分析任务。
---

# 本体约束业务分析

## 目标

先建模业务世界，再决定算什么。

先建立：

1. 本体原子知识库
2. 本体识别规则库

后续指标、问题、Signal、Finding 和 Dashboard 必须可回溯到本体。

目标不是增加指标。目标是缩小分析空间，用真实数据得到少量高价值 Finding。

## 输入约束

严格遵守用户指定的数据源、表、字段、时间范围、执行引擎、SQL、权限和输出要求。

未知信息标记“待验证”。源字节未进入运行时前，不得使用历史 Schema、预设结果或生成 Finding。

## Runtime Gate

任务指定执行引擎、读取方式或 SQL 时，先锁定执行契约：

```text
执行引擎
数据源
读取函数
固定 SQL / 参数
允许范围
禁止范围
初始化要求
```

区分网络、数据和 SQL 故障。锁定数据源与执行引擎。

DuckDB 不得替换。只锁定 URL 时，可暂存该 URL 的完整原始字节供 DuckDB 读取；核验字节数与 SHA-256。不得换源。

原始源 URL 可使用 `scripts/source_gate.py` 获取与校验。失败时脚本必须生成阻塞审计报告。规则见 `references/runtime.md`。

## 浏览器与单 HTML 交付门禁

涉及浏览器、DuckDB-WASM、单 HTML、远程数据或跨域资源时，先验证最终运行位置的真实能力，再实现或宣称可用。不得把服务器端可访问、连接器可读取、示例代码可运行，等同于最终浏览器可用。

必须记录：实际页面 Origin（包括 `file://` 的限制）、目标 URL 的浏览器 GET/HEAD 与实际 CORS 响应、Range 请求、DuckDB-WASM 资源及扩展可用性、内存预算、数据导入方式、实际 SQL 结果。没有可操作的浏览器环境时，标记“浏览器未实测”；不得把文档说明当作环境测试。

仅锁定数据源而未锁定读取 SQL 时，可将**从原 URL 取得且完整性校验通过**的原始字节注册到 DuckDB-WASM 虚拟文件系统，然后由原指定的 DuckDB 读取函数处理。远程 XLSX 直接读取失败时，优先尝试同源原始 XLSX 字节的 `registerFileBuffer` / `registerFileHandle` 与 `read_xlsx`，但必须实测扩展和函数；不得转为 CSV 或其他引擎。用户固定完整 SQL / URL 参数时，不得静默修改。

所有 SQL（静态、生成、示例、验证、最终）统一规范缩进和换行；网页呈现必须统一 SQL 语法高亮，复制操作输出**格式化后的纯 SQL**，不含 HTML、行号或装饰字符。单 HTML 不得依赖未验证的远程 CDN 才能阅读核心报告。详情见 `references/runtime.md`。

单 HTML 的所有 SQL 使用同一 `scripts/sql_ui.js` 格式化、语法高亮和复制入口；静态与动态代码路径一致。真实浏览器、实际页面 Origin、原生 Clipboard API 未实测时不得标记端到端通过；Mock 复制不算验收。

原始 `read_xlsx` 读取通过、CSV 导出成功，不等于四表各物化一次或业务分析完成。物化应在同一 DuckDB 会话中提供 `CREATE ... TABLE ... AS SELECT * FROM read_xlsx(...)` 的真实回执；后续查询只引用物化表。报告逐 Gate 记录真实 Result，未通过时保留阻塞证据。

## 同源 GitHub 资源恢复

原始 `raw.githubusercontent.com` 无法访问时，先定位对应 `github.com/{owner}/{repo}/blob/{ref}/{path}`，再验证 GitHub 仓库、ref、path 与原 URL 一一对应。能从 GitHub REST blobs 接口获取字节时，必须核对真实字节数、Git Blob SHA-1 以及 SHA-256；这是**同一 Git 对象的传输回退**，不能换用其他仓库、提交、镜像、样例或截图。访问 GitHub 页面不等于取得文件字节。

本地运行时无网络或 DuckDB 时，检查用户已授权且可执行的 GitHub Actions 原生 DuckDB Runner；仅以真实 SQL、Result 和执行回执确认成功。详细契约见 `references/runtime.md`。

## 大文件与同源下载执行顺序

源文件读取失败时，不得停留在“GitHub 页面存在”或“连接器已读取”的状态。先实际下载原 URL；失败后定位同一 GitHub owner/repo/ref/path，依次尝试 Git Blob 原始字节接口与 GitHub 文件原始下载地址。记录每次真实请求和错误。校验字节数、Git Blob SHA-1 和 SHA-256，完整原始字节必须进入 DuckDB 运行环境；否则只能生成阻塞审计报告。GitHub API 的文件大小限制、分片和内存限制必须主动核对。

用户要求一次性运行时，逐 Gate 自动继续到已验证 Finding 与报告，不在阶段成功后等待“继续”；只在缺少同源完整字节或等价 DuckDB 时停止，输出真实阻塞证据。禁止只交状态说明。

## 执行纪律

每次只处理一个阶段：

```text
执行
自检
修正当前阶段
复检
通过
停止
```

默认每次验收一个阶段，验收后停止。用户明确授权连续测试和自动修复时，按授权范围逐阶段执行，不必逐次确认。

上游修复后，重新执行受影响阶段。不要继承失效结果。

数据阻塞时停止分析，但必须交付阻塞审计报告：真实错误、已验证证据、未执行项、复跑命令、恢复条件。交付报告不等于完成分析。

## 固定流程

```text
真实数据或明确业务概念
业务语义还原
本体原子知识库
本体识别规则库
高质量指标
原子问题
真实数据验证
Signal
本体约束下的局部组合
复杂问题
复杂问题真实验证
竞争解释
稳健性验证
Validated Finding
Decision Value
Dashboard
```

不得跳步。

## 四个 Gate

**Gate 1：本体就绪**  
两张本体表通过 Validator。否则不生成复杂指标、问题或结论。

**Gate 2：Signal 就绪**  
原子问题已真实执行，并产生值得继续解释的信息。否则停止分支。

**Gate 3：Finding 就绪**  
重要 Signal 已经过竞争解释和必要稳健性验证。否则保持 Signal。

**Gate 4：Dashboard 就绪**  
Decision Value 是必要条件，不是充分条件。再核对决策场景、复用需求、数据口径和展示增量。无持续观察或复用价值时，保留报告，不强制生成 Dashboard。

## 核心规则

1. 字段是证据，不是业务知识。
2. 组合必须沿已登记本体关系。可 JOIN 不等于有业务关系。
3. 规则必须形成新的稳定业务模式。不要给单个状态或属性改名。
4. 指标量化业务现象。基础指标保持中性；派生指标必须可追溯。
5. 原子问题必须参数闭合、一次查询可回答，只改变一个主要判断。
6. 没有明确标准时，不使用“异常、明显、主要、高、低、集中”等判断词。
7. 没有真实 Result，不生成 Signal，不继续推论。来源元数据、解析统计与历史结果不得冒充本轮 DuckDB Result。
8. Signal 表示“值得解释”，不表示原因。小样本限制外推，不自动否决 Signal。
9. 局部组合区分“非法 / 合法但暂缓 / 合法并激活”。本体可达不等于值得展开。
10. 只使用当前有效证据链。旧轮次、作废分支、Eval、示例和未验证事实不得直接继承。
11. 多跳关系只证明可达。不得自动生成直接关系、资金来源或因果语义。
12. 跨对象关系记录 `join key`、实际类型和执行状态：`已验证 / 待验证 / 失败`。
    粒度不同先分别聚合；Join 后验证无重复计量。
13. 复杂问题形成后，先做真实验证，再进入竞争解释。
14. 竞争解释与稳健性验证分开执行：先提出可推翻当前解释的假设，再做最小必要验证。
15. Finding 必须区分：已确认事实、合理解释、未解决问题、数据限制。
16. Dashboard 需要 Decision Value 和独立展示必要性。一次性、不可持续复核的微小样本 Finding 不强制入看板。
17. 没有信息增量时，停止。
18. Eval 和测试夹具只验证 Skill，不得给真实分析提供问题、参数、阈值或答案。
19. SQL 枚举必须显式处理未知值。不要用 `ELSE` 静默归入已知类别。

## 按需读取

| 当前阶段 | 读取 |
|---|---|
| Runtime Gate | `references/runtime.md` |
| 业务语义、本体、关系、规则 | `references/ontology.md` |
| Lisp | `references/lisp.md` |
| 指标、问题、Signal、组合、Finding、Dashboard | `references/analysis-loop.md` |
| Validator、自检、修复 | `references/validator.md` |
| 示例 | `references/examples.md` |

按需读取，不在单轮重复加载无关 reference。

## 输出追溯链

完整分析保留：

```text
业务语义
本体原子知识库
本体识别规则库
指标
问题
SQL / 执行逻辑
真实 Result
Signal
复杂问题
复杂问题真实验证
竞争解释
稳健性验证
Validated Finding
Decision Value
Dashboard
```

不得虚构数据或结论。源字节未进入执行环境时，终态只能是阻塞报告。

## 停止条件

满足任一条件即停止当前分支：

1. 没有高价值 Signal。
2. 没有新的合法关系可展开。
3. 新问题不会改变判断。
4. 数据无法继续验证，且 Runtime Gate 无兼容路径。
5. 只剩低价值切片。
6. 复杂度增加，但信息不增加。
