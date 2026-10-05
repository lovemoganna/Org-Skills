# Golden: Operational Queue

适用：用户每天需要处理记录、对象、积压、SLA 或状态队列。

## Primary viewport

```text
┌ Scope / owner / queue filters ──────────────────────────────┐
│ Backlog | oldest/aging | SLA/breach if authoritative       │
├─────────────────────────────────────┬───────────────────────┤
│ Primary queue table                 │ Selected object       │
│ priority · age · state · owner      │ detail / timeline     │
│ records occupy most width           │ evidence / action     │
├─────────────────────────────────────┴───────────────────────┤
│ Small trend / workload context only if useful               │
└─────────────────────────────────────────────────────────────┘
```

## Required business logic

- queue population；
- priority basis；
- aging / due / breach when supported；
- owner or entity；
- record-level evidence。

## Interaction

row select → detail；filters update queue and summary consistently；操作按钮只能来自真实 workflow。

## Avoid

- KPI cards 占据主要视口；
- 先放趋势再让用户滚动找 queue；
- 自造 SLA / risk threshold。