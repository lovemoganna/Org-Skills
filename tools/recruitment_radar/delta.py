"""Fail-closed delta planner for overseas crypto risk recruitment.
Input: host-provided live Google Sheets rows and independently verified ATS records.
Output: a write PLAN. It never calls an API or declares a spreadsheet write complete.
"""
import json, re, sys
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
SHEET_ID="1861gbbpr23WhS08VM1zZUBusWxUHm3RclVes7tgWXZ8"
HEADER=["唯一键(Job ID/规范化)","公司","招聘主体","岗位","方向","城市/地区","办公方式","大陆雇佣资格","来源平台","官方申请链接","其他原始链接","首次发布日期","日期口径/来源","首次发现(北京)","最近核验(北京)","申请状态","增量类型","证据/限制","投递优先级","投递状态","备注"]
LOG_HEADER=["北京时间","唯一键","公司","岗位","变化类型","旧值","新值","证据链接","证据日期及口径","是否推送","核验备注"]
MATERIAL={5:"城市/地区",6:"办公方式",7:"大陆雇佣资格",9:"官方申请链接",15:"申请状态"}
PROTECTED={18,19,20}
BOARDS={"job-boards.greenhouse.io","job-boards.eu.greenhouse.io","boards.greenhouse.io"}
def url_clean(s):
    p=urlsplit(s)
    if p.scheme!="https" or not p.hostname or p.username or p.password: raise ValueError("HTTPS URL required")
    query=[(k,v) for k,v in parse_qsl(p.query,keep_blank_values=True) if not k.lower().startswith(("utm_","gh_src","trk","fbclid","gclid","referrer","source"))]
    return urlunsplit(("https",p.hostname.lower().removeprefix("www."),p.path.rstrip("/") or "/",urlencode(query),""))
def job_key(c):
    company=re.sub(r"[^\w]+","",str(c.get("company","")).casefold())
    if not company: return None
    u=c.get("official_url")
    if not u: return None
    p=urlsplit(url_clean(u))
    if p.hostname in BOARDS:
        m=re.fullmatch(r"/[A-Za-z0-9_-]+/jobs/(\d+)",p.path)
        if m:return company+"|"+m[1]
    if p.hostname=="jobs.lever.co":
        m=re.fullmatch(r"/[A-Za-z0-9_-]+/([a-fA-F0-9-]{36})",p.path)
        if m:return company+"|"+m[1].lower()
    stable=c.get("verified_job_id","")
    if re.fullmatch(r"[\w-]{5,100}",stable):return company+"|"+stable.lower()
    return None
def plan(data):
    if data.get("spreadsheet_id")!=SHEET_ID:raise ValueError("target spreadsheet mismatch")
    main,log=data["main_rows"],data["change_rows"]
    if main[0][:21]!=HEADER or log[0][:11]!=LOG_HEADER:raise ValueError("schema mismatch")
    index={}
    for i,row in enumerate(main[1:],2):
        if not any(row):continue
        key=str(row[0]).lower().strip()
        if not key or key in index:return {"status":"BLOCKED_BASELINE","writes":[],"reason":"missing/duplicate key"}
        index[key]=(i,row+[""]*(21-len(row)))
    prior={str(k).lower() for k in data.get("historical_keys",[])}
    complete=data.get("historical_complete") is True
    events=[];review=[];seen=set()
    for c in data.get("candidates",[]):
        try:key=job_key(c)
        except ValueError:key=None
        if not key:review.append({"reason":"UNVERIFIED_JOB_ID"});continue
        if key in seen:continue
        seen.add(key)
        aliases={key}|{a.lower() for a in c.get("historical_aliases",[])}
        matches=[(k,index[k]) for k in aliases if k in index]
        if len(matches)>1:review.append({"key":key,"reason":"AMBIGUOUS_MATCH"});continue
        if c.get("official_status")!="open" or c.get("application_verified") is not True:
            review.append({"key":key,"reason":"APPLY_NOT_VERIFIED"});continue
        if not (c.get("evidence_url") and c.get("checked_at_beijing")):
            review.append({"key":key,"reason":"MISSING_EVIDENCE"});continue
        url=url_clean(c["official_url"])
        if matches:
            oldkey,(rownum,row)=matches[0]
            if not c.get("prior_comparable_evidence"):
                review.append({"key":key,"reason":"NO_PRIOR_SNAPSHOT"});continue
            vals={5:c.get("location"),6:c.get("work_mode"),7:c.get("mainland_eligibility"),9:url,15:"官方申请入口开放"}
            changes=[]
            for col,label in MATERIAL.items():
                new=vals[col];old=row[col]
                proof=c.get("material_changes",{}).get(label)
                if new is not None and str(new)!=str(old) and isinstance(proof,dict) and proof.get("before")==old and proof.get("after")==new:
                    changes.append({"row":rownum,"column":col,"old":old,"new":new,"label":label})
            if changes:events.append({"type":"CHANGE","key":oldkey,"changes":changes,"source":c["evidence_url"],"timestamp":c["checked_at_beijing"]})
            else:review.append({"key":key,"reason":"NO_VERIFIED_CHANGE"})
        elif aliases & prior or (not complete and not (
            c.get("newness_basis")=="official_first_published"
            and c.get("first_published_source")=="official_ats"
            and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",str(c.get("first_published",""))))
            and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}",str(c.get("historical_last_push_date",""))))
            and c["first_published"] > c["historical_last_push_date"]
        )):
            review.append({"key":key,"reason":"INCOMPLETE_HISTORY_OR_NO_AUTHORITATIVE_NEWNESS"})
        elif c.get("newness_basis") not in ("official_first_published","proven_absent_prior_snapshot") or not c.get("newness_evidence_url"):
            review.append({"key":key,"reason":"NEWNESS_UNVERIFIED"})
        else:
            row=[key,c["company"],c.get("employer","待核实"),c.get("title",""),c.get("direction",""),c.get("location",""),c.get("work_mode",""),c.get("mainland_eligibility","待确认"),c.get("source","官方ATS"),url,c.get("original_url",""),c.get("first_published",""),c.get("date_basis","首发未知"),c["checked_at_beijing"],c["checked_at_beijing"],"官方申请入口开放","证实新增",c.get("limitations",""),"","未投递",""]
            events.append({"type":"NEW","key":key,"row":row,"source":c["evidence_url"],"timestamp":c["checked_at_beijing"]})
    return {"status":"PLANNED_NOT_WRITTEN" if events else "NO_PROVEN_DELTA","existing_count":len(index),"writes":events,"review":review,"protected_columns":sorted(PROTECTED),"readback_required":True}
if __name__=="__main__":print(json.dumps(plan(json.load(sys.stdin)),ensure_ascii=False,indent=2))
