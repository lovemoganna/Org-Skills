#!/usr/bin/env python3
"""真实第18章重构：对象适配、原始参数、数字证据、来源、反例的客观回归。"""
import json, re, subprocess, sys
from pathlib import Path
base=Path(__file__).resolve().parent
r=base.parent.parent
source=(base/"source.md").read_text(encoding="utf-8")
draft=(base/"draft.next.md").read_text(encoding="utf-8")
meta=json.loads((base/"metadata.json").read_text(encoding="utf-8"))
assert len(source)==meta["input_length"],"source changed"
assert len(draft)==meta["output_length"],"draft changed"
assert source.startswith("第18章 自我迭代：")
assert "第19章" not in source
assert not re.search(r"(?m)^\s*```(?:python|javascript|sql|sh|shell|bash)",source),"wrong noncode task"
for term in ["方法实验记录","个人学习特征反思","年度学习系统复盘","两周","错误率可翻倍","每年","能量节奏","刺激偏好","社交偏好","启动难易","注意稳定性","1—2 小时","20分钟","15分钟"]:
    assert term in draft,("lost a unique source term or parameter",term)
for i in range(1,9):
    q=[line for line in source.splitlines() if line.startswith(f"> **Q18-{i}**")][0]
    assert q in draft,("lost authored exploration prompt",i)
assert draft.count("〔补〕") == 1
assert "不应当作实测规律" in draft and "不能承诺两周必见效" in draft
assert "来源章节没有提供该数值的测量出处" in draft
assert "不支持把所谓固定学习风格" in draft
assert "https://doi.org/10.1111/j.1539-6053.2009.01038.x" in draft
assert "CC BY-NC-SA 4.0" in draft
assert "illustrations/45_五大特质雷达图.svg" in draft
assert "cards/card_方法实验卡.svg" in draft
assert draft.count("# ")==1
case=json.loads((base/"case.json").read_text(encoding="utf-8"))
import tempfile
def evaluate(doc):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"case.json";p.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
        run=subprocess.run([sys.executable,str(r/"scripts/evaluate_case.py"),str(p)],capture_output=True,text=True)
        return run.returncode,json.loads(run.stdout)
status,v=evaluate(case)
assert status==2 and v["判定"]=="有条件通过"
import copy
wrong=copy.deepcopy(case);wrong["scope"]["task_capabilities"]=["可执行代码教程"]
assert evaluate(wrong)[1]["判定"]=="测试设计无效"
fabricated=copy.deepcopy(case);fabricated["content"]["grounding"]={"status":"失败","evidence":"故意变异：把两周与理科错误率翻倍作为已实测普遍定论"}
assert evaluate(fabricated)[1]["判定"]=="测试失败"
self_eval=copy.deepcopy(case)
for k in self_eval["content"]: self_eval["content"][k]["status"]="通过"
assert evaluate(self_eval)[1]["判定"]=="有条件通过"
print(json.dumps({"结果":"客观与变异回归通过","原始字符":len(source),"重写字符":len(draft),"压缩幅度":round((1-len(draft)/len(source))*100,2),"保留提问":8,"原图片引用":2,"裁决":v["判定"],"独立语义评价":"未执行"},ensure_ascii=False))
