# 固定数据契约（V2.2）

## 工作簿

- 工作簿：<https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/edit?gid=1585191605#gid=1585191605>
- XLSX 导出：`https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx`
- **唯一允许读取的表**：`users`、`fiat_transactions`、`crypto_transactions`、`exchange_rates`。
- **禁止读取**：`Executive_Dashboard`、`expected_fiat_result`、`expected_crypto_result`、`data_rules`、`qa_result`、`fix_log`、备份页，以及所有未明确允许的表。不得读取这些页的结构、字段、规则、预期结果、答案、异常提示或分析线索。

## 读取契约

第一种方式：以 DuckDB `read_xlsx` 直接读取 XLSX；首次环境准备仅执行一次：

```sql
INSTALL httpfs;
LOAD httpfs;
INSTALL excel;
LOAD excel;

SELECT *
FROM read_xlsx(
  'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
  sheet = 'users',
  header = true
);
```

读取其他三张表时仅改变 `sheet` 参数。每张表在本轮最多物化一次，以免重复对远程 XLSX 抓取；以后通过已物化表名查询。四表 SQL 的字段名与类型必须来源于实际 DuckDB 勘察，不允许根据名称推断。

如果浏览器因 `file://` Origin、CORS、远程导出权限或 DuckDB-WASM 虚拟文件约束无法使用远程 URL：先取得**同一真实 XLSX** 的文件字节，上传 DuckDB Web Shell 或通过 DuckDB-WASM 文件 API 注册为 `workbook.xlsx`，之后运行：

```sql
SELECT *
FROM read_xlsx(
  'workbook.xlsx',
  sheet = 'users',
  header = true
);
```

这一兜底只改变可访问文件路径；不更换原始工作簿、不读取禁止页、不改用 CSV、Pandas 或模拟数据，不把旧快照悄悄充作当前数据。记录本地文件版本、来源时间及读取成功与否。对远程授权、扩展可用性与文件内容真实性没有证据时标记未确认。

## 启动检查

- 能否运行 DuckDB 引擎，`excel` 是否可加载？浏览器要验证 `registerFileBuffer`/上传与 Worker/WASM 支持。
- Google XLSX 导出是否返回真实 XLSX，而不是登录页或 HTML 错误？
- 能否指定四个白名单 `sheet` 并得到实际列/行？
- 对读取失败保留源错误，禁止“估算”数据来继续。

注意：本文件是该用户指定数据集的固定契约，不是任意 Google Sheets 的通用授权。
