---
name: org-literate-engineering
description: 将编程文章、脚本、教程、查询和笔记转成干净、可执行、可参数化、可复用、可验证、可自动修复、可受控积累经验的 Org Mode / Org Babel 文学编程系统。适用于 Org Mode、Org Babel、文学编程、可执行教程、#+call、:var、noweb、tangle、代码块复用、Org 调试和 E2E 验证，以及 Python / Shell / SQL / DuckDB / JavaScript 等代码教程的可执行化。
---

# Org Literate Engineering

## 0. Purpose

把编程材料转成：

~~~text
短
干净
可执行
可参数化
可复用
可验证
可修复
可回归
可积累稳定经验
~~~

核心目标：

~~~text
复杂性留在内部
用户最终只看到完成任务所需的最小文学编程内容
~~~

Loop 是内部执行机制，不是正文内容。

---

# 1. Trigger

出现以下需求时启用：

~~~text
Org Mode
Org Babel
文学编程
可执行教程
可执行笔记
变量透传
#+call
:var
noweb
tangle
代码块复用
Org 自动化
Org 调试
Org E2E 验证
Python / Shell / SQL / DuckDB / JavaScript 等代码材料可执行化
~~~

即使用户没明确说 Org Mode，只要目标是：

> 把编程材料变成可执行、可参数化、可反复实验的学习或工程系统。

也可以启用。

---

# 2. Non-Goals

本 Skill 不负责：

~~~text
把普通文章机械改成 .org
为了“教程完整”补百科知识
为了展示 Org 技巧堆 header args
把 Loop / Eval / Memory 日志写进正文
无依据重写正确代码
无限反思或无限自提示
把单次 Case 经验直接写成长期规则
~~~

---

# 3. Input Contract

最低输入：

~~~text
material:
  编程文章 / 教程 / 脚本 / 查询 / 笔记

language:
  编程语言或 Runtime
~~~

推荐输入：

~~~text
material:
language:
runtime:
goal:
environment:
constraints:
~~~

信息足够时直接执行。

禁止要求用户重复提供已知信息。

---

# 4. Core Loop

统一执行模型：

~~~text
Material
→ Reverse Engineer
→ Variable Extraction
→ Org Design
→ Execute
→ Eval
→ State
→ Decision
   ├─ FAIL → Diagnose → Minimal Patch → Execute
   ├─ BLOCKED → Degraded Verify / Stop
   └─ PASS → Regression → Memory Gate → Stop
~~~

原则：

~~~text
固定逻辑只写一次
变化部分尽量参数化
正确内容默认锁定
修改必须由证据驱动
Loop 必须收敛
最终正文必须比内部过程更短
~~~

---

# 5. Reverse Engineer

先逆向材料，不急着生成 Org。

识别：

| Object | Question |
|---|---|
| Goal | 材料真正要教会或完成什么 |
| Runtime | 谁执行代码 |
| Source | 数据 / 文件 / API / 代码来自哪里 |
| Fixed | 哪些逻辑不应反复修改 |
| Variable | 用户以后最可能修改什么 |
| Output | 最终结果是什么 |
| Dependency | Block 之间如何依赖 |
| Contract | 输入输出必须满足什么 |
| Side Effect | 是否写文件或修改外部状态 |
| Risk | 哪些操作不可逆 |

重点扫描：

~~~text
文件路径
URL
Sheet
Table
Column
函数参数
阈值
时间范围
过滤条件
排序
分组
输出格式
运行环境
~~~

只提取与材料主题和用户目标直接相关的内容。

---

# 6. Variable Extraction

变量分成：

~~~text
Data Variable
Structure Variable
Environment Variable
Execution Variable
~~~

判断规则：

> 用户下一次可能只想改这个值，而不想重新理解整段代码，则优先参数化。

示例：

~~~text
sheet="users"       → Structure
min_amount=10000   → Data
xlsx_url="..."     → Environment
limit=20           → Execution
~~~

---

# 7. Org = Source of Truth

统一：

~~~text
Org
↓
Babel
↓
Runtime
↓
Result / Artifact
~~~

说明、参数、代码、调用、结果和验证优先维护在 Org 中。

禁止同时手工维护一份重复脚本。

需要外部程序文件时：

~~~text
Org
→ :tangle
→ Generated File
→ Runtime
~~~

生成文件不是长期事实源。

---

# 8. Org Technique Selection

只使用能真实降低重复、建立依赖、改善执行或验证的 Org 能力。

优先考虑：

~~~text
#+name
:var
#+call
:results
:tangle
:noweb
:session
:cache
:dir
:file
:cmdline
:exports
#+PROPERTY
Org Table
~~~

但必须满足：

~~~text
Backend 支持
+
当前任务需要
~~~

禁止为了显得高级而堆 Org 技法。

判断：

> 删除这个 Org 特性后，复用、依赖、执行或验证是否变差？

否：不用。

---

# 9. Named Block

固定逻辑需要复用时使用命名 Block：

~~~org
#+name: calculate
#+begin_src python
...
#+end_src
~~~

原则：

~~~text
固定逻辑 → Block
变化内容 → 参数
~~~

禁止复制多个几乎相同的 Block。

---

# 10. Parameterization with :var

高频变化内容优先用 `:var`：

~~~text
文件
Sheet
Table
Column
阈值
时间范围
字段
过滤条件
limit
函数输入
~~~

示例：

~~~org
#+name: squares
#+begin_src python :var n=10
result = [x**2 for x in range(n)]
return result
#+end_src
~~~

不要让用户每次进入实现内部修改常量。

---

# 11. Minimal Call

已经封装好的 Block，日常调用尽量缩短为：

~~~org
#+call: squares(n=6)
~~~

目标：

> 用户操作参数，不重复编辑实现。

---

# 12. Org Table as Data

Org Table 能直接作为输入时，不额外复制成 JSON / CSV / Python List。

~~~org
#+name: orders
| user | amount |
|------+--------|
| A    |   1000 |
| B    |   5000 |

#+name: summarize
#+begin_src python :var rows=orders
...
#+end_src
~~~

让数据与代码形成真实依赖。

---

# 13. Block Dependencies

Block B 依赖 Block A 时，明确表达依赖，不复制结果。

根据 Backend 能力选择：

~~~text
:var
#+call
:noweb
:session
文件 Artifact
~~~

优先使用最简单、最透明的依赖方式。

依赖扫描优先使用 Org 语法树（如 `org-element`），不要对全文机械跑正则。

只解析真实执行区域：

~~~text
Source Header / Body
#+call
:var
:noweb
:tangle
文件输入输出
~~~

排除普通正文、quote、comment、example 和纯展示语法。

无法做语法级依赖分析时标记：

~~~text
DEPENDENCY_SCAN_DEGRADED
~~~

---

# 14. Noweb

Noweb 只用于真实代码组合。

如果普通函数、`:var` 或 `#+call` 已能解决：

~~~text
不要使用 noweb
~~~

原则：

> 使用最低复杂度表达真实依赖。

---

# 15. Tangle

需要真实 `.py` / `.sh` / `.el` / `.sql` / `.js` / 配置文件时使用 `:tangle`。

~~~org
#+begin_src python :tangle app.py
...
#+end_src
~~~

禁止手工把 Org 中代码复制到外部文件后双份维护。

运行错误必须回溯到来源 Org Block 修复，再重新 tangle。

`:tangle` 只声明生成目标，不代表文件已经生成。下游 Block 依赖 Tangle 产物时，执行链必须显式包含 Tangle，再确认 Artifact 存在，最后执行下游 Block。禁止假设 `org-babel-execute-buffer` 会自动完成 Tangle。

如果 `:tangle` 目标的父目录或执行使用的 `:dir` 可能不存在，使用 `:mkdirp yes`。不要假设 `:dir` 会自动创建目录。

`:tangle` 属于 WRITE，遵守第 35 节 Side Effect Gate。

---

# 16. Session

默认：

~~~text
Stateless First
~~~

只有明确需要：

~~~text
共享运行状态
交互式实验
昂贵初始化
REPL 工作流
~~~

才使用 `:session`。

禁止隐藏依赖前序 Session 状态。

---

# 17. Cache

只有纯计算且 Cache Key 覆盖全部真实依赖时才缓存。

以下情况默认谨慎或禁用：

~~~text
远程数据
文件变化
Noweb 隐式依赖
环境状态
时间变化
随机数
Stateful Session
API freshness
~~~

Cache 不能制造假 PASS。

---

# 18. Results

`:results` 只服务于理解与验证。

只保留：

~~~text
直接回答问题的结果
必要中间结果
断言结果
生成 Artifact
~~~

按场景使用：

~~~text
value
output
table
file
silent
~~~

禁止大量终端噪声污染 Org。

---

# 19. Generate

不要固定生成同一模板。

默认按材料实际需要选择最小结构，例如：

~~~org
#+TITLE: <topic>

* <concept / task>
一句必要说明。

#+name: <block>
#+begin_src <language> <minimal headers>
...
#+end_src

#+RESULTS:
...
~~~

需要参数时加参数。
需要复用时加调用。
需要验证时加验证。
不需要的章节不要生成。

---

# 20. Literate Content Purity

文学编程正文只允许保留：

~~~text
完成当前任务必须知道的说明
实际可执行代码
必要参数
输入输出关系
必要运行步骤
直接影响理解的解释
必要验证结果
~~~

禁止写入：

~~~text
AI 分析过程
Loop 日志
Eval 日志
Memory 讨论
Agent 架构解释
调试流水账
与原材料无关的知识扩展
为了教学完整补的背景知识
重复解释代码已经表达清楚的内容
泛化最佳实践
无实际作用的小结
套话
过渡废话
重复总结
~~~

每个自然语言段落必须至少回答一个问题：

~~~text
帮助理解当前代码？
帮助修改当前代码？
帮助运行当前代码？
帮助验证结果？
帮助定位错误？
~~~

全部为否：

~~~text
DELETE
~~~

代码已经表达清楚：不解释。

一个说明删除后不影响执行、理解、修改、验证：必须删除。

---

# 21. Source Boundary

Loop 只能提高执行质量，不能扩大内容范围。

最终正文严格围绕：

~~~text
用户输入材料
用户真实任务
原材料主题
当前代码
当前结果
~~~

默认规则：

> 原文没有、任务不需要、验证不依赖，就不要输出。

需要外部事实才能正确执行时，可以补最少必要信息，并标明来源；不得借机扩写教程。

---

# 22. Explain Through Execution

需要解释机制时，优先顺序：

~~~text
输入
↓
实际执行代码
↓
运行结果
↓
一句必要机制
~~~

禁止先写长篇语法百科。

---

# 23. Expanded Source First

动态变量、Noweb、Call、模板或执行异常时，优先还原：

~~~text
原始 Block
+
Header Args
+
变量
+
Noweb
+
Call
↓
最终实际执行代码
~~~

诊断最终执行代码，不只看 Org 模板。

---

# 24. Block Contract

重要 Block 定义：

~~~text
Input Contract
Execution Contract
Output Contract
Assertions
~~~

始终遵循：

~~~text
执行成功 ≠ 结果正确
~~~

简单示例无需把 Contract 全部写进正文；可以作为内部 Eval 规则存在。

---

# 25. Execute

环境允许时必须真实执行。

验证链：

~~~text
Org
↓
Babel Backend
↓
Runtime
↓
Variables
↓
Expanded Source
↓
Execution
↓
Result
↓
Assertions
~~~

禁止静态阅读后声称“已验证”。

记录实际 Runtime 和关键版本。

执行失败时先确认：

~~~text
Backend
→ Runtime / 方言
→ Advice / Hook / Extension
→ Core Function
~~~

环境问题不得误修成业务代码问题。

---

# 26. Eval Contract

每轮执行后只允许：

~~~text
PASS
FAIL
BLOCKED
~~~

Eval 基于：

~~~text
用户目标
材料明确行为
Block Contract
Assertions
实际执行结果
~~~

禁止“感觉不错”式评估。

---

# 27. Eval Self-Check

实现结果与 Expected / Eval 冲突时，不得默认实现错误。

检查：

~~~text
Implementation
Eval
Expected
Source
~~~

由证据决定修改哪一方。

禁止为了通过错误测试而破坏正确代码。

---

# 28. State Contract

每轮只保留：

~~~text
已验证事实
已完成事项
失败原因
未解决问题
当前约束
下一步动作
~~~

禁止把上一轮完整输出重新塞回下一轮。

禁止把无关解释、模型自言自语、重复代码和完整聊天历史写入 State。

State 的目标是推进任务，不是保存对话。

---

# 29. Diagnose

错误统一按最短因果链定位：

~~~text
现象
↓
直接原因
↓
根因
↓
最小修改位置
~~~

常见分类：

~~~text
ORG
BABEL
HEADER
VARIABLE
DEPENDENCY
RUNTIME
VERSION
PATH
DATA
CODE
RESULT
CALL
NOWEB
TANGLE
FILE
CONTRACT
ENVIRONMENT
EVAL
~~~

禁止输出模糊诊断：

~~~text
可能有问题
建议检查
可以尝试
~~~

---

# 30. Repair Loop

FAIL 时：

~~~text
FAIL
→ Diagnose
→ Minimal Patch
→ Execute
→ Eval
~~~

原则：

~~~text
Correct Content = Locked
Broken Content = Patch
~~~

修复优先级：

~~~text
参数
> 环境
> Header
> 语法
> 局部逻辑
> 依赖
> 结构
> 整体重构
~~~

禁止：

~~~text
局部错误导致整体重写
顺手优化无关内容
删除正确功能
改变用户目标
通过升级版本逃避兼容问题
~~~

---

# 31. Regression

每个重要能力维护 Golden Case：

~~~text
Input
Expected
Actual
Status
~~~

修复后至少验证：

~~~text
原失败 Case
受影响 Block
历史 Golden Case
一个相邻泛化 Case
必要边界 Case
~~~

当前修好了，历史能力不能被破坏。

---

# 32. Stop Contract

满足以下条件立即停止：

~~~text
目标完成
关键 Assertion PASS
受影响 Regression PASS
无未解决阻塞
~~~

以下情况也停止：

~~~text
继续循环没有有效增量
剩余变化只是低价值润色
开始损害历史能力
必要外部信息缺失
达到明确边界
~~~

禁止：

~~~text
无限反思
无限自提示
为了继续优化而继续修改
~~~

---

# 33. Memory Gate

不是每次执行都写长期记忆。

候选经验必须经过：

~~~text
Observation
→ 可复现？
→ 已验证？
→ 具有跨 Case 价值？
→ 与现有 Memory 冲突？
→ Promote / Reject
~~~

长期 Memory 只允许保存：

~~~text
稳定规则
重复失败模式
有效修复方法
验证方法
兼容边界
回归 Case
~~~

禁止写入：

~~~text
具体用户数据
具体 URL
单次任务细节
未经验证的模型推断
临时状态
文章里的偶然示例值
~~~

同一条 Memory 连续两次误导任务：

~~~text
降级
→ 隔离
→ 修正或删除
~~~

Memory 是可维护资产，不是更长的上下文。

---

# 34. Dreaming / Maintenance Loop

周期性维护 Memory 时执行：

~~~text
去重
→ 冲突检测
→ 事实核验
→ 过期检测
→ 经验晋升
→ 错误降级
→ Memory Diff
→ Regression
~~~

Dreaming 不得自动把所有新观察提升为长期规则。

任何长期规则变化必须可回滚。

---

# 35. Side Effect Gate

Block 分类：

~~~text
PURE
READ
WRITE
DESTRUCTIVE
EXTERNAL
~~~

策略：

~~~text
PURE / READ
→ 自动执行

WRITE
→ 隔离 / staging → Preview / Diff → Run / Publish

DESTRUCTIVE
→ 默认禁止自动执行
~~~

高风险示例：

~~~text
DROP
DELETE
UPDATE
rm
覆盖文件
修改配置
外部 API 写入
~~~

---

# 36. Degraded Verification

原生 Org / Babel Backend / Runtime 不可用时：

~~~text
Native capability → BLOCKED
Runtime-equivalent / Static Check → 可继续
~~~

必须分账。

等价验证不能冒充 Babel-native PASS。

只有原生适用项真实通过后才允许输出：

~~~text
LITERATE_PROGRAMMING_PASS
~~~

---

# 37. Verification Closure

验证集合：

~~~text
实际使用能力
∪ 可执行 Source Blocks
∪ Assertion Coverage
∪ Dependency
∪ Negative / Boundary Cases
∪ Regression
∪ Document / Export Checks（如适用）
~~~

典型 Org/Babel 能力按实际使用选择：

~~~text
Babel Base
Runtime
:var
Org Table → Code
Block → Block
#+call
Noweb
Tangle
Tangled File Execution
File Artifact
Dependency
Contract
Full Workflow
~~~

不用的能力标记 N/A，不为了测试矩阵强行加入正文。

---

# 38. Export Integrity

需要导出 HTML / PDF 时，再验证：

~~~text
Org Parse
→ org-lint（可用时）
→ Strict Export Smoke Test
→ Broken Link / Syntax Check
~~~

禁止通过放宽 broken-link 设置掩盖错误。

---

# 39. Skill Bug vs Case Bug

Case Bug：

~~~text
字段写错
路径错误
材料缺失
单次数据异常
当前代码局部 Bug
~~~

处理：修 Case，不改 Skill。

Skill Bug 只有在：

~~~text
同类问题重复发生
或
明确暴露通用机制缺陷
~~~

才成立。

修改 Skill 前必须有：

~~~text
真实执行证据
通用机制问题
局部修复不足
明确预期收益
最小修改范围
可验证收益
可运行历史回归
~~~

任一不满足：

~~~text
DO_NOT_MODIFY_SKILL
~~~

---

# 40. Anti-Overfitting

禁止因为一个用户、一个教程、一组数据、一个字段、一次失败或一个特殊 Runtime，把样例特例写进 Skill。

新增规则必须：

~~~text
可解释
可泛化
可验证
~~~

否则留在 Case 层。

---

# 41. Output Contract

默认最终只输出用户真正需要的文学编程产物和必要验证状态。

禁止默认输出：

~~~text
Reverse Engineer 报告
完整 Loop 日志
State 内容
Memory 内容
Agent 方法论
内部 Eval 推理
无关扩展说明
~~~

如果用户明确要求调试过程，再单独输出必要证据。

---

# 42. Output Compression

每句话必须至少增加一种：

~~~text
事实
机制
边界
动作
验证
~~~

否则删除。

全文再做一次删除检查：

> 删除后是否影响任务完成、代码理解、实际执行或结果验证？

四项都不影响：

~~~text
DELETE
~~~

同一事实只说一次。
同一结论只留一个权威位置。
过程日志默认删除。

---

# 43. Output Voice

面向人类的文字：

~~~text
短句
直接
具体
主动语态
少套话
少总结
不做百科式扩写
~~~

技术精确性高于文风。

不得为了“像人话”修改数字、代码、命令、断言或边界。

---

# 44. Final Acceptance

完成前检查：

~~~text
[ ] 是否只围绕原材料和用户目标？
[ ] 文学编程正文是否无垃圾信息？
[ ] Org 是否为 Source of Truth？
[ ] 固定逻辑是否只写一次？
[ ] 高频变化是否参数化？
[ ] Org 技法是否有真实收益而非炫技？
[ ] Block 依赖是否清晰？
[ ] 用户日常操作面是否足够小？
[ ] 是否真实执行而非静态声称？
[ ] 是否验证结果而非只验证“跑过”？
[ ] Eval 本身是否可能有错并得到检查？
[ ] FAIL 是否只做最小 Patch？
[ ] 是否完成必要 Regression？
[ ] Loop 是否达到 Stop 条件？
[ ] Memory 是否只晋升验证过的跨 Case 规则？
[ ] 原生验证与降级验证是否分账？
[ ] 最终输出是否删除内部 Loop / Eval / Memory 垃圾？
~~~

全部适用项通过才结束。

---

# 45. Success Criterion

成功不是“生成一个 Org 文件”。

成功是换语言、换 Runtime、换材料、换任务后，只改变输入，核心 Skill 无需重写，仍能：

~~~text
逆向
→ 参数化
→ 选择最小 Org 技法
→ 生成干净正文
→ 执行
→ Eval
→ 修复
→ 回归
→ 收敛
→ 必要时积累稳定经验
~~~

最终原则：

> 内部形成可靠 Loop；外部只留下一个干净、短小、可执行、可修改、可验证的 Org 文学编程系统。
