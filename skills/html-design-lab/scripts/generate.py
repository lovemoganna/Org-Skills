#!/usr/bin/env python3
"""Generate a self-contained HTML design laboratory from one document, stdlib only."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'assets' / 'v55-renderer.html'
ID = re.compile(r'^[a-z0-9][a-z0-9_-]{0,53}$')
TYPES = {'paragraph', 'code', 'list', 'table', 'callout'}
KINDS = {'poem', 'tutorial', 'report', 'article'}

class DocumentError(ValueError):
    pass

def validate_document(doc):
    """Mirror critical browser-side DocumentSpec constraints and reject malformed inputs."""
    if not isinstance(doc, dict):
        raise DocumentError('DocumentSpec 必须为 JSON 对象')
    if not isinstance(doc.get('id'), str) or not ID.fullmatch(doc['id']):
        raise DocumentError('id 格式错误')
    if doc.get('kind') not in KINDS:
        raise DocumentError('kind 必须为 poem/tutorial/report/article')
    if set(doc)-{'id','kind','title','kicker','lead','description','ending','chapters','annotations'}:
        raise DocumentError('DocumentSpec 含不支持字段：'+','.join(sorted(set(doc)-{'id','kind','title','kicker','lead','description','ending','chapters','annotations'})))
    for field in ('title','kicker','lead','description','ending'):
        val = doc.get(field)
        if not isinstance(val, str) or not val.strip() or len(val)>400:
            raise DocumentError('无效文档字段：'+field)
    chapters = doc.get('chapters')
    if not isinstance(chapters, list) or not 1<=len(chapters)<=40:
        raise DocumentError('chapters 必须包含 1–40 章')
    annotations=doc.get('annotations',{})
    if not isinstance(annotations,dict) or len(annotations)>120:
        raise DocumentError('annotations 格式错误')
    for aid,annot in annotations.items():
        if isinstance(annot,dict) and set(annot)-{'text','gloss'}:raise DocumentError('批注包含不支持字段')
        if not isinstance(aid,str) or not ID.fullmatch(aid) or not isinstance(annot,dict) or not isinstance(annot.get('text'),str) or len(annot['text'])>500 or not isinstance(annot.get('gloss'),str) or len(annot['gloss'])>1200:
            raise DocumentError('无效 annotation：'+str(aid))
    seen=set(); used=set(); nblocks=0
    for chapter in chapters:
        if not isinstance(chapter,dict):raise DocumentError('章节必须为对象')
        if set(chapter)-{'id','title','subtitle','blocks'}:raise DocumentError('章节包含不支持字段')
        cid=chapter.get('id')
        if not isinstance(cid,str) or not ID.fullmatch(cid) or cid in seen:
            raise DocumentError('章节 id 缺失或重复')
        seen.add(cid)
        for name,maxlen in [('title',90),('subtitle',150)]:
            val=chapter.get(name,'')
            if not isinstance(val,str) or len(val)>maxlen or (name=='title' and not val.strip()):
                raise DocumentError('章节字段错误：'+name)
        blocks=chapter.get('blocks')
        if not isinstance(blocks,list) or not blocks:raise DocumentError('空章节不允许')
        nblocks+=len(blocks)
        for block in blocks:
            if not isinstance(block,dict) or block.get('type') not in TYPES:raise DocumentError('未知内容块')
            typ=block['type']
            allowed={'paragraph':{'type','segments','translation','featured'},'code':{'type','code','language'},'list':{'type','items'},'table':{'type','columns','rows'},'callout':{'type','label','text'}}[typ]
            if set(block)-allowed:raise DocumentError('内容块包含不支持字段：'+str(set(block)-allowed))
            if typ=='paragraph':
                segs=block.get('segments')
                if not isinstance(segs,list) or not segs:raise DocumentError('段落缺少 segments')
                tr=block.get('translation','')
                if not isinstance(tr,str) or len(tr)>3000:raise DocumentError('translation 超长')
                for seg in segs:
                    if isinstance(seg,str):
                        if len(seg)>4000:raise DocumentError('段落过长')
                    elif isinstance(seg,dict):
                        if set(seg)-{'text','annotationId'}:raise DocumentError('片段存在不支持字段')
                        aid=seg.get('annotationId');val=seg.get('text')
                        if not isinstance(aid,str) or aid not in annotations or aid in used or not isinstance(val,str) or len(val)>500 or annotations[aid]['text']!=val:
                            raise DocumentError('批注引用缺失、不一致或重复')
                        used.add(aid)
                    else:raise DocumentError('段落 segment 类型无效')
            elif typ=='code':
                if not isinstance(block.get('code'),str) or len(block['code'])>16000 or not isinstance(block.get('language',''),str) or len(block.get('language',''))>32:raise DocumentError('code 块格式错误')
            elif typ=='list':
                items=block.get('items')
                if not isinstance(items,list) or not 1<=len(items)<=80 or any(not isinstance(x,str) or len(x)>1000 for x in items):raise DocumentError('list 块格式错误')
            elif typ=='table':
                cols=block.get('columns');rows=block.get('rows')
                if not isinstance(cols,list) or not 1<=len(cols)<=12 or any(not isinstance(x,str) or len(x)>160 for x in cols) or not isinstance(rows,list) or len(rows)>150 or any(not isinstance(row,list) or len(row)!=len(cols) or any(not isinstance(x,str) or len(x)>700 for x in row) for row in rows):
                    raise DocumentError('table 块格式错误')
            elif typ=='callout':
                if not isinstance(block.get('label'),str) or len(block['label'])>100 or not isinstance(block.get('text'),str) or len(block['text'])>3000:raise DocumentError('callout 块格式错误')
    if nblocks>400:raise DocumentError('正文块数量超过 400')
    if used!=set(annotations):raise DocumentError('存在未被引用的批注')
    return doc

def clean_inline(value):
    """Preserve link targets and inline code content; discard only markup markers."""
    value=re.sub(r'!\[([^]]*)\]\(([^)]+)\)',lambda m: f'图片：{m[1]}（{m[2]}）',value)
    value=re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m: f'{m[1]}（{m[2]}）',value)
    value=re.sub(r'\[\[([^]]+)\]\[([^]]+)\]\]',lambda m: f'{m[2]}（{m[1]}）',value)
    value=re.sub(r'\[\[([^]]+)\]\]',lambda m: m[1],value)
    value=re.sub(r'(?<!\\)(\*\*|__|~~)(.+?)\1',lambda m:m[2],value)
    value=re.sub(r'(?<!\\)`([^`]*)`',lambda m:m[1],value)
    value=re.sub(r'(?<!\\)(?<!\*)\*([^*\n]+)\*(?!\*)',lambda m:m[1],value)
    return value.replace('\\*','*').replace('\\_','_')

def parse_text(source, kind, docid, title_override=None, fmt='md'):
    """Parse intentionally limited Markdown/Org subset; fail on unsupported directives."""
    lines=source.replace('\r\n','\n').replace('\r','\n').split('\n')
    title=title_override or ''
    chapters=[];current=None; paragraph=[];i=0
    def new_ch(name):
        nonlocal current
        if current and not current['blocks']:
            raise DocumentError('空章节：'+current['title'])
        current={'id':f'section-{len(chapters)+1}', 'title':clean_inline(name.strip())[:90], 'subtitle':'', 'blocks':[]}
        if not current['title']:raise DocumentError('章节标题为空')
        chapters.append(current)
        if len(chapters)>40:raise DocumentError('章节超过 40 个')
    def need_current():
        if current is None:new_ch('正文')
    def flush():
        if paragraph:
            need_current()
            p=clean_inline(' '.join(x.strip() for x in paragraph))
            if len(p)>4000:raise DocumentError('单段正文超过 4000 字')
            current['blocks'].append({'type':'paragraph','segments':[p]})
            paragraph.clear()
    def add(block):
        need_current();current['blocks'].append(block)
    while i<len(lines):
        raw=lines[i]; val=raw.strip()
        if not val:
            flush();i+=1;continue
        if fmt=='org' and re.match(r'^#\+TITLE:\s*',val,re.I):
            if not title:title=val.split(':',1)[1].strip()
            i+=1;continue
        if fmt=='org' and re.match(r'^#\+((?!begin_src|begin_quote|end_src|end_quote)[A-Z_]+):',val,re.I):
            if val.upper().startswith(('#+AUTHOR:','#+DATE:','#+OPTIONS:','#+LANGUAGE:')):
                i+=1;continue
            raise DocumentError('不支持的 Org 指令：'+val[:80])
        heading=(re.match(r'^(#{1,6})\s+(.+?)\s*#*$', val) if fmt=='md' else re.match(r'^(\*{1,6})\s+(.+)$',val))
        if heading:
            flush(); level=len(heading[1]); name=heading[2]
            if fmt=='md' and level==1 and not title:
                title=clean_inline(name);i+=1;continue
            new_ch(name);i+=1;continue
        fence=re.match(r'^```\s*([\w.+-]*)\s*$',val) if fmt=='md' else re.match(r'^#\+begin_src\s*([\w.+-]*)',val,re.I)
        if fence:
            flush();lang=fence[1].lower() or 'text';i+=1;code=[]
            close=re.compile(r'^```\s*$' if fmt=='md' else r'^#\+end_src\s*$',re.I)
            while i<len(lines) and not close.fullmatch(lines[i].strip()):
                code.append(lines[i]);i+=1
            if i==len(lines):raise DocumentError('代码块没有结束标记')
            body='\n'.join(code).rstrip('\n')
            if len(body)>16000:raise DocumentError('代码块过长')
            add({'type':'code','language':lang[:32],'code':body});i+=1;continue
        if fmt=='org' and re.match(r'^#\+begin_quote\s*$',val,re.I):
            flush();i+=1;vals=[]
            while i<len(lines) and not re.match(r'^#\+end_quote\s*$',lines[i].strip(),re.I):
                vals.append(lines[i].strip());i+=1
            if i==len(lines):raise DocumentError('引用块未结束')
            add({'type':'callout','label':'引文','text':clean_inline(' '.join(vals))});i+=1;continue
        if fmt=='md' and re.match(r'^>\s?',val):
            flush(); vals=[]
            while i<len(lines) and re.match(r'^>\s?',lines[i].strip()):
                vals.append(re.sub(r'^>\s?','',lines[i].strip()));i+=1
            add({'type':'callout','label':'引文','text':clean_inline(' '.join(vals))});continue
        if val.startswith('|') and val.endswith('|'):
            flush(); rows=[]
            while i<len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                if re.fullmatch(r'[|\s+:-]+',lines[i].strip()):
                    i+=1;continue
                rows.append([clean_inline(s.strip()) for s in lines[i].strip().strip('|').split('|')]);i+=1
            rows=[r for r in rows if not all(re.fullmatch(r':?-{3,}:?',x or '') for x in r)]
            if len(rows)<2:
                raise DocumentError('表格需有表头及至少一行数据')
            cols=rows.pop(0)
            if any(len(row)!=len(cols) for row in rows):raise DocumentError('表格行列数不一致')
            add({'type':'table','columns':cols,'rows':rows});continue
        bullet=re.match(r'^\s*(?:[-+]\s+|\d+[.)]\s+)(.+)$',raw)
        if bullet:
            flush();items=[]
            while i<len(lines):
                m=re.match(r'^\s*(?:[-+]\s+|\d+[.)]\s+)(.+)$',lines[i]);
                if not m:break
                items.append(clean_inline(m[1]));i+=1
            add({'type':'list','items':items});continue
        if (fmt=='md' and re.match(r'^\s*([-*_])\1{2,}\s*$',val)):
            flush();i+=1;continue
        if fmt=='org' and val.startswith('#+'):
            raise DocumentError('不支持的 Org 指令：'+val[:80])
        if fmt=='org' and val.startswith(':') and val.endswith(':'):
            raise DocumentError('Org 属性抽屉须先转换，避免静默丢失：'+val[:80])
        paragraph.append(raw);i+=1
    flush()
    if not chapters:raise DocumentError('没有可用正文')
    if not title:title='未命名文档'
    if len(title)>400:raise DocumentError('标题过长')
    all_text=[clean_inline(' '.join(b['segments'])) for ch in chapters for b in ch['blocks'] if b['type']=='paragraph']
    lead=next((x for x in all_text if x.strip()),title)[:400]
    ending=(all_text[-1] if all_text else title)[:400]
    doc={'id':docid,'kind':kind,'title':title,'kicker':f'{kind.upper()} · 单文档','lead':lead,
         'description':lead,'ending':ending,'chapters':chapters,'annotations':{}}
    return validate_document(doc)

def get_style_ids(template):
    m=re.search(r'const STYLES\s*=\s*(\[.*?\]);',template,re.S)
    if not m:raise DocumentError('无法从模板读取 30 种风格')
    data=json.loads(m[1]);ids=[x['id'] for x in data]
    if len(ids)!=30 or len(set(ids))!=30:raise DocumentError('风格注册表数量不一致')
    return ids

def replace_once(body, old, new):
    count=body.count(old)
    if count!=1:raise DocumentError(f'模板锚点数量不是 1：{old[:72]!r}，实际 {count}')
    return body.replace(old,new,1)

def render(doc,style,template):
    validate_document(doc)
    if style not in get_style_ids(template):raise DocumentError('未知设计风格：'+style)
    data=json.dumps([doc],ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template,n=re.subn(r'(<script\s+type="application/json"\s+id="document-spec-data">).*?(</script>)',lambda m:m[1]+data+m[2],template,count=1,flags=re.S)
    if n!=1:raise DocumentError('DocumentSpec 模板占位符缺失')
    template=replace_once(template,"setDocument(builtinMap.get('poem'),false);",f"setDocument(builtinMap.get('{doc['id']}'),false);")
    choices=re.compile(r'(<div class="document-lab__choices" role="group" aria-label="选择文档">).*?(</div>)',re.S)
    newbutton=f'<button type="button" data-doc-choice="{doc["id"]}" aria-pressed="true">{html.escape(doc["title"])}</button>'
    template,n=choices.subn(lambda m:m[1]+newbutton+m[2],template,count=1)
    if n!=1:raise DocumentError('文档选择器替换失败')
    template=replace_once(template,'同一套界面 · 三种文档结构','单份文档 · 30 种可切换风格')
    template=replace_once(template,"let active=styleMap.has(localStorageSafeGet('guanshi-visual-style')) ? localStorageSafeGet('guanshi-visual-style'):'oriental';",f"let active=styleMap.has(localStorageSafeGet('document-style-{doc['id']}')) ? localStorageSafeGet('document-style-{doc['id']}'):'{style}';")
    template=template.replace("localStorageSafeSet('guanshi-visual-style',id)",f"localStorageSafeSet('document-style-{doc['id']}',id)")
    template=template.replace("storage.get('guanshi-theme')",f"storage.get('document-theme-{doc['id']}')")
    template=template.replace("storage.set('guanshi-theme',theme)",f"storage.set('document-theme-{doc['id']}',theme)")
    template=template.replace('一纸观心 · ','专题阅读 · ')
    template=template.replace('观世有感原文及今译','当前文档正文')
    template=template.replace('观世有感 / FIN.','阅读结束')
    template=template.replace('内容实验室 · ','专题阅读 · ')
    template=template.replace('READ · REFLECT · REMEMBER','READ · EXPLORE · CREATE')
    template=template.replace('<strong>一纸观心</strong>','<strong>专题阅读</strong>')
    template=template.replace("'一纸观心 · '+next.title","'专题阅读 · '+next.title")
    template=template.replace("version:'V4.5'","version:'V6-generated'")
    template=template.replace('<title>30 风格内容实验室 · V5.5 发布候选版</title>','<title>'+html.escape(doc['title'])+'</title>')
    template=template.replace('V5.5 设计风格实验室：30 种风格、30 套独立构图，支持文言文、教程、报告与本地 JSON 文档。','独立专题阅读页：'+html.escape(doc['title'],quote=True)[:90])
    wrapping='''<style id="v6-prose-wrapping">
.document-list li, .document-callout p, .reader-main .chapter p, .reader-main .chapter h2, .reader-main .chapter h3 { overflow-wrap:anywhere; }
.document-table-wrap, .document-code { max-width:100%; }
</style>
'''
    template=replace_once(template,'</head>',wrapping+'</head>')
    template=template.replace('V5.5 发布候选版','')
    return template

def main(argv=None):
    ap=argparse.ArgumentParser(description='Generate one offline HTML with 30 selectable designs')
    ap.add_argument('--input','-i',required=True,type=Path)
    ap.add_argument('--output','-o',required=True,type=Path)
    ap.add_argument('--kind',choices=sorted(KINDS),help='Required for Markdown/Org; JSON contains its own kind')
    ap.add_argument('--style',default='auto',help='Auto chooses by content type; or specify one of 30 style IDs')
    ap.add_argument('--id',default=None,help='Optional stable ID; otherwise derived from source content hash')
    ap.add_argument('--title',help='Override title for Markdown/Org')
    ap.add_argument('--template',type=Path,default=TEMPLATE)
    args=ap.parse_args(argv)
    try:
        source=args.input.read_text(encoding='utf-8-sig')
        fmt=args.input.suffix.lower()
        if fmt=='.json':doc=validate_document(json.loads(source))
        elif fmt in ('.md','.markdown','.org'):
            if not args.kind:raise DocumentError('--kind 在 Markdown/Org 输入时必填')
            docid=args.id or ('doc-'+hashlib.sha256(source.encode('utf-8')).hexdigest()[:12])
            if not ID.fullmatch(docid):raise DocumentError('--id 格式错误')
            doc=parse_text(source,args.kind,docid,args.title,fmt='org' if fmt=='.org' else 'md')
        else:raise DocumentError('支持 .json、.md、.markdown 和 .org 文件')
        style={'poem':'oriental','tutorial':'terminal','report':'saas','article':'editorial'}[doc['kind']] if args.style=='auto' else args.style
        output=render(doc,style,args.template.read_text(encoding='utf-8'))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output,encoding='utf-8')
        print(f'OK: {args.output} | {doc["title"]} | {len(doc["chapters"])} chapters | style={style}')
    except (OSError,ValueError,KeyError,json.JSONDecodeError) as e:
        ap.exit(2,'ERROR: '+str(e)+'\n')

if __name__=='__main__':main()
