.mode json
.once dual-evidence/status.json
SELECT 'fiat' AS rail, status, COUNT(*) AS rows
FROM fiat_transactions GROUP BY status
UNION ALL
SELECT 'crypto' AS rail, status, COUNT(*) AS rows
FROM crypto_transactions GROUP BY status
ORDER BY rail,status;

.once dual-evidence/quality.json
WITH x AS (
 SELECT 'fiat' AS rail, CAST(uid AS VARCHAR) AS uid, currency AS asset, status, TRY_CAST(amount AS DECIMAL(38,8)) AS amount FROM fiat_transactions
 UNION ALL SELECT 'crypto', CAST(uid AS VARCHAR), asset, status, TRY_CAST(amount AS DECIMAL(38,8)) FROM crypto_transactions
)
SELECT rail,COUNT(*) AS rows,COUNT(*) FILTER(WHERE amount IS NULL) AS invalid_amounts,
 COUNT(*) FILTER(WHERE asset IS NULL OR TRIM(asset)='') AS missing_assets,
 COUNT(*) FILTER(WHERE uid IS NULL OR TRIM(uid)='') AS missing_uids,
 COUNT(*) FILTER(WHERE status='completed') AS completed_rows
FROM x GROUP BY rail ORDER BY rail;

.once dual-evidence/rates.json
SELECT asset,COUNT(*) AS rate_rows, COUNT(DISTINCT effective_date) AS effective_dates,
 COUNT(*) FILTER(WHERE rate_to_usdt IS NULL OR rate_to_usdt<=0) AS invalid_rates
FROM exchange_rates GROUP BY asset ORDER BY asset;

.once dual-evidence/concentration.json
WITH x AS (
 SELECT 'fiat' AS rail, CAST(uid AS VARCHAR) AS uid, currency AS asset,
        TRY_CAST(amount AS DECIMAL(38,8)) AS amount
 FROM fiat_transactions WHERE status='completed'
 UNION ALL
 SELECT 'crypto', CAST(uid AS VARCHAR), asset,
        TRY_CAST(amount AS DECIMAL(38,8))
 FROM crypto_transactions WHERE status='completed'
), by_user AS (
 SELECT rail,asset,uid,COUNT(*) AS n,SUM(amount) AS v
 FROM x WHERE amount IS NOT NULL AND uid IS NOT NULL AND asset IS NOT NULL
 GROUP BY rail,asset,uid
), by_asset AS (
 SELECT rail,asset,SUM(n) AS completed_orders,COUNT(*) AS active_users,
  SUM(v) AS native_total,MAX(v) AS top1_native_total
 FROM by_user GROUP BY rail,asset
)
SELECT rail,asset,completed_orders,active_users,native_total,top1_native_total,
 CASE WHEN native_total>0 THEN ROUND(100*top1_native_total/native_total,3) END AS top1_share_pct
FROM by_asset ORDER BY rail,asset;

.once dual-evidence/source-counts.json
SELECT (SELECT COUNT(*) FROM users) AS users_rows,
 (SELECT COUNT(*) FROM fiat_transactions) AS fiat_rows,
 (SELECT COUNT(*) FROM crypto_transactions) AS crypto_rows,
 (SELECT COUNT(*) FROM exchange_rates) AS exchange_rate_rows;
