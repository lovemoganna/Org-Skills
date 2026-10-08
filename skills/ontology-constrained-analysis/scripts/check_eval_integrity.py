#!/usr/bin/env python3
"""Deterministic eval definition validation; does not evaluate model behavior."""
import json, pathlib, sys
root=pathlib.Path(__file__).resolve().parents[1]
files=[root/'evals'/'quality-evals.json', root/'evals'/'trigger-evals.json']
errors=[]
for path in files:
 data=json.loads(path.read_text(encoding='utf-8'))
 rows = data if isinstance(data,list) else data.get('evals') if isinstance(data,dict) else None
 if not isinstance(rows,list):
  errors.append(f'{path.name}: invalid top-level eval format')
  continue
 seen=set()
 for i,case in enumerate(rows):
  if path.name == 'trigger-evals.json':
   ident=case.get('query','')
   if not ident or ident in seen:errors.append(f'{path.name} missing/duplicate query at {i}')
   seen.add(ident)
   if not isinstance(case.get('should_trigger'),bool):errors.append(f'{path.name} bad should_trigger at {i}')
  else:
   ident=case.get('id','')
   if not ident or ident in seen:errors.append(f'{path.name} bad/duplicate id at {i}: {ident}')
   seen.add(ident)
   if not case.get('prompt'):errors.append(f'{ident}: missing prompt')
   if not isinstance(case.get('assertions'),list) or not case['assertions']:errors.append(f'{ident}: missing assertions')
 print(f'{path.name}: {len(rows)} cases')
if errors:
 print('FAIL:',*errors,sep='\n- ');sys.exit(1)
print('PASS definition integrity (not LLM behavior)')
