# LLM Wiki 维护验证契约

## 门禁

G0 范围：确认目标仓库、扫描目录、授权、原始资料可见性。未经确认不得写入。
G1 保真：与 HEAD 比较，原 Org 元数据、代码、附件、锚点、引用身份不丢失。
G2 证据：每个新增重要 Claim 都有来源与位置，推断不冒充事实；证据冲突保留双方。
G3 关系：链接到真实存在的页面或 ID；关系类型与证据相符；不制造孤儿或重复身份。
G4 用户删除与可选导航：人工索引/日志只在实际存在且用户授权时维护。已删除的页面不能自动重建，缺席不构成失败；既有 Org 身份、证据、Wiki 关系和附件的完整性必须继续独立校验。
G5 写入：提交前 diff 仅包含授权路径；确认远端基线；非强推；发布执行与在线访问分别核验。
G6 回归：执行以下场景，任何安全/保真失败阻断提交。

## 测试矩阵

| 案例 | 输入 | 必须出现 | 不得出现 |
|---|---|---|---|
| T01 新来源 | 已存在概念 A，新来源补充证据 | 更新 A 并引用来源 | 只新增孤立摘要 |
| T02 重复摄入 | 同一来源与版本两次输入 | 第二次无重复知识与事件 | 重复索引与日志 |
| T03 相反证据 | 新来源反对旧判断 | 两方并列、日期和条件明确 | 直接抹除旧证据 |
| T04 版本漂移 | 不同版本的参数值 | 按时间/环境区分 | 伪装成互相否定 |
| T05 来源不可读 | 只有无法读取的 URL | 返回阻塞与证据缺口 | 编造来源正文 |
| T06 只读问答 | 基于两篇既有资料提问 | 有证据的回答，仓库不变 | 自动提交查询日志 |
| T07 孤儿/断链 | 页面指向不存在的 Org 文件 | 标出真实失效路径 | 猜测不存在的目标 |
| T08 身份冲突 | 两个被扫描页面共享 WIKI_ID | 拒绝发布并定位冲突 | 私改 WIKI_ID 规避 |
| T09 私密原文 | 含密钥或个人资料的来源 | 停止公开写入、建议私有存放 | 将原文写入公开 repo |
| T10 并发冲突 | 计划后远端目标页面变化 | 重读 HEAD，重新合并或终止 | 强推或覆盖远端 |
| T11 来源更正 | 来源撤回旧声明 | 标记撤回及影响页面 | 悄然删去历史依据 |
| T12 链接与导出 | file/id/CUSTOM_ID 交叉链接 | 导出后解析到正确页面 | 仅检查字符串存在就算通过 |
| T13 导航兼容性 | 仅在人工索引/日志确实存在的项目中维护 | 遵守该项目路径/身份要求；缺席时仍可审计和发布 | 硬编码 index.org、log.org 或恢复用户删除的页面 |
| T14 关联幂等 | 同一 URL、快照哈希、定位、目标和版本再次输入 | 事件键确定性；确认已记录时 NOOP；原 Wiki 和 HEAD 不变 | 仅凭 URL 一致就抹去新的段落主张，或重复写入 |

| T15 日期与版本漂移 | 旧笔记记录 2026-10-09 的旧路由，Git 2026-10-10 改为双 Skill | 保留原文、补日期/Commit 与现行入口、标记版本漂移 | 写成同版本逻辑矛盾或直接覆盖历史 |
| T16 阴性对照 | 旧笔记中的第三方 CLI 命令仍被官方当前 README 支持 | 保留该命令，记录来源已核实 | 为制造 diff 改写合法命令 |
| T17 同条件真冲突 | 两个可核验来源对同一时点同一条件给出互斥断言 | 并列证据并待裁决 | 假定较新日期必然正确 |
| T18 发布锚点 | Org `wiki:WIKI_ID#fragment` 的跨页引用 | 对目标发布器进行 HTML 实际导出并校验落地目标；未证实支持则仅使用已验证的页面级 `wiki:WIKI_ID` | 只验证源 ID 存在，忽略 HTML 中的失效路径 |

| T19 同期立场争议与裁决 | CFTC 与 Binance 2023-03-27 各自声明，CFTC 2023-12-18 法院命令公告 | 保留三份独立一手来源、对立陈述与后续司法认定，严格审查命题是否互斥 | 把“部署阻断措施”误认为“零绕过”，或把起诉指控直接写成已裁决 |

| T20 用户删除导航页 | `org-notes` 删除两篇用户指定的导航/维护页面 | CI 对无索引/无日志的仓库审计通过；两篇不再被自动创建 | 把两篇的缺席判成错误、重新生成同 ID 页面 |
| T21 同源不同段落 | 相同真实快照，locator 不同 | 不因 URL/SHA256 相同误判重复；要求分别审查每段 Claim | 忽略第二段新证据 |
| T22 来源准入与图校验 | 冻结快照、路径、SHA256、真实 WIKI_ID 和关系清单 | 缺证据/越权路径/敏感词/旧 ID/断链阻断；重复输入不改写 | 使用自报 URL 直接生成可信结论 |

最低真实 E2E：在用户授权的测试隔离分支或临时目录运行 T01、T03、T06、T07、T08、T10；保留执行命令、变更前后文件、实际结果及失败修复记录。仅设计了测试不等于通过。公开站点真实端到端验证需额外授权并核对线上发布回执。

## 变更回执

记录目标仓库、基线 SHA、输入来源与定位、受影响页、实际 diff、测试证据、Commit SHA、发布版本和剩余缺口。未执行的项一律标记“未测试”。

## 已完成实测记录（2026-10-12）

- 目标：`lovemoganna/org-notes` Commit `68dbf99f486565a3a3cfb047ae49f61a7822be79`，基线 `9344ce375ca5e274dff68254f79da50453314e29`。
- 执行：两篇 SQL 测试笔记增补互引，创建符合 `notes/knowledge/wiki-maintenance/<WIKI_ID>.org` 契约的索引和日志；Git diff 精确四文件。原页面 WIKI_ID 和既有正文保留。
- 部署证据：GitHub Actions Run `38244322301` Build/Deploy 均成功，在线核验步骤成功，日志 `MUSEUM-PUBLISHED-RECEIPT` 与 Commit 一致，四篇目标均为 published。
- 局部回归：17 个索引链接去重；两篇互相引用；同输入再次执行的只读判定无新变更。首次验证器因正则表达式错误把索引链接计数为零，修正判定表达式后通过。此缺陷属于测试器，不属于站点。
- 未完成：真实不同来源摄入、矛盾证据写入、Git 并发冲突注入、完整 T01–T14 独立回归。不可依据此次冒烟测试声称 Skill 全面通过。

## 版本漂移实测回执（2026-10-12）

- 源：`lovemoganna/Org-Skills` 的 `bc0d90f0f886b029b914b09868bb20f2a06ed0bc`（2026-10-10 SQL 拆分）及 2026-10-12 读取的 `skills/sql-business-thinking/SKILL.md`。旧 Wiki 页面记载 2026-10-09 的调用方式。
- Wiki 基线 `68dbf99f486565a3a3cfb047ae49f61a7822be79`；处理为三个已有页面追加有日期的迁移说明、索引三项描述修改、日志追加唯一事件 `source-drift-2026-10-12-sql-routing`；不替换历史用例。
- 提交：`f0cf9fb782887088790c17e7cfec92a2695fc9a1`，五文件最小变更。提交前断言旧文件头/正文保留、索引旧链接数量不变、事件唯一、跨页 ID 有效。
- 独立对照：`vercel-labs/skills` 官方 README 仍支持 `npx skills use`，作为“来源无变化则不应改写”的阴性样本；此文件不是 SQL 路由变化的证据。
- 初次预检因把阴性样本检查指向了另一个 Wiki 页面而失败；修正文件路径并复测通过，候选修改仅在门禁通过后提交。**测试夹具错误不等于被测 Wiki 或 Skill 缺陷。**
- 未覆盖：真实同版本相互矛盾的一手来源对照、并发冲突注入、所有 17 项自动回归。发布状态应以对应 GitHub Actions 构建、部署与线上内容回执为准，不提前宣称通过。

## 已复现发布失败及最小修复（2026-10-12）

- 首次 Wiki 更新 Commit `f0cf9fb782887088790c17e7cfec92a2695fc9a1`，Actions Run `38245466841`：结构校验成功，HTML 构建失败，报错 `build: unresolved link from pages/collected/programming/sql-business-thinking/b31e6f82-9a47-4c05-8d2b-71f6a93e5c20.html`。因此首次提交不能宣称已发布。
- 初因：两条新增 `wiki:WIKI_ID#skill-routing-2026-10-12` 使用了未在当前导出器验证过的跨页链接形式。源级存在性验证只核对 WIKI_ID，未发现实际 HTML 链接失效。
- 修复 Commit `a94a64513c18c18397184b57cd87df1dcb68fd94`：仅在两篇引用方笔记中删去 `#fragment`，保留 Wiki 目标 ID、原文及其他引用。需要再次核对 Actions 构建、部署与发布回执；不得以补丁已提交推断通过。

## 发布修复回归通过（2026-10-12）
- 修复提交：`a94a64513c18c18397184b57cd87df1dcb68fd94`；修复前构建失败提交：`f0cf9fb782887088790c17e7cfec92a2695fc9a1`。
- GitHub Actions Run：`38245753459`。实际 Build=success、Deploy=success、Verify live published content=success；部署日志含 `MUSEUM-PUBLISHED-RECEIPT`，sourceCommit 精确等于 `a94a645...`。
- 五个受影响 ID 出现在回执，状态均为 published；整个站点回执共 18 条 Org 来源记录。
- HEAD 与修改前 Commit 的独立读回检查通过：三篇历史正文和原 ID 保留，索引 link set 未变化，日志事件键唯一，两处跨页 URL 不再使用未经验证的 #fragment；一篇无关 CLI 文档的 Git blob SHA 完全一致。
- 幂等判定：重复输入时能够识别同一事件和已有更新，无必要新改动。未实际执行第二次写入，不能声称完成并发写入冲突演练。
- 本轮剩余风险：尚无真实“同一时点同条件互斥的一手来源”对抗样例；Git 并发冲突注入、完整 T01–T18 自动回归未执行。判定：本轮真实来源版本漂移维护与发布闭环通过，Skill 整体有条件通过。

## 2026-10-12 真实同期争议案例回归

- 三份一手来源：CFTC Release 8680-23（2023-03-27）、Binance CEO 官方回应（2023-03-27）、CFTC Release 8837-23（2023-12-18）。URL 分别为 https://www.cftc.gov/PressRoom/PressReleases/8680-23 、https://www.binance.com/en/blog/from-our-ceo/2408916493005890282 、https://www.cftc.gov/PressRoom/PressReleases/8837-23 。
- org-notes 基线 a94a64513c18c18397184b57cd87df1dcb68fd94；变更 f5f6e72826e444953ed54e19e438283833771dd5：三篇独立 Source、一篇 Synthesis、追加 4 个索引入口和 1 条维护日志事件 source-conflict-binance-cftc-2023-20261012。原有 16 篇业务/资料笔记未改写；2 篇既有 Wiki 维护页分别追加索引与日志内容。
- GitHub Actions Run 38246856330：Build、Deploy、Verify live published content 均为 success；MUSEUM-PUBLISHED-RECEIPT sourceCommit 与实际提交相等，22 条 Org 发布记录包含六个受影响目标。
- 裁决：同期对立说法和后续司法认定得到区分；但“存在准入阻断措施”不排除“有人绕过”，严格 P/非 P 未成立。T19 范围内通过；T17 严格命题互斥仍未验证，不得以此次样例冲抵。
- 第一次校验器使用错误 Org Wiki 链接正则，将旧链接误判为不存在。修正后通过：原有 17 个索引链接保留，新索引共 21 个不同目标，真实发布器 HTML 校验通过。该错误属于测试器，不是知识库。
- 同事件的幂等性仅通过唯一事件键和已有文件读回进行无须写入判断；未实施第二次写入、并发变更对抗或完整 T01–T19 自动回归。

## 自动化契约测试回执（2026-10-12）

- 新测试脚本：`skills/llm-wiki-maintainer/tests/check_conflict_contract.py`；GitHub Actions：`.github/workflows/wiki-maintainer-regression.yml`。
- 首次真实 CI：Run `38251605133`，Workflow `Wiki Maintainer Regression`，conclusion `success`。覆盖 13 项合成断言：同条件 P/非 P、同命题一致、时间/版本/范围/谓词/量词差异、缺少适用范围、Binance 误判反例、重复摄入预判、HEAD 不匹配停止等。
- 本地试跑原型通过 12 项断言，提交版增加了 1 项同命题一致性检查；两份脚本不是同一精确版本，不应把本地结果充当 CI 回执。
- 范围严格限制：测试器是确定性结构化 Claim 契约，不进行自然语言抽取、真实来源读取、完整 Git 写入或实际并发注入。T17 真实互斥一手来源仍为 NOT_RUN；T02 与 T10 仅通过模拟决策预检，未完成端到端实测。
- 安全：合成姓名和参数不是实际用户数据。未将合成测试内容录入公开 org-notes。

## T17 外部来源资格门禁（2026-10-12）

- 基线测试器 `check_conflict_contract.py` 之前只有结构化合成 Claim 判定，不能证明真实文件来源校验。
- 本轮重审 CFTC 2023-03-27 指控、Binance 官方回应和后续 CFTC 命令，以及 SEC 一手争议材料。未找到证据充分、同对象同一窗口同口径、可以严格表达为 P / 非 P 的一手来源对。监管指控与被指控方否认，或者存在控制与存在绕过，不能自动计作严格矛盾的已证实事实。
- 已添加 `live_t17_gate` 的四项前置回归：缺失来源拒收、未独立核实来源拒收、同一来源拒收、Binance 非互斥场景拒收。测试中 URL/locator 字段是模拟来源元数据，`verified_directly` 是调用者申报值；函数本身**无法读取 URL，不能把 CANDIDATE 判为 T17 PASS**。
- 本次 T17 的真实判定仍是 **NOT_VERIFIED**；未向公开 Wiki 增加制造的矛盾。之后需要具有原文精确定位、来源真实性、时间/定义/量词一致性的真实证据对，及独立复核结果。预检通过仅表示可以进入人工/独立验证，不表示事实真实性。

## Git E2E 与真实站点发布门禁回执（2026-10-12）

- 失败基线：此前 `skills/llm-wiki-maintainer/tests/check_conflict_contract.py` 只有 17 项结构化合成断言；T02/T10 缺少真实 Git 仓库竞争写入，索引和日志缺乏发布前全库门禁。上述合成逻辑保留，不伪称曾完成真实写入。
- 修复产物（公开仓库）：`lovemoganna/org-notes/tools/check_wiki_integrity.py`（只读全库源码审计）；`tools/test_wiki_integrity.py`（仅临时目录内 Git bare remote + 两个 writer，重复摄入与真实非快进拒绝）；`.github/workflows/publish.yml` 在发布前先跑测试和全库审计，失败不能进入 Build/Deploy。原 Org Museum publisher 未替换。
- Git Commit：`ec99b271a6cc46ba9b55f078ec83b76810f8d0b9`。GitHub Actions：https://github.com/lovemoganna/org-notes/actions/runs/38254107223 ，Build 和 Deploy 都是 success；`Run Wiki disposable Git and negative regressions`、`Verify Wiki source integrity`、`Build without running note code`、`Verify live published content` 均 success。Deploy 实际 `MUSEUM-PUBLISHED-RECEIPT` 的 sourceCommit 与提交 SHA 一致，22 个发布页。
- 确定性实测：T01/T02/T14 单次写入、相同事件第二次无工作区差异及无新增 commit；T10 两个独立本地 Git writer 真实竞争，远端先行写入保留、陈旧 writer push 被 non-fast-forward 拒绝；T06 查询读取不写；T07 断链、T08 重复 WIKI_ID、T12 文件链接、T18 含 fragment 的未经验证 Wiki 形式，以及 ID 错配、索引缺项、重复日志事件、缺 SOURCE 均能拒绝。测试内容只在临时目录，没有提交模拟资料。
- 真实 `org-notes` 发布前只读扫描回执：22 个 published 源页、54 条 Wiki 引用、22 条文件链接、21 条索引链接和 3 个维护事件；与真实 Publisher 生成的 HTML 和线上源 Commit 回执均核对通过。
- 独立远端负向边界：曾以陈旧 expected_sha 对主分支发出不改变目标 SHA 的条件更新请求，接口返回非特定 GraphQL 错误，随后 HEAD 未改变。**不能从这一错误单独认定 GitHub 远端 lease 拒绝机制已通过**；真正通过的竞争实测是临时 bare Git remote 的 non-fast-forward 拒绝。
- 尚未完成：T17 可信同期严格 P/非 P 一手来源对，T05 外部来源不可读全链路，T09 实际隐私泄漏故障注入，T11 真正撤回声明的来源更新；本轮不补造结果。这些需要原始资料或独立授权测试，不影响已验证的确定性门禁范围。
- Loop 结论：G0/G1/G3/G4/G5 的确定性来源与发布边界实测通过，G2 的事实语义和 T17 未独立通过。结论仅为 **发布与 Git 故障控制闭环通过；证据语义仍有剩余风险**。

## 2026-10-12 最终 Loop 回归与覆盖口径修正

- 公开知识库最终提交 `d133283a1458eba4aeedfc6d2cca6b217cf58180`；[Actions 38254835520](https://github.com/lovemoganna/org-notes/actions/runs/38254835520) 中 Build/Deploy/Verify live published content 均为 success。实际 `MUSEUM-PUBLISHED-RECEIPT` 的 sourceCommit 与该提交一致，22 篇源页面发布成功。
- 同一次流水线中真实运行 `tools/test_wiki_integrity.py` 和 `tools/check_wiki_integrity.py`，分别成功执行临时双 Git writer 竞争、重复摄入、负例测试，以及对真实 22 篇笔记的只读索引/链接/文件/日志审计（54 条 Wiki 引用、22 条 file 引用、21 条索引条目、3 个日志事件）。
- 为消除测试口径虚高，T01 的隔离夹具已改为**向已有概念页面追加指向新来源的关系**，原文完整保留、第二次重复输入不新增提交；这仍是夹具逻辑测试，不等于真实外部来源 T01 E2E。
- T06 的当前覆盖明确降级为**只读不写这一前置条件**，没有执行“基于两篇真资料生成可追溯问答”的完整能力测试，不得把该项标为全部通过。
- T09 经**当前实际固定发布器**的 `privacy()` 函数验证：动态构造的合成 GitHub 凭据、API_KEY 及私有路径均被拒绝，普通安全字符串放行。不会使用真实秘密或公开用户隐私，不能证明所有语义隐私风险可由规则发现。
- GitHub 远端旧 expected_sha 的否定调用仅得到不明确 GraphQL 错误，未造成主分支变更，因此不声称真实 GitHub 远端 CAS 机制已被独立核验；T10 有充分证据的范围是**两个写入者对隔离 bare remote 的真实 Git 推送竞争**。
- 未通过或未完成项：真正可核验同条件 P/非 P 一手证据对（T17）；真实源不可读的完整处置（T05）；基于多份原文的只读引用问答（T06 全量）；真实撤回来源的知识状态更新（T11）；完整隐私语义审查。此轮其余确定性发布门禁已核实，不再扩张合成案例制造表面覆盖率。

## 2026-10-12 可重复知识维护 Loop 与用户删除约束

- 已取消要求必须存在 `Org Wiki 知识导航索引`、`Org Wiki 维护日志` 的强制规则；这两篇文章由用户明确移除，原 ID 不得被自动重新摄入。原来已执行过的索引/日志测试记录仍作为历史事实保留，不代表未来必须恢复。
- `scripts/wiki_loop.py` 执行 `audit`（只读 Org 目录、WIKI_ID、已有关系、删除页检查）及 `plan`（冻结来源快照和哈希、定位粒度去重、已知页面关联及条件 HEAD）。`references/operations.md` 定义来源、审核、Git 条件写入、HTML 发布及 Loop 停止条件。`plan` **永不写入**，也不自动核实互联网 URL 与内容对应关系；这部分必须依靠真实原文访问和独立人工/模型复核。
- `tests/test_wiki_loop.py` 在隔离目录测试重复执行、同源不同定位、证据哈希变更、引用丢失、已删除页复活、隐私特征、路径穿越、Git HEAD 变化等负例；原 `check_conflict_contract.py` 用例继续保留。流水线应在真实只读 `org-notes` 检查通过后才声称工程门禁通过。
- 剩余边界不变：T17 真实严格 P/非 P、完整自然语言知识问答、多来源来源撤回及公开发布的语义正确性不能用这些结构测试冒充通过。输出候选结果、失败记录和回归证据需区分 `PROPOSE`、`NOOP`、`BLOCKED` 与已发布。

## 2026-10-12 最终工程回归回执

- 基线 `lovemoganna/Org-Skills` commit `0eaecd7905af3e0d04c6e0c698acbbf48bddc4b0`。真实 GitHub Actions Run [38261241125](https://github.com/lovemoganna/Org-Skills/actions/runs/38261241125) 为 success，原有 17 项合成冲突测试、新增 19 项独立对抗测试、真实 `org-notes` 只读审计均通过。
- 实际 `org-notes` 仓库只读审计返回 `gate=PASS`、`pages=21`、`retired_absent=true`；不重建用户已经删除的人工索引和维护日志。此结果独立于私有 Skill 的合成笔记测试。
- 新源码 `scripts/wiki_loop.py` 的 `plan` 必须具有真实临时来源快照、SHA256、定位以及已知关系 ID；输出建议而不修改任何 Org 或 Git。引入三元组 `URL+SHA256+locator` 的确切证据记录，避免把同文章不同段落误判成重复。未运行完整自然语言事实归纳、源撤回或实际写入本工具的端到端测试，因此它们仍需人工证据验收。
- Loop 结论：对 **可重复的发现/去重/关系预检、已删除身份防复活、Git 源版本门禁、CI 仓库审计** 已具备实测支持；自动事实判断、无监督自主更新和严格 T17 真实冲突仍不属于已验证能力。
