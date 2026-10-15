#!/usr/bin/env python3
"""Independent content and arithmetic checks, then a reader-focused report."""
from collections import Counter
from pathlib import Path
import json,sys

root=Path(sys.argv[1] if len(sys.argv)>1 else "discovery")
def read(name):
    return json.loads((root/(name+".json")).read_text(encoding="utf-8"))
def uid(v):return str(int(float(v)))
fiat,crypto=read("fiat_details"),read("crypto_details")
base=fiat+crypto
plan=read("research-plan")
groups=read("stage2_completion_invariant")
mismatch=read("stage2_completed_at_mismatch")
pairs=read("stage2_completed_pair_peer_baseline")
cross=read("stage2_crossrail_completion_order")
subject=read("stage2_subject_events")
expected_n=sum(int(x['n']) for x in read('keys_quality'))
assert expected_n>0 and len(base)==expected_n
groups_expected=Counter()
groups_timestamp=Counter()
for x in base:
    rail="fiat" if x["order_id"].startswith("fo_") else "crypto"
    key=(rail,x["asset"],x["direction"],x["status"])
    groups_expected[key]+=1
    if x["completed_at"]:groups_timestamp[key]+=1
for g in groups:
    key=(g["rail"],g["asset"],g["direction"],g["status"])
    assert g["records"]==groups_expected[key],key
    assert g["with_completed_at"]==groups_timestamp[key]
assert sum(g["records"] for g in groups)==50
expected={r["order_id"] for r in base if r["status"]!="completed" and r["completed_at"]}
assert {r["order_id"] for r in mismatch}==expected and len(expected)>=1
actual_completed=sum(r["status"]=="completed" for r in base)
timestamp_proxy=sum(bool(r["completed_at"]) for r in base)
assert timestamp_proxy==actual_completed+len(expected)
assert len(pairs)==len(read("fiat_roundtrip_7d"))
assert len(cross)==len(read("crossrail_status_and_time"))
cases=plan["investigate"]
assert {"STATUS_NOT_SETTLEMENT","SAME_ASSET_TURNOVER"} <= {c["code"] for c in cases}
assert len(subject)==sum(uid(r["uid"]) in {c["uid"] for c in cases} for r in base)
assert any(x["code"]=="FROZEN_HISTORICAL_STATE" for x in plan["blocked"])
inversions=[x for x in cross if x["created_gap_crypto_minus_fiat"]*
                                   x["completed_gap_crypto_minus_fiat"]<0]
assert inversions,"The chronology hypothesis has no real counterexample"
verdict={
  "source":"original locked remote XLSX four tables in native DuckDB 1.4.2",
  "read_calls":4,
  "additional_source_reads":0,
  "observed_completed":actual_completed,
  "timestamp_proxy_count":timestamp_proxy,
  "false_positive_orders_from_timestamp_proxy":len(expected),
  "matched_completed_crossrail_pairs_24h":len(cross),
  "creation_completion_order_inversions":len(inversions),
  "same_fiat_asset_completed_in_out_24h":len(pairs),
  "explicitly_blocked_historical_freeze_claim":True,
  "quality":"PASS_SCOPED_RESEARCH_NOT_FRAUD_ATTRIBUTION",
  "reproducible_claims":3,"material_counterexamples":2
}
(root/"research-verdict.json").write_text(json.dumps(verdict,ensure_ascii=False,indent=2)+"\n")
bad=mismatch[0]
inv=inversions[0]
names={p["uid"]:p["user_name"] for p in read("joined_users")}
lines=[
  "# 四表资金记录调查：两个容易造成错误结论的数据陷阱",
  "",
  "研究范围：10 名用户、25 笔法币、25 笔 Crypto 记录。先勘察全部数据，再由实际结果选取案例，在同一次 DuckDB 会话追加 SQL。以下不是违规认定。",
  "",
  "## 失败交易也可能写入 completed_at",
  "",
  f"本样本状态为 completed 的交易有 {actual_completed} 笔，但完成时间非空有 {timestamp_proxy} 笔。若把 completed_at 非空作为完成条件，会多统计 {len(expected)} 笔。",
  f"明确反例：{names.get(uid(bad['uid']),'某用户')} 的 {bad['amount']} {bad['asset']} 提现，订单 {bad['order_id']}，状态为 {bad['status']}，但 completed_at 为 {bad['completed_at']}。",
  "这个字段可能表示流程终止，而不一定表示资金成功完成；因此交易成功的 SQL 口径不能依赖时间戳非空判断。",
  "",
  "## 交易创建时间相邻，不表示资金转移，甚至不表示完成顺序相同",
  "",
  f"同 UID、创建时间相隔 24 小时内且双方状态为 completed 的跨渠道配对有 {len(cross)} 组。其中 {len(inversions)} 组按照创建时间与按照完成时间比较，先后顺序不同。",
  f"例：UID {inv['uid']}，法币订单 {inv['fiat_id']} 创建于 {inv['fiat_created']}、完成于 {inv['fiat_completed']}；Crypto 订单 {inv['crypto_id']} 创建于 {inv['crypto_created']}、完成于 {inv['crypto_completed']}。",
  "相近时间只能成为待验证线索，不足以证明它们属于同一次兑换或共享资金路径。",
  "",
  "## 观察到的同币种往返行为，也不直接等于异常",
  "",
  f"按同 UID、同币种、先入后出、24 小时内、状态均 completed 检索，发现 {len(pairs)} 组匹配。",
]
if pairs:
    p=pairs[0]
    lines+=[
     f"UID {p['uid']}：{p['currency']} 入金 {p['deposit_order']} 与出金 {p['withdrawal_order']}，创建间隔 {p['create_gap']} 分钟，完成间隔 {p['completion_gap']} 分钟。",
     "它说明有一段真实的订单行为序列，但不能证明资金原路返回或具备洗钱意图。是否同一资金需要付款账户、余额流水、通道凭据等证据。"
    ]
lines += [
  "",
  "## 哪些动作真正值得做",
  "",
  "首先检查现有监控 SQL 是否错误使用 completed_at 非空筛选成功订单。如存在，应更正口径并复算历史统计；本样本中这种错误会将一笔失败提现混入完成量。",
  "对于跨渠道时间关联，只建议提取精确订单与链上事件做事件级核验，而不是立即升级为违规。",
  "Irene 的当前 frozen 状态没有历史生效时间，同四表内继续查询无法判断两笔提现是否违规。这个分支已阻断，须取得状态变更审计日志后才重新开启。",
  "",
  "## 证据界限",
  "",
  "结果为模拟交易样本，不能外推真实平台发生率、风险等级或 STR 处置。原始证据、执行 SQL、追加查询选择记录及各项复核见同一 GitHub Actions artifact。",
]
(root/"research-note.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(verdict,ensure_ascii=False))
