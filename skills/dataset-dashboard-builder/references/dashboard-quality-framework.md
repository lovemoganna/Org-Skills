# Dashboard Quality Framework

目标：给 `dataset-dashboard-builder` 一个可执行的“好 Dashboard”判定标准。

Dashboard 不是图表集合，也不是分析报告换成 HTML。它的任务是围绕明确业务问题，帮助用户：

```text
看状态
→ 发现变化
→ 识别异常
→ 解释原因
→ 定位对象
→ 下钻验证
→ 查看证据
```

如果页面只能被动阅读，不能支持判断或继续分析，它不是高质量 Dashboard。

## 1. 五层质量模型

| 层级 | 核心问题 | 典型失败 |
|---|---|---|
| L1 数据 | 数据到底是什么？ | 字段堆砌、口径错误、单位混乱 |
| L2 业务 | 用户到底需要知道什么？ | 没有业务问题，只有字段和指标 |
| L3 分析 | 如何从数据得到判断？ | 图表集合，没有解释路径 |
| L4 信息架构 | 信息应该如何组织？ | 所有模块同权，读完仍不知道先看什么 |
| L5 表达 | 如何让人快速理解和操作？ | UI 漂亮但不可读、不可操作 |

L1–L3 决定“有没有用”；L4–L5 决定“好不好用”。

任何上层设计都不能修复下层错误。

## 2. Dashboard Mission Contract

生成页面前先建立：

| 字段 | 内容 |
|---|---|
| Primary Business Question | 这个 Dashboard 主要解决什么问题 |
| Primary User / Mode | monitoring / investigation / review / operational analysis |
| Core Objects | 用户、订单、交易、渠道、产品等真实业务对象 |
| Key Decisions | 用户看完后需要判断什么 |
| Key Actions | 需要继续定位、筛选、下钻或核查什么 |
| Evidence Path | 结论如何回到对象和明细 |
| Known Limits | 哪些判断当前数据不能支持 |

若用户没有明确业务问题，只能根据数据推导“最合理的分析任务”，并标明推导依据。禁止编造业务目标。

## 3. Dashboard Information Chain

高质量 Dashboard 优先形成：

```text
What
→ So What
→ Why
→ Who / Where
→ Evidence
```

对应：

```text
当前状态 / 核心变化
→ 为什么值得关注
→ 原因 / 驱动
→ 具体对象 / 维度
→ 明细 / 原始证据
```

禁止默认采用：

```text
KPI → 饼图 → 柱状图 → 折线图 → 表格
```

## 4. 功能模块

模块按作用定义，不按固定数量定义。

### A. 状态模块

回答：`现在怎么样？`

适合：核心规模、当前状态、风险水平、待处理量、完成率。

### B. 变化模块

回答：`发生了什么变化？`

适合：趋势、前后期、结构变化、增长/下降、波动。

### C. 异常模块

回答：`哪里不正常？`

适合：异常增长、异常下降、集中、异常对象、Outlier。

### D. 解释模块

回答：`为什么发生？`

必须把结果拆到真实可解释维度，而不是重复描述现象。

### E. 定位模块

回答：`谁 / 哪里贡献了问题？`

适合：用户、地址、渠道、产品、地区、交易类型、资产。

### F. 下钻模块

回答：`下一步如何验证？`

适合：对象 → 事件 → 交易 → 明细 → 证据。

不是所有页面都需要全部模块。由 Mission Contract 和数据决定。

## 5. Information Architecture Gate

渲染前先生成 Dashboard IA Plan：

| 顺序 | 模块 | 功能类型 | 回答问题 | 优先级 | 进入下一层的动作 |
|---|---|---|---|---|---|

硬规则：

- 第一屏优先回答当前最重要的业务问题；
- P0/P1 信息必须明显高于 Context / P2；
- 总览、解释、定位、明细必须形成阅读路径；
- 共享同一驱动的模块必须靠近或合并；
- 不允许长篇文字先于核心状态和重点；
- 不允许所有模块使用相同视觉权重；
- 可以滚动，但首屏必须完成“状态 + 重点 + 下一步入口”。

## 6. Visualization Gate

图表选择继续遵守 `visualization-registry.md`。

额外原则：

- 先写“这个模块帮助用户做什么判断”；
- 如果表格更适合精确核查，优先表格；
- 如果图表不能提高比较、识别、解释或定位能力，删除；
- 不为视觉多样性切换图表类型；
- 不允许图表取代 Evidence Path。

## 7. Interaction Gate

交互只在能推进分析时存在。

支持的功能包括：

- 全局 / 局部筛选；
- 点击交叉筛选；
- drill-down / drill-through；
- hover / tooltip；
- TopN 展开；
- 对象详情；
- 明细抽屉 / 明细表；
- 重置筛选。

硬规则：

1. 用户需要“定位 / 验证”且数据存在稳定对象键时，静态页面默认不足；
2. 点击或筛选后，相关 KPI / 图 / 表必须使用一致范围；
3. 交互必须明显可发现；
4. 不为“像产品”添加无意义控件；
5. 如果输出明确是静态导出、截图或汇报页，可以不强制交互。

## 8. UI Gate

目标视觉：专业分析工具，而不是营销页面。

优先：

- 清晰层级；
- 高信息密度但不拥挤；
- 统一间距；
- 可读字体；
- 一致单位和格式；
- 重点颜色有限；
- 状态颜色语义稳定；
- 详情按需显示；
- 移动端控制区不得长期占据主要视口；桌面 sticky filter 在窄屏应折叠、收起或取消 sticky。

主动避免：

- 大面积渐变；
- Glow；
- Glassmorphism；
- 无意义动画；
- 大量 Icon；
- 过度阴影；
- 装饰性地图 / 仪表盘；
- 用空白和大标题制造“高级感”。

## 9. Anti-AI Dashboard Rules

禁止：

1. 因为有数字就生成 KPI Card；
2. 为填充页面凑图；
3. 分类字段默认画饼图；
4. 有时间字段就必画折线；
5. 所有模块同等重要；
6. 装饰性 UI 掩盖分析逻辑；
7. 从不存在的数据关系生成解释；
8. 把随机波动包装成 Insight；
9. 补造数据；
10. 页面“看起来像 Dashboard”但不能回答业务问题；
11. 用长篇分析文字替代可操作的信息架构；
12. 把所有 Finding 都塞进首页。

## 10. Dashboard Build Pipeline

```text
Input Data
→ Data Understanding
→ Business Modeling
→ Analytical Model
→ Portfolio Synthesis
→ Information Architecture
→ Visualization
→ Interaction
→ UI Implementation
→ Quality Evaluation
→ Revise
→ Final
```

禁止直接执行：

```text
Data → Chart → HTML
```

## 11. 最终自问

发布前必须能明确回答：

1. 这个 Dashboard 最核心解决什么问题？
2. 用户第一眼应该发现什么？
3. 用户能够发现哪些异常？
4. 用户能够如何解释异常？
5. 用户能够如何定位对象？
6. 用户能够如何继续下钻？
7. 哪三个模块最重要？
8. 哪些模块删除后不会影响业务判断？

如果第 1–6 项不能清晰回答，Dashboard 未完成。
