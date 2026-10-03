# Domain Intelligence Routing

目标：让 `dataset-dashboard-builder` 在通用分析能力之上，加载与当前数据真实匹配的领域语义，而不是把所有数据集都当成 generic BI。

## 1. Domain Detection Gate

在 Source Map / Dataset Map / Quality Gate 之后执行。

先生成候选 Domain，不直接决定。

Domain 证据必须先满足对应 Domain Pack 自己的 **Detection Signature**，再检查以下三类证据：

1. **Entity evidence**：核心对象是否符合该领域语义；
2. **Event / state evidence**：事实表是否存在该领域典型事件、方向、阶段或状态；
3. **Dimension evidence**：字段是否出现该领域特有维度。

禁止把“有 entity + status + 某个常见字段”本身当作领域证据。字段名 `network / asset / channel / status` 在不同领域可能重名，必须结合事实粒度与事件语义判断。

只有：

- 用户显式指定领域；或
- 对应 Pack 的 Detection Signature 成立，且数据证据足够一致；

才允许加载 Domain Pack。

若存在多个合理领域，保留多候选并选择最能解释 Primary Business Question 的一个；必要时仅使用通用层，不强行分类。

## 2. Confidence

建议内部记录：

```text
Domain
Evidence
Confidence: high / medium / low
Missing evidence
Competing domain
```

规则：

- high：对象、事实事件、维度三层均一致；
- medium：两层一致，且没有明显冲突；
- low：只有字段名字像，或仅凭文件名 / 用户措辞猜测。

只有 high / medium 默认加载 Domain Pack。low 使用 generic。

## 3. Domain Pack Contract

Domain Pack 不是固定 Dashboard 模板。

它只提供：

- Domain Ontology；
- Event / State Model；
- Domain Question Library；
- Metric Roles；
- Investigation Playbooks；
- Exception Patterns；
- Entity Relationship Hints；
- Action / Evidence Model；
- Domain Visual Grammar；
- Domain Evaluation。

当前数据不支持的规则必须跳过。

禁止：

- 为了匹配 Domain Pack 补造字段；
- 为了凑齐模块生成无证据图表；
- 把候选异常规则当成已发生异常；
- 把领域经验覆盖 Source Authority / Quality / Unit / Time Gate；
- 因为加载了 Domain Pack 就绕过 Investigation / Robustness。

## 4. Execution Order

```text
Source / Quality
→ Domain Detection
→ Domain Pack
→ Dashboard Mission
→ Domain Question Map
→ Generic Analysis Depth
→ Investigation
→ Domain Composition
→ Dashboard Quality
```

Domain Pack 提供“该领域值得问什么”。

Generic Analysis / Investigation 负责证明“当前数据实际支持什么”。

## 5. Explicit Domain Override

用户明确指定领域时：

- 优先加载对应 Domain Pack；
- 仍需检查 Schema 是否能支持 Pack 中的对象和问题；
- 不支持的部分标记 unavailable，不得模拟。

用户明确要求 generic / neutral 时，不加载领域 Pack。

## 6. Generic Fallback

以下情况使用 generic：

- Domain confidence = low；
- 多领域混杂且无法确定主任务；
- 当前仓库没有对应 Domain Pack；
- 用户明确要求通用数据探索。

缺少 Domain Pack 不是阻塞条件。Skill 必须保持现有 generic 能力。
