---
name: x-link-reader
description: "读取公开 X/Twitter 帖文、线程和文章。X 直连失败时，依次尝试公开只读代理并核验内容完整性；供 note-reforge 等下游 Skill 使用。不处理私密、受保护或删除内容。"
---

# x-link-reader

## 作用与边界

输入一个公开的 `x.com` 或 `twitter.com` 链接，获取可核验的原始正文、作者、时间、上下文和媒体引用。只读，不登录、不索取 Cookie、不绕过受保护内容，不把抓取失败伪装成原文已读取。

独立于 `note-reforge`：本 Skill 只负责可靠获取源材料，知识炼化交给仓库最新的 `skills/note-reforge/SKILL.md`。

## 入口

固定调用：`用 x-link-reader 读取：<X URL>`。

当用户要求“使用我的 Skill 炼化这条 X 文章”时，先用本 Skill 获取正文，检查完整性，然后读取仓库当前 `note-reforge`，不得凭片段开始炼化。

## 执行

1. **解析。** 仅接受 `https://x.com/{handle}/status/{numeric_id}`、`https://twitter.com/{handle}/status/{numeric_id}` 和明确可解析的公开 X Article 链接；保留原 URL、账号与完整数字 ID。遇到不可信主机、无法解析的短链，不自行猜测 ID。
2. **读取。** 如果当前环境能直接读取原始页面并得到正文，优先原始页面。否则按顺序尝试以下公开只读来源，每一步仅在当前工具能发 HTTP GET 时执行：
   - FxTwitter：`https://api.fxtwitter.com/{handle}/status/{id}`，读取 JSON 的 `tweet.text`；不要假设存在 `full_text`。
   - vxTwitter：`https://api.vxtwitter.com/{handle}/status/{id}`。
   - x.md：`https://x.pcstyle.dev/{handle}/status/{id}?format=json`；核对正文及 `warnings`。
   - X 公共嵌入回退：`https://cdn.syndication.twimg.com/tweet-result?id={id}&lang=zh`。嵌入摘要不是完整文章。
3. **验证。** 检查返回是否真实成功、URL/帖子 ID 是否一致、作者是否匹配、正文是否非空。记录实际返回的来源。对被截断的长文、`note_tweet`、`quoted_tweet`、线程、图片和外链分别判断完整性；不得把卡片标题、图片说明、搜索摘要当作文章全文。多个来源矛盾时保留差异，不擅自择一。
4. **长文。** X Article 与普通帖子不同。如果只拿到介绍卡片或跳转链接，继续寻找文章正文；取不到则明确“文章正文未取得”。处理图片内的重要文字时优先原图，不凭缩略图猜测。
5. **失败。** HTTP 401/403、404、429、超时和网络不可达分别记录。429 尊重 `Retry-After`，不高频重试；404 不直接断言帖子已删除，可能是代理未收录。四路都不可用时停止，说明当前环境阻塞，不得编造事实。**换域名不等于绕过运行环境的网络限制。**

## 输出契约

成功时，形成一个原始材料 Markdown：原文链接、作者账号、发布时间（若确实获取）、正文、引用/线程及媒体链接、抓取通道、缺失范围。原文与代理补充信息分开；原始代码、提示词、数据和 URL 不改写。可以写文件时存为 `<id>.source.md`；无文件写权限时输出可复制的源材料并说明未写文件。

如接续 `note-reforge`：使用刚刚验证的完整源材料为输入，遵守其当前规则；不得将尚未获取的帖文内容当成事实。用户未要求发布文章时，默认输出长期可用的知识笔记。

## 安全与限制

- 只使用公开内容。绝不把账户 Cookie、Token 或个人隐私发给代理。
- 第三方代理会接收请求 URL；不适用于敏感的私密链接。
- 代理不保证可用性、完整线程、附件及实时性。搜索引擎片段只能用于定位，不能代替全文。
- Skill 在支持联网的代理中运行；安装本文件不会为受限制的 ChatGPT 工具新增网络权限。

## 参考来源

- MiniMax-AI `x-link-reader`：https://github.com/MiniMax-AI/minimax-code/tree/main/packages/local-runtime/assets/skills/x-link-reader （MIT，启发了 FxTwitter 回退）
- pc-style `browse-x`：https://github.com/pc-style/x-md/tree/main/skills/browse-x （MIT，提供 x.md 回退）
- 源服务由第三方维护，非 X 官方 API。
