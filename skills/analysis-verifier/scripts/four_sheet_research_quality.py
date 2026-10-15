#!/usr/bin/env python3
"""Independent source-result reconciliation and content-value gate.

The report is organized by evidence-backed findings, not stages or QA logs.
A sparse/uninteresting dataset produces a research receipt, not a fake feature.
"""
from collections import Counter
from pathlib import Path
import json,sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "discovery")
def load(n): return json.loads((root/(n+".json")).read_text(encoding="utf-8"))
def uid(v):return str(int(float(v)))
f=load("fiat_details");c=load("crypto_details");allrows=f+c
assert f and c
assert len(allrows)==sum(int(x["n"]) for x in load("keys_quality"))
plan=load("research-plan")
subject=load("stage2_subject_events")
group=load("stage2_completion_invariant")
mismatch=load("stage2_completed_at_mismatch")
returns=load("stage2_completed_pair_peer_baseline")
near=load("stage2_crossrail_completion_order")
# Reconcile every second-pass aggregation with independent first-pass row details.
expected=Counter();stamp=Counter()
for x in allrows:
    rail="fiat" if x["order_id"].startswith("fo_") else "crypto"
    key=(rail,x["asset"],x["direction"],x["status"])
    expected[key]+=1
    if x["completed_at"]:stamp[key]+=1
for x in group:
    key=(x["rail"],x["asset"],x["direction"],x["status"])
    assert x["records"]==expected[key] and x["with_completed_at"]==stamp[key]
assert sum(x["records"] for x in group)==len(allrows)
wrong={x["order_id"] for x in allrows if x["status"]!="completed" and x["completed_at"]}
assert {x["order_id"] for x in mismatch}==wrong
assert len(returns)==len(load("fiat_roundtrip_7d"))
assert len(near)==len(load("crossrail_status_and_time"))
uid_set={x["uid"] for x in plan["investigate"]}
assert len(subject)==sum(uid(x["uid"]) in uid_set for x in allrows)
done=sum(x["status"]=="completed" for x in allrows)
with_time=sum(bool(x["completed_at"]) for x in allrows)
completed_missing_time=sum(x["status"]=="completed" and not x["completed_at"] for x in allrows)
assert with_time==done-completed_missing_time+len(wrong)
inverse=[x for x in near if x["created_gap_crypto_minus_fiat"] *
                              x["completed_gap_crypto_minus_fiat"]<0]
signals=sum(bool(x) for x in [wrong,returns,inverse])
is_report=signals>=2
v={"source":"Authorized four-sheet remote XLSX / Native DuckDB 1.4.2",
   "read_xlsx_calls":4,"additional_source_reads":0,
   "source_records":len(allrows),
   "completed_by_status":done,
   "non_null_completion_timestamp":with_time,
   "noncompleted_with_timestamp":len(wrong),
   "completed_missing_timestamp":completed_missing_time,
   "completed_crossrail_near_pairs":len(near),
   "creation_completion_order_inversions":len(inverse),
   "same_fiat_asset_return_pairs":len(returns),
   "blocked_questions":len(plan["blocked"]),
   "independent_evidence_clusters":signals,
   "reader_value_gate":"SCOPED_REPORT_READY" if is_report else "RESEARCH_NOTE_ONLY",
   "claim_boundary":"No causal fund tracing, fraud or historical freeze proof"}
(root/"research-verdict.json").write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")
names={p["uid"]:p["user_name"] for p in load("joined_users")}
lines=["# 四表业务研究：记录中真正能验证什么",
       "",
       f"本轮用 DuckDB 在一个会话中读取四表，得到 {len(allrows)} 条交易。第二轮的对象和 SQL 由第一轮实际结果选择，没有预先指定用户。",
       ""]
if wrong:
    t=mismatch[0]
    lines.extend([
       "## 成功状态和完成时间不是同一回事",
       "",
       f"按业务状态完成的是 {done} 笔，而完成时间非空有 {with_time} 笔。两种口径相差 {with_time-done} 笔，其中非成功状态却填写完成时间的有 {len(wrong)} 笔。",
       f"实例：{names.get(uid(t['uid']),'用户')} 的 {t['amount']} {t['asset']} 提现，订单 {t['order_id']}，状态为 {t['status']}，却填有完成时间 {t['completed_at']}。",
       "错误的 SQL 若仅用 completed_at 非空判断成功，会把这类记录当作完成的提现。正确动作是核对现有监控、报表与案件筛选中的状态定义；不是据此判用户异常。",
       ""])
if inverse:
    t=inverse[0]
    lines.extend([
       "## 跨渠道订单相邻，不代表完成顺序相同",
       "",
       f"在 {len(near)} 组已完成状态、同 UID、创建时间相隔 24 小时内的法币与 Crypto 配对中，有 {len(inverse)} 组创建和完成顺序相反。",
       f"UID {t['uid']}：法币订单 {t['fiat_id']} 创建于 {t['fiat_created']}、完成于 {t['fiat_completed']}；Crypto 订单 {t['crypto_id']} 创建于 {t['crypto_created']}、完成于 {t['crypto_completed']}。",
       "因此不能仅凭时间接近解释为兑换或资金路径。还需订单关联标识、支付/结算流水或链上入账的外部证据。",
       ""])
if returns:
    t=returns[0]
    lines.extend([
       "## 同资产短期入出仅证明发生过两种交易行为",
       "",
       f"已完成状态的同 UID、同币种法币入金后 24 小时内出金，共匹配 {len(returns)} 组。",
       f"例如 UID {t['uid']}，{t['currency']} 入金订单 {t['deposit_order']} 与出金订单 {t['withdrawal_order']}，创建相隔 {t['create_gap']} 分钟。",
       "短期往返是值得复核的行为模式，但没有付款账户、具体余额和资金来源证据时，不等于资金原路返回或存在违规目的。",
       ""])
if plan["blocked"]:
    lines.extend([
       "## 已停止一条无法证明的推断",
       "",
       "用户表的 frozen 是状态快照，不是冻结生效历史。现有四表无法判断冻结前后提现的控制执行是否有效，该问题需要账户状态日志才可继续。",
       ""])
if not is_report:
    lines.extend(["## 本轮验收","",
        "实际数据不足以产生两项相互独立且有业务意义的发现。本轮交付为调查记录，不应包装成专业深度文章。",
        ""])
lines.extend(["## 使用限制","",
              "这是一份教学用小样本的可复核调查，不是平台总体风险估计、个人违法认定、STR 或制裁筛查结论。",
              "证据链：原始读取 SQL、第二轮 SQL、case selection、两轮结果及 research-verdict.json。"])
(root/"research-note.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(v,ensure_ascii=False))
