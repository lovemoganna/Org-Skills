# 电力负荷阻塞审计报告

**状态：阻塞，未完成分析。**

指定源：https://raw.githubusercontent.com/movingpictures83/Electricity/main/LD2011_2014.txt

DuckDB 执行环境：{'duckdb': '1.4.2', 'platform': 'linux', 'html_mode': 'single self-contained static HTML', 'browser_remote_fetch': False, 'wasm': False, 'cors_required': False, 'file_origin': 'opaque/null when opened as file://; no fetch calls'}

真实错误：

AssertionError: 

运行步骤：
[
  {
    "stage": "Source Gate",
    "status": "PASS"
  },
  {
    "stage": "Format Gate",
    "status": "PASS"
  },
  {
    "stage": "DuckDB Grain + Quality Gate",
    "status": "PASS"
  }
]

未执行：阻塞点后的所有下游分析；不得生成 Finding。

复跑：python skills/ontology-constrained-analysis/scripts/electricity_case_runner.py

恢复条件：指定 URL 原始字节成功取得，且原生 DuckDB 可以执行当前脚本。
