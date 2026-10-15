#!/usr/bin/env python3
"""First pass: materialize four user-authorized remote Excel sheets ONCE.

Recover the immutable original read_xlsx block; introspection and downstream SQL
only refer to the four materialized tables. Never inspect other sheets.
This records sufficient scoped facts for a NEW, evidence-led second investigation.
"""
from pathlib import Path
import hashlib
import re
import sys

out=Path(sys.argv[1] if len(sys.argv)>1 else "discovery")
out.mkdir(exist_ok=True,parents=True)
original=Path(".github/workflows/sql-business-thinking-native-duckdb-url-test.yml").read_text()
m=re.search(r"cat > d02\.sql <<'SQL'\n([\s\S]*?)\n\s+SQL\b",original)
assert m,"Original authorized D02 contract not found"
source="\n".join(line[10:] if line.startswith("          ") else line
                  for line in m.group(1).splitlines())+"\n"
url="https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx"
tables=["users","fiat_transactions","crypto_transactions","exchange_rates"]
assert source.count("read_xlsx(")==4
assert source.count("'"+url+"'")==4
for table in tables:
    assert source.count(f"sheet = '{table}'")==1
    assert source.count(f"CREATE TEMP TABLE {table} AS")==1
for init in ["INSTALL httpfs;","LOAD httpfs;","INSTALL excel;","LOAD excel;"]:
    assert source.count(init)==1
(out/"read-plan.sha256").write_text(hashlib.sha256(source.encode()).hexdigest())
# Original source SQL contains 4 read_xlsx calls, then only materialized table queries.
statements=["\n.mode json\n"]
def query(name,sql):
    assert "read_xlsx" not in sql.lower()
    statements.append(f".once {out.as_posix()}/{name}.json\n{sql.strip()};\n")
for table in tables:
    query(f"schema_{table}",f"DESCRIBE {table}")
query("user_base","SELECT CAST(uid AS VARCHAR) uid,CAST(account_status AS VARCHAR) account_status FROM users ORDER BY uid")
query("fiat_details", """
 SELECT CAST(uid AS VARCHAR) uid, CAST(fiat_order_id AS VARCHAR) order_id,
 CAST(currency AS VARCHAR) asset,CAST(direction AS VARCHAR) direction,
 CAST(status AS VARCHAR) status,CAST(amount AS DECIMAL(24,8)) amount,
 CAST(fee AS DECIMAL(24,8)) fee,
 CAST(created_at AS VARCHAR) created_at,
 CAST(completed_at AS VARCHAR) completed_at
 FROM fiat_transactions ORDER BY created_at,order_id
""")
query("crypto_details","""
 SELECT CAST(uid AS VARCHAR) uid,CAST(crypto_order_id AS VARCHAR) order_id,
 CAST(asset AS VARCHAR) asset,CAST(direction AS VARCHAR) direction,
 CAST(status AS VARCHAR) status,CAST(amount AS DECIMAL(24,8)) amount,
 CAST(fee AS DECIMAL(24,8)) fee,
 CAST(created_at AS VARCHAR) created_at,
 CAST(completed_at AS VARCHAR) completed_at
 FROM crypto_transactions ORDER BY created_at,order_id
""")
query("rates_detail","""
 SELECT CAST(asset AS VARCHAR) asset,CAST(effective_date AS VARCHAR) effective_date,
 CAST(rate_to_usdt AS DECIMAL(24,8)) rate_to_usdt
 FROM exchange_rates ORDER BY asset,effective_date
""")
query("uid_rail_coverage","""
 WITH f AS (SELECT CAST(uid AS VARCHAR) uid,COUNT(*) n,
               COUNT(*) FILTER(WHERE status='completed') completed_n
            FROM fiat_transactions GROUP BY uid),
      c AS (SELECT CAST(uid AS VARCHAR) uid,COUNT(*) n,
               COUNT(*) FILTER(WHERE status='completed') completed_n
            FROM crypto_transactions GROUP BY uid)
 SELECT CAST(u.uid AS VARCHAR) uid,
 COALESCE(f.n,0) fiat_n,COALESCE(c.n,0) crypto_n,
 COALESCE(f.completed_n,0) fiat_completed,
 COALESCE(c.completed_n,0) crypto_completed
 FROM users u LEFT JOIN f ON CAST(u.uid AS VARCHAR)=f.uid
 LEFT JOIN c ON CAST(u.uid AS VARCHAR)=c.uid ORDER BY uid
""")
query("date_coverage","""
SELECT 'fiat' rail,COUNT(*) total,MIN(created_at) first_at,
 MAX(created_at) last_at,COUNT(DISTINCT uid) users,
 COUNT(*) FILTER(WHERE completed_at IS NOT NULL) with_completed_at
 FROM fiat_transactions
UNION ALL SELECT 'crypto',COUNT(*),MIN(created_at),MAX(created_at),
 COUNT(DISTINCT uid),COUNT(*) FILTER(WHERE completed_at IS NOT NULL)
 FROM crypto_transactions
""")

# Evidence-led second group: normalized identity, time proximity, bidirectional assets.
query("joined_users","""
 WITH f AS (SELECT TRY_CAST(uid AS BIGINT) uid,COUNT(*) n FROM fiat_transactions GROUP BY 1),
      c AS (SELECT TRY_CAST(uid AS BIGINT) uid,COUNT(*) n FROM crypto_transactions GROUP BY 1)
 SELECT CAST(u.uid AS VARCHAR) uid,u.user_name,u.account_status,
 COALESCE(f.n,0) fiat_n,COALESCE(c.n,0) crypto_n
 FROM users u LEFT JOIN f ON TRY_CAST(u.uid AS BIGINT)=f.uid
 LEFT JOIN c ON TRY_CAST(u.uid AS BIGINT)=c.uid ORDER BY uid
""")
query("crossrail_24h","""
 SELECT CAST(TRY_CAST(f.uid AS BIGINT) AS VARCHAR) uid,
 f.fiat_order_id fiat_order,f.currency fiat_asset,f.direction fiat_direction,
 f.amount fiat_amount,CAST(f.created_at AS VARCHAR) fiat_time,
 c.crypto_order_id crypto_order,c.asset crypto_asset,c.direction crypto_direction,
 c.amount crypto_amount,CAST(c.created_at AS VARCHAR) crypto_time,
 ABS(DATE_DIFF('minute',f.created_at,c.created_at)) gap_minutes
 FROM fiat_transactions f JOIN crypto_transactions c
 ON TRY_CAST(f.uid AS BIGINT)=TRY_CAST(c.uid AS BIGINT)
 WHERE f.status='completed' AND c.status='completed'
 AND ABS(DATE_DIFF('minute',f.created_at,c.created_at))<=1440
 ORDER BY gap_minutes,uid
""")
query("fiat_roundtrip_7d","""
 SELECT CAST(TRY_CAST(a.uid AS BIGINT) AS VARCHAR) uid,a.currency asset,
 a.fiat_order_id in_order,b.fiat_order_id out_order,a.amount amount_in,
 b.amount amount_out,DATE_DIFF('minute',a.created_at,b.created_at) minutes
 FROM fiat_transactions a JOIN fiat_transactions b
 ON TRY_CAST(a.uid AS BIGINT)=TRY_CAST(b.uid AS BIGINT) AND a.currency=b.currency
 WHERE a.status='completed' AND b.status='completed'
 AND a.direction='deposit' AND b.direction='withdrawal'
 AND b.created_at>=a.created_at AND b.created_at<=a.created_at+INTERVAL 7 DAY
 ORDER BY minutes,uid
""")
query("snapshot_rate_coverage","""
 WITH tx AS (
 SELECT currency asset,CAST(created_at AS DATE) d FROM fiat_transactions
 UNION ALL SELECT asset,CAST(created_at AS DATE) FROM crypto_transactions
 ) SELECT COUNT(*) rows_total,
 COUNT(*) FILTER(WHERE r.asset IS NULL) missing_currency_rate,
 COUNT(*) FILTER(WHERE r.effective_date=tx.d) matching_date_rates,
 MIN(tx.d) min_tx_date,MAX(tx.d) max_tx_date,
 MIN(r.effective_date) min_rate_date,MAX(r.effective_date) max_rate_date
 FROM tx LEFT JOIN exchange_rates r USING(asset)
""")

query("keys_quality","""
 SELECT 'fiat' rail,COUNT(*) n,
 COUNT(DISTINCT fiat_order_id) unique_orders,
 COUNT(*) FILTER(WHERE uid IS NULL) missing_uid,
 COUNT(*) FILTER(WHERE amount IS NULL OR amount<=0) invalid_amount
 FROM fiat_transactions
 UNION ALL SELECT 'crypto',COUNT(*),COUNT(DISTINCT crypto_order_id),
 COUNT(*) FILTER(WHERE uid IS NULL),
 COUNT(*) FILTER(WHERE amount IS NULL OR amount<=0) FROM crypto_transactions
""")
(out/"first-pass.sql").write_text(source+"\n".join(statements))
print({"source_reads":4,"allowed_tables":tables,"queries_after_materialization":len(statements)-1,
       "source_read_sha256":hashlib.sha256(source.encode()).hexdigest()})
