# ChainSpec

- mode：direct | chain
- reason：复杂度信号编号，少于两项为 direct
- coverage：每条 TaskSpec.acceptance → 执行产物及重测活动

## steps（仅 chain）
| id | atom | input_from | output_name | check | on_fail |
|---|---|---|---|---|---|
| ... | ... | 用户输入/TaskSpec 字段/上步产物 | ... | ... | retry(n)/fallback(atom)/stop |

## branches（需要时）
- when：可观察条件 → 指向 step
