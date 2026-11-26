# 真实四表回归案例：把“正确 SQL”升级为“有阅读价值的业务发现”

该案例为仓库内针对真实远程 Google Sheets XLSX 的实验，不是需要依靠未来历史文件来假装当前执行的标准答案。

## 固定数据合同
- 原始 URL: https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx
- 仅 users, fiat_transactions, crypto_transactions, exchange_rates；禁止其他 Sheet；DuckDB 1.4.2 + read_xlsx；httpfs/excel 安装与加载各一次；四表分别只读、物化一次。后续仅查本会话物化表。
- 每次新的执行以当次回执为准。样本行数与用户名不能写死进通用 Skill。
- 真实试验：https://github.com/lovemoganna/Org-Skills/actions/runs/38748162141
- 变异测试及泛化修正：https://github.com/lovemoganna/Org-Skills/actions/runs/38750016332
- 现阶段这是 **确定性 SQL 结果驱动编排**，并非三个独立 LLM 自主研究的证据。

## 基线失败
旧版首先锁定 USD 流量集中度，得到 9 笔已完成交易、第一名用户 64% 占比；加入单笔 50,000 USD 敏感性验证后就生成 6 章 HTML。计算虽正确，但调查没有产生真实资金因果解释；技术通过不能证明读者获得了新业务认知。

## 本轮可审的新认识
| 现象 | 首轮证据 | 决定性的二轮 SQL | 能证实什么 | 不能证明什么 |
|---|---|---|---|---|
| 非 completed 仍有 completed_at | fiat_details 记录 status=failed | stage2_completed_at_mismatch + status aggregation | status=completed 43 笔，而 completed_at 非空 44 笔，失败 EUR 300 提现也有终止时间 | 不能凭这个字段认定失败交易实际到账 |
| 同 UID 的法币/Crypto 接近 | crossrail_status_and_time | stage2_crossrail_completion_order | 5 行近时配对实际只涉及 2 名 UID、3 笔法币订单、3 笔 Crypto 订单；2 行创建与完成排序相反，但同一订单可重复进入不同配对，不是 5 个独立案件 | 不能证明是一次换汇或同一资金路径 |
| BRL 短期入出 | fiat_roundtrip_7d | stage2_completed_pair_peer_baseline | 同 UID、同币种、24 小时内各 1 笔完成态入/出金 | 不能证明钱原路返回或洗钱目的 |
| frozen 用户仍有提现 | frozen_account_activity + schema_users | temporal_state_gate | 状态快照与两笔完成态提现共存 | 没有 frozen_at/变更日志就不能倒推出当时被冻结 |

该报告的重点不是这四条“风险”，而是它们揭示了一种业务研究能力：动态找到 **错误统计口径、时间逆序、伪关联、历史状态缺口**，并能提出能够改变监控规则的实际动作。

## 逆向测试：选题不是预设结果
运行中更改首轮记录构造反例：
1. 失败记录移除 filled completed_at，STATUS_NOT_SETTLEMENT 不再入选；
2. 再去掉 24 小时内法币往返，改选 CROSS_RAIL_NEARBY；
3. 所有证据候选消失时拒绝追加 SQL，也不生成文章。

通过后才称“会随结果改变追问方向”。这不是对任意陌生数据的通用研究性能证明，还应在不同领域、不同记录数、不同查询问题上反复检验。

## 成果格式
用户读到：事实是什么、为什么是错的/为什么成立、可排除什么、业务下一步怎么做。SQL 和验证日志只作可追溯证据；默认不出“角色协作与证据验收”“四表质量与分析边界”等流程章节。

## 推广前条件
- 至少在一个结构不同的真实数据集验证是否真的自主选择高价值问题；
- 上游研究目标不由测试代码硬编码；
- 用户或独立评审能证明内容比旧版有实质信息增量；
- 不涉及未授权数据、现时余额、真实违法结论或新 API 依赖。