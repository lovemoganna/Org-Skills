# Golden: Investigation Diagnostic

适用：围绕已知变化、异常或问题解释“为什么”。

## Primary viewport

```text
┌ Focal metric + comparator + delta ──────────────────────────┐
├──────────────────────────────┬──────────────────────────────┤
│ Focal trend / before-after   │ Driver / contribution       │
│                              │ decomposition               │
├──────────────────────────────┼──────────────────────────────┤
│ Segment / entity diagnostic  │ Counterexample / robustness │
└──────────────────────────────┴──────────────────────────────┘
          ↓ drill
      evidence / records
```

## Component budget

- Focal metric：1 dominant；
- comparator/delta：必须同屏；
- driver views：1–2；
- robustness：1 compact；
- evidence：drill，不写成长篇 narrative。

## Required business logic

- confirm movement；
- contribution / decomposition；
- competing explanation；
- counterexample；
- actor/record attribution when possible。

## Copy

标题描述测量对象，例如“转化率变化”“订单延迟驱动”，不要使用 WHAT / WHY / ROOT CAUSE 等过程词。

## Avoid

- 结论段落先于证据；
- current TopN 当 change driver；
- 每张图下固定 So-What 文案框。