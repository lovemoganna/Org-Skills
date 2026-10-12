# Org Wiki 维护执行规程（v0.2）

该 Skill 是知识维护编排层。自动化预检负责已冻结资料的发现、去重与关系校验，不能代替对原文的阅读、事实核验、撰写和授权。发布仍走原有 `org-museum-ingest` 与 GitHub Actions。

## 1. 发现与只读审计

从 GitHub 读取 `lovemoganna/org-notes` 最新 HEAD、`museum.json` 和 `notes/**.org`。当前存储与 HTML 发布契约以仓库为准。

```sh
python3 skills/llm-wiki-maintainer/scripts/wiki_loop.py audit --repo /path/to/org-notes
```

输出 `gate=PASS`、页数和 HEAD，或精确错误。审计包括页面身份、Org 结构、跨页 wiki 引用及用户已删除页面 ID，不创建文件。与网站自己的 `tools/check_wiki_integrity.py` 和发布器校验互补，不能替代全部 HTML、附件、隐私检查。

**用户删除约束**：原索引 `a4b7cf91-5db8-4a2f-90e2-89f3ea14bcd5` 与维护日志 `71e02e9d-80ff-4a75-a7aa-092532c14fd0` 已移除。不准自动重建，不因为缺少它们判为缺陷。可使用已有目录、Org 链接和网站生成导航，不新建名为 `index.org`、`log.org` 或同 ID 的替代页面。

## 2. 冻结与验证来源

真实外部 URL 需通过已授权的浏览器/连接器获取。把准确摘录或授权快照保存到**本地临时证据目录**，保留 URL、标题/发布者、段落定位、实际获取日、版本、SHA256、访问条件；敏感或非公开内容不能放入公开 repo。禁止把合成文本当作实际来源。输入示例：

```json
[
  {
    "url": "https://docs.python.org/3/library/itertools.html",
    "locator": "Itertools Recipes",
    "retrieved_at": "2026-10-12",
    "sha256": "<64位小写十六进制 SHA256>",
    "snapshot_file": "itertools-excerpt.txt",
    "target_wiki_id": "<需要更新的真实 WIKI_ID>",
    "related_wiki_ids": [],
    "revision": "页面版本或 Commit（若有）"
  }
]
```

`snapshot_file` 必须位于授权的证据目录下，不得使用路径穿越。快照大于 4 MiB、哈希不匹配、包含典型密钥、目标 ID 不存在或已移除、关联 ID 不存在都必须阻断或人工处理。哈希证明输入字节一致，**不能证明内容真实、URL 与快照对应或没有隐私风险**。

## 3. 生成确定性计划

```sh
python3 skills/llm-wiki-maintainer/scripts/wiki_loop.py plan \
  --repo /path/to/org-notes \
  --manifest /private/evidence/sources.json \
  --evidence-dir /private/evidence
```

状态定义：

- `NOOP_ALREADY_INDEXED`：已有页面明确记录相同 URL 与 SHA256 配对的 `#+EVIDENCE_RECORD: <sha256> <url>`；不重复收录。
- `NOOP_DUPLICATE_INPUT`：同批输入具有同一 URL、快照哈希、目标和版本；本轮不重复处理。
- `REVIEW_EXISTING_SOURCE`：URL 已被已有页面引用，但缺少同一哈希配对或快照可能改变；必须阅读原文后做差异判断，不能覆盖。
- `PROPOSE_UPDATE`：给现有页面追加已经核实的新证据；检查既有段落和适用范围。
- `PROPOSE_NEW`：找不到相应页面的建议，仍应先人工验证无语义重复。
- `BLOCKED` / `BLOCKED_REPOSITORY`：证据或图关系不符合准入契约，不写入。

此命令**纯只读**，输出 `writes_performed=0`；它不检索互联网、不调用模型、不擅自判断真伪或生成 Org 页面。事件键具有确定性，不需额外索引/日志文件。

## 4. 实际知识更新

仅对通过证据复核、拥有明确写入授权的变更执行：

1. 读取相关原 Org 全文，独立识别 Source、Entity、Claim、Relation、Synthesis；为每条主张绑定原文段落与适用日期。已删除的页面不能复活。
2. 按需使用最新版 `note-reforge` 组织现有知识；保留旧日期、Claim、代码和附件，新增不确定判断须标 `〔补〕`。关系仅在原文支持时建立。对相反证据先检查时间、条件、量词；未经裁决不能抹除任一方。
3. 生成最小 diff，核对 WIKI_ID、已有标题/路径、证据 URL、未授权文件和目录边界。新页遵守 `notes/<kind>/<topic>/<ID>.org`，不会新建用户已删除的人工索引/日志。
4. 在写入前复核 `git rev-parse HEAD` 等于冻结基线；如发生竞争写入必须重新读取、重建计划，拒绝 force push。可用 `--expected-head <sha>` 令本工具发现 HEAD 漂移，但实际 Git 提交另需条件更新。
5. 用既有 `org-museum-ingest` 完成授权提交，依次验证源码与附件、HTML 构建、Deploy 和 `MUSEUM-PUBLISHED-RECEIPT`。失败仅做最小修复并回归，保留失败运行 ID。

## 5. 停止条件

无新证据、同来源同快照已收录：`NOOP`。来源不可读、敏感数据、身份冲突、过期 HEAD、未授权写入、HTML 失效：`BLOCKED`。可信证据之间无法比较条件/量词：`REVIEW_REQUIRED`。只读问题无论成功失败都不创建笔记。

重复运行时应得到稳定计划，除非输入字节、源 Wiki 或 Git HEAD 实际改变。Skill 和原仓库 CI 必须保留确定性回归；语义验收不能靠测试通过率或自报代替。
