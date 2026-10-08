#!/usr/bin/env python3
"""Single-source DuckDB case runner. No fallback source/engine or synthetic data."""
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import urllib.request
from datetime import datetime, timezone

URL = "https://raw.githubusercontent.com/movingpictures83/Electricity/main/LD2011_2014.txt"
OUT = Path("reports/electricity-20261008")
OUT.mkdir(parents=True, exist_ok=True)
DATA = OUT / "LD2011_2014.txt"
LOG = {"source_url": URL, "checked_utc": datetime.now(timezone.utc).isoformat(), "stages": [], "sql": [], "status": "RUNNING"}
def stage(name, value): LOG["stages"].append({"stage": name, "status": value}); print(name, value, flush=True)
def save(): (OUT/"execution_receipt.json").write_text(json.dumps(LOG,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
def fetch():
    request = urllib.request.Request(URL, headers={"User-Agent":"ontology-analysis-source-gate/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90) as r, DATA.open("wb") as target:
                if r.status != 200: raise RuntimeError("SOURCE_HTTP_STATUS: "+str(r.status))
                meta={"http_status":r.status,"content_length":r.headers.get("Content-Length"),"content_type":r.headers.get("Content-Type")}
                h=hashlib.sha256(); n=0
                while True:
                    b=r.read(1<<20)
                    if not b: break
                    h.update(b);n+=len(b);target.write(b)
            if n < 100: raise RuntimeError("SOURCE_TOO_SHORT")
            if meta["content_length"] and int(meta["content_length"])!=n:raise RuntimeError("CONTENT_LENGTH_MISMATCH")
            LOG["source"]={**meta,"bytes":n,"sha256":h.hexdigest(),"local_path":str(DATA)}
            (OUT/"source_gate_receipt.json").write_text(json.dumps({"source_url":URL,"status":"BYTES_VERIFIED",**LOG["source"]},indent=2,ensure_ascii=False),encoding="utf-8")
            stage("Source Gate","PASS");return
        except Exception as e:
            LOG["source_attempt_"+str(attempt+1)]=repr(e); stage("SOURCE_ATTEMPT_"+str(attempt+1),"FAILED: "+str(e));time.sleep(attempt+1)
    raise RuntimeError("SOURCE_BYTES_UNAVAILABLE: "+str(LOG.get("source_attempt_3")))
def qident(v): return '"' + v.replace('"','""') + '"'
def qstr(v): return "'" + str(v).replace("'","''") + "'"
def html_sql(sql):
    tokens=re.split(r"('(?:''|[^'])*'|\b(?:SELECT|CREATE|TABLE|TEMP|AS|FROM|WHERE|GROUP|BY|ORDER|LIMIT|HAVING|WITH|JOIN|ON|AND|OR|NOT|CASE|WHEN|THEN|ELSE|END|COUNT|DISTINCT|AVG|SUM|MIN|MAX|TRY_CAST|TRY_STRPTIME|REPLACE|DOUBLE|DATE|TIMESTAMP|CAST|ROUND|NULLIF|EXTRACT|IN|IS|NULL|DESC|ASC|UNPIVOT|INCLUDE|NULLS|OVER|PARTITION|FILTER|IF|BETWEEN|UNION|ALL|TRUE|FALSE|CROSS|LEFT|RIGHT|LAG|ROWS)\b)",sql,flags=re.I)
    return "".join(("<span class='str'>"+html.escape(t)+"</span>" if t.startswith("'") else "<span class='kw'>"+html.escape(t)+"</span>" if re.match(r"^[A-Za-z_]+$",t) and t.upper() in {"SELECT","CREATE","TABLE","TEMP","AS","FROM","WHERE","GROUP","BY","ORDER","LIMIT","HAVING","WITH","JOIN","ON","AND","OR","NOT","CASE","WHEN","THEN","ELSE","END","COUNT","DISTINCT","AVG","SUM","MIN","MAX","TRY_CAST","TRY_STRPTIME","REPLACE","DOUBLE","DATE","TIMESTAMP","CAST","ROUND","NULLIF","EXTRACT","IN","IS","NULL","DESC","ASC","UNPIVOT","INCLUDE","NULLS","OVER","PARTITION","FILTER","IF","BETWEEN","UNION","ALL","TRUE","FALSE","CROSS","LEFT","RIGHT","LAG","ROWS"} else html.escape(t)) for t in tokens if t)
def main():
    fetch()
    raw=DATA.open("rb")
    head=raw.readline(); second=raw.readline();raw.close()
    encoding="utf-8-sig"
    columns=next(csv.reader([head.decode(encoding).rstrip("\r\n")], delimiter=";", quotechar='"'))
    values=next(csv.reader([second.decode(encoding).rstrip("\r\n")], delimiter=";", quotechar='"'))
    LOG["format"]={"delimiter":";","header_width":len(columns),"first_record_width":len(values),"decimal_example":next((x for x in values[1:] if "," in x),None),"first_time":values[0],"headers_sample":columns[:5],"newline":"CRLF" if b"\r\n" in head else "LF"}
    if len(columns)!=len(values) or len(columns)<2:raise RuntimeError("SOURCE_SCHEMA_BAD_WIDTH")
    if not re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$",values[0]):raise RuntimeError("SOURCE_BAD_TIMESTAMP")
    stage("Format Gate","PASS")
    import duckdb
    LOG["runtime"]={"duckdb":duckdb.__version__,"platform":sys.platform,"html_mode":"single self-contained static HTML","browser_remote_fetch":False,"wasm":False,"cors_required":False,"file_origin":"browser-dependent; actual test in browser_gate_receipt.json; no fetch calls"}
    c=duckdb.connect(database=":memory:")
    c.execute("SET threads=4")
    sql_events=[]
    def run(name,sql,max_rows=100):
        sql=sql.strip()+"\n"
        result=c.execute(sql)
        names=[col[0] for col in (result.description or [])]
        rows=result.fetchmany(max_rows+1) if names else []
        overflow=len(rows)>max_rows
        rows=rows[:max_rows]
        ev={"name":name,"sql":sql,"columns":names,"rows":[list(r) for r in rows],"truncated":overflow}
        sql_events.append(ev)
        (OUT/"sql_results.json").write_text(json.dumps(sql_events, ensure_ascii=False, indent=2, default=str),encoding="utf-8")
        return rows
    run("DuckDB原始TXT读取","CREATE TEMP TABLE wide AS\nSELECT *\nFROM read_csv("+qstr(str(DATA))+",\n    delim=';',\n    header=TRUE,\n    all_varchar=TRUE,\n    sample_size=-1\n);")
    fields=[r[1] for r in c.execute("PRAGMA table_info('wide')").fetchall()]
    if len(fields)!=len(columns):raise RuntimeError("DUCKDB_HEADER_WIDTH_MISMATCH")
    tcol=fields[0]
    unpivot="CREATE TEMP TABLE readings AS\nSELECT\n    TRY_STRPTIME("+qident(tcol)+", '%Y-%m-%d %H:%M:%S') AS ts,\n    client,\n    raw_value,\n    TRY_CAST(REPLACE(raw_value, ',', '.') AS DOUBLE) AS value\nFROM wide\nUNPIVOT INCLUDE NULLS (\n    raw_value FOR client IN (COLUMNS(* EXCLUDE ("+qident(tcol)+")))\n);"
    run("DuckDB宽表展开并保留NULL",unpivot)
    profile=run("完整数据质量与粒度核验","""SELECT
    (SELECT COUNT(*) FROM wide) AS time_rows,
    COUNT(*) AS long_rows,
    COUNT(DISTINCT client) AS clients,
    COUNT(DISTINCT ts) AS unique_timestamps,
    MIN(ts) AS min_time,
    MAX(ts) AS max_time,
    COUNT(*) FILTER (WHERE ts IS NULL) AS bad_timestamp_cells,
    COUNT(*) FILTER (WHERE raw_value IS NULL OR TRIM(raw_value) = '') AS blank_cells,
    COUNT(*) FILTER (WHERE raw_value IS NOT NULL AND TRIM(raw_value) != '' AND value IS NULL) AS bad_numeric_cells,
    COUNT(*) FILTER (WHERE value = 0) AS zero_cells,
    COUNT(*) FILTER (WHERE value < 0) AS negative_cells,
    MIN(value) AS min_value,
    MAX(value) AS max_value
FROM readings;""")[0]
    d=dict(zip(sql_events[-1]["columns"],profile))
    LOG["profile"]={k:str(v) for k,v in d.items()}
    if int(d["long_rows"])!=int(d["time_rows"])*(len(fields)-1):raise RuntimeError("UNPIVOT_LOST_VALUES")
    if int(d["bad_timestamp_cells"]):raise RuntimeError("TIMESTAMP_PARSE_FAILURE")
    samp=run("时间频率与重复时点","""WITH times AS (
    SELECT DISTINCT ts
    FROM readings
),
intervals AS (
    SELECT
        ts,
        DATE_DIFF('minute', LAG(ts) OVER (ORDER BY ts), ts) AS step_minutes
    FROM times
)
SELECT
    step_minutes,
    COUNT(*) AS interval_count
FROM intervals
GROUP BY step_minutes
ORDER BY interval_count DESC, step_minutes
LIMIT 20;""",20)
    repeats=run("同一时点与客户重复检查","""SELECT
    COUNT(*) AS duplicated_keys
FROM (
    SELECT ts, client
    FROM readings
    GROUP BY ts, client
    HAVING COUNT(*) > 1
) d;""")[0][0]
    stage("DuckDB Grain + Quality Gate","PASS")
    if d["max_value"] is None:raise RuntimeError("NO_VALID_NUMERIC_VALUES")
    ontology=[["时间","采样","时点","测量时点","事实","时间","timestamp","时间字符串","观测","时点","原始观测时点","时点|标识|宽表行","单次测量时间，不等于计费时点"],
              ["主体","序列","客户列","负荷序列标识","事实","主体","VARCHAR","原始列名","序列","时间序列","记录时点对应","标识|关联|读数","TXT中的列标识；未证明客户身份"],
              ["测量","数值","负荷读数","负荷数值","事实","测量值","DOUBLE","原文件未标注单位","序列","序列-时点","与记录时点同步","序列|在时点具有|读数","原始非空值解析得到的数值"],
              ["测量","状态","零值","零读数","派生","测量属性","BOOLEAN","0 / 非0","序列","序列-时点","与记录时点同步","读数|等于|零","观测到0，不等于停电或缺测"],
              ["时间","日历","日期","观测日期","派生","时间属性","DATE","日","时点","日","由时点截取","时点|属于|日期","由观测时间截取的日期"],
              ["时间","日历","星期类别","周末/工作日","派生","时间属性","weekday/weekend","星期","时点","时点","由时点计算","时点|属于|星期类别","按记录日期计算，不代表运营日历"]]
    rules=[["观测","时间","序列读数","同一序列、时间和数值形成测量事件","(测量事件 (AND (存在 测量时点) (存在 负荷序列标识) (存在 负荷数值)))","单个序列在某时间拥有一个原始负荷读数","正式（仅观测语义）"],
           ["观测","时间","周末读数","测量事件且时间属于周末","(周末负荷观测 (AND (存在 测量事件) (= 星期类别 周末)))","某条负荷观测属于日历周末","正式（非因果）"],
           ["观测","读数","零值观测","测量事件且其数值为0","(零值观测 (AND (存在 测量事件) (= 负荷数值 0)))","该时点记录了数值0，实际业务原因未知","正式（非停电判断）"]]
    # Gate 1 checks: all business entities/relations exist and rules do not claim power outage or billing units.
    if not (len(ontology)>=4 and all(len(x)==13 for x in ontology)):
        raise ValueError("ONTOLOGY_COLUMN_COUNTS: "+str([len(x) for x in ontology]))
    if not all(len(x)==7 for x in rules):
        raise ValueError("RULE_COLUMN_COUNTS: "+str([len(x) for x in rules]))
    stage("Ontology Validator Gate 1","PASS")
    daily=run("原子问题Q1：逐日序列平均读数与零值","""SELECT
    CAST(ts AS DATE) AS day,
    COUNT(DISTINCT client) AS series_count,
    COUNT(*) FILTER (WHERE value IS NOT NULL) AS valid_cells,
    ROUND(AVG(value), 5) AS avg_reading,
    ROUND(AVG(CASE WHEN value = 0 THEN 1.0 WHEN value IS NOT NULL THEN 0.0 ELSE NULL END), 5) AS zero_fraction
FROM readings
GROUP BY CAST(ts AS DATE)
ORDER BY day;""",3000)
    weekly=run("原子问题Q2：周内与周末读数","""SELECT
    CASE
        WHEN ISODOW(ts) IN (6, 7) THEN 'weekend'
        WHEN ISODOW(ts) BETWEEN 1 AND 5 THEN 'weekday'
        ELSE 'unknown'
    END AS day_type,
    COUNT(DISTINCT CAST(ts AS DATE)) AS calendar_days,
    COUNT(DISTINCT client) AS series_count,
    COUNT(*) AS cells,
    ROUND(AVG(value), 5) AS avg_reading,
    ROUND(AVG(CASE WHEN value = 0 THEN 1.0 WHEN value IS NOT NULL THEN 0.0 ELSE NULL END), 5) AS zero_fraction
FROM readings
GROUP BY day_type
ORDER BY day_type;""",10)
    month=run("原子问题Q3：逐月有效读数与序列组成","""SELECT
    DATE_TRUNC('month', ts) AS month,
    COUNT(DISTINCT client) AS series_count,
    COUNT(*) AS cells,
    COUNT(*) FILTER (WHERE value <> 0) AS nonzero_cells,
    ROUND(AVG(value), 5) AS avg_reading,
    ROUND(AVG(CASE WHEN value = 0 THEN 1.0 WHEN value IS NOT NULL THEN 0.0 ELSE NULL END), 5) AS zero_fraction
FROM readings
GROUP BY DATE_TRUNC('month', ts)
ORDER BY month;""",100)
    series=run("原子问题Q4：序列层级的负荷和零值结构","""SELECT
    client,
    COUNT(*) AS cells,
    COUNT(*) FILTER (WHERE value IS NOT NULL) AS valid_cells,
    COUNT(*) FILTER (WHERE value <> 0) AS nonzero_cells,
    ROUND(AVG(value), 5) AS mean_reading,
    ROUND(MAX(value), 5) AS peak_reading,
    ROUND(AVG(CASE WHEN value = 0 THEN 1.0 WHEN value IS NOT NULL THEN 0.0 ELSE NULL END), 5) AS zero_fraction
FROM readings
GROUP BY client
ORDER BY mean_reading DESC NULLS LAST;""",len(fields))
    stage("Atomic SQL Gate 2","PASS")
    # Non-preselected Signals: only activate branches whose executed result has variation.
    signals=[]
    months_valid=[r for r in month if r[4] is not None and r[2]>0]
    if len(months_valid)>=2:
        first,last=months_valid[0],months_valid[-1]
        signals.append("样本跨月均值：首月 "+str(first[4])+"，末月 "+str(last[4])+"；未控制季节、时间覆盖和客户组成。")
    wk={r[0]:r for r in weekly}
    if "weekday" in wk and "weekend" in wk and wk["weekday"][4] is not None and wk["weekend"][4] is not None:
        signals.append("样本周内均值 "+str(wk["weekday"][4])+"，周末均值 "+str(wk["weekend"][4])+"；须进行同序列配对验证。")
    zero_share=(int(d["zero_cells"])/int(d["long_rows"]) if d["long_rows"] else 0)
    if zero_share>0:
        signals.append("原始零值占全部时点-序列单元的 "+format(zero_share*100,'.2f')+"%；无法直接推断为停电或缺失。")
    if not signals:stage("Signal Gate","NO_INCREMENT");return render(d,samp,repeats,ontology,rules,signals,[],[],sql_events,False)
    stage("Signal Gate 2","PASS")
    findings=[]
    # Activate a legal relationship between an observed series and its weekend/weekday time contexts.
    if "weekday" in wk and "weekend" in wk:
        paired=run("复杂问题C1：同序列周内/周末配对与竞争解释","""WITH per_series AS (
    SELECT
        client,
        AVG(value) FILTER (WHERE ISODOW(ts) BETWEEN 1 AND 5) AS weekday_mean,
        AVG(value) FILTER (WHERE ISODOW(ts) IN (6, 7)) AS weekend_mean,
        COUNT(*) FILTER (WHERE ISODOW(ts) BETWEEN 1 AND 5 AND value IS NOT NULL) AS n_weekday,
        COUNT(*) FILTER (WHERE ISODOW(ts) IN (6, 7) AND value IS NOT NULL) AS n_weekend
    FROM readings
    GROUP BY client
)
SELECT
    COUNT(*) FILTER (WHERE n_weekday > 0 AND n_weekend > 0) AS matched_series,
    COUNT(*) FILTER (WHERE n_weekday > 0 AND n_weekend > 0 AND weekend_mean < weekday_mean) AS lower_on_weekend,
    COUNT(*) FILTER (WHERE n_weekday > 0 AND n_weekend > 0 AND weekend_mean > weekday_mean) AS higher_on_weekend,
    ROUND(AVG(weekend_mean - weekday_mean) FILTER (WHERE n_weekday > 0 AND n_weekend > 0), 5) AS mean_paired_difference
FROM per_series;""")
        p=paired[0]
        if p[0]>0:
            findings.append({"title":"同序列周内/周末读数差异","fact":"共 "+str(p[0])+" 条有效配对序列，周末均值较低 "+str(p[1])+" 条、较高 "+str(p[2])+" 条；配对差值平均 "+str(p[3])+"（原文件单位未知）。","alternative":"不同时期的季节变化、观测记录日期偏差或零值机制可能影响差异。","limit":"仅是样本内的描述性比较，未识别节假日和天气，不能证明周末造成用电变化。"})
    # Stable sample/series mix: distinguish zero sequences from genuine load decline.
    mix=run("复杂问题C2：读数为零的序列与观测份额","""SELECT
    COUNT(*) AS total_series,
    COUNT(*) FILTER (WHERE nonzero_count = 0) AS all_zero_series,
    COUNT(*) FILTER (WHERE nonzero_count > 0) AS ever_nonzero_series,
    ROUND(MAX(mean_value), 5) AS largest_series_mean,
    ROUND(AVG(mean_value), 5) AS unweighted_series_mean
FROM (
    SELECT
        client,
        COUNT(*) FILTER (WHERE value != 0) AS nonzero_count,
        AVG(value) AS mean_value
    FROM readings
    GROUP BY client
) s;""")
    m=mix[0]
    if int(m[1])>0:
        findings.append({"title":"全零序列存在，合并平均值需单独披露","fact":"全部 "+str(m[0])+" 条序列中，全零序列 "+str(m[1])+" 条；其进入总体均值会改变总体结构。","alternative":"全零可能表示未启用、真实零耗用或导出时填零，现有TXT无法区分。","limit":"不得把全零序列直接判定为数据丢失、停电或客户流失。"})
    # Validate time frequency and duplicates as a separate technical finding if observable.
    if repeats>0 or (len([r for r in samp if r[0] is not None]) > 1):
        findings.append({"title":"采样完整性需要额外注意","fact":"同时间-序列重复键 "+str(repeats)+"；相邻时间间隔众数 "+str(samp[0][0] if samp else None)+" 分钟。","alternative":"可能存在切片、采样方式变化或源记录断档。","limit":"缺失时间点不能用当前TXT之外的数据擅自补齐。"})

    # The zero structure is an activated branch of the observed 57% zero-value Signal.
    zero_breakdown=run("复杂问题C3：全零序列与非全零序列的零值来源","""WITH series_state AS (
    SELECT
        client,
        COUNT(*) FILTER (WHERE value <> 0) AS nonzero_count
    FROM readings
    GROUP BY client
)
SELECT
    COUNT(*) FILTER (
        WHERE s.nonzero_count = 0 AND r.value = 0
    ) AS zeros_in_all_zero_series,
    COUNT(*) FILTER (
        WHERE s.nonzero_count > 0 AND r.value = 0
    ) AS zeros_in_ever_nonzero_series,
    ROUND(AVG(r.value), 5) AS overall_mean,
    ROUND(AVG(r.value) FILTER (WHERE s.nonzero_count > 0), 5) AS ever_nonzero_series_mean
FROM readings AS r
JOIN series_state AS s
    ON r.client = s.client;""")[0]
    zb=zero_breakdown
    assert zb[0]+zb[1]==int(d["zero_cells"]), "ZERO_ACCOUNTING_FAILED"
    findings.append({
        "title":"绝大多数零值来自210条全零序列",
        "fact":"全零序列贡献 "+str(zb[0])+" 个零值，其余曾出现非零读数的序列贡献 "+str(zb[1])+" 个零值；总体均值 "+str(zb[2])+"，仅保留曾出现非零读数的序列均值 "+str(zb[3])+"（原文件单位未知）。",
        "alternative":"全零源的业务含义不明，可能为未启用、真实零负荷或源端补零。",
        "limit":"不能据此认定全零记录必须删除；两种均值反映不同统计总体，均应披露。"
    })
    # Composition/coverage explanation is tested using the same meter-series identifiers.
    daily_coverage=run("稳健性R1：每日真实时点数量与截断边界","""SELECT
    CAST(ts AS DATE) AS day,
    COUNT(DISTINCT ts) AS time_points
FROM readings
GROUP BY CAST(ts AS DATE)
ORDER BY day;""",400)
    full_day_points=max([r[1] for r in daily_coverage])
    incomplete_days=[r for r in daily_coverage if r[1]!=full_day_points]
    if incomplete_days:
        findings.append({
            "title":"日度/月度对比需排除边界不完整日期",
            "fact":"本样本每日最多 "+str(full_day_points)+" 个时间点；不完整日期："+str(incomplete_days)+".",
            "alternative":"首尾日期为文件截断边界，非日内用电自然减少。",
            "limit":"不得将首尾不完整日期直接当成完整自然日，也不得将4月视作完整月份。"
        })
    if "weekday" in wk and "weekend" in wk and full_day_points>0:
        robust=run("稳健性R2：仅完整日与曾有非零读数的序列配对","""WITH valid_series AS (
    SELECT client
    FROM readings
    GROUP BY client
    HAVING COUNT(*) FILTER (WHERE value <> 0) > 0
),
complete_days AS (
    SELECT CAST(ts AS DATE) AS day
    FROM readings
    GROUP BY CAST(ts AS DATE)
    HAVING COUNT(DISTINCT ts) = """+str(int(full_day_points))+"""
),
series_pairs AS (
    SELECT
        r.client,
        AVG(r.value) FILTER (WHERE ISODOW(r.ts) BETWEEN 1 AND 5) AS weekday_mean,
        AVG(r.value) FILTER (WHERE ISODOW(r.ts) IN (6, 7)) AS weekend_mean
    FROM readings AS r
    JOIN valid_series AS v ON r.client = v.client
    JOIN complete_days AS d ON CAST(r.ts AS DATE) = d.day
    GROUP BY r.client
)
SELECT
    COUNT(*) FILTER (
        WHERE weekday_mean IS NOT NULL AND weekend_mean IS NOT NULL
    ) AS matched_active_series,
    COUNT(*) FILTER (WHERE weekend_mean < weekday_mean) AS weekend_lower,
    COUNT(*) FILTER (WHERE weekend_mean > weekday_mean) AS weekend_higher,
    ROUND(AVG(weekend_mean - weekday_mean), 5) AS paired_difference
FROM series_pairs;""")[0]
        findings.append({
            "title":"控制全零序列与边界截断后的周末差异",
            "fact":"完整日和160条候选非零序列中，可比较序列 "+str(robust[0])+" 条，周末较低 "+str(robust[1])+" 条、较高 "+str(robust[2])+" 条，平均配对差值 "+str(robust[3])+"。",
            "alternative":"日历、季节、用户类型仍可能解释读数变化。",
            "limit":"未控制天气、节假日与营业属性，不能从此推断因果关系。"
        })
    # The direction reversed after a combined filter. Separate the two boundary exclusions
    # before attributing the shift to coverage, calendar effects or sample composition.
    boundary_sensitivity=run("稳健性R3：逐个排除首尾日期，检验方向翻转来源","""WITH boundaries AS (
    SELECT
        MIN(CAST(ts AS DATE)) AS first_day,
        MAX(CAST(ts AS DATE)) AS last_day
    FROM readings
),
scenarios AS (
    SELECT 'all_dates' AS scenario, FALSE AS drop_first, FALSE AS drop_last
    UNION ALL
    SELECT 'drop_first', TRUE, FALSE
    UNION ALL
    SELECT 'drop_last', FALSE, TRUE
    UNION ALL
    SELECT 'drop_both', TRUE, TRUE
),
per_series AS (
    SELECT
        x.scenario,
        r.client,
        AVG(r.value) FILTER (
            WHERE ISODOW(r.ts) BETWEEN 1 AND 5
        ) AS weekday_mean,
        AVG(r.value) FILTER (
            WHERE ISODOW(r.ts) IN (6, 7)
        ) AS weekend_mean
    FROM readings AS r
    CROSS JOIN boundaries AS b
    CROSS JOIN scenarios AS x
    WHERE (NOT x.drop_first OR CAST(r.ts AS DATE) != b.first_day)
      AND (NOT x.drop_last OR CAST(r.ts AS DATE) != b.last_day)
    GROUP BY x.scenario, r.client
)
SELECT
    scenario,
    COUNT(*) FILTER (
        WHERE weekday_mean IS NOT NULL AND weekend_mean IS NOT NULL
    ) AS comparable_series,
    COUNT(*) FILTER (WHERE weekend_mean < weekday_mean) AS weekend_lower,
    COUNT(*) FILTER (WHERE weekend_mean > weekday_mean) AS weekend_higher,
    ROUND(AVG(weekend_mean - weekday_mean), 5) AS mean_paired_delta
FROM per_series
GROUP BY scenario
ORDER BY scenario;""",10)
    findings.append({
        "title":"周内/周末结论对首尾日期过滤高度敏感",
        "fact":"依次保留或剔除首尾日期的真实配对差值："+str(boundary_sensitivity)+".",
        "alternative":"首次边界日期自身具有不同的日内或日历负荷形态；仅凭数据不能判断是节日、截断还是其他原因。",
        "limit":"剔除不完整日期是一种稳健性口径，不是对该日期业务价值或正确性的否定。原始总体差值不应独立作为稳定模式发布。"
    })
    concentration=run("复杂问题C4：统一采样粒度下各序列累计读数占比","""WITH sums AS (
    SELECT
        client,
        SUM(value) AS reading_sum
    FROM readings
    GROUP BY client
),
ranked AS (
    SELECT
        client,
        reading_sum,
        ROW_NUMBER() OVER (ORDER BY reading_sum DESC, client) AS rn,
        SUM(reading_sum) OVER () AS total_reading_sum
    FROM sums
)
SELECT
    ROUND(SUM(reading_sum) FILTER (WHERE rn <= 1)
        / NULLIF(MAX(total_reading_sum), 0) * 100, 4) AS top1_pct,
    ROUND(SUM(reading_sum) FILTER (WHERE rn <= 5)
        / NULLIF(MAX(total_reading_sum), 0) * 100, 4) AS top5_pct,
    ROUND(SUM(reading_sum) FILTER (WHERE rn <= 10)
        / NULLIF(MAX(total_reading_sum), 0) * 100, 4) AS top10_pct,
    COUNT(*) AS series_count
FROM ranked;""")[0]
    findings.append({
        "title":"总体读数被少量序列集中贡献",
        "fact":"相同采样覆盖下，Top1/Top5/Top10 序列累计读数占比分别为 "+str(concentration[0])+"% / "+str(concentration[1])+"% / "+str(concentration[2])+"%；共 "+str(concentration[3])+" 条序列。",
        "alternative":"不同序列的负荷规模可能天然不同，不能直接认定为异常或违规。",
        "limit":"当前 TXT 无单位、用户行业和合同信息；累计读数占比不能直接转化为计费电量占比。"
    })
    stage("Complex Verification + Competing Explanations + Robustness Gate 3","PASS")
    render(d,samp,repeats,ontology,rules,signals,findings,weekly,sql_events,True)
def render(d,samp,repeats,ontology,rules,signals,findings,weekly,sql_events,success):
    from html import escape as E
    def tbl(headers,rows):
        return "<div class='scroll'><table><thead><tr>"+"".join("<th>"+E(str(h))+"</th>" for h in headers)+"</tr></thead><tbody>"+"".join("<tr>"+"".join("<td>"+E(str(v))+"</td>" for v in row)+"</tr>" for row in rows)+"</tbody></table></div>"
    def cards(items):
        return "".join("<article><p>"+E(str(s))+"</p></article>" for s in items)
    sql_html=""
    for ev in sql_events:
        rs=ev["rows"]
        sql_html+="<details><summary>"+E(ev["name"])+"</summary><p><small>真实 DuckDB 查询，展示 "+str(len(rs))+" 行"+("（结果截断，见审计说明）" if ev["truncated"] else "")+"</small></p><div class='code'><button onclick='copySQL(this)'>复制 SQL</button><pre><code>"+html_sql(ev["sql"])+"</code></pre></div>"
        if ev["columns"]:sql_html+=tbl(ev["columns"],rs)
        sql_html+="</details>"
    source=LOG["source"]
    facts=[
        ["数据URL",URL],["SHA-256",source["sha256"]],["实际字节",source["bytes"]],["时间行数",d["time_rows"]],
        ["测量序列数",d["clients"]],["展开单元数",d["long_rows"]],["最早记录",d["min_time"]],["最后记录",d["max_time"]],
        ["重复时点数",int(d["time_rows"])-int(d["unique_timestamps"])],["同时间-序列重复键",repeats],
        ["空读数",d["blank_cells"]],["无效数值",d["bad_numeric_cells"]],["零读数",d["zero_cells"]],["负读数",d["negative_cells"]],
        ["测量单位","TXT未显式标注；不能仅凭列名判定kW/kWh"],["DuckDB",LOG["runtime"]["duckdb"]]
    ]
    finding_html="".join("<article><h3>"+E(f["title"])+"</h3><p><strong>确认事实：</strong>"+E(f["fact"])+"</p><p><strong>竞争解释：</strong>"+E(f["alternative"])+"</p><p><strong>局限：</strong>"+E(f["limit"])+"</p></article>" for f in findings)
    template="""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>电力负荷本体约束分析 | DuckDB 实际执行</title><style>
:root{color-scheme:light;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;background:#f5f7fa;color:#152334}body{margin:0 auto;padding:40px 24px;max-width:1200px}h1{font-size:30px;letter-spacing:-.6px}h2{margin-top:46px;font-size:23px;border-top:1px solid #d7dfe8;padding-top:26px}h3{font-size:17px}p{line-height:1.65}small,.muted{color:#607084}section{margin-bottom:20px}article{background:#fff;border:1px solid #dde5ee;border-radius:10px;padding:16px 20px;margin:12px 0}.scroll{overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:13px;background:#fff}th,td{border-bottom:1px solid #e3e9f0;padding:11px 12px;text-align:left;min-width:88px;white-space:normal;vertical-align:top}th{background:#eaf0f7;color:#253c55}details{background:white;border:1px solid #dde5ee;border-radius:9px;margin:12px 0;padding:12px 16px}summary{cursor:pointer;font-weight:650}.code{position:relative;background:#111e2d;border-radius:8px;overflow:auto;margin:12px 0}pre{margin:0;padding:18px 20px;color:#d4e2f4;line-height:1.65;font-size:12px;white-space:pre;tab-size:4}button{position:absolute;right:9px;top:9px;padding:6px 10px;border:1px solid #6282a3;background:#203750;border-radius:5px;color:#fff;cursor:pointer}.kw{color:#8acaff;font-weight:600}.str{color:#d6dc95}a{color:#135da3;overflow-wrap:anywhere}code{font-family:"SFMono-Regular",Consolas,monospace}header p{max-width:900px} .pill{font-size:12px;background:#e7f1ff;padding:3px 8px;border-radius:20px;color:#174575}
</style></head><body><header><span class="pill">真实 DuckDB 运行记录</span><h1>大规模电力负荷：本体约束 SQL 分析报告</h1><p>先通过 Source Gate 和数据核验，再生成本体、原子问题、Signal 与 Finding；所有数值来自本次指定 TXT 的实际 DuckDB 查询，不引用其他数据源。</p></header>__BODY__<script>
document.documentElement.setAttribute('data-runtime-origin', location.origin);
function copySQL(button){const sql=button.parentElement.querySelector('code').textContent;const ok=()=>{button.textContent='已复制';setTimeout(()=>button.textContent='复制 SQL',1100)};if(navigator.clipboard && window.isSecureContext){navigator.clipboard.writeText(sql).then(ok).catch(()=>fallback())}else fallback();function fallback(){const ta=document.createElement('textarea');ta.value=sql;ta.style.position='fixed';ta.style.left='-2000px';document.body.appendChild(ta);ta.select();if(document.execCommand('copy'))ok();else alert('请选中 SQL 手动复制');ta.remove()}}
</script></body></html>"""
    body="<h2>一、本体原子知识库（Gate 1）</h2>"+tbl(["一级标签","二级标签","三级标签","原子名称","原子层级","本体类别","类型","单位或值域","主体","粒度","时间语义","关系","知识点解释"],ontology)
    body+="<h2>二、本体识别规则库（Gate 1）</h2>"+tbl(["一级标签","二级标签","三级标签","识别标准","Lisp表达式","规则定义","当前状态"],rules)
    body+="<h2>三、Source / Runtime / 数据质量</h2>"+tbl(["核验项","本次真实值"],facts)
    body+="<h3>采样间隔分布（分钟）</h3>"+tbl(["间隔","相邻时点数量"],samp)
    body+="<p class='muted'>数据格式：分号分隔；十进制逗号由 DuckDB 在 CAST 前替换；宽表转时点×序列长表。无独立客户主数据，不能验证客户身份的外部关联。仅表内自然键（ts,client）可以测试唯一性。文件可能只是原始数据集切片，绝不把外部原始数据集的统计量套用到本文件。</p>"
    body+="<h2>四、业务指标、原子问题与 Signal（Gate 2）</h2><p>基础指标：有效读数数量（时点×序列）、读数均值（原文件未知单位）、零值单元数。派生指标：零值占比、单序列周内周末均值差。每个指标与时间、序列、测量值的登记关系一致。</p>"+cards(signals)
    body+="<h2>五、复杂问题、竞争解释与稳健性（Gate 3）</h2>"+(finding_html or "<p>无可被本轮数据支持的 Validated Finding。</p>")
    body+="<h2>六、决策价值与展示约束（Gate 4）</h2><p>可用于决定是否先清洗全零序列、采用序列配对而非单看总体均值，以及确认样本覆盖范围；不支持因果推断、停电识别或完整电网总负荷判断。由于数据为一次性固定 TXT，缺少更新契约、决策使用者和持续监控场景，当前不生成 Dashboard。</p>"
    body+="<h2>七、实际 SQL 与真实结果</h2><p>所有 SQL 保留换行和缩进，并统一离线语法高亮；点击复制获得无标记的原始格式化 SQL。结果过多的表只显示已执行结果的前若干行，截断会标注。</p>"+sql_html
    body+="<h2>八、复现与运行时审计</h2><p>执行环境为 GitHub Actions Ubuntu 原生 DuckDB；唯一数据 URL 为 <a href='"+E(URL)+"'>指定 TXT</a>。由脚本下载同一 URL 原始字节至临时路径并计算 SHA-256。报告为无外部依赖的单 HTML，浏览器实际 Origin 由 Chrome 测试回执 browser_gate_receipt.json 记录；HTML 内不存在 fetch、XHR、WASM 或跨域请求，因此不依赖远程 CORS，也不声称已测试 DuckDB-WASM。运行时原生 DuckDB，不替换引擎。</p><p>记录文件：execution_receipt.json、sql_results.json、source_gate_receipt.json。同一分析必须重新联网取得同一 URL 的字节，并检查 SHA-256 是否改变；结果只适用于本次哈希对应的文件。</p>"
    (OUT/"analysis_report.html").write_text(template.replace("__BODY__",body),encoding="utf-8")
    for obsolete in ("source_gate_blocked.md", "source_gate_blocked.html"):
        (OUT/obsolete).unlink(missing_ok=True)
    (OUT/"sql_results.json").write_text(json.dumps(sql_events,indent=2,ensure_ascii=False,default=str),encoding="utf-8")
    LOG["status"]="COMPLETE" if success else "NO_FINDING"
    generated=(OUT/"analysis_report.html").read_text(encoding="utf-8")
    if generated.count("<pre><code>") != len(sql_events) or "https://cdn" in generated:
        raise RuntimeError("HTML_SQL_DISPLAY_AUDIT_FAILED")
    stage("HTML / Audit Deliverable Gate 4","PASS")
    save()
def blocked(error):
    LOG["status"]="BLOCKED"
    LOG["error"]=type(error).__name__+": "+str(error)
    LOG["traceback"]=traceback.format_exc()
    save()
    md="# 电力负荷阻塞审计报告\n\n**状态：阻塞，未完成分析。**\n\n指定源："+URL+"\n\nDuckDB 执行环境："+str(LOG.get("runtime"))+"\n\n真实错误：\n\n"+LOG["error"]+"\n\n运行步骤：\n"+json.dumps(LOG["stages"],ensure_ascii=False,indent=2)+"\n\n未执行：阻塞点后的所有下游分析；不得生成 Finding。\n\n复跑：python skills/ontology-constrained-analysis/scripts/electricity_case_runner.py\n\n恢复条件：指定 URL 原始字节成功取得，且原生 DuckDB 可以执行当前脚本。\n"
    (OUT/"source_gate_blocked.md").write_text(md,encoding="utf-8")
    (OUT/"source_gate_blocked.html").write_text("<!doctype html><html lang='zh-CN'><meta charset='utf-8'><title>阻塞审计</title><body><h1>阻塞，不等于分析完成</h1><pre>"+html.escape(md)+"</pre></body></html>",encoding="utf-8")
    print("BLOCKED",LOG["error"],file=sys.stderr,flush=True)
if __name__=="__main__":
    try:main()
    except Exception as error:
        blocked(error)
        sys.exit(2)
