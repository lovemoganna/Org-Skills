"""Structural regression for result-driven investigation; not a substitute for real SQL or judgement."""
import copy
import json
import re
import sys
from pathlib import Path


def verify(t):
    def need(v, msg):
        if not v: raise ValueError(msg)
    need(isinstance(t, dict) and isinstance(t.get('meta'), dict), 'missing provenance')
    meta = t['meta']
    need(all(isinstance(meta.get(k), str) and meta[k] for k in ('run','skill','data')), 'incomplete provenance')
    for k in ('questions','results','updates','findings'):
        need(isinstance(t.get(k), list), 'missing '+k)
    def indexed(k):
        a=t[k]
        need(all(isinstance(v, dict) and isinstance(v.get('id'),str) and v['id'] for v in a), 'invalid '+k)
        d={v['id']:v for v in a}
        need(len(d)==len(a), 'duplicate '+k)
        return d
    q,results,findings=indexed('questions'),indexed('results'),indexed('findings')
    need(q and results, 'empty question/result')
    order={r['id']:i for i,r in enumerate(t['results'])}
    for r in results.values():
        need(r.get('question') in q and r.get('status')=='PASS', 'unexecuted SQL or orphan result')
        need(all(r.get(k)==meta[k] for k in ('run','skill','data')), 'stale evidence')
        need(all(isinstance(r.get(k),str) and re.fullmatch('[a-f0-9]{64}',r[k]) for k in ('sql_sha','result_sha')), 'missing SQL/Result digest')
    edges=set()
    for u in t['updates']:
        need(u.get('source') in results and bool(u.get('observed')) and bool(u.get('change')), 'empty frontier update')
        if u.get('next') is not None:
            need(u['next'] in q and q[u['next']].get('parent')==u['source'], 'unbound next question')
            edges.add((u['source'],u['next']))
    need(t['updates'], 'no result-driven frontier')
    for question in q.values():
        id=question['id']; own=[order[r['id']] for r in results.values() if r['question']==id]
        need(own and bool(question.get('trigger')), 'unexecuted or unmotivated question')
        branches=question.get('branches')
        need(isinstance(branches,list) and len(branches)>=2 and len(set(branches))>=2 and all(isinstance(x,str) and x for x in branches), 'answers do not change next judgement')
        if question.get('parent') is not None:
            p=question['parent']; need(p in order and order[p]<min(own) and (p,id) in edges, 'prewritten or unlinked follow-up')
    for f in findings.values():
        ev=f.get('evidence'); need(isinstance(ev,list) and ev and all(v in results for v in ev),'finding without SQL')
        need(bool(f.get('claim')) and bool(f.get('limits')), 'unsupported finding narrative')
        need(f.get('kind') in ('descriptive','investigative'),'bad finding kind')
        if f['kind']=='investigative':
            hs=f.get('alternatives',[])
            need(len(hs)>=2 and all(isinstance(h,dict) and h.get('prediction') and h.get('refutation') for h in hs), 'no falsifiable competing hypotheses')
            need(f.get('diagnostic') in ev and f.get('robustness') in ev and bool(f.get('decision_change')), 'unverified test or decision')
    report=t.get('report',{})
    ids=report.get('findings')
    need(isinstance(ids,list) and ids and all(id in findings for id in ids), 'report cites absent finding')
    depth=report.get('depth')
    need(depth in ('PASS','DESCRIPTIVE_ONLY','NO_DECISION_GRADE_FINDING'), 'missing honest report depth state')
    investigative=any(findings[id]['kind']=='investigative' for id in ids)
    need((depth=='PASS')==investigative, 'descriptive facts promoted to investigative PASS')


def case():
    meta=dict(run='current-run',skill='current-skill',data='current-data')
    def result(id,question): return dict(id=id,question=question,status='PASS',**meta,sql_sha='a'*64,result_sha='b'*64)
    return dict(meta=meta,
      questions=[dict(id='q1',trigger='authorized temporal event fields',branches=['screen','stop']),
                 dict(id='q2',trigger='r1 event signal',parent='r1',branches=['verify relation','reject relation']),
                 dict(id='q3',trigger='r2 chronology ambiguous',parent='r2',branches=['narrow','keep unresolved'])],
      results=[result('r1','q1'),result('r2','q2'),result('r3','q3')],
      updates=[dict(source='r1',next='q2',observed='observed one candidate',change='check time order'),
               dict(source='r2',next='q3',observed='time order uncertain',change='test counterexample'),
               dict(source='r3',observed='evidence insufficient for cause',change='stop and bound finding')],
      findings=[dict(id='f1',kind='investigative',evidence=['r1','r2','r3'],claim='sequence candidate with limits',limits='not settlement proof',
        alternatives=[dict(prediction='repeat independent activity',refutation='different timestamps'),
                      dict(prediction='related ordered activity',refutation='no ordered match')],
        diagnostic='r2',robustness='r3',decision_change='request account ownership evidence')],
      report=dict(findings=['f1'],depth='PASS'))


def selftest():
    p=case();verify(p)
    mutants={
      'static ranking claims deep':lambda a:a['findings'][0].update(kind='descriptive'),
      'prewritten checklist':lambda a:a['questions'][1].pop('parent'),
      'inverted query chronology':lambda a:a['results'].reverse(),
      'no differentiated answer':lambda a:a['questions'][0].update(branches=['same','same']),
      'phantom diagnostic':lambda a:a['findings'][0].update(diagnostic='missing'),
      'unbound robustness':lambda a:a['findings'][0].update(evidence=['r1','r2']),
      'stale result':lambda a:a['results'][0].update(data='stale'),
      'fake claim':lambda a:a['report'].update(findings=['phantom']),
      'no alternative':lambda a:a['findings'][0].update(alternatives=[]),
      'unbound update':lambda a:a['updates'][0].update(next='q3'),
    }
    for name, mutate in mutants.items():
        bad=copy.deepcopy(p);mutate(bad)
        try:verify(bad)
        except (ValueError,TypeError,KeyError):continue
        raise AssertionError('MUTATION_NOT_REJECTED '+name)
    downgraded=copy.deepcopy(p);downgraded['findings'][0]['kind']='descriptive';downgraded['report']['depth']='DESCRIPTIVE_ONLY';verify(downgraded)
    print('PASS: trace contract, 10 independent negative mutations, honest descriptive downgrade')


if __name__=='__main__':
    if len(sys.argv)>1:
        verify(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))
        print('PASS: trace structural provenance (not business correctness)')
    else:selftest()
