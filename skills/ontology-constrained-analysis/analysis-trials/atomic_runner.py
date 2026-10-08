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
"Q02-status-clock":"""WITH both AS (
 SELECT 'fiat' AS rail,status,completed_at FROM fiat_transactions
 UNION ALL SELECT 'crypto' AS rail,status,completed_at FROM crypto_transactions
)
SELECT rail,status,COUNT(*) AS records,
 SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS has_completed_at
FROM both GROUP BY rail,status ORDER BY rail,status""",
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
GROUP BY ALL ORDER BY asset""",
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
