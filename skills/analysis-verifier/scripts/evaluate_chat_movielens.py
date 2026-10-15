#!/usr/bin/env python3
"""Chat-requested second-domain SQL experiment, no model API.

Source: official GroupLens ml-100k, licensed research benchmark.
The SQL arms are hand-authored in one chat context: not isolated-model A/B.
Only derived aggregate receipts are uploaded; NEVER redistribute source data.
"""
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import urllib.request
import zipfile
from collections import Counter

import duckdb

OUT=Path(sys.argv[1] if len(sys.argv)>1 else "movielens-eval")
OUT.mkdir(parents=True,exist_ok=True)
BASE="https://files.grouplens.org/datasets/movielens/ml-100k.zip"
def grab(url,limit):
    req=urllib.request.Request(url,headers={"User-Agent":"sql-quality-research-eval/1.0"})
    with urllib.request.urlopen(req,timeout=50) as resp:
        data=resp.read(limit+1)
    if not data or len(data)>limit: raise ValueError("SOURCE_UNAVAILABLE_OR_TOO_LARGE")
    return data
md5_text=grab(BASE+".md5",10000).decode("ascii","replace")
m=re.search(r"(?<![a-fA-F0-9])([a-fA-F0-9]{32})(?![a-fA-F0-9])",md5_text)
if not m: raise ValueError("PUBLISHER_CHECKSUM_MISSING")
archive=grab(BASE,12_000_000)
archive_md5=hashlib.md5(archive).hexdigest()
if archive_md5.lower()!=m.group(1).lower(): raise ValueError("PUBLISHER_CHECKSUM_MISMATCH")
sha=hashlib.sha256(archive).hexdigest()
with zipfile.ZipFile(io.BytesIO(archive)) as z:
    desired=["ml-100k/u.data","ml-100k/u.item","ml-100k/u.user"]
    for name in desired:
        if name not in z.namelist() or z.getinfo(name).file_size>3_000_000:
            raise ValueError("BAD_ARCHIVE_ENTRY:"+name)
    rb=z.read(desired[0]); mb=z.read(desired[1]); ub=z.read(desired[2])
rating_path=OUT/"u.data"
rating_path.write_bytes(rb) # ephemeral runner only; never an artifact
genres=["unknown","Action","Adventure","Animation","Children","Comedy","Crime","Documentary","Drama","Fantasy","Film-Noir","Horror","Musical","Mystery","Romance","Sci-Fi","Thriller","War","Western"]
movie_rows=[]; genre_rows=[]
for line in mb.decode("latin-1").splitlines():
    parts=line.split("|")
    if len(parts)!=24: raise ValueError("MOVIE_SCHEMA_MISMATCH")
    mid=int(parts[0])
    bits=[int(x) for x in parts[5:]]
    if any(x not in (0,1) for x in bits):raise ValueError("INVALID_GENRE_FLAG")
    tags=[g for g,bit in zip(genres,bits) if bit]
    movie_rows.append((mid,parts[1],len(tags)))
    for g in tags: genre_rows.append((mid,g))
user_ids=[int(ln.split("|")[0]) for ln in ub.decode("latin-1").splitlines()]
if len(set(user_ids))!=len(user_ids):raise ValueError("DUPLICATE_USER")
movies_file=OUT/"movies-slim.csv"; genres_file=OUT/"genres-slim.csv"
for path,head,vals in [(movies_file,["movie_id","title","genre_count"],movie_rows),
                       (genres_file,["movie_id","genre"],genre_rows)]:
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(head);w.writerows(vals)
source={"publisher":"GroupLens University of Minnesota","data_url":BASE,
        "publisher_md5":archive_md5,"archive_sha256":sha,
        "rated_rows_source":len(rb.splitlines()),"movies":len(movie_rows),
        "users":len(user_ids),"genre_edges":len(genre_rows),
        "dataset_period":"1997-09-19 through 1998-04-22 per publisher",
        "source_license":"research use; do not redistribute source data"}
def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+"\n",encoding="utf-8")
save("source-receipt.json",source)
db=OUT/"movielens.duckdb"
if db.exists():db.unlink()
with duckdb.connect(str(db)) as c:
    assert duckdb.__version__=="1.4.2"
    c.execute("""CREATE TABLE ratings AS SELECT CAST(column0 AS INTEGER) user_id,
            CAST(column1 AS INTEGER) movie_id, CAST(column2 AS INTEGER) rating,
            CAST(column3 AS BIGINT) rating_unix
            FROM read_csv(?,header=false,delim='\\t',auto_detect=true)""",[str(rating_path)])
    c.execute("CREATE TABLE movies AS SELECT * FROM read_csv(?,header=true)",[str(movies_file)])
    c.execute("CREATE TABLE movie_genres AS SELECT * FROM read_csv(?,header=true)",[str(genres_file)])
    qa_sql="""SELECT COUNT(*) AS ratings,
      COUNT(DISTINCT user_id) AS rating_users,
      COUNT(DISTINCT movie_id) AS rated_movies,
      COUNT(*)-COUNT(DISTINCT CAST(user_id AS VARCHAR)||':'||CAST(movie_id AS VARCHAR)) AS duplicate_user_movie,
      COUNT(*) FILTER(WHERE rating<1 OR rating>5 OR rating IS NULL) AS bad_ratings,
      COUNT(*) FILTER(WHERE movie_id NOT IN (SELECT movie_id FROM movies)) AS orphan_ratings
      FROM ratings"""
    col=[x[0] for x in c.execute(qa_sql).description]
    qa=dict(zip(col,c.execute(qa_sql).fetchone()))
    q2="""SELECT COUNT(*) AS joined_rows,
      COUNT(DISTINCT r.user_id||':'||r.movie_id) AS distinct_rating_keys
      FROM ratings r JOIN movie_genres g USING(movie_id)"""
    keys=[x[0] for x in c.execute(q2).description]
    fanout=dict(zip(keys,c.execute(q2).fetchone()))
    assert qa["ratings"]==100000 and qa["rating_users"]==943 and len(movie_rows)==1682
    assert qa["duplicate_user_movie"]==0 and qa["orphan_ratings"]==0 and qa["bad_ratings"]==0
    assert fanout["joined_rows"]>qa["ratings"]
    source["db_version"]=duckdb.__version__
    save("source-receipt.json",source)
    # OLD: faithfully useful raw mean PLUS sample size (not artificially incompetent).
    old_sql="""SELECT r.movie_id,m.title,COUNT(*) rating_count,
       ROUND(AVG(r.rating),4) avg_rating
       FROM ratings r JOIN movies m USING(movie_id)
       GROUP BY r.movie_id,m.title
       ORDER BY avg_rating DESC,rating_count DESC,r.movie_id LIMIT 20"""
    # NEW: same observable movie grain, shrink tiny samples toward overall rating.
    # k=20 is an analyst's illustrative sensitivity parameter, NOT a platform policy.
    new_sql="""WITH t AS(
       SELECT movie_id,COUNT(*) AS n,SUM(rating)::DOUBLE AS score_sum
       FROM ratings GROUP BY movie_id
       ), global AS(SELECT AVG(rating) overall_mean FROM ratings)
       SELECT t.movie_id,m.title,n rating_count,
              ROUND(score_sum/n,4) avg_rating,
              ROUND((score_sum+20*global.overall_mean)/(n+20),4) shrunk_mean
       FROM t JOIN movies m USING(movie_id) CROSS JOIN global
       ORDER BY shrunk_mean DESC,n DESC,t.movie_id LIMIT 20"""
    def query(sql):
        r=c.execute(sql);return [dict(zip([x[0] for x in r.description],row)) for row in r.fetchall()]
    old=query(old_sql);new=query(new_sql)
    # Verifier does NOT take top-20 result as its source; aggregates all raw ratings again.
    verify=query("""SELECT movie_id,COUNT(DISTINCT user_id) AS n,
        SUM(CAST(rating AS BIGINT)) AS raw_sum,AVG(CAST(rating AS DOUBLE)) AS avg_rating
        FROM ratings GROUP BY movie_id ORDER BY movie_id""")
    assert len(verify)==qa["rated_movies"]
    byid={int(x["movie_id"]):x for x in verify}
    overall=float(c.execute("SELECT SUM(CAST(rating AS BIGINT))*1.0/COUNT(*) FROM ratings").fetchone()[0])
    # Truly independent source-level holdout: direct TSV parser, no SQL / DuckDB.
    from collections import defaultdict
    counts=Counter();sums=Counter();pair_seen=set();raw_n=0;total_score=0
    for row in csv.reader(io.StringIO(rb.decode("ascii")),delimiter="\t"):
        if len(row)!=4: raise ValueError("RAW_TSV_SHAPE")
        uid,mid,rating,ts=map(int,row)
        if (uid,mid) in pair_seen: raise ValueError("RAW_DUPLICATE_RATING_KEY")
        pair_seen.add((uid,mid))
        if rating not in (1,2,3,4,5): raise ValueError("RAW_BAD_RATING")
        counts[mid]+=1;sums[mid]+=rating;raw_n+=1;total_score+=rating
    assert raw_n==qa["ratings"] and len(counts)==qa["rated_movies"]
    independent_global=total_score/raw_n
    assert abs(overall-independent_global)<1e-11
    for mid,v in byid.items():
        assert v["n"]==counts[mid] and v["raw_sum"]==sums[mid]
    # An intentionally corrupted held-out metric must be rejected.
    def independent_score_matches(x):
        mid=int(x["movie_id"])
        if x["rating_count"]!=counts[mid]:return False
        if abs(x["avg_rating"]-sums[mid]/counts[mid])>0.000051:return False
        if "shrunk_mean" in x:
            expected=(sums[mid]+20*independent_global)/(counts[mid]+20)
            return abs(x["shrunk_mean"]-expected)<=0.000051
        return True
    assert all(independent_score_matches(x) for x in old+new)
    altered=dict(new[0],shrunk_mean=new[0]["shrunk_mean"]+0.1)
    assert not independent_score_matches(altered), "mutated score incorrectly accepted"
    for rows in (old,new):
        for row in rows:
            v=byid[int(row["movie_id"])]
            assert row["rating_count"]==v["n"] and abs(row["avg_rating"]-v["avg_rating"])<0.000051
            if "shrunk_mean" in row:
                expected=(v["raw_sum"]+20*overall)/(v["n"]+20)
                assert abs(row["shrunk_mean"]-expected)<0.000051
    tiny=query("""SELECT COUNT(*) AS rated_movies,
      COUNT(*) FILTER(WHERE n<5) AS n_below_5,
      COUNT(*) FILTER(WHERE n<20) AS n_below_20,
      COUNT(*) FILTER(WHERE n>=50) AS n_at_least_50,
      COUNT(*) FILTER(WHERE a=5.0 AND n<=2) AS five_stars_with_at_most_two_ratings
      FROM (SELECT movie_id,COUNT(*) n,AVG(rating) a FROM ratings GROUP BY movie_id)""")[0]
    # Sensitivity diagnostic: at least 20 / 50 ratings, and shrink prior 20 vs 50.
    sensitivity=query("""WITH t AS (SELECT movie_id,COUNT(*) n,SUM(rating) s FROM ratings GROUP BY movie_id),
    g AS(SELECT AVG(rating) mean FROM ratings)
    SELECT
      arg_max(movie_id,(s+20*g.mean)/(n+20)) AS best_shrink_20_id,
      arg_max(movie_id,(s+50*g.mean)/(n+50)) AS best_shrink_50_id,
      arg_max(movie_id,CASE WHEN n>=20 THEN s*1.0/n END) AS best_min20_id,
      arg_max(movie_id,CASE WHEN n>=50 THEN s*1.0/n END) AS best_min50_id
    FROM t CROSS JOIN g""")[0]
    # Independent genre-grain reconciliation: each movie can have more than one genre.
    genre_sql="""SELECT COUNT(*) AS expanded_ratings
       FROM ratings JOIN movie_genres USING(movie_id)"""
    expanded=c.execute(genre_sql).fetchone()[0]
    assert expanded==fanout["joined_rows"]
    # Asymmetric temporal metadata missingness is a policy issue not a popularity signal.
    # Genre uses multiple labels, not a partition of movie universe.
    severity={
       "naive_genre_total_would_exceed_ratings":expanded-qa["ratings"],
       "naive_genre_sum_is_invalid":True,
       "single_rating_five_star_count":tiny["five_stars_with_at_most_two_ratings"],
       "invalid_inference":"High sample mean does not imply overall audience satisfaction, reach, conversion, or platform demand.",
    }
    # Negative controls intentionally WRONG, separate from both legitimate SQL arms.
    negatives={
      "genre_join_inflation": {"source_ratings":qa["ratings"],"after_join":expanded,
                               "verdict":"REJECT_NON_ADDITIVE_GENRE_EXPANSION"},
      "one_rating_perfect_score": {"movies_with_avg5_and_n_le2":tiny["five_stars_with_at_most_two_ratings"],
                                    "verdict":"REJECT_AUTOMATIC_TOP_CONTENT_PROMOTION"},
      "filtered_before_join_unknown_movie": {"orphan_ratings":qa["orphan_ratings"],"verdict":"SOURCE_KEYS_PASS"},
      "fake_priority_rule":{"requested_business_threshold":"UNKNOWN","verdict":"BLOCK_UNAUTHORIZED_POLICY"}
    }
    # Portable source authority: scoped QA backed by raw-data and source-receipt.
    materialization="sha256:"+sha
    scope={"grain":"one movie_id","population":"all valid ml-100k movie ratings",
        "time_window":"1997-09-19 to 1998-04-22 historical collection",
        "status_meaning":"1-5 subjective user rating, not commercial sale or full-audience preference",
        "metrics":["rating_count","avg_rating","shrunk_mean"]}
    qa_receipt={"verdict":"PARTIAL","run_id":os.getenv("GITHUB_RUN_ID","LOCAL"),
        "source_id":BASE,"materialization_id":materialization,
        "read_plan_sha256":hashlib.sha256(b"official_zip:ratings+movies+genres:2026-10-15").hexdigest(),
        "qa_receipt_ref":"source-receipt.json","checked_scopes":[scope]}
    finding={k:qa_receipt[k] for k in ("run_id","source_id","materialization_id","read_plan_sha256")}
    finding.update({"verdict":"VERIFIED","packet_id":"MOVIE-RATING-01","revision":1,
       "verified_packet_id":"MOVIE-RATING-01","verified_revision":1,
       "result_receipt_ref":"new-sql-result.json","verification_receipt_ref":"reconciliation.json",
       "scope":scope})
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
    from scope_gate import check_scope
    gate=check_scope(qa_receipt,finding)
    assert gate["verdict"]=="PASS"
    changed=dict(finding,scope=dict(scope,status_meaning="box office sales"))
    rejected=check_scope(qa_receipt,changed)
    assert rejected["verdict"]=="BLOCKED"
    save("baseline-sql-result.json",{"sql":old_sql,"rows":old})
    save("new-sql-result.json",{"sql":new_sql,"rows":new})
    save("reconciliation.json",{"source_qa":qa,"genre_fanout":fanout,
          "movies_count":len(movie_rows),"genre_edges":len(genre_rows),
          "overall_rating":overall,"tiny_sample":tiny,
          "top_old_movie_id":old[0]["movie_id"],"top_new_movie_id":new[0]["movie_id"],
          "top_old_ratings":old[0]["rating_count"],"top_new_ratings":new[0]["rating_count"],
          "sensitivity":sensitivity,"negative_controls":negatives,
          "independent_parser":"Python csv.reader over publisher u.data (not DuckDB table)",
          "independent_source_rows":raw_n,"corrupted_score_negative_test":"REJECTED",
          "scope_pass":gate,"scope_bad":rejected})
    summary={
      "evaluation_type":"same-conversation SQL strategy contrast, not independent model behavior eval",
      "business_question":"Should a media product promote highest-average-rated movies as most liked?",
      "owner_brief":"Measure evidence support and sensitivity. No business action without exposure and randomized impact.",
      "old_skill_arm":"Raw average with review count; correct as descriptive ranking; cannot support a high-confidence launch decision.",
      "new_skill_arm":"Count plus shrinkage prior=20; demonstrates sensitivity to low sample counts. No policy authorization.",
      "source_qa":qa, "raw_top":old[:3],"shrink_top":new[:3],
      "tiny_samples":tiny,"sensitivity":sensitivity,"genre_join_rows":expanded,
      "scope_gate":gate,"negative_gate":rejected,
      "owner_final":"NEEDS_EVIDENCE: Avoid automatic promotion based on unadjusted ratings.",
      "caveats":["MovieLens is a research sample with selected raters; not a streaming service's user base.",
        "Shrinkage prior=20 is an analytical illustration, not a validated ranking algorithm.",
        "The old skill could also use shrinkage; performance improvement caused by skill decomposition is not established.",
        "No source content redistributed."]
    }
    save("summary.json",summary)
    print(json.dumps({"status":"MOVIELENS_PAIRED_SQL_PASS","runtime":"DuckDB "+duckdb.__version__,
       "rating_rows":qa["ratings"],"rated_movies":qa["rated_movies"],
       "raw_top":old[:3],"shrink_top":new[:3],"tiny_samples":tiny,
       "sensitivity":sensitivity,"genre_rows":expanded,
       "scope_gate":gate,"negative_scope_gate":rejected},ensure_ascii=False,default=str))
# Clean ephemeral copies; artifacts must never contain source data.
rating_path.unlink(missing_ok=True)
movies_file.unlink(missing_ok=True)
genres_file.unlink(missing_ok=True)
db.unlink(missing_ok=True)
