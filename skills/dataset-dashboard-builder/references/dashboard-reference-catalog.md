# Dashboard Reference Catalog

目标：让模型复用专业 Dashboard 的**工作流与构图骨架**，而不是从空白 HTML 自由拼装。

公开依据：

- Microsoft Power BI：Dashboard 是单页 overview，应突出最重要信息，并尽量在一个屏幕完成主要判断。https://learn.microsoft.com/en-us/power-bi/create-reports/service-dashboards-design-tips
- Power BI Sales & Marketing Sample：围绕 market share、sales、competition、time、region 组织管理视图，而不是按字段逐图展示。https://learn.microsoft.com/en-us/power-bi/create-reports/sample-sales-and-marketing
- Power BI Store Sales Sample：围绕 current vs last year、variance、margin、store/district 等业务比较组织页面。https://learn.microsoft.com/en-us/power-bi/create-reports/sample-store-sales
- Looker Dashboard Quickstart：把 Top Spenders、Sales Goal Tracking、Shipping Trends 组合成可继续下钻的业务工作流。https://docs.cloud.google.com/looker/docs/looker-core-create-dashboard-quickstart
- Looker Best Practice：隐藏无关字段，把常用工作流和 aggregate → detail drill 内置到分析体验。https://docs.cloud.google.com/looker/docs/best-practices/how-to-create-a-positive-experience-for-looker-users

## 1. Reference Selection Gate

Mission Contract + Primary Analysis Model 明确后选择一个 Primary Archetype。

选择输入：

```text
Audience
+ Decision / Action
+ Dashboard Mode
+ Primary Analysis Model
+ Comparison Basis
+ Core Objects
+ Evidence Path
```

禁止按“哪个模板更漂亮”选择。

## 2. Golden Index

每次正常生成只读取一个 Primary Golden；确有第二个独立工作流时才读取第二个。

| Archetype | Golden file | 典型 Primary Model |
|---|---|---|
| executive | `goldens/executive-performance.md` | Performance / Variance |
| monitoring | `goldens/monitoring-state.md` | Change / Trend + Process |
| investigation | `goldens/investigation-diagnostic.md` | Change / Contribution / Concentration |
| operational | `goldens/operational-queue.md` | Operational Queue / Process |
| exploration | `goldens/exploration-comparison.md` | Distribution / Contribution / Concentration / Relationship |
| entity | `goldens/entity-360.md` | entity history / peer / process |

Golden 是可执行的结构先验：包含 primary viewport wireframe、component budget、required business logic、interaction 和 avoid 列表。

## 3. Reference Fit Gate

生成前记录：

```text
Primary Archetype:
Golden file:
Why it fits:
Primary Analysis Model:
Primary viewport:
Required interaction:
Slots removed because unsupported:
```

生成后检查：

1. 去掉颜色、圆角和品牌后，页面结构是否仍能看出所选 Archetype？
2. Primary viewport 是否遵循 Golden 的 decision path？
3. Analysis Model 的 required calculations 是否真的有对应 view？
4. 交互是否推动 compare / investigate / locate / verify？
5. 是否复制了 Golden 中当前数据不支持的 slot？

如果只复制了卡片样式或图表类型，Reference Fit = FAIL。

## 4. Dashboard / Report Boundary

Golden 只提供业务工作区，不提供分析报告目录。

默认禁止业务页面顶层出现：

`WHAT / SO WHAT / WHY / WHO / EVIDENCE / PROVENANCE / METHOD / QA / REGRESSION`

也默认不显示：

`Primary / Driver / Guardrail / Diagnostic / Context / Exploration / Executive / Investigation`

这些是内部角色与路由标签。最终 UI 使用真实业务语言。

## 5. Custom Composition

没有 Golden 适用时允许 custom，但必须明确：

- Primary Job；
- Primary Analysis Model；
- 2–5 个 Decision Questions；
- primary viewport composition；
- component budget；
- comparison strategy；
- interaction path；
- evidence path；
- 为什么六类 Golden 都不适用。

Custom 不等于自由堆组件。