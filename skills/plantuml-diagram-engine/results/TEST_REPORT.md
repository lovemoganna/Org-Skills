# plantuml-diagram-engine v1.3 — 9 大图类型全量扩展与 Ink & Signal 样式报告

## 1. 变更与扩展范围
- **图类型体系全量支持（9 大类图）**：
  - 正式支持并建立基线：`WBS`、`Activity`、`Deployment`、`Gantt`、`MindMap`、`Sequence`、`State`、`Component`、`Class`。
  - 为全部 9 种图提供官方独立标准示例：`examples/01_wbs.puml` 到 `examples/09_class.puml`。
- **架构解耦与防误判指南（独立 Registry）**：
  - 更新 `registry/diagram_types.json`：建立 `selection_decision_tree`、各图类型的 `delimiters`、`semantic_purpose`、`selection_rules`、`syntax_constraints`、`anti_patterns` 以及关键的 `disambiguation_vs_adjacent`（相邻易混类型防误判指南，如 Activity vs State、Component vs Deployment、Sequence vs Activity、WBS vs MindMap）。
- **默认通用样式基线（Ink & Signal v7）**：
  - 所有 9 个示例文件统一采用 `!include ../styles/style-ink-and-signal.puml` 加载官方样式。
  - 核心设计：暖纸底 `#FAF8F3` + 靛蓝墨色 `#1B1836` + 信号黄 `#FFCD00`；无阴影、发丝线边框（1.25px）、圆角统一（10px）。
  - 语义构造型支持：`<<low>>`、`<<mid>>`、`<<high>>`、`<<ok>>`。
- **离线预处理引擎（`scripts/encode_url.py`）**：
  - 原生支持 `resolve_includes` 递归内联预处理。在生成直链时，自动在内存展开外部样式，避免公网 PlantUML / Kroki 服务因本地文件访问受限报 `HTTP 403 Forbidden`。
- **核心语法规约与门禁强化**：
  - **Class 类图**：属性与方法必须独立成行，严禁单行分号（`{ id; name }` 会导致服务端误判为 Sequence 并触发 HTTP 400）。
  - **Component 组件图**：强制显式声明组件（`component "Name" as alias`），严禁使用裸写纯方括号（`[A] --> [B]`），避免引擎按 Sequence 误解析。
  - **Gantt 甘特图**：任务依赖强制使用标准撇号语法 `[Task2] starts at [Task1]'s end`，定界符严格使用 `@startgantt`。
  - **MindMap 思维导图**：定界符严格使用 `@startmindmap`，支持 `left side` 双向展开。
  - **敏感信息前置门禁**：生成公开 URL 前拦截敏感信息（Fail-Closed）。

---

## 2. 真实服务端渲染验证（9 类图官方验证矩阵）

全部 9 个基准示例通过 `python scripts/encode_url.py examples/*.puml --check-online --public-ok --json` 向官方 PlantUML 远程服务发起真实 HTTP 请求并校验图片字节，状态全部达到 **PNG_VALIDATED / VISUAL_UNVERIFIED**：

| 示例文件 | 图类型 | 包含语法与语义特性 | 官方远程响应 | 图片分辨率 |
| :--- | :--- | :--- | :---: | :---: |
| `01_wbs.puml` | WBS | 4 大分类 / 12 叶子节点 / MECE | **HTTP 200** | 1401 × 745 |
| `02_activity.puml` | Activity | 顺序、分支、双向回路、有限回修退出 | **HTTP 200** | 1218 × 1424 |
| `03_deployment.puml` | Deployment | 物理节点、DMZ 隔离区、TCP/HTTPS 端口与协议 | **HTTP 200** | 1729 × 1374 |
| `04_gantt.puml` | Gantt | `@startgantt`、工期、里程碑、依赖关系 | **HTTP 200** | 1570 × 395 |
| `05_mindmap.puml` | MindMap | `@startmindmap`、双向展开 `left side`、知识树 | **HTTP 200** | 1684 × 804 |
| `06_sequence.puml` | Sequence | 顾客/网关/订单/风控/库存时序交互、生命线、alt 分支 | **HTTP 200** | 1990 × 1586 |
| `07_state.puml` | State | 订单全生命周期（待支付/已支付/发货/售后/退款/完成） | **HTTP 200** | 1035 × 1830 |
| `08_component.puml` | Component | 网关/业务核心/数据层包围、显式声明、语义构造型 | **HTTP 200** | 2431 × 935 |
| `09_class.puml` | Class | DDD 实体（Order, Customer, Product）、属性方法独立成行 | **HTTP 200** | 1136 × 1607 |

---

## 3. 单元回归测试（Unit Test Suite）

执行命令：`python -m pytest -v tests/test_encode_url.py`
- **测试结果**：**29 passed / 0 failed** (0.24s)
- **测试覆盖维度**：
  - 9 大图类型专属语义结构测试（如分支标签、端口协议、甘特依赖、双向脑图、生命线激活、状态转移、显式组件、DDD 类关系）。
  - 通用样式 `styles/style-ink-and-signal.puml` 文件与令牌完整性。
  - 本地 `!include` 预处理内联与 CLI 往返解析测试。
  - 全部 9 个 `.puml` 文件 CJK 往返编解码测试（`test_cjk_roundtrip_both_backends` 全部通过）。
  - 全部 9 个 `.puml` 定界符配对静态合法性校验（`test_source_type_valid` 全部通过）。
  - 敏感信息拦截门禁、未授权禁止外发网络、Kroki 安全降级、语法错误防盲目 Fallback。

---

## 4. 交付文件清单与代码差异
1. `registry/diagram_types.json`：新增/扩充 9 种图类型的决策树、定界符、语法门禁、防误判指南与反模式约束。
2. `styles/style-ink-and-signal.puml`：Ink & Signal (v7) 官方通用样式文件。
3. `scripts/encode_url.py`：新增 `resolve_includes` 递归内联预处理器，支持包含 `!include` 语法的直接公网直链生成。
4. `SKILL.md`：
   - 纳入全部 9 种支持的图类型与路由规则。
   - 切换默认视觉方案至 Ink & Signal (v7)，设为生图必须加载的基线样式。
   - 补充参数注入规范（主题、折线、状态图紧凑、字体标准）。
   - 强化组件图与类图语法门禁。
   - 补充 9 个官方样例的回归用例清单。
5. `examples/`：完整覆盖 9 种图型的官方样例（`01_wbs.puml` ~ `09_class.puml`），全部加载通用样式。
6. `tests/test_encode_url.py`：扩充至 29 个端到端结构与安全回归测试用例。

---

## 5. 剩余限制与后续建议
1. **本地纯离线渲染**：由于运行环境未配置 Java Runtime 及 Graphviz (`dot`)，目前仍依赖在线 PlantUML / Kroki 生成图片直链；本地直出 PNG 需要部署本地渲染容器或安装 JRE + Graphviz。
2. **超长图 URL 长度限制**：PlantUML GET URL 最大长度建议在 2000~4000 字符内，对于包含数千节点的特大型图，需建议用户分拆子图或使用 POST 协议/本地渲染。
3. **甘特图与脑图的专用引擎差异**：Gantt 与 MindMap 在 PlantUML 内部属于专用引擎，不支持常规 UML 图的全部通用 skinparam，需遵循其专属内联与 `<style>` 语法。
