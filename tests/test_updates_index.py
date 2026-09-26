import tempfile
import unittest
from pathlib import Path

from scripts import build_updates_index as updates


class UpdatesIndexTest(unittest.TestCase):
    def test_index_uses_actual_heading_not_stale_ledger_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'seo-updates' / '2026-09-27-test'
            folder.mkdir(parents=True)
            url = updates.ORIGIN + '/seo-updates/2026-09-27-test/'
            (folder / 'index.html').write_text(
                f'<link rel="canonical" href="{url}"><h1>새로운 &amp; 실제 제목</h1>',
                encoding='utf-8',
            )
            (root / 'seo-updates' / 'index.html').write_text('잘못된 제목' * 5, encoding='utf-8')
            self.assertEqual(updates.build(root), 1)
            result = (root / 'seo-updates' / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(result.count('<li>'), 1)
            self.assertIn('새로운 &amp; 실제 제목', result)
            self.assertNotIn('잘못된 제목', result)
            updates.build(root)
            self.assertEqual(result, (root / 'seo-updates' / 'index.html').read_text(encoding='utf-8'))

    def test_invalid_canonical_does_not_replace_existing_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / 'seo-updates' / '2026-09-27-test'
            folder.mkdir(parents=True)
            (folder / 'index.html').write_text('<h1>제목</h1>', encoding='utf-8')
            target = root / 'seo-updates' / 'index.html'
            target.write_text('keep', encoding='utf-8')
            with self.assertRaises(ValueError):
                updates.build(root)
            self.assertEqual(target.read_text(encoding='utf-8'), 'keep')
