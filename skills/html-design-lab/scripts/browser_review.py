#!/usr/bin/env python3
"""Browser boundary smoke check. Optional playwright dependency. JSON trace written to --out."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys

def run(htmlfile, out):
    from playwright.sync_api import sync_playwright
    data=htmlfile.read_text(encoding='utf-8')
    report={'source':htmlfile.name,'sha256':hashlib.sha256(data.encode('utf-8')).hexdigest(),
            'boundary':'Chromium page.set_content; not local file://, Firefox, Safari, or visual blind review',
            'cases':[],'errors':[]}
    with sync_playwright() as p:
        browser_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('chrome')
        launch={'headless':True}
        if browser_path:launch['executable_path']=browser_path
        b=p.chromium.launch(**launch)
        page=b.new_page(viewport={'width':390,'height':844})
        page.on('pageerror',lambda e:report['errors'].append(str(e)))
        page.set_content(data,wait_until='load')
        page.wait_for_function('window.DocumentEngine && document.querySelectorAll("#document-toc a").length>0')
        title=page.locator('#hero-title').inner_text()
        doc=page.evaluate('window.DocumentEngine.getCurrent()')
        report['cases'].append({'check':'document title from input','pass':title==doc['title'],'value':title})
        report['cases'].append({'check':'chapter navigation regenerated','pass':page.locator('#document-toc a').count()==len(doc['chapters'])})
        report['cases'].append({'check':'single default document selector','pass':page.locator('[data-doc-choice]').count()==1})
        report['cases'].append({'check':'no external HTTP resources','pass':len(page.locator('script[src],link[href^="http"],img[src^="http"]').all())==0})
        for width in [320,390,768,1024,1440]:
            page.set_viewport_size({'width':width,'height':844})
            page.wait_for_timeout(25)
            diff=page.evaluate('Math.max(document.body.scrollWidth,document.documentElement.scrollWidth) - window.innerWidth')
            report['cases'].append({'check':f'viewport {width} overflow','pass':diff<=1,'value':diff})
        page.set_viewport_size({'width':390,'height':844})
        visited=set()
        for _ in range(30):
            visited.add(page.locator('html').get_attribute('data-style'))
            page.locator('#next-style').click()
        report['cases'].append({'check':'30 clickable styles','pass':len(visited)==30 and len(set(visited))==30,'count':len(visited)})
        report['cases'].append({'check':'document kept after style switching','pass':page.locator('#hero-title').inner_text()==doc['title']})
        report['cases'].append({'check':'no legacy QA shell',
            'pass':page.locator('.v45qa,#v45-qa').count()==0 and 'guanshi-v45-compat-check' not in data})
        report['cases'].append({'check':'bundled syntax highlighter',
            'pass':page.locator('#code-syntax-theme').count()==1 and 'function highlightCode(' in data})
        # Browser-level content-fidelity and inert-markup verification, never evaluating user-supplied code.
        malicious="<img src=x onerror='window.__code_attack=1'>\n<script>window.__code_attack=1</script>"
        languages={
            'sql':"SELECT 'safe' AS name;\n-- "+malicious+"\nSELECT COUNT(*) FROM users;",
            'python':"# "+malicious+"\ndef total(items):\n    return len(items)",
            'javascript':"// "+malicious+"\nconst x = 42; function example(){ return x; }",
            'bash':"# "+malicious+"\nif true; then echo 'ok'; fi"
        }
        for lang,source in languages.items():
            verify=page.evaluate("""({lang,source})=>{
              const data=JSON.parse(JSON.stringify(window.DocumentEngine.getCurrent()));
              data.chapters[0].blocks.push({type:'code',language:lang,code:source});
              window.DocumentEngine.load(data,false);
              const codes=[...document.querySelectorAll('#document-content .document-code code')];
              const code=codes[codes.length-1];
              const kw=code.querySelector('.tok-keyword');
              const style=kw ? getComputedStyle(kw).color : '';
              return {text:code.textContent,keywords:code.querySelectorAll('.tok-keyword').length,
                      noMarkup:code.querySelectorAll('script,img,iframe').length===0,
                      notExecuted:window.__code_attack===undefined,
                      computedColor:style,rawColor:getComputedStyle(code).color};
            }""",{'lang':lang,'source':source})
            report['cases'].append({'check':f'{lang} code fidelity, inert tags, offline token highlight',
                'pass':verify['text']==source and verify['keywords']>0 and verify['noMarkup'] and
                       verify['notExecuted'] and verify['computedColor']!=verify['rawColor'],
                'data':{k:v for k,v in verify.items() if k!='text'}})

        report['cases'].append({'check':'no JavaScript runtime errors','pass':len(report['errors'])==0,'errors':report['errors']})
        b.close()
    report['passed']=sum(x['pass'] for x in report['cases'])
    report['total']=len(report['cases'])
    report['verdict']='PASS' if report['passed']==report['total'] else 'FAIL'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['verdict'],f"{report['passed']}/{report['total']}",out)
    return 0 if report['verdict']=='PASS' else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--html',required=True,type=Path)
    parser.add_argument('--out',required=True,type=Path)
    a=parser.parse_args()
    try:sys.exit(run(a.html,a.out))
    except Exception as e:
        print('BLOCKED/ERROR:',type(e).__name__,str(e),file=sys.stderr);sys.exit(2)
