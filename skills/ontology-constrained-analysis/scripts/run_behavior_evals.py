#!/usr/bin/env python3
"""Controlled paired model-behavior evals. Never put answer keys in subject prompts.

Plan mode works offline. Real execution requires OPENAI_API_KEY and an explicit --model.
The optional separate model judge is fallible; inspect its raw judgments.
"""
import argparse, json, os, hashlib, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'evals'


def case_refs(ident):
    if ident.startswith(('runtime-', 'blocked-', 'source-', 'url-', 'fixed-', 'reusable-runtime-', 'no-false-completion-')): return ['runtime.md']
    if ident.startswith(('rule-','relation-','aggregation-','multihop-')): return ['ontology.md','lisp.md']
    if ident.startswith(('sql-','question-','signal-','metric-','complex-','competition-','robustness-','dashboard-','multigrain-')): return ['analysis-loop.md','validator.md']
    if ident.startswith(('local-','evidence-','cross-object-')): return ['analysis-loop.md','validator.md']
    return ['validator.md']


def make_subject_context(ident, with_skill):
    if not with_skill:
        return '你是数据分析助手。按用户任务作答。不要假设存在外部文件或数据库。'
    parts=[(ROOT/'SKILL.md').read_text(encoding='utf-8')]
    for name in case_refs(ident):
        parts.append(f'\n# Reference: {name}\n'+(ROOT/'references'/name).read_text(encoding='utf-8'))
    return '\n'.join(parts)


def make_plan(cases):
    return [{'id':c['id'],'variant':v,'prompt':c['prompt'],
             'refs':case_refs(c['id']) if v=='with_skill' else [],
             'has_fixture':bool(c.get('files'))}
            for c in cases for v in ('baseline','with_skill')]


def openai_call(client,model, instructions, prompt, recorder=None):
    started=time.perf_counter()
    try:
        response=client.responses.create(model=model,instructions=instructions,input=prompt)
        if recorder is not None:
            usage=getattr(response,'usage',None)
            recorder['usage']={
                'input_tokens':getattr(usage,'input_tokens',None),
                'output_tokens':getattr(usage,'output_tokens',None),
                'total_tokens':getattr(usage,'total_tokens',None),
            }
        return response.output_text
    finally:
        if recorder is not None:
            recorder['elapsed_seconds']=round(time.perf_counter()-started,6)


def judge(client,model,case,output,recorder=None):
    rubric={'prompt':case['prompt'],'expected_output':case['expected_output'],
           'assertions':case['assertions'],'actual_output':output}
    instr='你是独立评测员。仅根据当前问题、预期要求、实际答案评估每条断言。不要因措辞相近而放行实质错误。只输出JSON对象：{"passed":boolean,"failed_assertions":[string],"rationale":string}。无法判断则passed=false。'
    raw=openai_call(client,model,instr,json.dumps(rubric,ensure_ascii=False),recorder=recorder)
    try:
        text=raw.strip(); text=text[7:-3] if text.startswith('```json') and text.endswith('```') else text
        return json.loads(text)
    except Exception:
        return {'passed':False,'failed_assertions':case['assertions'],'rationale':'judge not parseable','raw_judge':raw}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',action='store_true',help='actually call model API; default is offline plan only')
    parser.add_argument('--model',default=None,help='subject model name (required for --run)')
    parser.add_argument('--judge-model',default=None,help='optional evaluator model; without it results ungraded')
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--output',default=None)
    args=parser.parse_args()
    cases=json.loads((BASE/'quality-evals.json').read_text(encoding='utf-8'))['evals']
    plan=make_plan(cases)
    out=Path(args.output) if args.output else ROOT.parent/'behavior-eval-results.json'
    # Preserve independence: sealed expectations only used AFTER the model responds.
    if not args.run:
        stats={'mode':'OFFLINE_PLAN_ONLY','cases':len(cases),'paired_requests':len(plan)*args.repeat,
               'executed_subject_requests':0,'judged_requests':0,
               'blocked':'No local model endpoint / API credential. Offline mode does not establish model behavior.'}
        # Export prompt/variant plan, not expected answers, separately from the original eval definitions.
        out.write_text(json.dumps({'status':stats,'plan':plan},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(stats,ensure_ascii=False))
        return
    if not os.environ.get('OPENAI_API_KEY') or not args.model:
        raise SystemExit('Blocked: --run requires OPENAI_API_KEY and --model; no fallback or invented results.')
    from openai import OpenAI
    client=OpenAI()
    results=[]
    byid={c['id']:c for c in cases}
    for item in plan:
        for repetition in range(args.repeat):
            ident=item['id'];c=byid[ident]
            record={'id':ident,'variant':item['variant'],'repeat':repetition,'model':args.model}
            try:
                record['subject_call']={}
                text=openai_call(client,args.model,make_subject_context(ident,item['variant']=='with_skill'),c['prompt'],recorder=record['subject_call'])
                record['output_text']=text
                if args.judge_model:
                    record['judge_call']={}
                    record['judge']=judge(client,args.judge_model,c,text,recorder=record['judge_call'])
                else:
                    record['judge']={'status':'NOT_SCORED'}
            except Exception as ex:
                record['error']=str(ex)[:400]
            results.append(record)
            out.write_text(json.dumps({'model':args.model,'judge_model':args.judge_model,'results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    usages=[x[call]['usage'] for x in results for call in ('subject_call','judge_call')
            if call in x and 'usage' in x[call]]
    totals={key:sum(u[key] for u in usages) if usages and all(isinstance(u.get(key),int) for u in usages) else None
            for key in ('input_tokens','output_tokens','total_tokens')}
    print(json.dumps({'cases':len(cases),'attempted':len(results),
                      'successful_subject_requests':sum('output_text' in x for x in results),
                      'errors':sum('error' in x for x in results),
                      'judged':sum(x.get('judge',{}).get('passed') in (True,False) for x in results),
                      'recorded_usage':totals,'usd_cost':'NOT_ESTIMATED_NO_VERIFIED_MODEL_PRICING'},ensure_ascii=False))

if __name__=='__main__':main()
