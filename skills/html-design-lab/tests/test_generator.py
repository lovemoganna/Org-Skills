"""Deterministic contract, fidelity, and adverse input tests (stdlib only)."""
import copy
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generator',ROOT/'scripts/generate.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
TEMPLATE=(ROOT/'assets/v55-renderer.html').read_text()
POEM=json.loads((ROOT/'examples/poem.document.json').read_text())

class TestGenerator(unittest.TestCase):
    def test_template_30_styles(self):
        self.assertEqual(len(g.get_style_ids(TEMPLATE)),30)
        self.assertEqual(len(set(g.get_style_ids(TEMPLATE))),30)

    def test_poem_exact_segments(self):
        output=g.render(POEM,'oriental',TEMPLATE)
        match=re.search(r'<script\s+type="application/json"\s+id="document-spec-data">(.*?)</script>',output,re.S)
        self.assertIsNotNone(match)
        docs=json.loads(match[1]);self.assertEqual(docs,[POEM]);self.assertEqual(len(docs[0]['annotations']),11)
        self.assertNotIn('data-doc-choice="duckdb"',output)
        self.assertIn('data-doc-choice="poem"',output)

    def test_embedded_script_inert(self):
        d=copy.deepcopy(POEM)
        for chapter in d['chapters']:
            for block in chapter['blocks']:
                if block['type']=='paragraph':block['segments']=[seg if isinstance(seg,str) else seg['text'] for seg in block['segments']]
        d['chapters'][0]['blocks'][0]['segments']=['</script><script>alert(1)</script>']
        d['annotations']={}
        output=g.render(d,'oriental',TEMPLATE)
        self.assertNotIn('</script><script>alert(1)</script>',output)
        self.assertIn('\\u003cscript\\u003ealert(1)',output)
        raw=re.search(r'<script\s+type="application/json"\s+id="document-spec-data">(.*?)</script>',output,re.S)[1]
        self.assertEqual(json.loads(raw)[0]['chapters'][0]['blocks'][0]['segments'][0],'</script><script>alert(1)</script>')

    def test_invalid_annotations_rejected(self):
        d=copy.deepcopy(POEM);d['annotations']['dew']['text']='错误文字'
        with self.assertRaisesRegex(g.DocumentError,'批注'):g.validate_document(d)

    def test_unknown_fields_rejected(self):
        d=copy.deepcopy(POEM);d['secret_api_call']='curl malicious.example'
        with self.assertRaisesRegex(g.DocumentError,'不支持字段'):g.validate_document(d)

    def test_unsupported_style_rejected(self):
        with self.assertRaisesRegex(g.DocumentError,'未知设计风格'):g.render(POEM,'invented',TEMPLATE)

    def test_markdown_structure(self):
        doc=g.parse_text((ROOT/'examples/tutorial.md').read_text(),kind='tutorial',docid='tutorial-test')
        self.assertEqual(len(doc['chapters']),4)
        typ={b['type'] for ch in doc['chapters'] for b in ch['blocks']}
        self.assertTrue({'paragraph','table','code','list'}<=typ)
        self.assertIn('SELECT category',next(b['code'] for ch in doc['chapters'] for b in ch['blocks'] if b['type']=='code'))

    def test_org_structure(self):
        doc=g.parse_text((ROOT/'examples/tutorial.org').read_text(),kind='tutorial',docid='org-test',fmt='org')
        self.assertEqual(doc['title'],'DuckDB 分组聚合实验')
        self.assertEqual(len(doc['chapters']),3)
        self.assertEqual(next(b for ch in doc['chapters'] for b in ch['blocks'] if b['type']=='table')['rows'][0],['A','100'])

    def test_unsupported_org_directive_fails(self):
        with self.assertRaisesRegex(g.DocumentError,'不支持的 Org 指令'):
            g.parse_text('#+TITLE: T\n* Chapter\n#+ATTR_HTML: :width 500\nparagraph',kind='article',docid='test-x',fmt='org')

    def test_actual_report_parse(self):
        doc=g.parse_text((ROOT/'examples/real-loop-review.md').read_text(),kind='report',docid='report-test')
        self.assertGreaterEqual(len(doc['chapters']),4)
        self.assertTrue(any(b['type']=='table' for ch in doc['chapters'] for b in ch['blocks']))
        self.assertIn('G0',str(doc))

    def test_custom_document_single_default(self):
        doc=g.parse_text('# Report\n## Facts\nOne fact.',kind='report',docid='custom-doc')
        s=g.render(doc,'saas',TEMPLATE)
        self.assertIn("setDocument(builtinMap.get('custom-doc'),false)",s)
        self.assertEqual(s.count('data-doc-choice="custom-doc"'),1)
        self.assertIn('document-theme-custom-doc',s)

if __name__=='__main__':unittest.main()
