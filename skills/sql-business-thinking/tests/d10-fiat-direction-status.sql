-- D10 design only: do not execute until D11.
-- Source: D01-authorized fiat_transactions view created from read_xlsx.
-- Grain: one output row per direction; each input row is one fiat order.
-- Scope: all authorized fiat transaction records, no date filter.
WITH per_direction AS (
    SELECT
        direction,
        COUNT(*) AS total_order_records,
        COUNT(*) FILTER (WHERE status = 'completed') AS completed_records,
        COUNT(*) FILTER (
            WHERE status IN ('pending', 'processing')
        ) AS in_progress_records,
        COUNT(*) FILTER (
            WHERE status IN ('failed', 'cancelled')
        ) AS terminal_noncompleted_records,
        COUNT(*) FILTER (
            WHERE status IS NULL
               OR status NOT IN ('completed', 'pending', 'processing', 'failed', 'cancelled')
        ) AS unknown_status_records
    FROM fiat_transactions
    GROUP BY direction
)
SELECT
    direction,
    total_order_records,
    completed_records,
    in_progress_records,
    terminal_noncompleted_records,
    unknown_status_records,
    CAST(completed_records AS DOUBLE)
        / NULLIF(total_order_records, 0) AS completed_state_share
FROM per_direction
ORDER BY direction;
