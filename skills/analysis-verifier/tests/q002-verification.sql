.once dual-evidence/q002-orders.json
SELECT COUNT(*) AS completed_usd_orders,
 COUNT(DISTINCT fiat_order_id) AS distinct_order_ids,
 COUNT(*) FILTER(WHERE fiat_order_id IS NULL) AS null_order_ids,
 COUNT(*) FILTER(WHERE uid IS NULL) AS null_uids,
 COUNT(*) FILTER(WHERE TRY_CAST(amount AS DECIMAL(38,8)) IS NULL) AS invalid_amounts
FROM fiat_transactions WHERE currency='USD' AND status='completed';

.once dual-evidence/q002-mechanism.json
WITH usd AS (
 SELECT CAST(uid AS VARCHAR) AS uid, CAST(fiat_order_id AS VARCHAR) AS order_id,
        TRY_CAST(amount AS DECIMAL(38,8)) AS amount
 FROM fiat_transactions
 WHERE currency='USD' AND status='completed'
), valid AS (
 SELECT * FROM usd WHERE uid IS NOT NULL AND order_id IS NOT NULL AND amount IS NOT NULL
), ordered AS (
 SELECT *, ROW_NUMBER() OVER(ORDER BY amount DESC,order_id) AS amount_rank FROM valid
), by_user AS (
 SELECT uid, COUNT(*) AS orders, SUM(amount) AS total FROM ordered GROUP BY uid
), user_rank AS (
 SELECT *, ROW_NUMBER() OVER(ORDER BY total DESC,uid) AS rnk FROM by_user
), trimmed AS (
 SELECT * FROM ordered WHERE amount_rank>1
), reduced_users AS (
 SELECT uid,COUNT(*) AS orders,SUM(amount) AS total FROM trimmed GROUP BY uid
), reduced_rank AS (
 SELECT *,ROW_NUMBER() OVER(ORDER BY total DESC,uid) AS rnk FROM reduced_users
)
SELECT
 (SELECT COUNT(*) FROM valid) AS completed_usd_orders,
 (SELECT COUNT(DISTINCT uid) FROM valid) AS distinct_users,
 (SELECT SUM(amount) FROM valid) AS native_total,
 (SELECT total FROM user_rank WHERE rnk=1) AS top1_native_total,
 (SELECT orders FROM user_rank WHERE rnk=1) AS top1_order_count,
 (SELECT MAX(amount) FROM valid) AS largest_single_order,
 (SELECT COUNT(*) FROM trimmed) AS trimmed_orders,
 (SELECT SUM(amount) FROM trimmed) AS trimmed_native_total,
 (SELECT total FROM reduced_rank WHERE rnk=1) AS trimmed_top1_native_total,
 (SELECT ROUND(100*total / NULLIF((SELECT SUM(amount) FROM trimmed),0),3) FROM reduced_rank WHERE rnk=1) AS trimmed_top1_share_pct,
 (SELECT uid FROM user_rank WHERE rnk=1)=(SELECT uid FROM reduced_rank WHERE rnk=1) AS same_top_user;
