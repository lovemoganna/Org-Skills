# Runtime Gate

## 目标

解决执行环境问题，不改变分析契约。

运行时修复只允许改变“在哪里执行”。不得改变“读什么、怎么读、允许读什么”。

## 锁定执行契约

任务明确指定以下任一内容时，先记录并锁定：

```text
执行引擎
数据源或 URL
读取函数
SQL 文本
参数
扩展
初始化顺序
允许表或工作表
禁止表或工作表
权限边界
```

用户明确要求“不得改写”时，以上内容视为硬约束。

## 能力检查

执行前检查当前运行时是否具备：

1. 指定引擎。
2. 指定扩展及版本所需能力。
3. 指定读取函数。
4. 数据源网络可达性。
5. 必要认证或权限。
6. 当前平台限制，包括浏览器 CORS。
7. 足够的内存和文件大小支持。

检查只用于判断能否执行，不得借此读取禁止数据。

## 运行时修复顺序

当前运行时失败时，依次尝试当前工具可用的同引擎运行时：

```text
原运行时
原生 DuckDB
DuckDB 浏览器/WASM
托管或云端 DuckDB
其他能够原样执行当前契约的 DuckDB 运行时
```

不要求机械尝试所有类型。只尝试当前实际可用且可能满足契约的路径。

每次切换前必须确认：

```text
引擎仍是 DuckDB
数据源未变化
读取函数未变化
固定 SQL 未变化
允许/禁止范围未变化
查询结果仍来自真实执行
```

任何一项变化，都不是等价运行时。


## 源 URL 与读取函数分离

分别确认用户锁定的是“数据来源”还是“读取函数”。

- 只锁定源 URL 和 DuckDB、未锁定读取函数：可以从相同 URL 获取完整原始字节并暂存本地，再由 DuckDB 使用适合实际文件格式的读取函数读取；这是传输缓冲，不是更换来源。必须记录 URL、实际文件字节数、SHA-256、读取时间和 DuckDB 实际使用的暂存路径。不能用镜像、其他仓库、示例数据替换。
- 同时锁定 `read_csv('https://...')`、`read_xlsx('https://...')` 或完整读取 SQL：必须保持函数、URL 和参数，不得擅自改成本地路径。
- 无论何种方式，网络允许看见 GitHub 元数据不代表容器已取得文件字节；`Blob SHA` 不能代替本地文件哈希和读取成功。
- 暂存路径可以不同于原始 URL，但来源链必须可逐字节复核。

若既没有直连网络，也没有经用户指定 URL 得到的完整原始字节，判为 `SOURCE_BYTES_UNAVAILABLE`，不得借助另一个数据集完成分析。

## 阻塞交付合同

优先执行 `python scripts/source_gate.py --manifest <manifest.json> --out <out>`；失败必须生成 `source_gate_receipt.json`、`source_gate_blocked.md` 和 `source_gate_blocked.html`。禁止因源不可达只输出状态消息而丢失报告。源 Gate 通过后仍需独立 DuckDB 文件格式解析检查，不能将 Source Gate 通过等同分析成功。

遇到源不可用时，必须写出：

```text
本次状态：阻塞，不等于分析通过
已验证：URL/元数据/本地字节/文件格式解析/DuckDB读取（逐项标注）
实际错误：原文
最后成功阶段：有证据的阶段
后续状态：未执行，不得用计划结果替代
可复跑命令与 SQL
恢复条件：网络可达或完整的同源字节已进入 DuckDB 环境
报告链接：即使失败也交付
```

用户授权“执行全流程”只代表正常路径无需逐阶段确认；一旦源数据 Gate 失败，绝不越权生成 Finding。

## DuckDB-Wasm

DuckDB-Wasm 可以作为等价运行位置，但不能默认认为兼容。

必须实际验证：

```text
所需扩展可以 LOAD
所需函数存在
远程源可以访问
CORS 允许访问
原始 SQL 可以执行
```

DuckDB-Wasm 中 `INSTALL` 可能是 no-op；这属于运行时实现差异，不得据此改写用户 SQL。

浏览器 HTTP 能力受 CORS 限制。锁定远程读取函数或 SQL 时，不得改为本地路径；未锁定读取函数时，允许经过来源和完整性验证的同源字节暂存。

如果当前版本的扩展或 `read_xlsx` 存在平台问题，判定该运行时不兼容，继续检查其他 DuckDB 运行时。

## 浏览器 Origin / CORS / 虚拟文件门禁

仅在用户最终运行环境进行的检查，才能标记“已实测”。记录实际网页 URL 与 Origin。单文件 `file://` 打开时，Origin 可能为 `null`；不可把服务器端请求或第三方抓取的成功当成浏览器 CORS 验收。没有可操控的最终浏览器时，标记“未实测”，禁止写“浏览器可运行”。

远程数据读取依次检查：

1. 最终浏览器能否下载指定 URL 的完整原始字节：真实 GET/HEAD 状态、重定向、`Access-Control-Allow-Origin` 对实际 Origin 是否有效，读取内容的实际字节数和 SHA-256；按实际读取方式验证 Range / `Accept-Ranges` / `Content-Range`，不能从 HTTP 状态推断完整性。
2. DuckDB-WASM 是否可加载、内存是否足够、需要的扩展与读取函数是否可用；随后用真实同源字节执行最小读取 SQL。
3. 原生 DuckDB 与 DuckDB-WASM 需要分别验收；API / GitHub 连接器读到文件，不等于本机或浏览器 VFS 已收到文件。

若**只锁定源 URL，不锁定读取函数与固定 SQL**，且浏览器从该 URL 取得完整原始字节，则可以：

```js
const response = await fetch(sourceUrl);
if (!response.ok) throw new Error(`HTTP ${response.status}`);
const bytes = new Uint8Array(await response.arrayBuffer());
await db.registerFileBuffer('source_original.txt', bytes);
```

上例是实现方式，不是通过证据：需要实际核验源字节、长度、哈希与目标环境。对于远程 XLSX，优先注册完整原始 XLSX 到虚拟文件系统，继续使用 DuckDB 的 `read_xlsx('source_original.xlsx')`，并实测 excel 扩展、格式和函数；禁止替换成 CSV、openpyxl 或模拟数据。对于 TXT，按真实分隔符、编码、值格式选择原生 DuckDB 的文本读取函数，不将 TXT 当 XLSX。

如果用户锁定完整远程 SQL 或精确路径参数，改变路径并不自动等价；除非用户另行明确授权，否则保留原 SQL，记录“不兼容”并检查其他等价 DuckDB 运行时。

## SQL 展示验收

单 HTML 报告须在无需外网 CSS/JS 的情况下可读。所有 SQL 经过同一格式化流程，保留语句层级、换行、缩进。所有 SQL 容器使用同一套语法高亮规则；静态、动态、教程、验证和最终 SQL 不能各用一套。复制动作读取格式化后的 SQL 原文，不能复制 HTML、行号或转义展示字符。若浏览器不可实测，明确标记复制按钮的运行状态，不能宣称通过端到端验收。

## GitHub 同源文件回退

当指定 URL 是 `raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}` 且本地不能连通该主机时：

1. 使用同一 owner/repo/ref/path 查找 GitHub 文件元数据，确认与指定文件相符。`github.com` 的大文件预览提示不代表源文件不存在。
2. 若 GitHub Git Blobs API 能返回完整原始字节，可使用 `api.github.com/repos/{owner}/{repo}/git/blobs/{sha}` 取得原始内容，解码后独立计算 Git Blob SHA-1 与 SHA-256，并与同一路径的元数据 SHA 比对；如提供预期哈希，还必须核对预期哈希。
3. 任何失败只说明该传输路线不可用；继续检查可用的同引擎执行环境，例如已授权 GitHub Actions Runner。不得把搜索网页、截断内容、API 元数据或文件大小推测当作 DuckDB Result。
4. `source_gate_receipt.json` 同时保留原 URL、实际获取端点、字节数、SHA-256、Git Blob SHA、请求时间与真实错误。仅在完整性通过后才解析格式和执行 SQL。

## 同源源文件实际恢复顺序

1. 原 URL：使用 `scripts/source_gate.py`，默认三次重试；检查 HTTP 完整长度或用户固定哈希。断点续传必须校验 ETag、Content-Range 与完整长度。缺失长度和哈希不能判为下载成功。
2. 同一 GitHub 文件：若 `raw.githubusercontent.com` 失败，用 `--prefer-github-blob` 直接走 GitHub 回退。先从 Contents 元数据取得同一 owner/repo/ref/path 对应的 Git Blob SHA 与字节数，再尝试 Git Blobs 原始字节接口，失败后尝试对应的 `github.com/{owner}/{repo}/raw/{ref}/{path}`。仅接受实际落盘、长度一致、Git Blob SHA 校验通过的字节。GitHub 文件网页与元数据不是文件内容。
3. 大文件：API Git Blobs 存在文件大小限制；API 失败不能说明文件不存在。改试同一仓库的文件原始下载端点，流式落盘并核验 Git Blob SHA；不下载一个截断的网页预览代替数据。若 Contents 元数据也无法取得，标记路径校验未完成，不得宣称通过。
4. 运行环境：本机缺 DuckDB 时，检查当前获授权、能真实运行 DuckDB 的等价环境。GitHub 连接器读取原文不意味着字节已进入本地或浏览器运行时。任何等价环境都要重新实测文件路径、扩展、格式读取及 SQL。
5. 文件已就绪才进入格式、记录、粒度、单位核验。数据门禁失败时写出三份阻塞回执，记录各传输端点和错误、已验证范围、明确的重跑入口；不得生成 SQL Result 或 Finding。

清单示例（仅传输约束，不预设数据结构）：

```json
{
  "files": [{
    "name": "LD2011_2014.txt",
    "url": "https://raw.githubusercontent.com/movingpictures83/Electricity/main/LD2011_2014.txt"
  }]
}
```

```bash
python scripts/source_gate.py --manifest manifest.json --out artifacts/source
python scripts/source_gate.py --manifest manifest.json --out artifacts/source --prefer-github-blob
```

`--prefer-github-blob` 是同源传输回退，不代表绕过 Git Blob SHA 校验；上述示例 URL 不是测试答案或数据分析模板。

## 禁止降级

用户指定 DuckDB `read_xlsx` 时，未经用户明确允许，不得改成：

```text
pandas
openpyxl
Google Sheets API
CSV 导出
手工下载后改成本地路径
其他数据库
从禁止工作表取得字段或答案
```

这些方法即使能得到相同数据，也改变了执行契约。

## 原始读取

找到兼容运行时后，直接执行用户指定读取。

用户要求 `INSTALL` 和 `LOAD` 只执行一次时，在同一执行会话中只执行一次。

读取其他允许对象时，只修改用户明确允许修改的参数。

不得为了“探测”读取禁止对象。

## Runtime Receipt

记录：

| 字段 | 内容 |
|---|---|
| 原运行时 | 实际环境 |
| 原失败 | 具体失败点 |
| 替代运行时 | 实际采用环境 |
| 契约变化 | 必须为“无”，否则不得继续 |
| 能力验证 | 扩展、函数、网络、权限结果 |
| 原始读取 | 成功 / 失败 |

## 失败条件

只有满足以下条件才能停止：

```text
当前运行时失败
没有可用等价运行时，或所有可用等价运行时都已验证失败
禁止使用非等价读取方法
```

此时标记“执行阻塞”。

不得生成数据 Result、Signal、Finding 或 Dashboard。
