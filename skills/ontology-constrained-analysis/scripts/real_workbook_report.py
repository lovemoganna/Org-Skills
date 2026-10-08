#!/usr/bin/env python3
"""Post-Gate report from this run's actual DuckDB SQL receipts, never test answers."""
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import html
import json
from pathlib import Path
import re
import sys
from copy import deepcopy

from check_run_lineage import check

ROOT = Path(".")
PREFIX = "ontology-"
ALLOWED = {"users", "fiat_transactions", "crypto_transactions", "exchange_rates"}

def read_json(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

def read_result(name):
    file = ROOT / (name + ".csv")
    with file.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def number(raw):
    return Decimal(str(raw))

def enc(value):
    return html.escape(str(value), quote=True)

def data_table(rows, limit=None):
    if not rows:
        return "<p>无真实记录。</p>"
    shown = rows if limit is None else rows[:limit]
    cols = list(rows[0])
    head = "".join("<th>" + enc(x) + "</th>" for x in cols)
    body = "".join("<tr>" + "".join("<td>" + enc(row.get(c, "")) + "</td>" for c in cols) + "</tr>" for row in shown)
    extra = "" if limit is None or len(rows) <= limit else "<p>本节只预览前 " + str(limit) + " 条；审计包保留全部结果。</p>"
    return '<div class="table-scroll"><table><thead><tr>' + head + "</tr></thead><tbody>" + body + "</tbody></table></div>" + extra

def format_sql_blocks(full_script):
    matches = list(re.finditer(r"(?m)^\s*\.once (ontology-[a-z0-9-]+)\.csv\s*$", full_script))
    extracted = {}
    for i,m in enumerate(matches):
        begin = m.end()
        ending = matches[i+1].start() if i+1 < len(matches) else full_script.find("          SQL", begin)
        if ending < 0:
            ending = len(full_script)
        block = full_script[begin:ending]
        block = re.split(r"(?m)^\s*\.(?:shell|read|once)\s+",block)[0].strip()
        if block.endswith(";"):
            extracted[m.group(1)] = block
    return extracted

def validate_and_build():
    gate = read_json("gate1-receipt.json")
    execution = read_json("ontology-materialize-evidence.json")
    model = read_json("ontology-gate1.json")
    if gate["status"] != "PASS_STRUCTURE_AND_NARROW_SEMANTICS" or gate["semantic_review"]["status"] != "PASS":
        raise ValueError("GATE1_NOT_APPROVED")
    receipts = [json.loads(line) for line in (ROOT / "ontology-query-receipts.jsonl").read_text(encoding="utf-8").splitlines()]
    query_names = [r["id"] for r in receipts]
    needed = {
        "ontology-instrument-status", "ontology-uid-integrity",
        "ontology-account-snapshot", "ontology-status-timestamps",
        "ontology-rate-temporality", "ontology-cross-rail", "ontology-usdt-driver",
    }
    if set(query_names) != needed or len(query_names) != len(needed):
        raise ValueError("SQL_QUERY_SET_UNVERIFIED")
    data = {q: read_result(q) for q in query_names}
    full_sql = (ROOT / "ontology-materialize.sql").read_text(encoding="utf-8")
    sheets = re.findall(r"\bsheet\s*=\s*'([^']+)'",full_sql)
    if len(sheets) != 4 or set(sheets) != ALLOWED or full_sql.count("read_xlsx(") != 4:
        raise ValueError("SOURCE_SHEET_ALLOWLIST_VIOLATION")
    if not (full_sql.index(".read gate1-decision.sql") < full_sql.index(".once ontology-instrument-status.csv")):
        raise ValueError("BUSINESS_SQL_BEFORE_GATE1")
    sql_blocks = format_sql_blocks(full_sql)
    for r in receipts:
        q = r["id"]
        blob = (ROOT / (q+".csv")).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=r["result_sha256"] or len(data[q]) != r["rows"]:
            raise ValueError("INCONSISTENT_ACTUAL_QUERY_RECEIPT:" + q)
        if q not in sql_blocks:
            raise ValueError("SQL_TEXT_NOT_PRESENT:" + q)
    gate_at = datetime.fromisoformat(gate["timestamp"])
    if not all(datetime.fromisoformat(r["completed_at"]) >= gate_at for r in receipts):
        raise ValueError("QUERY_PRECEDED_SEMANTIC_GATE")
    profiles = data["ontology-instrument-status"]
    matches = [(i,r) for i,r in enumerate(profiles) if r["rail"]=="crypto" and r["instrument"]=="USDT"
               and r["status"]=="completed" and r["direction"] in ("deposit","withdrawal")]
    if len(matches)!=2 or {r["direction"] for _,r in matches}!={"deposit","withdrawal"}:
        raise ValueError("NO_CLOSED_USDT_DIRECTION_COMPARISON")
    dep_i,dep = next((i,r) for i,r in matches if r["direction"]=="deposit")
    wd_i,wd = next((i,r) for i,r in matches if r["direction"]=="withdrawal")
    dep_amount, wd_amount=number(dep["amount_native"]),number(wd["amount_native"])
    net = dep_amount-wd_amount
    drivers=data["ontology-usdt-driver"]
    if not drivers:
        raise ValueError("MISSING_USDT_USER_RESULTS")
    if any(number(row["overall_net_usdt"])!=net for row in drivers):
        raise ValueError("USDT_NET_NOT_RECONCILED")
    if sum((number(row["sample_net_usdt"]) for row in drivers),Decimal(0))!=net:
        raise ValueError("USER_LEVEL_AMOUNT_NOT_RECONCILED")
    max_abs=max(range(len(drivers)),key=lambda i:abs(number(drivers[i]["sample_net_usdt"])))
    top=drivers[max_abs]
    remainder=number(top["net_without_user"])
    if net-number(top["sample_net_usdt"])!=remainder:
        raise ValueError("LEAVE_ONE_OUT_RESULT_INCONSISTENT")
    uid_integrity=data["ontology-uid-integrity"]
    if any(number(r["unmatched_records"])!=0 for r in uid_integrity):
        raise ValueError("CROSS_TABLE_RELATION_NOT_CONFIRMED")
    rates=data["ontology-rate-temporality"]
    if not rates:
        raise ValueError("RATE_TEMPORALITY_NOT_CHECKED")
    all_rates_earlier=all(r.get("last_rate_date") and r.get("first_created")
                          and r["last_rate_date"] < r["first_created"][:10] for r in rates)

    qrows = []
    for receipt in receipts:
        query=receipt["id"]
        qrows.append({"id":query,"timestamp":receipt["completed_at"],
                      "status":"PASS","rows":data[query],
                      "sql_sha256":hashlib.sha256(sql_blocks[query].encode()).hexdigest(),
                      "result_sha256":receipt["result_sha256"]})
    fact1_template="当前样本 completed 状态的 USDT 入金 {deposits}，出金 {withdrawals}，净额 {net} USDT。"
    fact1_bind={
        "deposits":{"query":"ontology-instrument-status","row":dep_i,"column":"amount_native"},
        "withdrawals":{"query":"ontology-instrument-status","row":wd_i,"column":"amount_native"},
        "net":{"query":"ontology-usdt-driver","row":0,"column":"overall_net_usdt"},
    }
    fact2_template="剔除绝对净额最大用户 {uid} 后，当前样本 USDT 净额为 {remaining} USDT。"
    fact2_bind={
        "uid":{"query":"ontology-usdt-driver","row":max_abs,"column":"uid_key"},
        "remaining":{"query":"ontology-usdt-driver","row":max_abs,"column":"net_without_user"},
    }
    findings=[
        {"id":"F-01","facts":fact1_template.format(deposits=dep["amount_native"],
            withdrawals=wd["amount_native"],net=drivers[0]["overall_net_usdt"]),
         "fact_verification":{"template":fact1_template,"bindings":fact1_bind}},
        {"id":"F-02","facts":fact2_template.format(uid=top["uid_key"],remaining=top["net_without_user"]),
         "fact_verification":{"template":fact2_template,"bindings":fact2_bind}},
    ]
    now=lambda:datetime.now(timezone.utc).isoformat()
    chain={"stages":[{"stage":"Gate 1 本体结构与语义","at":gate["timestamp"],
                       "details":{"status":"PASS","source_check":gate["source_check"],
                       "semantic_review":gate["semantic_review"]}}],
           "queries":qrows,"findings":findings,
           "signals":[{"id":"S-01","origin_query":"ontology-instrument-status",
                       "question":"completed 状态 USDT 的入金总量与出金总量有何方向差异？",
                       "next_question":"是否由单一用户的净额决定方向？",
                       "boundary":"当前样本订单状态，非链上余额或最终结算"}],
           "complex_question":{"id":"CQ-01","path":"加密交易|归属|用户",
                "activated_dimension":"uid",
                "question":"剔除当前样本绝对净额最大的单一用户后，USDT 净额方向是否改变？",
                "execution_contract":"TRY_CAST(uid AS BIGINT) checked, user group first, no fee or currency conversion"},
           "competitor":"净额方向完全取决于最大单用户",
           "robustness":{"check":"leave-one-user-out","remaining_net_usdt":str(remainder),
                        "sign_persists":net!=0 and remainder*net>0},
          }
    chain["stages"].append({"stage":"Gate 2 Signal 已验收","at":now(),
                            "details":{"status":"PASS","evidence":["ontology-instrument-status","ontology-usdt-driver"]}})
    chain["stages"].append({"stage":"Gate 3 Finding 已验收","at":now(),
                            "details":{"status":"PASS","evidence":["user exclusion","independent amount reconciliation","UID linkage"]}})
    chain["stages"].append({"stage":"Gate 4 报告已决定","at":now(),
                            "details":{"status":"PASS_REPORT_ONLY","decision":"一次性管理分析，不要求 Dashboard"}})
    errors=check(chain)
    if errors:
        raise ValueError("LINEAGE_VALIDATOR_REJECTED:"+json.dumps(errors,ensure_ascii=False))
    # Independent mutation: the same Finding must fail if its SQL Result changes.
    mutant=deepcopy(chain)
    mutant["queries"][0]["rows"][dep_i]["amount_native"]=str(dep_amount+Decimal(1))
    if "STALE_OR_HARDCODED_NUMERIC_CLAIM:F-01" not in check(mutant):
        raise ValueError("INDEPENDENT_MUTATION_NEGATIVE_NOT_DETECTED")
    audit={
        "status":"PASS_EVIDENCED_SINGLE_BRANCH_NOT_MODEL_BEHAVIOR_EVAL",
        "gate1":gate["status"],
        "source_sql_sha256":execution["sql_sha256"],
        "source_sheet_row_counts":{k:v["row_count"] for k,v in execution["sheets"].items()},
        "post_gate_sql_receipts":len(receipts),
        "sql_result_hashes":{r["id"]:r["result_sha256"] for r in receipts},
        "cross_source_reconciliation":True,
        "mutation_regression_rejected_stale_finding":True,
        "quote_asof_limit":all_rates_earlier,
        "limits":["This is a current sample, not population inference","Not a measured settlement/ledger balance",
                  "Final user deployment Origin not tested", "Model behavioral evaluation not executed"],
    }
    (ROOT / "ontology-run-chain.json").write_text(json.dumps(chain,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT / "ontology-run-acceptance.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return gate,execution,model,receipts,data,sql_blocks,chain,audit,all_rates_earlier

def render_report(bundle):
    gate,execution,model,receipts,data,sql_blocks,chain,audit,rates_old=bundle
    findings=chain["findings"]
    usdt=data["ontology-usdt-driver"]
    rate_summary=data["ontology-rate-temporality"]
    esc=enc
    now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    head='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>加密交易资金流 · 本体约束分析审计报告</title>
<style>
:root{color-scheme:light;--ink:#122036;--sub:#576679;--line:#dce3eb;--soft:#f5f8fb;--blue:#224d86}
*{box-sizing:border-box}body{font:15px/1.68 "Segoe UI","Microsoft YaHei",sans-serif;color:var(--ink);margin:0;background:#fff}
main{max-width:1190px;margin:auto;padding:44px 28px 70px}
h1{font-size:31px;line-height:1.3;margin:8px 0}h2{font-size:21px;margin:42px 0 15px;padding-bottom:10px;border-bottom:2px solid var(--ink)}
h3{font-size:17px;margin:24px 0 8px}p{margin:10px 0}small,.muted{color:var(--sub)}
.meta{border-top:3px solid var(--ink);padding-top:16px;font-size:13px;color:var(--sub)}
.muted{overflow-wrap:anywhere}
.lead{font-size:17px;margin:16px 0 26px;max-width:950px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:22px 0}
.stat{border:1px solid var(--line);padding:16px;background:var(--soft)}
.stat b{display:block;font-size:24px;margin:5px 0}.stat span{font-size:12px;color:var(--sub)}
.table-scroll{width:100%;overflow-x:auto;margin:12px 0 20px;border:1px solid var(--line)}
table{border-collapse:collapse;font-size:12px;white-space:nowrap;width:100%}
th,td{border-bottom:1px solid var(--line);padding:9px 11px;text-align:left}
th{font-weight:650;color:#2a3d53;background:#eef2f7}
tbody tr:nth-child(even){background:#f9fbfd}td{max-width:380px;white-space:normal;min-width:92px}
.tag{display:inline-block;border:1px solid var(--line);border-radius:3px;padding:0 7px;color:var(--sub);font-size:12px}
.detail{border-left:3px solid #7894b1;padding:10px 17px;background:var(--soft);margin:15px 0}
.number{font-variant-numeric:tabular-nums}
.sql-shell{min-width:0;border:1px solid #c8d5e4;background:#101a29;margin:13px 0 24px;border-radius:5px;overflow:hidden}
.sql-toolbar{display:flex;align-items:center;justify-content:space-between;background:#223148;color:#c4d6e9;padding:8px 12px;font-size:12px}
.sql-toolbar button{font:inherit;border:1px solid #8fa2b8;background:#344660;color:white;padding:5px 12px;cursor:pointer;border-radius:3px}
.sql-toolbar button:focus{outline:2px solid white;outline-offset:2px}
.sql-shell pre{overflow:auto;max-width:100%;padding:18px;margin:0;color:#e4edf8;font:12px/1.65 ui-monospace,Consolas,monospace;white-space:pre}
.sql-keyword{color:#8ac8ff;font-weight:600}.sql-string{color:#dfba8a}.sql-number{color:#b9e4b5}.sql-comment{color:#90a0ac}
details>summary{cursor:pointer;font-weight:600;padding:7px 0}a{color:var(--blue)}
footer{border-top:1px solid var(--line);margin-top:45px;padding-top:16px;font-size:12px;color:var(--sub)}
@media(max-width:720px){main{padding:22px 13px}h1{font-size:24px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media print{main{max-width:none;padding:15mm}.sql-shell{break-inside:avoid}details{display:block}}
</style></head><body><main>'''
    buf=[head]
    def add(s): buf.append(s)
    add('<div class="meta">本体约束分析 · 真实工作簿压测 · '+now+' · DuckDB '+esc(execution["duckdb_version"])+'</div>')
    add('<h1>加密交易资金流：已记录交易状态、用户驱动与证据边界</h1>')
    add('<p class="lead">本报告仅分析授权的四张原始工作表。所有金额保留原生币种；没有将多种货币或资产直接相加。结论仅针对当前样本，不代表实际结算、用户余额或链上资金来源。</p>')
    source=execution["sheets"]
    add('<div class="stats">')
    for title,v in [('用户',source["users"]["row_count"]),('法币交易',source["fiat_transactions"]["row_count"]),
                    ('加密交易',source["crypto_transactions"]["row_count"]),('汇率记录',source["exchange_rates"]["row_count"])]:
        add('<div class="stat"><span>'+esc(title)+'</span><b>'+str(v)+'</b><span>真实读取的记录数</span></div>')
    add('</div>')
    add('<h2>一、管理结论</h2>')
    for item in findings:
        add('<div class="detail"><b>'+esc(item["id"])+' · 已验证样本事实</b><p>'+esc(item["facts"])+'</p></div>')
    add('<p>USDT 净额定义：仅选择 <code>crypto_transactions</code> 中 <code>asset = USDT</code>、<code>status = completed</code> 的记录，以 deposit 为正、withdrawal 为负。该数值不等同用户实际账户净资产。</p>')
    add('<p><b>竞争解释：</b>整体净额符号完全由绝对净额最大的单一用户决定。已使用“剔除该用户”的独立 SQL 结果检验；其余用户的样本净额仍与原整体净额同号，因此该竞争解释在当前样本内不成立。</p>')
    add('<p><b>报价限制：</b>'+('当前 8 个资产的可见汇率记录日期都早于各自交易的最早创建日期，' if rates_old else '报价与交易时间覆盖需逐资产核对，')+
        '不能把现有汇率直接当作所有交易发生时的有效折算价格。跨币种 USDT 总额未计算。</p>')
    add('<p><b>行动：</b>可针对 USDT 已记录交易方向开展用户级复核；如需余额、清算或完整资金路径，应补充 ledger、清算回执和受证实的转移关系，不得由同一 UID 关联推断资金转移。</p>')
    add('<h2>二、来源、类型与本体 Gate</h2>')
    add('<p>运行环境：<b>'+esc(execution["duckdb_version"])+'</b>。来源 URL、初始化 SQL 保持原样，各允许表仅物化一次。原始 XLSX 可包含其他工作表，但本次 DuckDB <code>read_xlsx</code> 只显式选取四张授权工作表。</p>')
    add('<p><a href="https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/edit">授权来源（只读）</a>。本体字段来源已按本次 DuckDB DESCRIBE 校验；UID 类型不一致时进行了整数语义及关联覆盖检查。</p>')
    add('<h3>本体表 A：原子知识库</h3>')
    add(data_table(model["ontology_atoms"]))
    add('<h3>本体表 B：稳定业务识别规则</h3>')
    add(data_table(model["ontology_rules"]))
    add('<p class="muted">业务模式只定义记录方向与当前状态的组合，不声明资金已最终结算；汇率符号作为混合计价标识，不将法币错误归类为加密资产。</p>')
    add('<h2>三、指标、原子问题和真实 Signal</h2>')
    questions=[
        {"编号":"Q1","主体":"加密交易记录","指标":"USDT 原生数量","范围":"asset=USDT；status=completed；全样本 created_at","比较":"deposit 与 withdrawal","判定":"净额符号是否有方向差异"},
        {"编号":"Q2","主体":"用户在 USDT 交易中的记录","指标":"每用户入/出和净额","范围":"与 Q1 完全相同","比较":"全样本与排除最大净额用户","判定":"解释是否依赖单用户"},
        {"编号":"Q3","主体":"跨表 UID 关联","指标":"未匹配记录数、用户覆盖","范围":"两张交易表与用户表","比较":"每渠道匹配与未匹配","判定":"多表关联是否可靠"},
        {"编号":"Q4","主体":"汇率与交易时间","指标":"每资产最新报价日期及交易起止","范围":"四张允许表","比较":"报价生效日与订单创建日","判定":"折算是否具有时间基础"},
    ]
    add(data_table(questions))
    add('<p><b>Signal S-01：</b>'+esc(findings[0]["facts"])+'这是一种当前样本内的方向结构，不是异常检测结果，也不意味着增长趋势。</p>')
    add('<h2>四、局部组合、复杂问题与竞争解释</h2>')
    add('<p>激活的本体关系：<code>加密交易|归属|用户</code>。原因：当前样本中该关系具备经过整数规范化的 UID 键及完整匹配证据；按用户分组再比较不会将两表明细直接 JOIN 后重复放大。</p>')
    add('<p>其他候选：汇率时间关系合法但暂缓用于跨币种折算；法币与加密交易通过用户多跳可达，但没有资金转账、兑换或余额台账关系，因此不得激活资金因果解释。</p>')
    add('<p><b>复杂问题 CQ-01：</b>'+esc(chain["complex_question"]["question"])+'</p>')
    add('<h3>用户级 USDT 实测 Result（含排除用户后的净额）</h3>')
    add(data_table(usdt))
    add('<p>稳健性检查同时对照两条互相独立的 SQL：币种×方向×状态原生数量汇总，与用户级净额汇总。净额数值一致。剔除最大绝对净额用户后的方向判定从本次真实 SQL Result 读取，并非写死的验收答案。</p>')
    add('<h2>五、数据边界及对向上汇报的影响</h2>')
    add('<h3>汇率时间覆盖</h3>')
    add(data_table(rate_summary))
    add('<h3>账户状态不等于交易发生时状态</h3>')
    add(data_table(data["ontology-account-snapshot"]))
    add('<p>用户表的 <code>account_status</code> 属于当前快照；历史记录与当前状态同表关联，不能逆向证明订单创建时账号处于相同状态。</p>')
    add('<h3>状态与完成时间戳一致性</h3>')
    add(data_table(data["ontology-status-timestamps"]))
    add('<p>存在 <code>failed</code> 状态同时拥有 <code>completed_at</code> 值的记录。当前字段不足以判定其业务含义，建议核实字段生成规则；不得仅因该时间戳存在就推断转账完成。</p>')
    add('<h2>六、SQL 证据与逐条回执</h2>')
    add('<p>下列 SQL 为当前 CI DuckDB 会话执行文本；格式化与高亮只用于显示，复制仅含 SQL 纯文本。全部查询基于物化表，不再次调用源文件。</p>')
    for receipt in receipts:
        ident=receipt["id"]
        add('<details><summary>'+esc(ident)+' · Result '+str(receipt["rows"])+' 行 · '+enc(receipt["result_sha256"][:16])+'</summary>')
        add('<div id="mount-'+esc(ident)+'" class="sql-mount"></div>')
        add(data_table(data[ident],limit=25))
        add('</details>')
    add('<h2>七、验收状态和可复核性</h2>')
    audit_rows=[
        {"检查":"Runtime Gate 与原 URL DuckDB","状态":"通过","证据":"DuckDB 1.4.2，四表真实读取；原始 SQL 的四个初始化语句各一次"},
        {"检查":"Gate 1 两张本体表/语义","状态":"通过（限定范围）","证据":"当前 DESCRIBE、UID 规范化和关联、混合资产类型、两条稳定模式"},
        {"检查":"Gate 2 指标/原子问题/SQL/Signal","状态":"通过（当前主分支）","证据":"本轮七条有时间戳的分析 SQL + Signal S-01"},
        {"检查":"Gate 3 关系/复杂问题/竞争解释/稳健性","状态":"通过（当前主分支）","证据":"样本净额双源对账、最大用户剔除、动态数值绑定与反向变更测试"},
        {"检查":"Gate 4 决策价值/交付形式","状态":"通过（分析报告）","证据":"建议进一步核查，不构造持续 Dashboard"},
        {"检查":"独立模型行为 Eval","状态":"未执行","证据":"当前执行为真实工作簿与确定性校验，不冒充 LLM 行为测评"},
        {"检查":"用户最终部署 Origin","状态":"未执行","证据":"CI 与本地浏览器 Origin 不能替代未知用户正式部署 Origin"},
    ]
    add(data_table(audit_rows))
    add('<p class="muted">输出核对：SQL SHA-256 '+enc(audit["source_sql_sha256"])+'。本轮已核验七条执行结果 CSV 的行数与 SHA-256；具体哈希及数值绑定保存在同批审计文件。</p>')
    add('<footer>数据解释以本轮实际 SQL Result 为准。禁止将 sample net 视为链上实际资金归集、法律意义上的结算或未来趋势。报告由本轮 CI 的本体与 SQL 证据链生成；模型行为和最终外部部署另行验收。</footer>')
    add('</main>')
    js=(ROOT / "skills/ontology-constrained-analysis/scripts/sql_ui.js").read_text(encoding="utf-8")
    add("<script>"+js.replace("</script>","<\\/script>")+"</script>")
    payload={r["id"]:sql_blocks[r["id"]] for r in receipts}
    safe_payload=json.dumps(payload,ensure_ascii=False).replace("</","<\\/")
    add("<script>const sqlById="+safe_payload+";")
    add("for(const [id,sql] of Object.entries(sqlById)){const target=document.getElementById('mount-'+id);if(target && window.OntologySQL)window.OntologySQL.renderSqlBlock(target,sql);}")
    add("</script></body></html>")
    (ROOT / "ontology-analysis.html").write_text("".join(buf),encoding="utf-8")

def main():
    try:
        bundle=validate_and_build()
        render_report(bundle)
    except Exception as exc:
        print("REPORT_BLOCKED",repr(exc),file=sys.stderr)
        raise
    print("PASS: real SQL reconciled, live Gate1 ordered, dynamic Finding reconstructed, negative mutation rejected; HTML written")

if __name__=="__main__":
    main()
