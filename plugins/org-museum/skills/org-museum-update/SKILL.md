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
4. 读取 `lovemoganna/Org-Skills` 当前默认分支的 `skills/note-reforge/SKILL.md`
   加工指定的完整 Org，不得用插件内旧副本，不能静默回退旧规则。用户最近一次明确编辑标准决定本次
   可删改内容；保留同一原路径、WIKI_ID 和除 TITLE 外的元数据，不改其他文章。
   不得把应删除的内容挪入附录或正文其他位置伪装完成。
5. **写入前预检：默认严格，明确授权删改时按范围精确放行。** 比对完整 original 与
   candidate 的原有标题、链接、锚点、字面块，计算出现次数（多重集）差异。
   若本次用户明确要求删减，编制 scope.json：包含 `user_directive`（用户原意）
   和 `references`、`heading references`、`anchors`、`literal blocks`
   中实际被删除的字符串数组（逐字、重复项逐个列出）。空泛的“全部放行”无效。
   执行 `python skills/note-reforge/tests/check_published_update.py original.org candidate.org
   --authorized-removals scope.json`；无删减时省略 scope 以维持严格保留。
   无执行环境必须完成同等的多重集差异审查；无法核验则停止。
6. **提交与审计。** 可运行本地发布器时使用
   `tools/museum_update.py update --authorized-removals scope.json`；仅 GitHub 插件
   可用时，基于 latest main 创建只修改原 Org 的 tree/commit/ref，禁止 force。
   有用户授权删减时，Commit 标题仍为 `Museum-Update: <id>`，另加单行
   `Museum-Update-Authorized-Removals: <scope-json>`，其值为紧凑合法 JSON，
   要与提交前精确清单相同。CI 对提交中的实际删除与声明执行逐项一致性核对；
   未授权的引用、标题、锚点或逐字块被删除时拒绝发布。提交后仍须通过
   页面构建、部署和线上版本核验，不能以“GitHub 提交成功”冒充发布成功。
7. Commit 成功后继续检查 publish.yml 的 build 与 deploy，且在线核验步骤成功。
   `MUSEUM-PUBLISHED-RECEIPT` 中目标 id、path、源内容 sha256 必须属于本次版本。
   只有 Pages 核验完成才回复更新完成；超时回复已提交、发布中，失败报告阶段。

最终给原文件、Commit、构建和原页面链接，状态明确。历史元数据不强制改成新建
规范；现有安全校验不能处理时报告限制，不能改身份或路径绕过校验。
