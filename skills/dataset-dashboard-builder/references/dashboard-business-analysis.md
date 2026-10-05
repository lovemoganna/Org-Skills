# Dashboard Business Analysis Contract

目标：让 Dashboard 的业务价值来自“可判断的比较与分解”，而不是数字数量、图表数量或分析术语数量。

## 1. Primary KPI Eligibility Gate

一个指标只有同时满足下列条件，才有资格成为 Primary KPI：

`Metric definition + Population / Period + Comparator + Delta / Difference + Decision Polarity + Driver Path + Evidence Path`

缺任一关键项时优先降级为 Driver / Diagnostic / Context，而不是强行放 KPI Card。

## 2. Comparator Gate

合法 comparator 只能来自真实证据：

- target / SLA / policy；
- prior comparable period；
- peer / control / segment；
- historical baseline；
- benchmark；
- same-view comparable object。

没有 comparator 时必须写清 `no meaningful comparison available`，并把数字降级为 Context Metric。禁止为了让 Dashboard “像 KPI”而生成目标、同比或阈值。

## 3. Decision Polarity Gate

Primary KPI 必须说明这个差异为什么影响决策：higher is better / lower is better / target band / two-sided deviation / neutral descriptive。

如果业务没有给出方向，数据本身也无法证明方向，则保持 neutral。禁止用绿/红、上/下箭头暗示价值判断。

## 4. Driver Proof Gate

`current largest ≠ change driver`。

解释变化时优先回答：总变化多少？谁贡献了变化？贡献方向和幅度是多少？去掉最大贡献者后结论还成立吗？

只展示当前 TopN 不能证明 driver。

## 5. Measure Decomposition

### Additive amount

优先检查 `amount = count × typical ticket = breadth × intensity × concentration`。根据数据粒度选择可验证分解，不要求机械全部计算。

### Ratio Decomposition

ratio 必须回到 `numerator / denominator`。比较两个 ratio 时至少展示 denominator；样本过小时降级。

### Duration / Latency

不能只看平均值。优先 median、P75 / P90（样本支持时）、tail / breach、N。

### Status / Funnel

保留真实状态语义，重点检查 conversion / completion、in-process / backlog、failed / cancelled / loss、aging / time-to-complete。

### Concentration

至少检查 Top1、Top2 / Top3、cumulative share、remove-Top1 / alternate denominator。

## 6. Actionability Gate

主要 Finding 必须映射到至少一个真实动作类型：monitor / compare / investigate / locate / verify。

“值得关注”“持续观察”本身不是动作。没有 case / owner / policy 时，不生成 freeze / assign / close 等业务动作。

## 7. Mode Downgrade Gate

Dashboard Mode 必须与证据能力匹配：

- 有可靠 current + baseline/target → monitoring / executive 可以成立；
- 有 focal problem + comparator + diagnostic path → investigation；
- 有 queue / state / owner / SLA / aging → operational；
- 只有静态切片、没有绩效基线 → exploration；
- 只有对象历史与 peer → entity。

如果数据无法支撑当前 Mode，必须降级 Mode，而不是补造 KPI、比较或动作。

## 8. Business Analysis Acceptance

最终页面至少让用户在不读取方法说明的情况下回答：

1. 我在看什么范围？
2. 与什么相比？
3. 差异多大？
4. 谁 / 什么贡献了差异？
5. 哪个对象或例外值得继续查？
6. 下一步从哪里进入证据？

如果数据无法回答其中某项，明确缺口；不得用 narrative 填空。
