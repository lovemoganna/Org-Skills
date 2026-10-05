# Golden: Exploration Comparison

适用：没有可靠绩效基线，目标是理解结构、差异、分布并选择对象继续探索。

## Primary viewport

```text
┌ Scope + high-value filters ─────────────────────────────────┐
├──────────────────────────────────┬───────────────────────────┤
│ Primary comparison / distribution│ Secondary relationship  │
│ largest analytical view          │ or concentration        │
├──────────────────────────────────┴───────────────────────────┤
│ Selectable segment/entity table + exact values              │
└──────────────────────────────────────────────────────────────┘
            ↓ selection
          detail / evidence
```

## Component budget

- Context numbers：0–3，不能伪装 performance KPI；
- Primary comparison/distribution：1；
- Secondary model：最多 1；
- selectable table/detail：1。

## Required business logic

优先使用 Distribution / Contribution / Concentration / Relationship。只有可比较完整时间序列时才把 trend 升为主视图。

## Interaction

filter 用于探索；关键比较必须同屏；点击 mark/row 进入 detail。

## Avoid

- North Star 强制存在；
- Guardrail / Context / Exploration 等内部角色显示给业务用户；
- 先放一排 KPI 卡再找问题；
- 所有图都有 narrative takeaway 卡。