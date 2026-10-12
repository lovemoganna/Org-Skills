#!/usr/bin/env python3
"""第二篇真实无代码知识笔记：严格增量、原文保留、链接保真、虚假结论反例。"""
from __future__ import annotations
import copy, json, re, subprocess, sys, tempfile
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
REPO=BASE.parents[3]
src=(BASE/"source.org").read_text(encoding="utf-8")
new=(BASE/"draft.next.org").read_text(encoding="utf-8")
anchor="* 验证边界\n"
assert src.count(anchor)==1,"missing target insertion point"
assert new.startswith(src[:src.index(anchor)+len(anchor)])
assert new.endswith(src[src.index(anchor)+len(anchor):])
added=new[len(src[:src.index(anchor)+len(anchor)]):].split(src[src.index(anchor)+len(anchor):],1)[0]
assert new.replace(added,"",1)==src
assert added.startswith("〔补〕")
assert "仓库版本已经变化" in added and "固定当前仓库提交" in added
assert "main" in added and "11 个条目" in added
assert "=SKILL.md=" in added and "=main=" in added
assert not re.search(r"`[^`]+`", added), "Org 增量禁止 Markdown 行内代码反引号"
assert 0<len(added)<300,(len(added),added)
assert new.count("〔补〕")==src.count("〔补〕")+1
assert not re.search(r"(?im)^#\+begin_src",src)
assert not re.search(r"(?im)^#\+begin_src",new)
for label in ("#+WIKI_ID:", "#+INGEST_ID:", "#+WIKI_STATUS:", "#+SOURCE:", "#+FILETAGS:"):
    s=next((x for x in src.splitlines() if x.startswith(label)),None)
    d=next((x for x in new.splitlines() if x.startswith(label)),None)
    assert s==d and s is not None,(label,s,d)
for item in re.findall(r"\[\[[^\n]+?\]\]",src): assert new.count(item)>=src.count(item)
for h in re.findall(r"^\*+ .+$",src,flags=re.M): assert new.count(h)>=src.count(h)
for row in [v for v in src.splitlines() if v.startswith("|")]: assert row in new
structure=REPO/"skills"/"note-reforge"/"tests"/"check_org_output.py"
with tempfile.TemporaryDirectory() as td:
    p=Path(td);indexed=p/"published";drafts=p/"drafts";indexed.mkdir();drafts.mkdir()
    source_file=indexed/"source.org";new_file=drafts/"draft.next.org"
    source_file.write_text(src,encoding="utf-8");new_file.write_text(new,encoding="utf-8")
    chk=subprocess.run([sys.executable,str(structure),str(source_file),str(new_file),"--indexed-root",str(indexed)],capture_output=True,text=True)
    assert chk.returncode==0,(chk.stdout,chk.stderr)
case=json.loads((BASE/"case.json").read_text(encoding="utf-8"))
evaluator=ROOT/"scripts"/"evaluate_case.py"
def judge(x):
    with tempfile.NamedTemporaryFile(mode="w",suffix=".json",encoding="utf-8",delete=False) as tmp:
        p=Path(tmp.name);p.write_text(json.dumps(x,ensure_ascii=False))
    try:
        r=subprocess.run([sys.executable,str(evaluator),str(p)],capture_output=True,text=True)
        return r.returncode,json.loads(r.stdout)
    finally: p.unlink(missing_ok=True)
code,verdict=judge(case)
assert code==2 and verdict["判定"]=="有条件通过",(code,verdict)
wrong=copy.deepcopy(case);wrong["scope"]["task_capabilities"]=["可执行代码教程"]
assert judge(wrong)[1]["判定"]=="测试设计无效"
false=copy.deepcopy(case);false["content"]["grounding"]={"status":"失败","evidence":"模拟将2026-10-09的旧版11项冒充今天已完整核验的清单"}
assert judge(false)[0]==1
self=copy.deepcopy(case)
for k in self["content"]: self["content"][k]["status"]="通过"
assert judge(self)[1]["判定"]=="有条件通过"
print(json.dumps({"结果":"第二个真实样本结构与异常回归通过","被测文章":"Skill选择索引","原文字符数":len(src),"草稿字符数":len(new),"增幅百分比":round((len(new)/len(src)-1)*100,2),"新增字符":len(added),"表格行数":len([v for v in src.splitlines() if v.startswith("|")]),"原始链接数":len(re.findall(r"\[\[[^\n]+?\]\]",src)),"正式发布":"未执行","内容独立评审":"未执行","裁决":verdict["判定"]},ensure_ascii=False,indent=2))
