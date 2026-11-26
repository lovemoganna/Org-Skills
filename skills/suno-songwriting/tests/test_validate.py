"""Regression tests for deterministic Skill output contracts. No audio-quality claims."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('suno_validator', ROOT / 'scripts' / 'validate.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = (ROOT / 'examples' / 'buxihuan-v1.1.md').read_text('utf-8')
        cls.style = (ROOT / 'examples' / 'style-only.md').read_text('utf-8')

    def test_full_song_passes(self):
        errors, stats = module.validate_song(self.full, '不喜欢')
        self.assertEqual([], errors)
        self.assertEqual('v1.1', stats['version'])
        self.assertLessEqual(stats['style_chars'], 1000)

    def test_style_only_passes(self):
        errors, stats = module.validate_song(self.style, mode='style-only')
        self.assertEqual([], errors)
        self.assertLessEqual(stats['style_chars'], 1000)

    def test_style_only_works_with_raw_prompt(self):
        errors, stats = module.validate_song('Mandarin R&B, 84 BPM, warm bass.', mode='style-only')
        self.assertEqual([], errors)
        self.assertGreater(stats['style_chars'], 0)

    def test_overlong_style_fails(self):
        changed = self.full.replace('Mandarin Pop, Contemporary R&B', 'A' * 1010 + ' Mandarin Pop, Contemporary R&B')
        errors, _ = module.validate_song(changed, '不喜欢')
        self.assertTrue(any('H4:' in e for e in errors), errors)

    def test_missing_bridge_fails(self):
        changed = self.full.replace('[Bridge]', '[Interlude]')
        errors, _ = module.validate_song(changed, '不喜欢')
        self.assertTrue(any('H5: missing [Bridge]' in e for e in errors), errors)

    def test_title_override_fails(self):
        errors, _ = module.validate_song(self.full, '不想你')
        self.assertTrue(any('H1: user-specified title changed' in e for e in errors), errors)

    def test_style_only_rejects_lyrics_leak(self):
        changed = self.style + '\n## Lyrics\n```text\n[Chorus]\ntext\n```\n'
        errors, _ = module.validate_song(changed, mode='style-only')
        self.assertTrue(any('style-only output must not include lyrics' in e for e in errors), errors)

    def test_missing_intro_fails(self):
        changed = self.full.replace('## 创作简介', '## 空白简介')
        errors, _ = module.validate_song(changed, '不喜欢')
        self.assertTrue(any('H2:' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
