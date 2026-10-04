# GitHub 连接操作

必须在当前 Chat 使用已连接 GitHub 插件的可用工具。名称因客户端前缀而异，
按描述发现工具，不能声称存在未暴露的工具。需要 read/fetch、create_tree、
create_commit、update_ref。不要创建 Work/Codex 任务来补工具。

read/fetch：
- https://api.github.com/repos/lovemoganna/org-notes/git/ref/heads/main
- https://api.github.com/repos/lovemoganna/org-notes/git/commits/<HEAD>
- https://api.github.com/repos/lovemoganna/org-notes/git/trees/<TREE>?recursive=1
- fetch_file 读取 museum.json 和候选目标文件，ref 固定为刚读取的 HEAD。

create_tree：repository_full_name=lovemoganna/org-notes，base_tree_sha=最新 tree，
tree_elements 只包含 {path,mode:"100644",type:"blob",content:Org全文}。
二进制附件先 create_blob(encoding=base64)，tree entry 使用 sha。
create_commit：parent_sha=HEAD，tree_sha=新 tree，message 包含批次 ingest ID。
update_ref：branch_name=main，sha=新 commit，force=false。
失败并发重读后检查原目标 blob，禁止只重试旧 ref 更新。

发布检查用通用 fetch：
https://api.github.com/repos/lovemoganna/org-notes/actions/runs?head_sha=<COMMIT>&event=push
随后 /actions/runs/<RUN_ID>/jobs，确认 build 与 deploy。
fetch_commit_workflow_runs 的当前快捷实现只筛 pull_request，不能用于本流程。

站点版本读取：
https://lovemoganna.github.io/org-notes/museum-release.json
使用当前可用的网页读取工具；若该工具不能获取 JSON，明确页面未核验。
GitHub fetch 不能读取 github.io，不要给它发送 Pages URL。网页工具不可用时，
通过 fetch_workflow_run_jobs 找 deploy job，确认 Verify live published content
步骤 success，再用 fetch_workflow_job_logs 读取 `MUSEUM-PUBLISHED-RECEIPT`
JSON。这个凭据由部署后的真实 HTTP 请求产生；按 commit、id、sha256、href
核对后可返回已发布。没有该记录则明确页面未核验。
源码链接：https://github.com/lovemoganna/org-notes/blob/<COMMIT>/<PATH>
提交链接：https://github.com/lovemoganna/org-notes/commit/<COMMIT>
页面链接以实际 museum-release.json 的 href 为准，不能仅凭文件名猜测已上线。

没有本机、Git CLI 或运行 Python 仍可用这些连接工具收录；若缺少 GitHub 写入
权限，则是 Chat 入口的具体阻塞，不能返回“已完成”。
