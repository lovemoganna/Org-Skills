决策：**PATCH**

替换“测试入口与执行边界”一节为以下内容；原始调用提示和历史任务语义保留不变。

```org
* 测试入口与执行边界
本页统一保存 S01–S13 和 T01–T10，两组是独立测试资产，不能合并通过率或互相代替。本节的历史调用入口只针对 sql-business-thinking 的 S 组；它不执行 T 组，也不代表本页任何案例已经运行。

执行时先读取实际 HEAD 对应的当前 Skill，按原本定义执行。探索性运行不等于发现可泛化的缺陷，更不能仅凭一个失败样本直接修改 Skill。

#+begin_example
按 skill-lab 测试 sql-business-thinking。
先按当前 Skill 原样执行。
把本任务视为 exploratory，不要因为单一样本直接修改 Skill。
如果发现可泛化缺陷，再进入修正和回归流程。
#+end_example

T01–T10 应分别使用对应案例提示，按 ontology-constrained-analysis 的要求执行并记录真实回执；不得将上述 sql-business-thinking 调用当作 T 组测试入口。测试当前双 Skill 时，应另建适配用例：由 business-reasoning 产出 Analysis Packet，由 analysis-verifier 依据原始数据白名单、固定 SQL 和执行环境独立验收。禁止静默改写历史提示或凭预期结果宣布测试通过。参见 [[wiki:c7fa8c19-59d3-49c1-a786-72f102daa568][入口版本说明]]。

以上为 2026-10-04 原始测试要求，保留作为历史任务语义。测试用例必须留下真实输入、输出、执行记录和可核验的裁决，未运行不可写为通过。历史独立任务原文见 [[https://github.com/lovemoganna/org-notes/blob/f947b20b84ccaefaab40f43a699c875110ebff00/notes/programming/sql-business-thinking/b31e6f82-9a47-4c05-8d2b-71f6a93e5c20.org][Git 快照]]。
```

