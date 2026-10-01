import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

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

    def test_duplicate_pointing_at_original_is_skipped_and_rss_carries_full_body(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / 'seo-updates' / '2026-09-27-orig'
            duplicate = root / 'seo-updates' / '2026-09-28-dup'
            original.mkdir(parents=True)
            duplicate.mkdir(parents=True)
            url = updates.ORIGIN + '/seo-updates/2026-09-27-orig/'
            (original / 'index.html').write_text(
                f'<html><head><link rel="canonical" href="{url}">'
                '<meta name="description" content="요약 문장">'
                '<script type="application/ld+json">{"@type": "Article", "datePublished": "2026-09-27T07:19:27"}</script>'
                '</head><body><article><h1>원본 제목</h1><p class="meta">소설가 이후 · 2026-09-27</p>'
                '<p>첫 문단입니다.</p><p>둘째 문단입니다.\n\n셋째 문단입니다.</p></article></body></html>',
                encoding='utf-8',
            )
            (duplicate / 'index.html').write_text(
                f'<link rel="canonical" href="{url}"><meta name="robots" content="noindex, follow"><h1>원본 제목</h1>',
                encoding='utf-8',
            )
            self.assertEqual(updates.build(root), 1)
            index = (root / 'seo-updates' / 'index.html').read_text(encoding='utf-8')
            self.assertEqual(index.count('<li>'), 1)
            self.assertNotIn('2026-09-28-dup', index)
            self.assertIn('href="' + updates.ORIGIN + '/seo-updates/rss.xml"', index)
            rss = ET.parse(root / 'seo-updates' / 'rss.xml')
            items = rss.findall('./channel/item')
            self.assertEqual([item.findtext('link') for item in items], [url])
            self.assertEqual(items[0].findtext('title'), '원본 제목')
            self.assertEqual(items[0].findtext('description'), '첫 문단입니다.\n\n둘째 문단입니다.\n\n셋째 문단입니다.')
            self.assertEqual(items[0].findtext('pubDate'), 'Sun, 27 Sep 2026 07:19:27 +0900')

    def test_rss_is_capped_to_the_latest_items(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for day in range(1, updates.RSS_ITEM_LIMIT + 3):
                stamp = (date(2026, 1, 1) + timedelta(days=day - 1)).isoformat()
                folder = root / 'seo-updates' / f'{stamp}-n{day}'
                folder.mkdir(parents=True)
                url = updates.ORIGIN + f'/seo-updates/{stamp}-n{day}/'
                (folder / 'index.html').write_text(f'<link rel="canonical" href="{url}"><h1>글 {day}</h1>', encoding='utf-8')
            self.assertEqual(updates.build(root), updates.RSS_ITEM_LIMIT + 2)
            items = ET.parse(root / 'seo-updates' / 'rss.xml').findall('./channel/item')
            self.assertEqual(len(items), updates.RSS_ITEM_LIMIT)
            self.assertEqual(items[0].findtext('title'), f'글 {updates.RSS_ITEM_LIMIT + 2}')
