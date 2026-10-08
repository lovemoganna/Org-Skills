-- ontology-constrained-analysis v16.2: one-session formal evidence run
-- All directions and questions below were selected AFTER independent, scoped cold discovery.
INSTALL httpfs;
LOAD httpfs;
INSTALL excel;
LOAD excel;

CREATE TEMP TABLE users AS
SELECT *
FROM read_xlsx(
  'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
  sheet = 'users',
  header = true
);

CREATE TEMP TABLE fiat_transactions AS
SELECT *
FROM read_xlsx(
  'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
  sheet = 'fiat_transactions',
  header = true
);

CREATE TEMP TABLE crypto_transactions AS
SELECT *
FROM read_xlsx(
  'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
  sheet = 'crypto_transactions',
  header = true
);

CREATE TEMP TABLE exchange_rates AS
SELECT *
FROM read_xlsx(
  'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
  sheet = 'exchange_rates',
  header = true
);

-- data_counts
.once artifacts/data_counts.csv
SELECT 'users' AS source, COUNT(*) AS records FROM users
UNION ALL
SELECT 'fiat_transactions' AS source, COUNT(*) AS records FROM fiat_transactions
UNION ALL
SELECT 'crypto_transactions' AS source, COUNT(*) AS records FROM crypto_transactions
UNION ALL
SELECT 'exchange_rates' AS source, COUNT(*) AS records FROM exchange_rates;

-- schema_users
.once artifacts/schema_users.csv
DESCRIBE SELECT * FROM users;

-- schema_fiat
.once artifacts/schema_fiat.csv
DESCRIBE SELECT * FROM fiat_transactions;

-- schema_crypto
.once artifacts/schema_crypto.csv
DESCRIBE SELECT * FROM crypto_transactions;

-- schema_rates
.once artifacts/schema_rates.csv
DESCRIBE SELECT * FROM exchange_rates;

-- created_date_coverage
.once artifacts/created_date_coverage.csv
SELECT 'users' AS source, COUNT(*) AS records, MIN(created_at) AS created_min, MAX(created_at) AS created_max
FROM users
UNION ALL
SELECT 'fiat_transactions', COUNT(*), MIN(created_at), MAX(created_at)
FROM fiat_transactions
UNION ALL
SELECT 'crypto_transactions', COUNT(*), MIN(created_at), MAX(created_at)
FROM crypto_transactions;

-- quality_keys
.once artifacts/quality_keys.csv
SELECT
  (SELECT COUNT(*) - COUNT(DISTINCT uid) FROM users) AS users_duplicate_uid,
  (SELECT COUNT(*) FILTER (WHERE TRY_CAST(uid AS BIGINT) IS NULL) FROM users) AS users_invalid_numeric_uid,
  (SELECT COUNT(*) - COUNT(DISTINCT fiat_order_id) FROM fiat_transactions) AS fiat_duplicate_order_id,
  (SELECT COUNT(*) - COUNT(DISTINCT crypto_order_id) FROM crypto_transactions) AS crypto_duplicate_order_id,
  (SELECT COUNT(*) - COUNT(DISTINCT asset) FROM exchange_rates) AS rate_duplicate_asset,
  (SELECT COUNT(*) FILTER (WHERE uid IS NULL OR uid <> TRUNC(uid)) FROM fiat_transactions) AS fiat_invalid_integer_uid,
  (SELECT COUNT(*) FILTER (WHERE uid IS NULL OR uid <> TRUNC(uid)) FROM crypto_transactions) AS crypto_invalid_integer_uid,
  (SELECT COUNT(*) FILTER (WHERE rate_to_usdt IS NULL OR rate_to_usdt <= 0) FROM exchange_rates) AS invalid_exchange_rate;

-- quality_relations
.once artifacts/quality_relations.csv
SELECT 'fiat' AS source,
  COUNT(*) AS native_records,
  COUNT(u.uid) AS matched_records,
  COUNT(*) FILTER (WHERE u.uid IS NULL) AS unmatched_records,
  COUNT(DISTINCT f.uid) AS native_distinct_uid
FROM fiat_transactions AS f
LEFT JOIN users AS u
  ON CAST(f.uid AS BIGINT) = TRY_CAST(u.uid AS BIGINT)
UNION ALL
SELECT 'crypto',
  COUNT(*),
  COUNT(u.uid),
  COUNT(*) FILTER (WHERE u.uid IS NULL),
  COUNT(DISTINCT c.uid)
FROM crypto_transactions AS c
LEFT JOIN users AS u
  ON CAST(c.uid AS BIGINT) = TRY_CAST(u.uid AS BIGINT);

-- users_dimensions
.once artifacts/users_dimensions.csv
SELECT account_status, COUNT(*) AS users,
  MIN(kyc_level) AS min_kyc_level,
  MAX(kyc_level) AS max_kyc_level
FROM users
GROUP BY account_status
ORDER BY account_status;

-- fiat_status
.once artifacts/fiat_status.csv
SELECT status, direction, COUNT(*) AS orders,
  COUNT(*) FILTER (WHERE completed_at IS NULL) AS completion_time_null,
  COUNT(*) FILTER (WHERE completed_at < created_at) AS completion_time_before_created
FROM fiat_transactions
GROUP BY status, direction
ORDER BY status, direction;

-- fiat_currency_status
.once artifacts/fiat_currency_status.csv
SELECT currency, status, direction,
  COUNT(*) AS orders, SUM(amount) AS amount_in_currency
FROM fiat_transactions
GROUP BY currency, status, direction
ORDER BY currency, status, direction;

-- crypto_status
.once artifacts/crypto_status.csv
SELECT status, direction, asset,
  COUNT(*) AS orders, SUM(amount) AS amount_in_asset,
  COUNT(*) FILTER (WHERE tx_hash IS NULL) AS missing_tx_hash,
  COUNT(*) FILTER (WHERE completed_at IS NULL) AS missing_completion_time
FROM crypto_transactions
GROUP BY status, direction, asset
ORDER BY status, direction, asset;

-- crypto_network_asset
.once artifacts/crypto_network_asset.csv
SELECT asset, network, status, COUNT(*) AS orders
FROM crypto_transactions
GROUP BY asset, network, status
ORDER BY asset, network, status;

-- rates_scope
.once artifacts/rates_scope.csv
SELECT asset, asset_type, quote_currency, effective_date, rate_to_usdt
FROM exchange_rates
ORDER BY asset;

-- rates_coverage_and_age
.once artifacts/rates_coverage_and_age.csv
WITH events AS (
  SELECT 'fiat' AS rail, currency AS instrument, created_at
  FROM fiat_transactions
  UNION ALL
  SELECT 'crypto', asset, created_at
  FROM crypto_transactions
)
SELECT
  e.rail,
  e.instrument,
  COUNT(*) AS order_count,
  COUNT(r.asset) AS rate_key_matches,
  COUNT(*) FILTER (WHERE r.asset IS NULL) AS no_rate_key,
  COUNT(*) FILTER (WHERE e.created_at::DATE > r.effective_date) AS dated_later_than_rate,
  MIN(r.effective_date) AS first_effective_date,
  MAX(e.created_at::DATE) AS last_order_date
FROM events AS e
LEFT JOIN exchange_rates AS r
  ON e.instrument = r.asset
GROUP BY e.rail, e.instrument
ORDER BY e.rail, e.instrument;

-- atomic_usdt
.once artifacts/atomic_usdt.csv
SELECT
  direction,
  COUNT(*) AS orders,
  SUM(amount) AS amount_usdt,
  SUM(fee) AS recorded_fee
FROM crypto_transactions
WHERE asset = 'USDT'
  AND status = 'completed'
GROUP BY direction
ORDER BY direction;

-- atomic_usdt_net
.once artifacts/atomic_usdt_net.csv
SELECT
  COUNT(*) AS completed_usdt_orders,
  COUNT(*) FILTER (WHERE direction = 'deposit') AS deposit_count,
  COUNT(*) FILTER (WHERE direction = 'withdrawal') AS withdrawal_count,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    ELSE NULL
  END) AS deposit_amount,
  SUM(CASE
    WHEN direction = 'withdrawal' THEN amount
    ELSE NULL
  END) AS withdrawal_amount,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_recorded_usdt,
  COUNT(*) FILTER (WHERE direction NOT IN ('deposit', 'withdrawal') OR direction IS NULL) AS unknown_direction
FROM crypto_transactions
WHERE asset = 'USDT'
  AND status = 'completed';

-- atomic_crypto_by_asset
.once artifacts/atomic_crypto_by_asset.csv
SELECT
  asset,
  COUNT(*) AS completed_orders,
  SUM(CASE WHEN direction = 'deposit' THEN amount ELSE NULL END) AS deposit_amount,
  SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE NULL END) AS withdrawal_amount,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_in_native_asset,
  COUNT(*) FILTER (WHERE direction NOT IN ('deposit', 'withdrawal') OR direction IS NULL) AS unknown_direction
FROM crypto_transactions
WHERE status = 'completed'
GROUP BY asset
ORDER BY asset;

-- atomic_eur_net
.once artifacts/atomic_eur_net.csv
SELECT currency,
  COUNT(*) AS completed_orders,
  SUM(CASE WHEN direction = 'deposit' THEN amount ELSE NULL END) AS deposit_amount,
  SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE NULL END) AS withdrawal_amount,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_amount_eur
FROM fiat_transactions
WHERE currency = 'EUR' AND status = 'completed'
GROUP BY currency;

-- atomic_fiat_by_currency
.once artifacts/atomic_fiat_by_currency.csv
SELECT currency,
  COUNT(*) AS completed_orders,
  SUM(CASE WHEN direction = 'deposit' THEN amount ELSE NULL END) AS deposit_amount,
  SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE NULL END) AS withdrawal_amount,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_in_native_currency
FROM fiat_transactions
WHERE status = 'completed'
GROUP BY currency
ORDER BY currency;

-- complex_usdt_by_user
.once artifacts/complex_usdt_by_user.csv
WITH per_user AS (
  SELECT CAST(uid AS BIGINT) AS user_key,
    COUNT(*) AS usdt_orders,
    SUM(CASE WHEN direction = 'deposit' THEN amount ELSE 0 END) AS deposit_usdt,
    SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE 0 END) AS withdrawal_usdt,
    SUM(CASE
      WHEN direction = 'deposit' THEN amount
      WHEN direction = 'withdrawal' THEN -amount
      ELSE NULL
    END) AS net_usdt
  FROM crypto_transactions
  WHERE asset = 'USDT' AND status = 'completed'
  GROUP BY CAST(uid AS BIGINT)
)
SELECT u.user_key, a.account_status, u.usdt_orders, u.deposit_usdt, u.withdrawal_usdt, u.net_usdt
FROM per_user AS u
LEFT JOIN users AS a
  ON u.user_key = TRY_CAST(a.uid AS BIGINT)
ORDER BY ABS(u.net_usdt) DESC, u.user_key;

-- complex_usdt_network
.once artifacts/complex_usdt_network.csv
SELECT
  network,
  COUNT(*) AS completed_orders,
  SUM(CASE WHEN direction = 'deposit' THEN amount ELSE 0 END) AS deposit_usdt,
  SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE 0 END) AS withdrawal_usdt,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_usdt
FROM crypto_transactions
WHERE status = 'completed' AND asset = 'USDT'
GROUP BY network
ORDER BY ABS(net_usdt) DESC;

-- complex_usdt_time
.once artifacts/complex_usdt_time.csv
SELECT YEAR(created_at) AS created_year,
  COUNT(*) AS orders,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_usdt
FROM crypto_transactions
WHERE asset = 'USDT' AND status = 'completed'
GROUP BY YEAR(created_at)
ORDER BY created_year;

-- complex_fiat_eur_by_user
.once artifacts/complex_fiat_eur_by_user.csv
SELECT CAST(uid AS BIGINT) AS user_key,
  COUNT(*) AS orders,
  SUM(CASE WHEN direction = 'deposit' THEN amount ELSE 0 END) AS deposit_eur,
  SUM(CASE WHEN direction = 'withdrawal' THEN amount ELSE 0 END) AS withdrawal_eur,
  SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_eur
FROM fiat_transactions
WHERE currency = 'EUR' AND status = 'completed'
GROUP BY CAST(uid AS BIGINT)
ORDER BY ABS(net_eur) DESC;

-- complex_cross_rail_user
.once artifacts/complex_cross_rail_user.csv
WITH f AS (
  SELECT CAST(uid AS BIGINT) AS user_key, COUNT(*) AS fiat_orders
  FROM fiat_transactions
  GROUP BY CAST(uid AS BIGINT)
),
c AS (
  SELECT CAST(uid AS BIGINT) AS user_key, COUNT(*) AS crypto_orders
  FROM crypto_transactions
  GROUP BY CAST(uid AS BIGINT)
)
SELECT TRY_CAST(u.uid AS BIGINT) AS user_key,
  u.account_status,
  COALESCE(f.fiat_orders, 0) AS fiat_orders,
  COALESCE(c.crypto_orders, 0) AS crypto_orders,
  (f.user_key IS NOT NULL AND c.user_key IS NOT NULL) AS both_rails
FROM users AS u
LEFT JOIN f ON TRY_CAST(u.uid AS BIGINT) = f.user_key
LEFT JOIN c ON TRY_CAST(u.uid AS BIGINT) = c.user_key
ORDER BY both_rails DESC, user_key;

-- complex_account_status_transactions
.once artifacts/complex_account_status_transactions.csv
WITH f AS (
  SELECT CAST(uid AS BIGINT) AS user_key,
    COUNT(*) AS fiat_orders,
    COUNT(*) FILTER (WHERE direction = 'withdrawal' AND status = 'completed') AS fiat_completed_withdrawal_rows
  FROM fiat_transactions
  GROUP BY CAST(uid AS BIGINT)
),
c AS (
  SELECT CAST(uid AS BIGINT) AS user_key,
    COUNT(*) AS crypto_orders,
    COUNT(*) FILTER (WHERE direction = 'withdrawal' AND status = 'completed') AS crypto_completed_withdrawal_rows
  FROM crypto_transactions
  GROUP BY CAST(uid AS BIGINT)
)
SELECT TRY_CAST(u.uid AS BIGINT) AS user_key,
  u.account_status,
  COALESCE(f.fiat_orders, 0) AS fiat_orders,
  COALESCE(c.crypto_orders, 0) AS crypto_orders,
  COALESCE(f.fiat_completed_withdrawal_rows, 0) AS fiat_completed_withdrawal_rows,
  COALESCE(c.crypto_completed_withdrawal_rows, 0) AS crypto_completed_withdrawal_rows
FROM users AS u
LEFT JOIN f ON TRY_CAST(u.uid AS BIGINT) = f.user_key
LEFT JOIN c ON TRY_CAST(u.uid AS BIGINT) = c.user_key
ORDER BY u.account_status, user_key;

-- robust_usdt_leave_one_out
.once artifacts/robust_usdt_leave_one_out.csv
WITH per_user AS (
  SELECT CAST(uid AS BIGINT) AS user_key,
    SUM(CASE
      WHEN direction = 'deposit' THEN amount
      WHEN direction = 'withdrawal' THEN -amount
      ELSE NULL
    END) AS net_usdt
  FROM crypto_transactions
  WHERE asset = 'USDT' AND status = 'completed'
  GROUP BY CAST(uid AS BIGINT)
),
total AS (
  SELECT SUM(net_usdt) AS all_user_net_usdt FROM per_user
)
SELECT p.user_key, p.net_usdt, t.all_user_net_usdt,
  t.all_user_net_usdt - p.net_usdt AS net_excluding_user
FROM per_user AS p
CROSS JOIN total AS t
ORDER BY ABS(p.net_usdt) DESC;

-- robust_usdt_status
.once artifacts/robust_usdt_status.csv
SELECT status, direction,
  COUNT(*) AS orders,
  SUM(amount) AS usdt_amount
FROM crypto_transactions
WHERE asset = 'USDT'
GROUP BY status, direction
ORDER BY status, direction;

-- robust_usdt_sum_reconcile
.once artifacts/robust_usdt_sum_reconcile.csv
WITH per_user AS (
  SELECT uid,
    SUM(CASE
      WHEN direction = 'deposit' THEN amount
      WHEN direction = 'withdrawal' THEN -amount
      ELSE NULL
    END) AS net_usdt
  FROM crypto_transactions
  WHERE asset = 'USDT' AND status = 'completed'
  GROUP BY uid
),
source_total AS (
  SELECT SUM(CASE
    WHEN direction = 'deposit' THEN amount
    WHEN direction = 'withdrawal' THEN -amount
    ELSE NULL
  END) AS net_usdt
  FROM crypto_transactions
  WHERE asset = 'USDT' AND status = 'completed'
)
SELECT
  s.net_usdt AS direct_net,
  (SELECT SUM(net_usdt) FROM per_user) AS regrouped_net,
  ABS(s.net_usdt - (SELECT SUM(net_usdt) FROM per_user)) AS absolute_difference
FROM source_total AS s;

-- robust_crossrail_count_reconcile
.once artifacts/robust_crossrail_count_reconcile.csv
WITH f AS (
  SELECT CAST(uid AS BIGINT) AS user_key, COUNT(*) AS n
  FROM fiat_transactions GROUP BY CAST(uid AS BIGINT)
),
c AS (
  SELECT CAST(uid AS BIGINT) AS user_key, COUNT(*) AS n
  FROM crypto_transactions GROUP BY CAST(uid AS BIGINT)
)
SELECT
  (SELECT COUNT(*) FROM fiat_transactions) AS fiat_source_count,
  (SELECT SUM(n) FROM f) AS fiat_grouped_count,
  (SELECT COUNT(*) FROM crypto_transactions) AS crypto_source_count,
  (SELECT SUM(n) FROM c) AS crypto_grouped_count;

-- runtime_verification
.once artifacts/runtime_verification.csv
SELECT version() AS duckdb_version;
