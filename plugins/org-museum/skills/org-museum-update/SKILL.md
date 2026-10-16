---
name: org-museum-update
description: 用户明确要求炼化、重写或更新一个已发布的 Org Museum 页面 URL 时，定位其原始 Org 源文件并原地更新、提交和验证发布。主题或来源参数不改变身份。仅解释页面或新建笔记时不使用。
---

# Museum URL 原地更新

此操作是更新已有文件。定位失败就停止，不退回收录、不创建新笔记。

1. 在 `lovemoganna/org-notes` 读取当前 main 和 museum.json，URL 必须属于配置的
   siteUrl 下的 pages/ 文章。去除 query 与 fragment 后作为页面身份。
2. 读取页面的 text/org alternate、museum-wiki-id、museum-source-path；与
   museum-release.json 的 href、id、path、sourceCommit、sha256 一致才采用。
   网页工具无法访问 Pages 时，读取当前成功发布的 deploy job 日志，选择 URL
   匹配的 `MUSEUM-URL-RESOLVED` 凭据。它由 Actions 的真实页面请求和 Git 核验产生。
   jobs/logs 工具使用 repo_full_name；查运行记录用 GitHub 通用 fetch 的
   `/actions/runs?head_sha=<HEAD>&event=push`，不用只筛 PR 的快捷工具。
3. 以准确 path 从 GitHub 读取完整 Org。页面的 Org Mode 视图是过滤正文，不能
   用它覆盖文件头。不存在唯一源绑定、源文件不存在或版本冲突时停止并说明。
4. 通过 `../note-reforge/SKILL.md` 启动入口读取 `lovemoganna/Org-Skills` 当前默认分支的
   `skills/note-reforge/SKILL.md` 加工当前单篇。canonical 读取失败即停止，不回退到内置旧版。
   此次要求覆盖其默认 .next 交付，
   更新准确的原路径。保留 wiki_id、所有原元数据及其写法（TITLE 可改文字）、
   链接目标、锚点、已有标题和代码；不动其他系列文件，不添加无依据内容。
5. **远程写入前强制预检。** 以最新 main 的完整 Org 源为 original、完整候选 Org 为 candidate，
   在首次提交、创建 PR、更新 GitHub 文件或移动 ref **之前**运行
   `python skills/note-reforge/tests/check_published_update.py <original.org> <candidate.org>`。
   该脚本来自 `lovemoganna/Org-Skills` 当前版本。预检保留已有 `WIKI_ID`、除 `TITLE` 外的元数据、
   章节标题引用（不仅是 `CUSTOM_ID`）、链接、ID 锚点和逐字代码/引用块；
   新增章节允许，但不能改写或删除旧标题。**任一失败即停止写入，不先提交再等 CI 拒绝。**
   如没有文件执行环境，必须对 GitHub 返回的**完整原稿与候选稿**执行相同的逐项多重集差异
   （含出现次数），核对全部结果；无法执行也无法等效验证时停止，不得以模型自评代替。
   如果 main/source blob 在检查后改变，重新读取并重跑预检。
6. 预检通过后，有执行工具时用发布器 `tools/museum_update.py` 的 resolve/update/status
   完成提交和验证。仅 GitHub 连接可用时，使用现有 GitHub tree/commit/ref 工具，
   latest main 作 parent，只修改已存在目标路径，message 为 `Museum-Update: <id>`，
   force=false；并发冲突后必须重新核验内容，不得覆盖。正式发布器还有自己的验证，
   不可用「PR CI 通过」替代源分支的提交前门禁。
7. Commit 成功后继续检查 publish.yml 的 build 与 deploy，且在线核验步骤成功。
   `MUSEUM-PUBLISHED-RECEIPT` 中目标 id、path、源内容 sha256 必须属于本次版本。
   只有 Pages 核验完成才回复更新完成；超时回复已提交、发布中，失败报告阶段。

最终给原文件、Commit、构建和原页面链接，状态明确。历史元数据不强制改成新建
规范；现有安全校验不能处理时报告限制，不能改身份或路径绕过校验。
