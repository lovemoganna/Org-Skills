---
name: plantuml-diagram-engine
description: 将文字、代码、业务流程或本体模型转为 PlantUML，按语义选择 WBS、活动图、时序图、组件图、状态图、类图、部署图、甘特图或思维导图，设计清晰统一的图形样式，并默认返回可直接打开的在线 PNG 图片 URL。适用于用户要求 PlantUML、图解、流程图、结构图、类图、架构部署图、排期甘特图、思维导图、在线渲染图片链接或优化已有 .puml；不默认下载文件。
---

# PlantUML Diagram Engine v1.4

## 唯一交付目标
**默认直接返还在线 PNG 图片直链**：`https://www.plantuml.com/plantuml/png/{TOKEN}`；同时允许附上 Kroki 备用 PNG 图片直链。不要把编辑器网址、`sandbox:`、PNG 附件、ZIP 或源代码当作主交付。仅在用户主动要求下载或本地渲染时保存文件。

## 输入契约
- 接受原始材料、已有 `.puml`、代码、业务描述和已有图；默认保留原始事实、专有名称、触发条件和证据状态。
- 缺少不影响画图的细节时做最小假设并标注；缺少关键条件时不捏造分支。除非用户明确授权，不处理真实 UID、密码、私有架构或内部风控参数到公共渲染服务；URL 是可解码的源码，**不是加密**。
- 用户只要链接，就不要额外输出冗长本体论、MECE 报告或 ZIP；源码按需附带。

## 合并决策协议：不是机械拼接两个提示
1. **语义重建**：抽取对象、属性、动作、条件、顺序、消息、状态与依赖；区分「明确事实 / 推断 / 缺口」。以最短路径推导图的真实阅读目的。
2. **按目的选主图**：分类与任务拆解选 WBS；顺序、条件、回路选 Activity；参与者消息交互选 Sequence；系统逻辑依赖选 Component；硬件/网络/容器节点分布选 Deployment；单实体生命周期演进选 State；实体属性契约与关系选 Class；时间线/工期前后置依赖选 Gantt；发散概念与知识脑图选 MindMap（各类型详细约束与语法门禁参考 `registry/diagram_types.json`）。默认只出一张主图；用户明确需要多个视角才多图。
3. **智能深度**：简单输入直接出图；只有复杂结构/术语歧义时启动本体建模；只有同口径互斥分类时做 MECE 检查；TRIZ/洞察仅在用户要求创新时启用。不把时间顺序或因果关系强塞进 MECE 树。
4. **语义映射**：关键对象、关系、条件必须在源码中可追溯；图型不可表达的关系用说明补足，不新增虚构关联。已给 `.puml` 时执行最小差异修改。
5. **输出源码**：编写一份完整的 UTF-8 `.puml`，确保 `@startuml`/`@enduml` 等匹配。不要把未经运行的代码称作“验证通过”。

## 默认视觉方案：Ink & Signal (v17)（默认生图必须加载）
所有生成的 PlantUML 图必须加载通用样式规范 `styles/style-ink-and-signal.puml`（通过 `!include styles/style-ink-and-signal.puml` 加载，或在单文件独立交付时完整内联注入）。`scripts/encode_url.py` 原生支持 `!include` 预处理内联，生成可直接在公网 PlantUML / Kroki 渲染的有效直链。

### 1. 设计语言与色彩规范
- **设计基调**：暖纸底 `#FAF8F3`（深色 `#13111F`）+ 靛蓝墨色 `#1B1836`（深色 `#EEEAFB`）+ 信号黄 `#FFCD00`。无阴影（`shadowing false`）、发丝线边框（1px）、圆角统一（10px）。
- **语义色只用于风险与状态**：
  - 极低/安全：构造型 `<<ok>>` 或常量 `COLOR_RISK_OK_BG`（`#EBF0D6`，边框 `#5F7600`）
  - 低风险：构造型 `<<low>>` 或常量 `COLOR_RISK_LOW_BG`（`#E3F2F3`，边框 `#2E7F85`）
  - 中风险：构造型 `<<mid>>` 或常量 `COLOR_RISK_MID_BG`（`#FDEEDC`，边框 `#C25E00`）
  - 高风险/错误：构造型 `<<high>>` 或常量 `COLOR_RISK_HIGH_BG`（`#F9E1E1`，边框 `#C82829`）

### 2. 参数注入规范（在 !include 之前声明）
- 深色主题：`!$THEME = "dark"`
- 正交连线：`!$LINETYPE = "ortho"`（默认 `polyline`）
- 状态图紧凑：`!$STATE_COMPACT = %true()`（写入 `hide empty description`；甘特图等非法类型默认关闭）
- 字体覆盖：`!$FONT_BODY`（默认 `"Noto Sans SC"`）、`!$FONT_TITLE`（默认 `"Noto Serif SC"`）、`!$FONT_NOTE`（默认 `"LXGW WenKai Mono"`）

### 3. 各图型排版与语法门禁
- **树状图/脑图/WBS**：根节点实心深色底（`#211551`），一级节点浅底（`#F1EEE6`），叶子节点白底（`#FFFFFF`）。平衡左右分支，层级不过载。
- **活动图**：主流程自上而下，分支标明「是 / 否」和退出条件，尽量采用显式 `if (...) then (...) else (...) endif`。
- **时序图**：消息严格按真实先后组织，生命线与分组边框采用低饱和暖灰。
- **甘特图**：必须使用专属定界符 `@startgantt`，前后置依赖必须使用撇号语法 `[Task2] starts at [Task1]'s end`。
- **组件图**：必须显式声明组件（如 `component "Name" as alias`），严禁使用无声明的裸写方括号（如 `[A] --> [B]`），否则会被服务端按时序图误解析导致 HTTP 400。
- **类图**：所有属性与方法必须独立成行，严禁单行分号压缩语法。
- 视觉评分不是事实验收。若无法取得远程图像，只能声称样式规则已写入，不能声称视觉检查通过。

## URL 与网络规则
- 默认用 `python skills/plantuml-diagram-engine/scripts/encode_url.py <file.puml>`（或在对应目录执行 `python scripts/encode_url.py`）离线生成可点击直链；无网络请求、无 PNG 下载。官方格式：raw DEFLATE + **PlantUML 专用 Base64 字符表**；Kroki：zlib + URL-safe Base64。这两种 token 不可混用。
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

## 回归用例（全部 9 类图已验证支持）
- Case 01 (WBS): 四个工作包组织，MECE 互斥分类，层级完整 (`examples/01_wbs.puml`)。
- Case 02 (Activity): 顺序/判断/修复闭环，分支标明条件标签 (`examples/02_activity.puml`)。
- Case 03 (Deployment): 节点集群、网络隔离区与通信端口协议 (`examples/03_deployment.puml`)。
- Case 04 (Gantt): 专用定界符 `@startgantt`，任务工期与前后置依赖 (`examples/04_gantt.puml`)。
- Case 05 (MindMap): 专用定界符 `@startmindmap`，放射状发散与双向分支 (`examples/05_mindmap.puml`)。
- Case 06 (Sequence): 交易支付时序交互、参与者生命线与分支响应 (`examples/06_sequence.puml`)。
- Case 07 (State): 订单全生命周期状态流转与守卫条件 (`examples/07_state.puml`)。
- Case 08 (Component): 电商微服务解耦、构造型语义色与数据持久层 (`examples/08_component.puml`)。
- Case 09 (Class): DDD 领域模型、字段方法独立成行与组合继承关联 (`examples/09_class.puml`)。
- Case Security & Offline: 默认离线 URL 生成不发起网络；明确 `--private` 必须阻断公共直链；未授权的 `--check-online` / `--download` 必须失败；语法错误不盲目降级。

参考文档：<https://plantuml.com/server> · <https://plantuml.com/text-encoding> · <https://plantuml.com/wbs-diagram> · <https://plantuml.com/activity-diagram-beta> · <https://docs.kroki.io/kroki/setup/usage>


## v17.1 样式回归与兼容性门禁（2026-10-20）
- 通用配置唯一来源：`styles/style-ink-and-signal.puml`。所有示例和新图必须通过 `!include` 加载；不得在业务图中复制第二套全局配色或强制覆盖样式。深色、正交连线、紧凑状态图参数必须在 `!include` 之前声明。
- v17 兼容矩阵：浅色活动图、深色时序图、正交组件图、紧凑状态图、甘特图；可复现源码见 `tests/style-v17/`。同时保留并回归 `examples/` 现有九类基准图，不允许以新增样例取代历史回归。
- 自动渲染：`.github/workflows/plantuml-style-v17.yml` 使用固定版本 PlantUML 和 SHA-256 校验，先 `-checkonly` 再输出 SVG，检查 SVG 格式并上传预览工件。源码解析通过不等于视觉已检查；图形实际被查看前不得标为 `VISUALLY_REVIEWED`。
- 稳定性检查：兼容常量与 `<<low>> / <<mid>> / <<high>> / <<ok>>` 需保留；禁止用 `root.LineColor` 或 `root.BackGroundColor` 覆盖子元素语义色；脑图/WBS 不得被组件图的全局居中规则污染。默认 `$STATE_COMPACT=%false()`，防止甘特图解析异常。
- 失败时保持最近一版有效源码、失败图型、错误日志及修复差异；不能将未运行的 fixture 或 URL 生成称为渲染通过。

- 活动图着色须用当前语法 `:动作; <<#RRGGBB>>`，不得再用会产生警告且错误显示的 `#RRGGBB:动作;`；全局 `skinparam padding` 已移除，以免渲染出废弃提示横幅。
