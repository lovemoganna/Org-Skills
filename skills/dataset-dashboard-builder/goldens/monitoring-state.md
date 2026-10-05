# Golden: Monitoring State

适用：周期性监控当前状态是否偏离 baseline / SLA / prior。

## Primary viewport

```text
┌ Scope + refresh/as-of + baseline ───────────────────────────┐
│ Current vs baseline      Current vs baseline      Guardrail │
├────────────────────────────────────────────┬────────────────┤
│ Main trend with baseline / band            │ Exceptions     │
│                                             │ compact list   │
├────────────────────────────────────────────┴────────────────┤
│ One diagnostic split / drill entry                          │
└─────────────────────────────────────────────────────────────┘
```

## Required business logic

- current state；
- valid baseline / threshold / prior；
- complete time bucket；
- exception definition；
- affected object count / amount where relevant。

没有合法 baseline 时，切换 exploration / investigation。

## Interaction

点击 exception 保留 filter/context 进入 entity/record；趋势选择只做定位，不改指标口径。

## Avoid

- 只有 current number；
- 无 baseline 的红绿灯；
- 每个 status 都做 KPI 卡。