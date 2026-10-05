# Golden: Entity 360

适用：围绕单个 customer/account/product/order 等稳定对象做状态与历史核查。

## Primary viewport

```text
┌ Entity identity + scope ────────────────────────────────────┐
│ status | peer/baseline comparison | key current attributes │
├──────────────────────────────┬──────────────────────────────┤
│ Timeline / history           │ Peer / segment comparison   │
├──────────────────────────────┴──────────────────────────────┤
│ Related events / records / evidence                         │
└─────────────────────────────────────────────────────────────┘
```

## Required business logic

- stable entity key；
- current state or scope state；
- peer/history comparator when available；
- event timeline；
- related records。

没有 comparator 时保持 descriptive，不用红绿评价。

## Interaction

entity selector / search；timeline event → record detail；保留对象上下文。

## Avoid

- 把全局 overview 和 entity detail 混成同一主任务；
- 只显示 profile card；
- 无历史却伪造 trend。