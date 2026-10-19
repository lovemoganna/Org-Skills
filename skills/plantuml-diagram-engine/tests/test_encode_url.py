import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib
import base64

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from encode_url import (plantuml_token, kroki_token, get_links, validate_source,
                        resolve_includes, verify_online, main, RenderError, DiagramError, ALPHABET)


def fake_png():
    out = io.BytesIO()
    Image.new('RGB', (80, 40), 'white').save(out, format='PNG')
    return out.getvalue()


class Response:
    status = 200
    def __init__(self, data, headers=None):
        self.data = data
        self.headers = headers if headers is not None else {'Content-Type': 'image/png'}
    def __enter__(self): return self
    def __exit__(self, *exc): return None
    def read(self, n): return self.data[:n]


def plantuml_decode(token):
    nums = [ALPHABET.index(c) for c in token]
    data = bytearray()
    for i in range(0, len(nums), 4):
        a, b, c, d = nums[i:i+4]
        data.extend(((a << 2) | (b >> 4), ((b & 15) << 4) | (c >> 2), ((c & 3) << 6) | d))
    return zlib.decompress(data, -15).decode('utf-8')


class TestMerge(unittest.TestCase):
    def test_known_official_vector(self):
        self.assertEqual(plantuml_token('Bob -> Alice : hello'), 'SyfFKj2rKt3CoKnELR1Io4ZDoSa70000')

    def test_cjk_roundtrip_both_backends(self):
        for path in sorted((ROOT / 'examples').glob('*.puml')):
            source = path.read_text(encoding='utf-8')
            self.assertEqual(plantuml_decode(plantuml_token(source)), source)
            packed = kroki_token(source)
            data = base64.urlsafe_b64decode(packed + '=' * (-len(packed) % 4))
            self.assertEqual(zlib.decompress(data).decode('utf-8'), source)

    def test_source_type_valid(self):
        for path in (ROOT / 'examples').glob('*.puml'):
            validate_source(path.read_text(encoding='utf-8'))

    def test_invalid_delimiters(self):
        with self.assertRaises(RenderError):
            validate_source('@startuml\nA->B:hello\n@endwbs')

    def test_wbs_four_groups_and_relationship_labels(self):
        text = (ROOT / 'examples/01_wbs.puml').read_text(encoding='utf-8')
        self.assertEqual(len([l for l in text.splitlines() if l.startswith('** ' ) or l.startswith('**< ')]), 4)
        self.assertEqual(len([l for l in text.splitlines() if l.startswith('***')]), 12)
        for item in ('输入与关系','结构表达','在线交付','验证与修复'):
            self.assertIn(item, text)

    def test_activity_branch_labels_and_exit(self):
        text = (ROOT / 'examples/02_activity.puml').read_text(encoding='utf-8')
        for item in ('if (', 'then (是)', 'else (否)', 'repeat while', 'stop', '少于两轮'):
            self.assertIn(item, text)

    def test_deployment_nodes_and_protocols(self):
        text = (ROOT / 'examples/03_deployment.puml').read_text(encoding='utf-8')
        for item in ('node "DMZ 隔离区"', 'database "高可用数据库集群"', 'HTTPS (443)', 'HTTP (8080)', 'WAL 流复制'):
            self.assertIn(item, text)

    def test_gantt_delimiters_and_dependencies(self):
        text = (ROOT / 'examples/04_gantt.puml').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('@startgantt'))
        self.assertTrue(text.strip().endswith('@endgantt'))
        for item in ('language zh', 'lasts 5 days', "'s end", 'happens at'):
            self.assertIn(item, text)

    def test_mindmap_delimiters_and_branches(self):
        text = (ROOT / 'examples/05_mindmap.puml').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('@startmindmap'))
        self.assertTrue(text.strip().endswith('@endmindmap'))
        for item in ('* 研发工程效能与质量体系', 'left side', '** 交付速度', '** 可观测性'):
            self.assertIn(item, text)

    def test_sequence_participants_and_messages(self):
        text = (ROOT / 'examples/06_sequence.puml').read_text(encoding='utf-8')
        for item in ('actor "顾客 (Customer)"', 'participant "订单中心 (Order Svc)"',
                     'autonumber', 'alt 风控通过', 'else 风控拦截', 'deactivate'):
            self.assertIn(item, text)

    def test_state_transitions_and_guards(self):
        text = (ROOT / 'examples/07_state.puml').read_text(encoding='utf-8')
        for item in ('[*] --> 待支付', '待支付 --> 已支付', '待支付 --> 已取消',
                     '已支付 --> 待发货', '已发货 --> 已签收', '已完成 --> [*]'):
            self.assertIn(item, text)

    def test_component_stereotypes_and_interfaces(self):
        text = (ROOT / 'examples/08_component.puml').read_text(encoding='utf-8')
        for item in ('package "接入与网关层', 'component "API 网关服务 (Gateway)" as gw',
                     'component "统一认证与鉴权 (OAuth/JWT)" as auth <<low>>',
                     'database "订单主从数据库 (MySQL Cluster)" as order_db',
                     'queue "交易事件消息总线 (Kafka)" as event_bus <<ok>>'):
            self.assertIn(item, text)

    def test_class_entities_and_relationships(self):
        text = (ROOT / 'examples/09_class.puml').read_text(encoding='utf-8')
        for item in ('class Order {', 'class Customer {', 'class Product {', 'class OrderItem {',
                     'enum OrderStatus {', 'Order "1" *-- "1..*" OrderItem'):
            self.assertIn(item, text)

    def test_activity_privacy_gate_before_public_url_and_request(self):
        text = (ROOT / 'examples/02_activity.puml').read_text(encoding='utf-8')
        assert text.index('含敏感信息或未经公开授权？') < text.index('编码生成在线 PNG URL')
        assert text.index('含敏感信息或未经公开授权？') < text.index('访问在线图片服务')
        assert text.index('禁止生成公共图片 URL') < text.index('编码生成在线 PNG URL')
        assert '具备联网验证条件？' in text
        assert '内容允许公开且可联网？' not in text

    def test_default_generates_online_url_without_network_or_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / 'case.puml'
            src.write_text('@startuml\nAlice -> Bob: ping\n@enduml', encoding='utf-8')
            with patch('urllib.request.urlopen') as mocked:
                with patch('sys.stdout', new_callable=io.StringIO) as out:
                    self.assertEqual(main([str(src)]), 0)
                mocked.assert_not_called()
            self.assertIn('https://www.plantuml.com/plantuml/png/', out.getvalue())
            self.assertIn('https://kroki.io/plantuml/png/', out.getvalue())
            self.assertIn('HTTP_UNVERIFIED', out.getvalue())
            self.assertFalse((Path(td) / 'case.png').exists())

    def test_json_output(self):
        p = ROOT / 'examples/01_wbs.puml'
        with patch('sys.stdout', new_callable=io.StringIO) as out:
            self.assertEqual(main([str(p), '--json']), 0)
        d = json.loads(out.getvalue())
        self.assertEqual(d['status'], 'URL_GENERATED / HTTP_UNVERIFIED')
        self.assertIsNone(d['backend'])

    def test_private_rejected(self):
        with self.assertRaisesRegex(RenderError, 'PRIVATE_SOURCE'):
            main([str(ROOT / 'examples/01_wbs.puml'), '--private'])

    def test_no_network_without_authorization(self):
        with self.assertRaisesRegex(RenderError, 'PUBLIC_UPLOAD_DENIED'):
            main([str(ROOT / 'examples/01_wbs.puml'), '--check-online'])

    def test_no_download_without_authorization(self):
        with self.assertRaisesRegex(RenderError, 'PUBLIC_UPLOAD_DENIED'):
            main([str(ROOT / 'examples/01_wbs.puml'), '--download', 'test.png'])

    def test_valid_png_online_response(self):
        with patch('urllib.request.urlopen', return_value=Response(fake_png())):
            _, dim = verify_online('https://www.plantuml.com/plantuml/png/example')
        self.assertEqual(dim, (80, 40))

    def test_reject_html_response(self):
        with patch('urllib.request.urlopen', return_value=Response(b'<html>bad</html>', {'Content-Type': 'text/html'})):
            with self.assertRaisesRegex(RenderError, 'NOT_PNG'):
                verify_online('https://www.plantuml.com/plantuml/png/example')

    def test_syntax_error_header(self):
        with patch('urllib.request.urlopen', return_value=Response(fake_png(), {'Content-Type': 'image/png', 'X-PlantUML-Diagram-Error': 'syntax'})):
            with self.assertRaises(DiagramError):
                verify_online('https://www.plantuml.com/plantuml/png/example')

    def test_fallback_only_for_network_errors(self):
        p = ROOT / 'examples/02_activity.puml'
        with patch('encode_url.verify_online', side_effect=[RenderError('timeout'), (fake_png(), (80, 40))]) as req:
            with patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main([str(p), '--check-online', '--public-ok', '--json']), 0)
        self.assertEqual(req.call_count, 2)
        self.assertEqual(json.loads(out.getvalue())['backend'], 'kroki')

    def test_do_not_fallback_on_syntax_error(self):
        with patch('encode_url.verify_online', side_effect=DiagramError('syntax')) as req:
            with self.assertRaises(DiagramError):
                main([str(ROOT / 'examples/01_wbs.puml'), '--check-online', '--public-ok'])
        self.assertEqual(req.call_count, 1)

    def test_download_explicit_only(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'image.png'
            with patch('encode_url.verify_online', return_value=(fake_png(), (80, 40))):
                with patch('sys.stdout', new_callable=io.StringIO):
                    self.assertEqual(main([str(ROOT / 'examples/01_wbs.puml'), '--download', str(out), '--public-ok']), 0)
            self.assertTrue(out.exists())

    def test_download_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'image.png'
            with patch('encode_url.verify_online', side_effect=RenderError('offline')):
                with self.assertRaisesRegex(RenderError, 'DOWNLOAD_FAILED'):
                    main([str(ROOT / 'examples/01_wbs.puml'), '--download', str(out), '--public-ok'])
            self.assertFalse(out.exists())

    def test_style_ink_and_signal_file_integrity(self):
        style_path = ROOT / 'styles/style-ink-and-signal.puml'
        self.assertTrue(style_path.exists(), 'styles/style-ink-and-signal.puml must exist')
        content = style_path.read_text(encoding='utf-8')
        for token in ('PlantUML Style · Ink & Signal  (v7)', '!$THEME', '!$BG', '!$INK',
                      'skinparam backgroundColor $BG', 'skinparam defaultFontName $FONT_BODY',
                      'COLOR_RISK_LOW_BG', 'COLOR_RISK_HIGH_BG',
                      '<style>', 'mindmapDiagram', 'wbsDiagram', 'ganttDiagram'):
            self.assertIn(token, content)

    def test_resolve_includes_inlining(self):
        sample = '@startuml\n!include styles/style-ink-and-signal.puml\nclass User\n@enduml'
        expanded = resolve_includes(sample, base_dir=ROOT)
        # Verify no active !include directive remains in the code
        self.assertFalse(any(l.strip().startswith('!include ') for l in expanded.splitlines()))
        self.assertIn('Ink & Signal  (v7)', expanded)
        self.assertIn('class User', expanded)

    def test_resolve_includes_via_main(self):
        with tempfile.TemporaryDirectory() as td:
            puml_file = Path(td) / 'test_inc.puml'
            puml_file.write_text('@startuml\n!include styles/style-ink-and-signal.puml\nclass Demo\n@enduml', encoding='utf-8')
            with patch('sys.stdout', new_callable=io.StringIO) as out:
                self.assertEqual(main([str(puml_file), '--json']), 0)
            data = json.loads(out.getvalue())
            self.assertIn('https://www.plantuml.com/plantuml/png/', data['urls']['plantuml'])
            # Verify decoded URL contains expanded style, not the raw !include directive
            token = data['urls']['plantuml'].split('/')[-1]
            decoded = plantuml_decode(token)
            self.assertFalse(any(l.strip().startswith('!include ') for l in decoded.splitlines()))
            self.assertIn('Ink & Signal  (v7)', decoded)
            self.assertIn('class Demo', decoded)


if __name__ == '__main__':
    unittest.main()

