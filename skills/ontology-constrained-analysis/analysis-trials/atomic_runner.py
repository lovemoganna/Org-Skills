"""Post-Gate atomic SQL: four independent questions, one source snapshot, no source reload."""
import concurrent.futures,csv,datetime,hashlib,json,pathlib,threading
import duckdb
OUT=pathlib.Path("atomic");OUT.mkdir(exist_ok=True)
BASE=pathlib.Path("evidence");DB=BASE/"snapshot.duckdb"
R=json.loads((BASE/"source-receipt.json").read_text())
assert R["status"]=="SOURCE_ONLY_PASS_NOT_GATE1"
assert set(R["tables"])=={"users","fiat_transactions","crypto_transactions","exchange_rates"}
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
assert sha(DB)==R["snapshot_sha256"]
QUESTIONS={
"Q01-USDT-direction":"""SELECT direction,COUNT(*) AS records,SUM(amount) AS amount_usdt
FROM crypto_transactions
WHERE asset='USDT' AND status='completed'
  AND direction IN ('deposit','withdrawal')
GROUP BY direction ORDER BY direction""",
"Q02-status-clock":"""WITH all_rails AS (
 SELECT 'fiat' AS rail,status,completed_at FROM fiat_transactions
 UNION ALL SELECT 'crypto' AS rail,status,completed_at FROM crypto_transactions
)
SELECT rail,status,COUNT(*) AS records,
 SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS has_completed_at
FROM all_rails GROUP BY rail,status ORDER BY rail,status""",
"Q03-rate-coverage":"""WITH tx AS (
 SELECT currency AS asset,CAST(created_at AS DATE) AS recorded_day FROM fiat_transactions
 UNION ALL SELECT asset,CAST(created_at AS DATE) FROM crypto_transactions
), tx_dates AS (
 SELECT asset,COUNT(*) AS tx_records,MIN(recorded_day) AS first_tx_day,
  MAX(recorded_day) AS last_tx_day FROM tx GROUP BY asset
)
SELECT t.*,COUNT(r.asset) AS rate_observations,
 MIN(r.effective_date) AS earliest_rate_day,
 MAX(r.effective_date) AS latest_rate_day,
 SUM(CASE WHEN r.effective_date BETWEEN t.first_tx_day AND t.last_tx_day THEN 1 ELSE 0 END) AS rates_within_tx_period
FROM tx_dates t LEFT JOIN exchange_rates r ON t.asset=r.asset
GROUP BY ALL ORDER BY t.asset""",
"Q04-cross-rail":"""WITH f AS (
 SELECT TRY_CAST(uid AS BIGINT) AS uid_key,COUNT(*) AS fiat_orders
 FROM fiat_transactions GROUP BY 1
),c AS (
 SELECT TRY_CAST(uid AS BIGINT) AS uid_key,COUNT(*) AS crypto_orders
 FROM crypto_transactions GROUP BY 1
)
SELECT TRY_CAST(u.uid AS BIGINT) AS uid_key,u.account_status,
 COALESCE(f.fiat_orders,0) AS fiat_orders,COALESCE(c.crypto_orders,0) AS crypto_orders
FROM users u LEFT JOIN f ON TRY_CAST(u.uid AS BIGINT)=f.uid_key
 LEFT JOIN c ON TRY_CAST(u.uid AS BIGINT)=c.uid_key
ORDER BY uid_key"""
}
barrier=threading.Barrier(len(QUESTIONS))
def worker(item):
 id,sql=item;conn=duckdb.connect(str(DB),read_only=True)
 barrier.wait(timeout=20);start=datetime.datetime.now(datetime.timezone.utc)
 try:
  c=conn.execute(sql);heads=[d[0] for d in c.description];rows=c.fetchall()
  path=OUT/(id+".csv")
  with path.open("w",newline="",encoding="utf-8") as f:
   w=csv.writer(f);w.writerow(heads);w.writerows(rows)
  end=datetime.datetime.now(datetime.timezone.utc)
  receipt={"question_id":id,"worker_id":threading.current_thread().name,
  "started_at":start.isoformat(),"ended_at":end.isoformat(),
  "snapshot_sha256":R["snapshot_sha256"],"sql":sql,
  "sql_sha256":hashlib.sha256(sql.encode()).hexdigest(),
  "result_path":path.as_posix(),"result_sha256":sha(path),
  "row_count":len(rows),"state":"REAL_SQL_RESULT_NOT_SIGNAL"}
  (OUT/(id+".json")).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
  return receipt
 finally:conn.close()
with concurrent.futures.ThreadPoolExecutor(max_workers=len(QUESTIONS),thread_name_prefix="atomic") as pool:
 results=list(pool.map(worker,QUESTIONS.items()))
assert len({r["worker_id"] for r in results})==len(QUESTIONS)
assert all(r["snapshot_sha256"]==R["snapshot_sha256"] for r in results)
assert any(a["started_at"]<b["ended_at"] and b["started_at"]<a["ended_at"] for i,a in enumerate(results) for b in results[i+1:])
(OUT/"atomic-manifest.json").write_text(json.dumps({"status":"EXECUTED_NOT_INTERPRETED",
"source_run_id":37793839441,"snapshot_sha256":R["snapshot_sha256"],"tasks":results},
ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"status":"PARALLEL_QUERIES_DONE","rows":{r["question_id"]:r["row_count"] for r in results}}))

# Trigger independent branch workflow after definition registration.

# Dependent Gate 3. Atomic results above must exist and their SQL has actually executed.
import math
q01=list(csv.DictReader((OUT/"Q01-USDT-direction.csv").open()))
values={r["direction"]:float(r["amount_usdt"]) for r in q01}
net=values.get("deposit",0)-values.get("withdrawal",0)
complex_status={"status":"STOPPED_NO_SIGNAL","reason":"No supported direction difference"}
if set(values)=={"deposit","withdrawal"} and net!=0:
 sql="""WITH per_user AS (
  SELECT TRY_CAST(uid AS BIGINT) AS uid_key,
   SUM(CASE WHEN direction='deposit' THEN amount
            WHEN direction='withdrawal' THEN -amount ELSE 0 END) AS net_usdt
  FROM crypto_transactions
  WHERE asset='USDT' AND status='completed'
    AND direction IN ('deposit','withdrawal')
  GROUP BY uid_key
)
SELECT uid_key,net_usdt,
 SUM(net_usdt) OVER () AS overall_net_usdt,
 SUM(net_usdt) OVER ()-net_usdt AS net_without_user
FROM per_user ORDER BY ABS(net_usdt) DESC,uid_key"""
 con=duckdb.connect(str(DB),read_only=True)
 cur=con.execute(sql);heads=[d[0] for d in cur.description];rs=cur.fetchall();con.close()
 path=OUT/"C01-leave-one-user-out.csv"
 with path.open("w",newline="",encoding="utf-8") as file:
  w=csv.writer(file);w.writerow(heads);w.writerows(rs)
 rows=list(csv.DictReader(path.open()))
 assert rows and all(math.isclose(float(r["overall_net_usdt"]),net,abs_tol=1e-7) for r in rows)
 assert math.isclose(sum(float(r["net_usdt"]) for r in rows),net,abs_tol=1e-7)
 left=[float(r["net_without_user"]) for r in rows]
 unchanged=all(x>0 for x in left) if net>0 else all(x<0 for x in left)
 complex_status={"status":"VALIDATED_SAMPLE_SCOPED","signal_source":"Q01-USDT-direction",
  "activated_dimension":"uid within crypto_transactions",
  "alternative":"one user entirely explains the directional difference",
  "minimum_check":"remove each user one at a time",
  "result":{"total_net_usdt":net,"users":len(rows),"min_leave_one_out":min(left),
            "max_leave_one_out":max(left),"sign_unchanged":unchanged},
  "sql":sql,"sql_sha256":hashlib.sha256(sql.encode()).hexdigest(),
  "result_sha256":sha(path),"limits":["record state, not final settlement",
  "no historical baseline","cannot rule out several users jointly driving the difference"]}
q04=list(csv.DictReader((OUT/"Q04-cross-rail.csv").open()))
assert sum(int(r["fiat_orders"]) for r in q04)==R["tables"]["fiat_transactions"]["rows"]
assert sum(int(r["crypto_orders"]) for r in q04)==R["tables"]["crypto_transactions"]["rows"]
assert len({r["uid_key"] for r in q04})==R["tables"]["users"]["rows"]
q03=list(csv.DictReader((OUT/"Q03-rate-coverage.csv").open()))
central={"status":"CENTRAL_RECONCILIATION_PASS",
 "snapshot_sha256":R["snapshot_sha256"],"uid_join_no_fanout":True,
 "rates_by_asset":{r["asset"]:int(r["rates_within_tx_period"]) for r in q03},
 "gate3":complex_status,
 "not_proven":["historical exchange rates for trading periods",
 "eventual settlement","fiat-crypto value transfer relationship"]}
(OUT/"gate3-central-receipt.json").write_text(json.dumps(central,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({"central":central["status"],"complex":complex_status["status"],
 "net_usdt":net,"zero_rates":sum(x==0 for x in central["rates_by_asset"].values())}))
