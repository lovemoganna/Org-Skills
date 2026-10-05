# Golden: Executive Performance

适用：管理者需要周期性判断业务绩效；必须有真实 comparator。

## Primary viewport

```text
┌ Scope / period / comparator ────────────────────────────────┐
│ KPI 1: actual | comparator | delta   KPI 2 ...  max 2–4   │
├──────────────────────────────┬──────────────────────────────┤
│ Primary trend / variance     │ Driver contribution         │
│ largest visual              │ waterfall / ranked delta    │
├──────────────────────────────┴──────────────────────────────┤
│ Guardrail / material exception + drill entry               │
└─────────────────────────────────────────────────────────────┘
```

## Component budget

- Primary KPI：2–4；
- Primary chart：1；
- Driver view：1；
- Guardrail / exception：0–1；
- Detail：不占首屏，通过 drill。

## Required business logic

- actual vs target/prior/peer；
- delta；
- contribution to delta；
- denominator / N when rate；
- no comparator → 不得使用此 Golden。

## Interaction

KPI / driver 可 drill 到 business area 或 entity；filter 不得替代主比较。

## Avoid

- 8+ KPI cards；
- 裸总量；
- evidence queue 作为首页主体；
- 目标不存在却自造 target。