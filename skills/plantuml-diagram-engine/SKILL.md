---
name: plantuml-diagram-engine
description: 将文字、代码、业务流程或本体模型转为 PlantUML，按语义选择 WBS、活动图、时序图、组件图或状态图，设计清晰统一的图形样式，并默认返回可直接打开的在线 PNG 图片 URL。适用于用户要求 PlantUML、图解、流程图、结构图、在线渲染图片链接或优化已有 .puml；不默认下载文件。
---

# PlantUML Diagram Engine v1.0

## 唯一交付目标
**默认直接返还在线 PNG 图片直链**：`https://www.plantuml.com/plantuml/png/{TOKEN}`；同时允许附上 Kroki 备用 PNG 图片直链。不要把编辑器网址、`sandbox:`、PNG 附件、ZIP 或源代码当作主交付。仅在用户主动要求下载或本地渲染时保存文件。

## 输入契约
- 接受原始材料、已有 `.puml`、代码、业务描述和已有图；默认保留原始事实、专有名称、触发条件和证据状态。
- 缺少不影响画图的细节时做最小假设并标注；缺少关键条件时不捏造分支。除非用户明确授权，不处理真实 UID、密码、私有架构或内部风控参数到公共渲染服务；URL 是可解码的源码，**不是加密**。
- 用户只要链接，就不要额外输出冗长本体论、MECE 报告或 ZIP；源码按需附带。

## 合并决策协议：不是机械拼接两个提示
1. **语义重建**：抽取对象、属性、动作、条件、顺序、消息、状态与依赖；区分「明确事实 / 推断 / 缺口」。以最短路径推导图的真实阅读目的。
2. **按目的选主图**：分类与任务拆解选 WBS；顺序、条件、回路选 Activity；参与者消息选 Sequence；系统依赖选 Component；状态转换选 State；对象类型和关系选 Class/Object。默认只出一张主图；用户明确需要多个视角才多图。
3. **智能深度**：简单输入直接出图；只有复杂结构/术语歧义时启动本体建模；只有同口径互斥分类时做 MECE 检查；TRIZ/洞察仅在用户要求创新时启用。不把时间顺序或因果关系强塞进 MECE 树。
4. **语义映射**：关键对象、关系、条件必须在源码中可追溯；图型不可表达的关系用说明补足，不新增虚构关联。已给 `.puml` 时执行最小差异修改。
5. **输出源码**：编写一份完整的 UTF-8 `.puml`，确保 `@startuml`/`@enduml` 等匹配。不要把未经运行的代码称作“验证通过”。

## 默认视觉方案：Editorial Light
采用白底 `#FFFFFF`、标题深蓝 `#172554`、正文深灰 `#334155`、连线灰蓝 `#94A3B8`、中性底 `#F8FAFC`；主流程淡蓝 `#DBEAFE`、成功浅青 `#CCFBF1`、待确认浅黄 `#FEF3C7`、错误浅红 `#FEE2E2`。同级节点用同一视觉语法，颜色只在传达语义时变化。

- 先优化结构再优化装饰；优先减少文字拥挤、缩短节点和交叉线；必要时换图型，不得删除真实节点求整洁。
- 字体使用现代无衬线中文字体；`Noto Sans CJK SC` 为候选，最终依服务端字体实际效果判断。相同层级的字重、字号、间距、圆角、边框要一致；至少保证中文与标签可读。
- WBS 平衡左右主分支，但不要求完全对称；层级不超过读者可理解的粒度。Activity 保持主流程自上而下，分支标明「是 / 否」和退出条件；序列图按消息真实先后组织。
- 优先使用官方文档确证的 `<style>`/`skinparam`；不同图型样式能力不同，不把 CSS 或 WBS 的参数直接套到 Activity。示例：`examples/01_wbs.puml` 与 `examples/02_activity.puml`。
- 视觉评分不是事实验收。若无法取得远程图像，只能声称样式规则已写入，不能声称视觉检查通过。

## URL 与网络规则
- 默认用 `python scripts/encode_url.py <file.puml>` 离线生成可点击直链；无网络请求、无 PNG 下载。官方格式：raw DEFLATE + **PlantUML 专用 Base64 字符表**；Kroki：zlib + URL-safe Base64。这两种 token 不可混用。
- 不得对敏感源码输出可公开解码的 URL；若确有敏感材料，优先本地 PlantUML 渲染（且不泄露源码）；`--private` 会拒绝公共 URL 生成。
- 仅在用户授权公共渲染与实际联网核验时调用 `--check-online --public-ok`；需要保存 PNG 时另外显式提供 `--download <path> --public-ok`。网络错误可尝试备用 Kroki；语法错误不可仅靠切换服务掩盖。
- 服务端即便 HTTP 200、PNG 签名有效，仍可能是 **PlantUML 错误图**。检查 HTTP 错误头、格式、尺寸，并在能够读取图片时检查内容；无法检查时明说「视觉未验证」。
- 图片 URL 很长时标注其长度与平台/代理截断风险；不剪掉 token 或伪造短链。

## 修复与退出
- **静态门**：起止语法标记、图类型、节点关系、条件标签、信息泄露门。
- **远程门**：取得 HTTP 2xx、`image/png`、结构有效图片、无明确错误头；完成后仍只能标为 `PNG_VALIDATED / VISUAL_UNVERIFIED`。
- **视觉门**：实际查看图片，检查中文字体、文字截断、重叠、跳线、语义颜色和移动端缩放。只有检查真实图像后才能标记 `VISUALLY_REVIEWED`。
- 单次最多两轮证据驱动的最小修复；每轮比较与前一轮的节点和关系。未达标时保留最后可运行源码、错误信息、待验证项目，不继续无限优化。

## 输出模板（默认紧凑）
在线 PNG：[PlantUML 图片直链](https://www.plantuml.com/plantuml/png/{TOKEN})
备用 PNG：[Kroki 图片直链](https://kroki.io/plantuml/png/{TOKEN})
状态：`URL_GENERATED / HTTP_UNVERIFIED`（如果没有实际访问）；或者实际观测到的更高状态。

用户明确请求源码/图型说明时补充相应内容。**用户只请求 URL 时，直接给 URL。**

## 回归用例
- Case A：把同一主题组织为四个工作包；预期 WBS，MECE 只施加在分类上，保证层级完整、没有伪造依赖。
- Case B：把同一主题表达为顺序/判断/修复闭环；预期 Activity，有条件标签、退出条件、不把循环当作分类。
- Case C：URL-only 不发起网络，也不写 PNG；明确 `--private` 必须拒绝；未授权的 `--check-online` / `--download` 必须失败。
- Case D：校验 PlantUML 官方已知编码值、中文 round trip、Kroki 编码、HTTP 错误、PNG 伪响应、主服务失败回退及语法错误不回退。

参考文档：<https://plantuml.com/server> · <https://plantuml.com/text-encoding> · <https://plantuml.com/wbs-diagram> · <https://plantuml.com/activity-diagram-beta> · <https://docs.kroki.io/kroki/setup/usage>
