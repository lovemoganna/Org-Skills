# plantuml-diagram-engine v1.0 — 回归记录

## 变更范围
- 两套旧版 Notion 提示保持原样；合并为独立的 `plantuml-diagram-engine`。
- 因仓库无同名 Skill，新增，而不是覆盖其他文件。
- 图型按目的分派；本体/MECE 只在确有必要时运行；默认输出公开 PNG 直链，禁止自动下载。

## 测试输入
- Case A：原第一套 WBS 工作包范例（4 大类 / 12 个子项），新样例 `examples/01_wbs.puml`。
- Case B：原第二套 Activity 流程（顺序、是/否分支、重试上限），新样例 `examples/02_activity.puml`。
- Case C：敏感源码禁止输出到公共 URL，以及未授权网络请求必须失败。
- Case D：官方已知编码样例、中文回环、响应错误、官方失败后 Kroki 回退。

## 执行与结果
- `python -m pytest -q tests`：19 passed / 0 failed（2026-10-19；包含新增敏感信息前置门禁回归）。
- 运行 `python scripts/encode_url.py examples/01_wbs.puml`：生成 PlantUML、Kroki 两条在线 PNG 直链，不触发 HTTP，不产生 PNG 文件。
- 同样执行 `examples/02_activity.puml`：通过。
- 官方案例编码完全匹配 `SyfFKj2rKt3CoKnELR1Io4ZDoSa70000`。
- WBS 的 4 个一级节点、12 个叶子节点静态覆盖检查通过。流程图的条件、回路、退出条件静态检查通过。
- 修复 Activity 样例在 URL 生成和在线请求后才执行敏感信息判断的问题；新增门禁顺序测试，要求每轮公开 URL 生成之前确认无敏感信息且已获公开授权。

## 未通过 / 未执行的测试
- 官方 PlantUML 与 Kroki **真实远程渲染**：未执行成功。执行容器 DNS 解析失败；网页访问通道未能取得新图 PNG，独立内容提取服务虽报告 HTTP 200 但未返回图片字节，不能据此判定渲染成功。
- **PlantUML 实际语法执行和文字/布局目视检查**：未验证；缺少 PlantUML JAR，不能用 Graphviz 模拟图来替代。
- 以上限制不可标为端到端成功；交付状态 `URL_GENERATED / HTTP_UNVERIFIED`。

## 风险与回滚
- 网络环境可能出现 CDN 超时、URL 长度限制、服务端字体差异或语法错误图。
- 新目录独立；回滚只需 revert 本次新增文件，不触及 Notion 原始提示和旧 Skill。
- 发布后先做带联网条件的线上验收，再根据实际图像执行至多两轮样式修复。
