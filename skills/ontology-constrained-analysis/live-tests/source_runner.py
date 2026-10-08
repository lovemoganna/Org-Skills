"""Exact locked SQL one-time source load, no analytical queries before ontology Gate 1."""
import csv,hashlib,json,pathlib,time
import duckdb
OUT=pathlib.Path("evidence");OUT.mkdir(exist_ok=True)
ALLOW=("users","fiat_transactions","crypto_transactions","exchange_rates")
URL="https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx"
TEMPLATE="""SELECT *
FROM read_xlsx(
    'https://docs.google.com/spreadsheets/d/1YRLbfW3qCs2PjSjt87-gqWevgkNRGdRqB-21ngGDWSs/export?format=xlsx',
    sheet = 'users',
    header = true
);"""
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 con=duckdb.connect(str(OUT/"snapshot.duckdb"))
 receipt={"status":"UNTESTED","phase":"SOURCE_ONLY","duckdb_version":duckdb.__version__,"source_url":URL,"tables":{},"analysis_sql_before_gate1":0}
 try:
  for q in ("INSTALL httpfs;","LOAD httpfs;","INSTALL excel;","LOAD excel;"): con.execute(q)
  for sheet in ALLOW:
   sql=TEMPLATE if sheet=="users" else TEMPLATE.replace("sheet = 'users'","sheet = '"+sheet+"'")
   cursor=con.execute(sql)
   source_types=[{"name":d[0],"type":str(d[1])} for d in cursor.description]
   batch=cursor.fetchdf()
   con.register("_batch",batch)
   con.execute("CREATE TABLE "+sheet+" AS SELECT * FROM _batch")
   con.unregister("_batch")
   schema=con.execute("DESCRIBE "+sheet).fetchall()
   with (OUT/("schema-"+sheet+".csv")).open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f);w.writerow(["column_name","column_type","null","key","default","extra"]);w.writerows(schema)
   con.execute("COPY (SELECT * FROM "+sheet+") TO '"+(OUT/(sheet+".csv")).as_posix()+"' (HEADER true, DELIMITER ',')")
   count=con.execute("SELECT COUNT(*) FROM "+sheet).fetchone()[0]
   if count!=len(batch):raise RuntimeError("ROW_MISMATCH:"+sheet)
   receipt["tables"][sheet]={"rows":count,"sql":sql,"original_column_types":source_types,"schema_sha256":digest(OUT/("schema-"+sheet+".csv")),"rows_sha256":digest(OUT/(sheet+".csv"))}
  con.execute("CHECKPOINT");con.close()
  receipt["status"]="SOURCE_ONLY_PASS_NOT_GATE1"
  receipt["snapshot_sha256"]=digest(OUT/"snapshot.duckdb")
 except Exception as exc:
  receipt["status"]="BLOCKED";receipt["error"]=repr(exc)
  (OUT/"source-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
  raise
 (OUT/"source-receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
 print(json.dumps({"status":receipt["status"],"rows":{k:v["rows"] for k,v in receipt["tables"].items()},"snapshot_sha256":receipt["snapshot_sha256"]}))
if __name__=="__main__": main()
