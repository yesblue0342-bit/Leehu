import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from scripts import build_literature as builder


class CorePageDatesTest(unittest.TestCase):
    def test_sitemap_keeps_profile_dates_when_a_new_note_is_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = {
                "index.html": "2026-09-08",
                "author/index.html": "2026-09-08",
                "works/index.html": "2026-09-07",
                "official-links/index.html": None,
            }
            for name, date in pages.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                node = {"@type": "WebPage", "dateModified": date}
                quote = "'" if name.startswith("author") else '"'
                path.write_text(
                    f"<script type={quote}application/ld+json{quote}>"
                    + json.dumps({"@graph": [node]}) + "</script>",
                    encoding="utf-8",
                )
            with patch.object(builder, "ROOT", root):
                builder.write_sitemap([{"slug": "new-note", "published_at": "2026-09-10T08:00:00+09:00"}])
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            entries = {
                node.findtext("sm:loc", namespaces=ns):
                node.findtext("sm:lastmod", namespaces=ns)
                for node in ET.parse(root / "sitemap.xml").getroot()
            }
            self.assertEqual(entries[builder.ORIGIN + "/"], "2026-09-10")
            self.assertEqual(entries[builder.ORIGIN + "/author/"], "2026-09-08")
            self.assertEqual(entries[builder.ORIGIN + "/works/"], "2026-09-07")
            self.assertEqual(entries[builder.ORIGIN + "/official-links/"], builder.CORE_PAGE_LASTMOD)


    def test_updates_index_date_tracks_latest_indexable_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            updates = root / "seo-updates"
            updates.mkdir()
            (updates / "index.html").write_text("index", encoding="utf-8")
            for slug, body in (
                ("2026-10-01-old", "<h1>Old</h1>"),
                ("2026-11-02-new", "<h1>New</h1>"),
                ("2026-11-03-duplicate", '<meta name="robots" content="noindex, follow">'),
                ("2026-99-99-invalid", "<h1>Invalid date</h1>"),
            ):
                page = updates / slug / "index.html"
                page.parent.mkdir()
                page.write_text(body, encoding="utf-8")
            with patch.object(builder, "ROOT", root):
                expected = [
                    (builder.ORIGIN + "/seo-updates/", "2026-11-02"),
                    (builder.ORIGIN + "/seo-updates/2026-10-01-old/", "2026-10-01"),
                    (builder.ORIGIN + "/seo-updates/2026-11-02-new/", "2026-11-02"),
                ]
                self.assertEqual(builder.additional_sitemap_urls(), expected)
                self.assertEqual(builder.additional_sitemap_urls(), expected)

    def test_updates_index_without_posts_keeps_stable_fallback_date(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(builder, "ROOT", root):
                self.assertEqual(builder.additional_sitemap_urls(), [])
                updates = root / "seo-updates"
                updates.mkdir()
                (updates / "index.html").write_text("index", encoding="utf-8")
                self.assertEqual(
                    builder.additional_sitemap_urls(),
                    [(builder.ORIGIN + "/seo-updates/", builder.CORE_PAGE_LASTMOD)],
                )

    def test_checked_in_updates_sitemap_dates_match_published_pages(self):
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = {
            node.findtext("sm:loc", namespaces=ns):
            node.findtext("sm:lastmod", namespaces=ns)
            for node in ET.parse(builder.ROOT / "sitemap.xml").getroot()
        }
        for url, expected_date in builder.additional_sitemap_urls():
            with self.subTest(url=url):
                self.assertEqual(entries.get(url), expected_date)
