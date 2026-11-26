"""Check employer Greenhouse listings against their live public application schema."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import html
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener

BOARDS = {"job-boards.greenhouse.io", "job-boards.eu.greenhouse.io", "boards.greenhouse.io"}
API = "boards-api.greenhouse.io"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def identity(value):
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        url = urlsplit(value)
    except ValueError:
        return None
    if url.scheme != "https" or url.netloc not in BOARDS:
        return None
    match = re.fullmatch(r"/([a-zA-Z0-9_-]{1,80})/jobs/([0-9]{1,16})/?", url.path)
    return (match[1].lower(), match[2]) if match else None


def fetch_json(url):
    try:
        with build_opener(NoRedirect).open(url, timeout=8) as response:
            content = response.read(1_000_001)
        if len(content) > 1_000_000:
            return url, None, "RESPONSE_TOO_LARGE"
        return url, json.loads(content), None
    except HTTPError as exc:
        return url, None, f"HTTP_{exc.code}"
    except (URLError, TimeoutError, ValueError):
        return url, None, "ATS_UNAVAILABLE"


def fetch(board, job):
    return fetch_json(f"https://{API}/v1/boards/{board}/jobs/{job}?questions=true&content=true")


def board_jobs(board):
    return fetch_json(f"https://{API}/v1/boards/{board}/jobs")


def terms(value):
    if not isinstance(value,list) or not 1 <= len(value) <= 12 or any(
        not isinstance(item,str) or not 1 <= len(item.strip()) <= 80 for item in value
    ):
        raise ValueError("expected 1..12 bounded search terms")
    return [item.strip().casefold() for item in value]


def verify(results, titles, locations, responsibilities, limit, fetch_job=fetch, fetch_board=board_jobs, exclude_titles=None):
    if type(limit) is not int or not 1 <= limit <= 15 or not isinstance(results,list) or len(results) > 60:
        raise ValueError("unsupported candidate count")
    title_terms, location_terms, duty_terms=map(terms,(titles,locations,responsibilities))
    excluded = terms(exclude_titles) if exclude_titles else []
    ids = list(dict.fromkeys(key for row in results if isinstance(row,dict)
                             and (key := identity(row.get("url")))))
    def matches(target, needles):
        return any(term in target.casefold() for term in needles)

    def title_matches(title):
        return matches(title,title_terms) and not matches(title,excluded)

    def check(key):
        board, job=key
        url,data,error=fetch_job(board,job)
        entry={"key":list(key),"api":url}
        if error:
            return dict(entry,reason=error)
        if not isinstance(data,dict) or str(data.get("id"))!=job or identity(data.get("absolute_url"))!=key:
            return dict(entry,reason="IDENTITY_MISMATCH")
        title=data.get("title")
        place=data.get("location")
        loc=place.get("name") if isinstance(place,dict) else None
        if not isinstance(title,str) or not isinstance(loc,str) or len(title)>240 or len(loc)>400:
            return dict(entry,reason="TITLE_OR_LOCATION_UNAVAILABLE")
        if not title_matches(title) or not matches(loc,location_terms):
            return dict(entry,reason="TITLE_OR_LOCATION_OUT_OF_SCOPE")
        questions=data.get("questions")
        if not isinstance(questions,list) or not questions or not any(q.get("fields") for q in questions if isinstance(q,dict)):
            return dict(entry,reason="APPLICATION_SCHEMA_UNAVAILABLE")
        body=" ".join(re.sub(r"<[^>]+>", " ",html.unescape(html.unescape(str(data.get("content",""))))).split())
        location=next(term for term in location_terms if term in loc.casefold())
        duty=next((term for term in duty_terms if term in body.casefold()),None)
        if duty is None:
            return dict(entry,reason="DUTY_EVIDENCE_UNAVAILABLE")
        at=body.casefold().find(duty)
        return dict(entry,role={"board":board,"job_id":job,"title":title,"location":loc,
            "url":data["absolute_url"],"duty_excerpt":body[max(0,at-70):at+len(duty)+90],
            "matched_location":location,"application_questions":len(questions)})
    fallbacks=[]
    with ThreadPoolExecutor(max_workers=5) as pool:
        checks=list(pool.map(check,ids[:25]))
        # A search index can lag the employer board. Derive replacements from the
        # same observed boards and verify each distinct substitute independently.
        if sum("role" in c for c in checks)<limit:
            boards=list(dict.fromkeys(board for board,_ in ids))[:3]
            for board,(api,data,error) in zip(boards,pool.map(fetch_board,boards)):
                jobs=data.get("jobs",[]) if isinstance(data,dict) else []
                substitute=[]
                known=set(ids)
                for job in jobs:
                    if not isinstance(job,dict):
                        continue
                    key=identity(job.get("absolute_url"))
                    title=job.get("title")
                    place=job.get("location")
                    loc=place.get("name") if isinstance(place,dict) else None
                    if key and key[0]==board and key not in known and isinstance(title,str) and isinstance(loc,str) and title_matches(title) and matches(loc,location_terms):
                        substitute.append(key)
                        known.add(key)
                    if len(substitute)>=8:
                        break
                fallbacks.append({"api":api,"board":board,"error":error,"candidates":[list(key) for key in substitute]})
                checks.extend(pool.map(check,substitute))
                if sum("role" in c for c in checks)>=limit:
                    break
    return {"checked_at":datetime.now(timezone.utc).isoformat(),
            "attempts":checks,"fallback_boards":fallbacks,
            "roles":[c["role"] for c in checks if "role" in c][:limit]}


if __name__ == "__main__":
    print(json.dumps(verify(**json.load(sys.stdin)),ensure_ascii=False))
