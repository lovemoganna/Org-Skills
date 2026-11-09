"""Regress the real archive self-inclusion failure and reusable package behavior."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('package_project', SKILL / 'scripts/package_project.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PackageChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / '工程'
        self.source.mkdir()
        (self.source / '稿件.md').write_text('真实教学案例', encoding='utf8')

    def test_original_in_tree_output_is_rejected_before_writing(self):
        target = self.source / 'result.zip'
        with self.assertRaisesRegex(ValueError, 'outside'):
            module.package(self.source, target)
        self.assertFalse(target.exists())

    def test_relative_dot_cannot_hide_self_inclusion(self):
        import os
        previous = Path.cwd()
        try:
            os.chdir(self.source)
            with self.assertRaisesRegex(ValueError, 'outside'):
                module.package('.', Path('.').parent / 'result.zip')
        finally:
            os.chdir(previous)

    def test_portable_project_keeps_assets_and_excludes_caches_and_old_revision(self):
        for name in ['node_modules', '.git', '.venv', 'public/audio', 'revisions/r001']:
            folder = self.source / name
            folder.mkdir(parents=True)
            (folder / 'file.txt').write_text(name)
        target = self.root / 'result.zip'
        report = module.package(self.source, target, ['revisions/r001'])
        with zipfile.ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {'工程/稿件.md', '工程/public/audio/file.txt'})
        self.assertEqual(report['files'], 2)
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            module.package(self.source, target)

    def test_missing_source_does_not_create_output(self):
        target = self.root / 'result.zip'
        with self.assertRaises(ValueError):
            module.package(self.root / 'missing', target)
        self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
