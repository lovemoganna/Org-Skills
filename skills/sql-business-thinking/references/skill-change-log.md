# Skills 缺陷沉淀

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| V2 首屏 Hero 源码逻辑有内容，但最终 HTML 实际为空 | Renderer 改为整块原子替换；验收加入真实渲染烟测 | 生成 Artifact 后必须验“渲染结果”，不能只验 DOM/源码意图 |
| 主问题要求“每个用户总交易额”，正文只展示 Top 用户 | 正文加入全量用户 Answer Block | 每个分析问题必须映射到正文可见结果，附录不能替正文回答 |
| Native DuckDB `httpfs` 加载路径直接复制到 DuckDB-Wasm | Wasm 使用 browser VFS / registerFileURL；只按 Wasm 支持加载 excel | 同一数据能力在不同运行时必须有 Platform Contract |
| 汇率表只有单日快照，却容易机械按 asset JOIN | 加 exact-date → as-of → snapshot 路由，结果命名随口径变化 | 时间维表必须先定义业务时间点和匹配策略 |
| 汇率表未来增加多日后会造成 JOIN 膨胀 | 聚合前强制右表键唯一 + JOIN 前后行数 | 金额 SUM 前必须通过 JOIN Cardinality Gate |
| Top 10 在 10 用户样本中等于 100% | Top N 随 active population 自适应 | 覆盖全部样本的 Top N 不能作为核心集中度指标 |
| 报告迭代容易只调 UI，不修生成机制 | 新增 Artifact Regression Loop，每轮缺陷必须回写 Skill | 结果修复和生成规则修复必须闭环验证 |
| Skills / Debug 元信息容易抢主报告 | 正文按决策价值，审计轨迹二级展开 | 过程是证据，不是页面主角 |
| 显式要求人物会话，却被“过程信息默认折叠”规则一起藏进附录 | 增加 Dialogue Coverage Gate；正文展示关键纠错回放 | 用户点名的人物会话属于交付物，不得按过程噪声降级 |
| 人物会话、SQL、Skill Trace 交错，角色阅读被不断打断 | 拆成三条信息通道 | 教学叙事 / 可执行证据 / 内部路由必须解耦 |
| Lucy 台词混有状态机语气，人物感弱 | 增加 Character Contract：先结论后依据、≤3 句、内部流程标签不进台词 | 角色只说推动当前阶段的话；流程元信息交给 UI |
| 移动端高维排名表被压缩到难读 | 保持表格最小宽度，容器内局部横向滚动 | 高维表优先局部滚动，不靠缩字号塞进一屏 |
| 会话像彼此独立的纠错卡，没有任务起点和汇报终点 | 增加 Conversation Arc Contract | 角色模拟必须覆盖 Assignment → Evidence → Revision → Synthesis → Report-back |
| star 被写成错误制造器，Lucy 像全知专家 | 重分角色职责：star=Analysis Owner，Lucy=Reviewer | Owner 必须提出假设、更新判断并完成最终汇报；Reviewer 只挑战和验证 |
| 对话存在“对 / 明白”等低信息回合 | 增加 Turn Delta Gate | 每句必须新增 FACT / JUDGMENT / QUESTION / DECISION，否则删除或合并 |
| 人物提前知道尚未跑出的最终数字 | 增加 Progressive Knowledge Gate | 角色只能使用当前阶段已经出现的事实，禁止结果倒灌到前文 |
| 最终汇报与前序讨论缺少显式追溯 | 增加 Report-back Traceability Gate | 最终每个关键结论必须能回指至少一个前序证据节点 |
| 正文已经重构会话，附录仍保留旧版人物全文 | 权威会话只保留一个版本 | 同一信息只保留一个权威叙事，旧过程日志不得造成“双重真相” |

## V6：代码必须在会话中产生

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| 人物讨论与 SQL 被拆成两条信息通道，代码像事后补证据 | 把每一步改成“对白 → 当前 SQL → Result → 基于结果继续对白” | Code-in-Conversation Contract：代码必须原位产生，不能集中后置 |
| 人物先说出数字，后面才看到 SQL / Result | 加 Result Dependency Gate | 具体数字第一次进入台词之前必须已有可见证据节点 |
| 会话阶段用累计摘要反复复述全局结论 | 删除 rolling summary，仅保留局部状态变化和最终 report-back | No Rolling Summary：推进中只处理当前问题，跨阶段汇总延后 |
| 查询动机、代码、结果相隔太远 | 强制 Evidence Adjacency | 产生判断的 evidence 必须与该判断相邻 |
| 正文有 SQL，附录又复制一套 SQL | 删除 SQL 副本，保留 Skill Trace | Single Code Source：同一查询只保留一个可执行实例 |
| “决策价值优先”的报告规则与教学推演认知顺序冲突 | 增加 Dialogue-Driven Report Override | 用户要求看推理形成过程时，认知顺序优先于管理层摘要顺序 |

## V7：代码增长与单步定位

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| “SQL 出现在会话里”但仍是完整 SQL 突然出现 | 加 Code Growth Gate，要求至少一次对白触发的可见代码增量 | Code-in-Conversation 还不等于 Code-Growth；逐步生成必须可见 |
| 一个阶段塞多个 SQL，读者失去当前判断点 | 加 One Step One Query | 一个推进点 = 一个问题 + 一个最终 SQL + 一个 Result + 一个判断变化 |
| Result 后又用旁白做“这一步确认 / 截至目前”汇总 | 改由 star/Lucy 自己说出刚刚发生的状态变化 | Human State Transition：角色模式下状态变化由角色承担 |
| 中间不断滚动汇总，干扰当前推进点 | 禁止跨阶段累计摘要 | Local Context Only：推进中只保留当前问题、当前证据和下一判断 |
| 草稿 SQL 与正式 SQL 容易形成双重事实源 | 草稿标“不单独执行”，正式 SQL 保持唯一可执行实例 | Draft vs Executable Contract：草稿只展示增量，不形成第二套权威代码 |


## V8：人物角色统一命名

| 暴露缺陷 | 修正意见 | 可泛化规则 |
|---|---|---|
| 人物角色命名需要统一，旧名仍散落在主协议、渲染协议、回归样本和历史规则中 | 将 `Yone/Carmen` 全量迁移为 `star/Lucy`，并新增仓库级旧角色名回归断言 | 角色重命名属于跨文件契约变更：必须搜索全部引用、同步测试，并阻止旧名重新进入主分支 |
