# Runtime Gate：数据、引擎、浏览器与报告

目标：保持用户输入和 SQL 契约，只修正执行位置或可证明等价的传输方式。来源可发现 ≠ 原始字节已取得 ≠ 引擎读取成功 ≠ 业务分析完成。

## 1. 锁定输入和执行契约

执行前逐项记录：引擎及版本、来源 URL、读取函数、完整 SQL/参数、扩展和初始化顺序/次数、允许/禁止表、工作表、权限、时间范围、最终部署 Origin、交付格式。

区分：

- **仅锁定原 URL、引擎，未锁定完整读取 SQL：** 可取得原 URL 的完整原始字节，校验来源、实际长度、SHA-256，暂存后由**原引擎**读取；记录暂存路径。这只改变传输位置。
- **锁定 `read_csv(URL)`、`read_xlsx(URL)`、完整 SQL 或固定路径参数：** 保留字面值、函数、参数及初始化次数；未获允许不得改成本地路径/VFS、CSV、其他引擎或其他来源。用户明确允许修改的 `sheet` 等参数除外。
- 任何情况下都不得读取禁止工作表、复用历史 Schema/结果、用连接器可见元数据冒充字节或 DuckDB 执行。

## 2. 当前运行时先验能力检查

实测：指定引擎、扩展/版本、读取函数、认证权限、远程可达、文件大小、内存、所需 SQL 与输出路径。安装成功不代表读取成功，格式解析通过不代表业务 SQL 成功。

当前运行时失败后，检查**当前获授权且可用**的等价 DuckDB 运行时（原生、浏览器 WASM、云端或 GitHub Actions 原生 DuckDB）。每次换位置重新验证引擎、固定 SQL、读取函数、来源和权限未变。不必机械测试不可用路径。环境不兼容时继续查下一个等价环境；全部不可用才阻塞。

如果用户要求 `INSTALL`/`LOAD` 各执行一次，必须同一 DuckDB 会话只执行一次。要求“每表读取并物化一次”时，逐表以原 `read_xlsx` 执行 `CREATE ... TABLE ... AS SELECT * FROM read_xlsx(...)`，保存真实执行回执；后续 SQL 只引用物化表，不得再次调用源读取函数。

## 3. 同源字节和 GitHub 传输恢复

先直连原 URL。失败且原 URL 是 `raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}` 时：

1. 解析并验证同一 owner、repo、ref、path，禁止推测有歧义的 ref/path。`github.com` 文件页或 Contents 元数据只证明定位，不证明取得原始内容。
2. 尝试同一 Git 对象的 REST Git Blobs 原始字节端点；不成功再试同一路径 `github.com/{owner}/{repo}/raw/{ref}/{path}`。只能接受实际落盘、长度一致、Git Blob SHA-1 与 SHA-256 已核验的完整字节。
3. GitHub API 大小限制/预览截断不证明文件不存在；可以流式读取同一 Git 对象。禁止改用不同仓库、提交、镜像、相似样例、截图或中断的预览页。
4. 断点续传需校验 ETag、Content-Range、完整长度；HTTP 响应不提供可信长度且无预期哈希时，不得把 EOF 当完整性通过。记录每次端点、错误、字节、取得时间及 SHA-256。
5. 字节进入指定 DuckDB 环境后，**重新**验证实际格式、读取函数、物化和业务 SQL；之前传输成功不是数据库成功。

`scripts/source_gate.py` 只承担传输和完整性检查；必要时按真实 manifest 执行：

```bash
python scripts/source_gate.py --manifest manifest.json --out artifacts/source
python scripts/source_gate.py --manifest manifest.json --out artifacts/source --prefer-github-blob
```

后者是同一 Git 对象的传输回退，不是绕过完整性检查。用户要求原完整远程 SQL 时，恢复同源字节不自动授权改写 SQL 路径。

## 4. 浏览器、WASM、CORS 与虚拟文件

针对**最终实际运行页面**逐项记录：

| 能力 | 实测证据 |
|---|---|
| Origin | 真实 URL/Origin；`file://` 可能产生 `null` Origin |
| 来源 HTTP | 浏览器 GET/HEAD 状态、重定向、有效 CORS 响应、字节数和 SHA-256 |
| Range | 实际 Range 请求、返回状态及 Content-Range；200 无有效范围回执只能 `NOT_CONFIRMED`，不能声称支持 206 |
| WASM | Worker/WASM 资源、内存、扩展 `LOAD`、函数可用性 |
| SQL | 保留固定 SQL 的实际执行 Result，以及物化/结果一致性 |
| VFS（允许时） | 原 URL 原始字节校验、`registerFileBuffer` / `registerFileHandle`、实际文件路径、`read_xlsx` 执行回执 |

原生 DuckDB、DuckDB-WASM、第三方连接器的成功互不替代。WASM 的 `INSTALL` 可能是 no-op；只能把它视为运行时差异，不能擅改固定 SQL。

只有来源 URL 被锁定、读取 SQL/路径未锁定时，才可把真实 XLSX 原始字节注册到 VFS 后使用 `read_xlsx`；必须验证 Excel 扩展和真实 SQL。用户锁定完整远程 SQL 时，即使 VFS 成功也只能把 VFS 标为独立能力检查，原 SQL 不兼容则寻找其他同引擎运行时。

没有可操作的**最终浏览器 Origin** 时，写“最终浏览器未实测”。`page.set_content`、Node 语法测试、Mock 复制、服务端 curl 和 CI 的其他 Origin 都不能替代最终部署端到端检查。

## 5. HTML 中 SQL 展示与复制

- 单 HTML 离线必须可阅读核心报告；不得依赖未经验证的 CDN 样式/脚本。
- 所有静态、动态、示例、验证、最终 SQL 块统一使用 `scripts/sql_ui.js` 格式化、语法高亮、纯 SQL 复制。格式化只服务展示，不改变已执行 SQL；复制不能包含 HTML、行号或装饰字符。
- 浏览器中分别实测格式、响应式布局、实际原生 Clipboard API。Clipboard 不可用时准确提示失败或使用已验证回退，不能把模拟点击等同系统剪贴板成功。
- 对于固定 SQL，保留“实际执行 SQL”和“仅展示用格式化 SQL”的区别；两者差异可追溯。

## 6. 阻塞报告与证据回执

当来源字节、权限或全部兼容 DuckDB 运行时均不可用时，停止生成数据 Result、Signal、Finding 和 Dashboard。即使用户要求完整报告，也必须提供：

- `source_gate_receipt.json`：原 URL、尝试端点、字节/哈希（成功时）、时间、具体错误及状态。
- `source_gate_blocked.md`、`source_gate_blocked.html`：明确“阻塞≠分析完成”，已完成与未执行步骤、原始报错、最后成功 Gate、可复跑命令和恢复条件。
- `Runtime Receipt`：原运行时、失败位置、兼容替代运行时、契约是否变化、扩展/网络/SQL 的真实验证结果。

只要源 Gate 失败就交付这三份审计文件；源 Gate 成功后仍需独立验证 DuckDB 实际读取和分析执行，不得因文件已下载便宣布完成。
