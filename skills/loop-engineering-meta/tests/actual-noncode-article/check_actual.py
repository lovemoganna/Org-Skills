#!/usr/bin/env python3
"""真实非代码文章基线/产物校验。结构通过不能冒充知识增量通过。"""
from pathlib import Path
import importlib.util, json, re, subprocess, sys, copy
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
src=(BASE/"published_source"/"source.org").read_text(encoding="utf-8")
draft=(BASE/"drafts"/"draft.next.org").read_text(encoding="utf-8")
anchor="工具决定 Agent 能做什么。反馈决定 Agent 能否知道自己做对了。Tools determine what an Agent can do. Feedback determines whether the Agent can know that it did the work correctly.\n"
start="\n* 故障先查哪一层〔补〕 | Where to Start Diagnosing\n"
assert src.count(anchor)==1
assert draft.count(start)==1
addition=draft[len(src[:src.index(anchor)+len(anchor)]):]
addition=addition.split("\n* 上下文 | Context",1)[0]
assert draft.replace(addition,"",1)==src,"not strictly additive: source material was deleted or modified"
assert not re.search(r"(?im)^#\+begin_src",src),"out of scope: source contains executable Org blocks"
assert draft.count("〔补〕")==1
assert "不是讲者给出的固定流程" in draft and "not a fixed procedure from the speaker" in draft
assert "先核对上下文来源和作用域" in addition and "assertions, and feedback" in addition
assert len(draft)<len(src)*1.17
# Compare all links and publication identity, treating header block and source body separately.
for mark in ("#+WIKI_ID:","#+INGEST_ID:","#+WIKI_STATUS:","#+SOURCE:","#+FILETAGS:"):
    left=next((x for x in src.splitlines() if x.startswith(mark)),None)
    right=next((x for x in draft.splitlines() if x.startswith(mark)),None)
    assert left==right and left is not None,(mark,left,right)
for match in re.findall(r"\[\[[^\n]+?\]\]",src):
    assert match in draft,("lost link",match)
# The published original is in a simulated indexed root; draft must be in sibling isolated folder.
checker=ROOT.parent/"note-reforge"/"tests"/"check_org_output.py"
verify=subprocess.run([sys.executable,str(checker),str(BASE/"published_source"/"source.org"),str(BASE/"drafts"/"draft.next.org"),"--indexed-root",str(BASE/"published_source")],capture_output=True,text=True)
assert verify.returncode==0,(verify.stdout,verify.stderr)
case=json.loads((BASE/"case.json").read_text(encoding="utf-8"))
evaluator=ROOT/"scripts"/"evaluate_case.py"
def run_case(doc):
    p=BASE/"_transient_case.json"
    try:
        p.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
        result=subprocess.run([sys.executable,str(evaluator),str(p)],capture_output=True,text=True)
        return result.returncode,json.loads(result.stdout)
    finally:
        p.unlink(missing_ok=True)
code,verdict=run_case(case)
assert code==2 and verdict["判定"]=="有条件通过",(code,verdict)
bad=copy.deepcopy(case);bad["scope"]["task_capabilities"]=["把代码教程改造成可执行 Org 文学编程"]
code,verdict2=run_case(bad)
assert code==2 and verdict2["判定"]=="测试设计无效" and verdict2["被测对象质量"]=="未评价"
false_claim=copy.deepcopy(case);false_claim["content"]["grounding"]={"status":"失败","evidence":"变异反例：自称来自讲者的官方操作流程（不受原文支持）"}
code,verdict3=run_case(false_claim)
assert code==1 and verdict3["判定"]=="测试失败"
self_grade=copy.deepcopy(case)
for item in self_grade["content"].values(): item["status"]="通过"
code,verdict4=run_case(self_grade)
assert code==2 and verdict4["判定"]=="有条件通过"
missing=copy.deepcopy(case);missing["execution"]["performed"]=False
code,verdict5=run_case(missing)
assert code==2 and verdict5["判定"]=="执行证据不足"
print(json.dumps({"结构检查":"通过","原文完整保留":True,"原文长度":len(src),"草稿长度":len(draft),"内容增幅":round(100*(len(draft)/len(src)-1),2),"新增段落":2,"新增章节":1,"代码块":0,"实际用例判定":"有条件通过","异常反例":{"误派":verdict2["判定"],"编造事实":verdict3["判定"],"仅自审":verdict4["判定"],"无执行":verdict5["判定"]}},ensure_ascii=False,indent=2))
