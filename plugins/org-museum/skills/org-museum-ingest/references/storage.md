# 公开源笔记契约

目录是 notes/<kind>/<topic>/<id>.org。kind 为 programming、knowledge、reading、ideas；
topic 只使用 a-z、0-9、连字符。id 为小写 UUID，后续更新不改 ID 或路径。

```org
#+TITLE: 面向问题的中文标题
#+WIKI_ID: 小写 UUID
#+CATEGORY: 主题名
#+FILETAGS: :主题词:类型词:
#+DATE: YYYY-MM-DD
#+SOURCE: 用户提供的材料；若有真实 URL、作者、页码则注明
#+INGEST_ID: 同一批次的小写 UUID
#+WIKI_STATUS: published

* 正文
```

DATE 是实际收录日，不能从程序版本推断材料的实验日期。原文已有日期单独保留。
SOURCE 不能编造 URL；用户只粘贴材料则写“用户提供，原始出处未提供”。
已有 Org 元数据保留，只有存储契约必需字段由入口补齐；原有 WIKI_ID 不符合
当前新建格式时不要擅自更改旧笔记，报告兼容缺口。

附件放 note-assets/<note-id>/<filename>，允许 png/jpg/jpeg/webp/gif/mp3/pdf/csv/json/txt/sql/py/sh，
单文件不超过 20 MiB。不要自动把整段聊天或原始文件作为附件上传。
file: 链接必须指向 notes/ 或 note-assets/ 中真实存在的文件，不能越出仓库。
MP3 以 =audio/mpeg= 交给站点原生音频播放器（支持试听和下载）；必须确认附件实际上传成功，
并在发布后核对页面音频源 HTTP 可访问、文件大小及 SHA-256。不能把站点渲染支持等同于文件已托管。
站内标题链接用真实 CUSTOM_ID；wiki: 链接只能指向已存在或同批提交的 ID。

公开检查：密钥、token、密码、私钥、带凭证的 URL、用户电脑绝对路径、UNC 和
file:/// 引用不得进入公开稿；用清楚的省略占位或公开可用的参数替代并说明。
私密个人经历、内部资料不能因关键词检测没命中就自动认为可公开；有明确私密
语境而无法无损整理为公开稿时停止，并指出需要解决的具体片段。
没有真实图片/附件工具时不要编造下载、上传或图像地址。

禁止 INCLUDE、SETUPFILE、BIND、HTML_HEAD、HTML_HEAD_EXTRA、MACRO
及 HTML export/script；教程中的调用示例放 example/src 块展示。本次仅发布代码，
不要执行外部副作用程序。所有 begin/end 块配对，代码中的星号按 Org 规则转义。
不要把验收检查清单和流程台账添加到用户正文。
