#!/usr/bin/env python3
"""Dual Skill split contracts: offline deterministic regression, no external data reads."""
from pathlib import Path
import json
import re
import sqlite3

ROOT=Path(__file__).resolve().parents[3]
a=(ROOT/"skills/business-reasoning/SKILL.md").read_text(encoding="utf-8")
b=(ROOT/"skills/analysis-verifier/SKILL.md").read_text(encoding="utf-8")
router=(ROOT/"skills/sql-business-thinking/SKILL.md").read_text(encoding="utf-8")
legacy=(ROOT/"skills/sql-business-thinking/legacy/SKILL.md").read_text(encoding="utf-8")
assert a.startswith("---\nname: business-reasoning\n")
assert b.startswith("---\nname: analysis-verifier\n")
assert router.startswith("---\nname: sql-business-thinking\n")
assert "Dataset-to-Report Autopilot" in legacy
assert len(router)<1700, "legacy execution contract accidentally active"
for token in ("业务", "结果表", "一行", "哪个表", "取什么", "条件", "Analysis Packet", "竞争解释", "REJECTED", "UNVERIFIED"):
    assert token in a, "A misses core thinking action: "+token
for token in ("Analysis Packet","Verification Feedback","JOIN","read_xlsx","原始 XLSX URL","REJECTED","UNRESOLVED","BLOCKED","净流量","反馈"):
    assert token in b, "B missing verification boundary: "+token
for token in ("packet_id","revision","data_contract_ref","business_goal","question","decision_branches","result_grain","source_candidates","candidate_sql_or_probe"):
    assert token in a, "analysis packet missing: "+token
for token in ("packet_id","revision","verdict","execution_receipt","counterevidence","root_cause","minimal_correction","next_test"):
    assert token in b, "verification feedback missing: "+token
for f in (a,b):
    assert "Dashboard" in f and "不" in f, "presentation boundary missing"
    assert "D01–D23" in f, "legacy stage exclusion missing"
for path in ("skills/business-reasoning/SKILL.md","skills/analysis-verifier/SKILL.md"):
    assert path in (ROOT/"README.md").read_text(encoding="utf-8")
# Negative control: two fiat rows and three crypto rows under same UID; direct JOIN amplifies.
db=sqlite3.connect(":memory:")
db.executescript("""
CREATE TABLE fiat(uid INTEGER, amount INTEGER);
CREATE TABLE crypto(uid INTEGER, amount INTEGER);
INSERT INTO fiat VALUES(7,10),(7,20);
INSERT INTO crypto VALUES(7,100),(7,200),(7,300);
""")
bad=db.execute("SELECT COUNT(*),SUM(f.amount),SUM(c.amount) FROM fiat f JOIN crypto c USING(uid)").fetchone()
good=db.execute("""WITH f AS(SELECT uid,SUM(amount) x FROM fiat GROUP BY uid),
 c AS(SELECT uid,SUM(amount) y FROM crypto GROUP BY uid)
 SELECT x,y FROM f JOIN c USING(uid)""").fetchone()
assert bad==(6,90,1200), bad
assert good==(30,600), good
print(json.dumps({"case":"uid_join_fanout","naive_rows":bad[0],"naive_fiat_sum":bad[1],"correct_fiat_sum":good[0],"outcome":"PASS","claim":"fixture-only; not a DuckDB or live workbook run"}))
# Question-level adversarial checks: no cross-currency net, no balance inference.
for value in ("跨币种相加","净流量","余额"):
    assert value in a+b, "semantic negative control not guarded: "+value
print("DUAL_SPLIT_STATIC_AND_SYNTHETIC_PASS")
