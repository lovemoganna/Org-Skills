#!/usr/bin/env python3
"""Static structural checks only; not a behavioral Claude/real-domain regression."""
from pathlib import Path
import json,re,sys,hashlib
root=Path(__file__).resolve().parents[1]
skill=(root/'SKILL.md').read_text(encoding='utf-8')
source=(root/'assets/original-sop-v3.md').read_text(encoding='utf-8')
checks=[]
checks.append(('frontmatter',bool(re.match(r'(?s)\A---\nname: standards-engineering-loop\ndescription: .+?\n---\n',skill))))
checks.append(('core under 500 lines',len(skill.splitlines())<500))
sections=re.findall(r'(?m)^#{1,2} [一二三四五六七八九十]+、',source)
checks.append(('34 numbered original sections',len(sections)==34))
parts=['01-scope-and-facts.md','02-ontology-and-rules.md','03-tests-sources-baseline.md','04-audit-and-regression.md','05-release-and-output.md']
joined=''.join((root/'references'/p).read_text(encoding='utf-8') for p in parts)
checks.append(('split sources exactly reconstruct original',joined==source))
refs=re.findall(r'\]\((references/[^)#]+)\)',skill)
checks.append(('all reference links exist',all((root/p).is_file() for p in refs)))
e=json.loads((root/'evals/evals.json').read_text(encoding='utf-8'))
checks.append(('8 behavioral scenarios',len(e['evals'])==8))
checks.append(('original SHA preserved',hashlib.sha256(joined.encode()).hexdigest()==hashlib.sha256(source.encode()).hexdigest()))
checks.append(('no DuckDB-specific source contamination',not any(s in skill for s in ['exchange_rates','fiat_transactions','crypto_transactions'])))
for n,ok in checks:print(('PASS' if ok else 'FAIL')+': '+n)
sys.exit(0 if all(ok for _,ok in checks) else 1)
