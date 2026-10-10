.mode json
.once three-role-evidence/coverage.json
WITH t AS (
 SELECT 'fiat' AS rail,CAST(created_at AS VARCHAR) AS created,CAST(completed_at AS VARCHAR) AS completed,CAST(status AS VARCHAR) AS state FROM fiat_transactions
 UNION ALL SELECT 'crypto',CAST(created_at AS VARCHAR),CAST(completed_at AS VARCHAR),CAST(status AS VARCHAR) FROM crypto_transactions
)
SELECT rail,COUNT(*) AS source_rows,CAST(MIN(TRY_CAST(created AS TIMESTAMP)) AS VARCHAR) AS min_created,
 CAST(MAX(TRY_CAST(created AS TIMESTAMP)) AS VARCHAR) AS max_created,
 COUNT(*) FILTER(WHERE TRY_CAST(created AS TIMESTAMP) IS NULL) AS bad_created,
 COUNT(*) FILTER(WHERE state='completed' AND TRY_CAST(completed AS TIMESTAMP) IS NULL) AS completed_without_time,
 COUNT(*) FILTER(WHERE TRY_CAST(completed AS TIMESTAMP)<TRY_CAST(created AS TIMESTAMP)) AS time_reversal
FROM t GROUP BY rail ORDER BY rail;

.once three-role-evidence/states.json
WITH t AS (
 SELECT 'fiat' AS rail,CAST(direction AS VARCHAR) AS direction,CAST(status AS VARCHAR) AS state FROM fiat_transactions
 UNION ALL SELECT 'crypto',CAST(direction AS VARCHAR),CAST(status AS VARCHAR) FROM crypto_transactions
)
SELECT rail,direction,state,COUNT(*) AS n FROM t GROUP BY rail,direction,state ORDER BY rail,direction,state;

.once three-role-evidence/quality.json
SELECT 'fiat' AS rail,COUNT(*) AS n,COUNT(DISTINCT fiat_order_id) AS unique_orders,
 COUNT(*) FILTER(WHERE fiat_order_id IS NULL OR uid IS NULL) AS null_keys,
 COUNT(*) FILTER(WHERE TRY_CAST(amount AS DECIMAL(38,8)) IS NULL OR TRY_CAST(amount AS DECIMAL(38,8))<0) AS invalid_amounts
FROM fiat_transactions
UNION ALL
SELECT 'crypto',COUNT(*),COUNT(DISTINCT crypto_order_id),
 COUNT(*) FILTER(WHERE crypto_order_id IS NULL OR uid IS NULL),
 COUNT(*) FILTER(WHERE TRY_CAST(amount AS DECIMAL(38,8)) IS NULL OR TRY_CAST(amount AS DECIMAL(38,8))<0)
FROM crypto_transactions;

.once three-role-evidence/flow.json
WITH tx AS (
 SELECT 'fiat' AS rail,CAST(currency AS VARCHAR) AS asset,CAST(direction AS VARCHAR) AS direction,
        CAST(status AS VARCHAR) AS state,TRY_CAST(amount AS DECIMAL(38,8)) AS amount FROM fiat_transactions
 UNION ALL
 SELECT 'crypto',CAST(asset AS VARCHAR),CAST(direction AS VARCHAR),CAST(status AS VARCHAR),
        TRY_CAST(amount AS DECIMAL(38,8)) FROM crypto_transactions
)
SELECT rail,asset,COUNT(*) AS all_orders,
 COUNT(*) FILTER(WHERE state='completed' AND direction='deposit') AS in_orders,
 COUNT(*) FILTER(WHERE state='completed' AND direction='withdrawal') AS out_orders,
 COUNT(*) FILTER(WHERE state<>'completed' AND direction='withdrawal') AS noncomplete_out_orders,
 SUM(CASE WHEN state='completed' AND direction='deposit' THEN amount ELSE 0 END) AS amount_in,
 SUM(CASE WHEN state='completed' AND direction='withdrawal' THEN amount ELSE 0 END) AS amount_out,
 SUM(CASE WHEN state='completed' AND direction='deposit' THEN amount
          WHEN state='completed' AND direction='withdrawal' THEN -amount ELSE 0 END) AS net_in
FROM tx GROUP BY rail,asset ORDER BY rail,asset;

.once three-role-evidence/reconcile.json
WITH t AS (
 SELECT 'fiat' AS rail,CAST(currency AS VARCHAR) AS asset,CAST(direction AS VARCHAR) AS direction,
        TRY_CAST(amount AS DECIMAL(38,8)) AS amount FROM fiat_transactions WHERE status='completed'
 UNION ALL
 SELECT 'crypto',CAST(asset AS VARCHAR),CAST(direction AS VARCHAR),
        TRY_CAST(amount AS DECIMAL(38,8)) FROM crypto_transactions WHERE status='completed'
), d AS (
 SELECT rail,asset,direction,COUNT(*) AS n,SUM(amount) AS total FROM t GROUP BY rail,asset,direction
)
SELECT rail,asset,COALESCE(SUM(total) FILTER(WHERE direction='deposit'),0) AS independent_in,
 COALESCE(SUM(total) FILTER(WHERE direction='withdrawal'),0) AS independent_out,
 COALESCE(SUM(n) FILTER(WHERE direction='deposit'),0) AS independent_in_orders,
 COALESCE(SUM(n) FILTER(WHERE direction='withdrawal'),0) AS independent_out_orders
FROM d GROUP BY rail,asset ORDER BY rail,asset;

.once three-role-evidence/concentration.json
WITH t AS (
 SELECT 'fiat' AS rail,CAST(currency AS VARCHAR) AS asset,CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) AS uid,
 CAST(direction AS VARCHAR) AS direction,TRY_CAST(amount AS DECIMAL(38,8)) AS amount FROM fiat_transactions WHERE status='completed'
 UNION ALL
 SELECT 'crypto',CAST(asset AS VARCHAR),CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR),
 CAST(direction AS VARCHAR),TRY_CAST(amount AS DECIMAL(38,8)) FROM crypto_transactions WHERE status='completed'
), per_user AS (
 SELECT rail,asset,uid,
 SUM(CASE WHEN direction='withdrawal' THEN amount ELSE 0 END) AS user_out,
 COUNT(*) FILTER(WHERE direction='withdrawal') AS withdrawal_n
 FROM t GROUP BY rail,asset,uid
)
SELECT rail,asset,COUNT(*) AS active_users,
 COUNT(*) FILTER(WHERE withdrawal_n>0) AS withdrawing_users,
 SUM(user_out) AS sum_out,MAX(user_out) AS max_user_out
FROM per_user GROUP BY rail,asset ORDER BY rail,asset;

.once three-role-evidence/user_rate_quality.json
WITH u AS (SELECT CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) AS uid FROM users),
 t AS (SELECT CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) AS uid FROM fiat_transactions
 UNION ALL SELECT CAST(TRY_CAST(uid AS BIGINT) AS VARCHAR) FROM crypto_transactions)
SELECT (SELECT COUNT(*) FROM u) AS users_rows,(SELECT COUNT(DISTINCT uid) FROM u) AS unique_users,
 (SELECT COUNT(*) FROM t LEFT JOIN u USING(uid) WHERE u.uid IS NULL) AS orphan_tx,
 (SELECT COUNT(*) FROM exchange_rates) AS rate_rows,
 (SELECT COUNT(DISTINCT effective_date) FROM exchange_rates) AS rate_dates;
