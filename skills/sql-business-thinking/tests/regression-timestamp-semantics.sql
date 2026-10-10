-- Regression: time-format ambiguity + event lifecycle; no external data files.
-- Run: DuckDB -c ".read skills/sql-business-thinking/tests/regression-timestamp-semantics.sql"
-- This tests the *parser invariant*. A separate reviewer must still check
-- that the Skill explicitly withholds time conclusions on unresolved ambiguity.
WITH samples(label,raw_text) AS (
  VALUES
  ('us_only','1/18/2018 0:00'),
  ('eu_only','18/1/2018 0:00'),
  ('ambiguous','3/4/2018 0:00'),
  ('invalid','not-a-date')
), parsed AS (
  SELECT label,
    try_strptime(raw_text,'%m/%d/%Y %H:%M') AS us,
    try_strptime(raw_text,'%d/%m/%Y %H:%M') AS eu
  FROM samples
), classified AS (
  SELECT label,
    CASE
      WHEN us IS NOT NULL AND eu IS NULL THEN 'US_ONLY'
      WHEN us IS NULL AND eu IS NOT NULL THEN 'EU_ONLY'
      WHEN us IS NULL AND eu IS NULL THEN 'INVALID'
      WHEN us<>eu THEN 'AMBIGUOUS'
      ELSE 'SAME_VALUE'
    END AS outcome
  FROM parsed
)
SELECT CASE WHEN
  (SELECT outcome FROM classified WHERE label='us_only')='US_ONLY'
  AND (SELECT outcome FROM classified WHERE label='eu_only')='EU_ONLY'
  AND (SELECT outcome FROM classified WHERE label='ambiguous')='AMBIGUOUS'
  AND (SELECT outcome FROM classified WHERE label='invalid')='INVALID'
THEN 'PASS' ELSE error('date format ambiguity regression failed') END AS parse_test,
CASE WHEN
  try_strptime('4/1/2018 0:00','%m/%d/%Y %H:%M') < TIMESTAMP '2018-04-03 09:00:00'
  AND try_strptime('4/4/2018 10:00','%m/%d/%Y %H:%M') > TIMESTAMP '2018-04-03 09:00:00'
THEN 'PASS' ELSE error('event lifecycle timestamp regression failed') END AS lifecycle_test;
