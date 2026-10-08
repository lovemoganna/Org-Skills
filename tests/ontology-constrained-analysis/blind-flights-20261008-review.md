# 陌生航班数据盲测：执行证据与验收边界

测试分支：`test/ontology-blind-flights-20261008`。主仓库 `main` 未因本报告变更。
最新成功执行：GitHub Actions [37762841001](https://github.com/lovemoganna/Org-Skills/actions/runs/37762841001)，提交 `cffd2110ff26c7aeaa4f3ca09feda6b8132d03d1`。

## 真实输入与运行

仅使用 Stanford 同一来源的三份真实 CSV：
- `https://web.stanford.edu/class/datasci112/data/nycflights13/flights11.csv`
- `https://web.stanford.edu/class/datasci112/data/nycflights13/weather.csv`
- `https://web.stanford.edu/class/datasci112/data/nycflights13/planes.csv`

执行器：DuckDB Native v1.4.2；工作流记录原始 HTTP 头、字节数、SHA-256、已执行 SQL 与 Result；数据分别为 23,300、26,115、3,322 行。

## 失败归因与原样本复测

原失败：[37762421084](https://github.com/lovemoganna/Org-Skills/actions/runs/37762421084) 报 `Binder Error: Referenced column "origin" not found in FROM clause!`。

分类：执行偏差（未根据实际表结构验证所需列就写跨表关联），不是外部网络故障。根因由真实 Binder 错误和三表 Schema 检查确认；不能将其泛化为所有数据集没有 `origin`。

修复：先读取真实 Schema；flights 使用 `origin`，weather 的站点键为 `airport`；只有键、粒度和语义都成立时才允许关联。复测：[37762565038](https://github.com/lovemoganna/Org-Skills/actions/runs/37762565038) PASS、[37762841001](https://github.com/lovemoganna/Org-Skills/actions/runs/37762841001) PASS。

新增真实发现：weather 的复合候选关联键存在 3 组重复，`weather_relation_status=BLOCKED_JOIN_FANOUT`，因此没有执行未证实为安全的一对一联接；时间语义亦未验实，不得据此声称天气因果解释。planes 的 `tailnum` 键唯一且航班连接覆盖 23,300/23,300。

## 实际 SQL 信号

在有 `dep_delay` 的航班记录范围内，按计划出发小时：
- 06–11：9,047 条，出发延误（`dep_delay > 0`）占比 21.38%，平均 `dep_delay` 1.52 分钟。
- 18–23：5,294 条，出发延误占比 41.48%，平均 `dep_delay` 10.95 分钟。
- 差值 20.10 个百分点（描述性）；按 `origin × carrier` 可比层加权后差值 20.48 个百分点，28 个可比层中 26 层晚间更高、2 层相反。
- 去除长尾（查询以 `dep_delay` 99 分位为上限）后占比分别为 20.83% 和 40.57%；上述差异未消失。

这些是实际 SQL 结果，不是模型模拟结论；数据仅为 2013 年 11 月样本。不能据此推断当前航班情况、天气因果、航空公司过错或整个年份。

## 阶段验收

- 源与运行时、SQL 执行、分层对照、部分稳健性：有真实运行证据。
- 本体 Gate 1：仅结构检查通过，自动语义审计未完成；`gate1.status=STRUCTURE_PASS_SEMANTIC_AUDIT_SEPARATE`。
- 天气关联：明确阻塞，不得以其他字段静默代替。
- 完整 Skill 端到端、模型行为 Eval、Browser Origin/CORS/DuckDB-WASM 和正式 HTML：本轮未验证，不得标 PASS。

下一步：以本次完整输出为输入，分别验证 Gate 1 本体语义、Finding 的竞争解释及反证边界，再考虑正式报告与 Dashboard 资格。每项保留独立证据，不因 CI 成功自动升级状态。
