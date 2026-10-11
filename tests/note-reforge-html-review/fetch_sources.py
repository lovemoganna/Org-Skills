#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

here=Path(__file__).resolve().parent
manifest=json.loads((here/"manifest.json").read_text(encoding="utf-8"))
output=[]
for x in manifest:
    url="https://raw.githubusercontent.com/"+x["repo"]+"/"+x["ref"]+"/"+urllib.parse.quote(x["path"],safe="/")
    req=urllib.request.Request(url,headers={"User-Agent":"note-reforge-heldout-review/1.0"})
    with urllib.request.urlopen(req,timeout=40) as response:
        raw=response.read()
    git_hash=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if git_hash!=x["sha"]:
        raise RuntimeError("source SHA mismatch for "+x["id"]+" "+git_hash+" != "+x["sha"])
    text=raw.decode("utf-8")
    if re.search(r"(?im)^#\+begin_src",text) or re.search(r"(?im)^\x60{3}\s*(python|js|javascript|shell|bash|sql)",text):
        raise RuntimeError("Noncode scope violation: "+x["id"])
    output.append({**x,"url":url,"text":text,"characters":len(text),"source_verified":True})
    print(x["id"],x["topic"],len(raw),"bytes",git_hash,"OK")
(here/"sources.json").write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
print("SIX_SOURCE_CAPTURED_AND_VERIFIED")
