"""Regression checks for ten source-backed work notes and their discovery links."""
from __future__ import annotations

import copy
import html
import json
import re
import unittest
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts import build_literature as builder
from scripts.literature_batch import validate_manifest_note


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content/leehu-works-20260922-10.json"


class LeeHuSeptember22BatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.ordered = builder.sort_for_publication(cls.notes)
        cls.works = (ROOT / "works/index.html").read_text(encoding="utf-8")

    def page(self, note):
        return (ROOT / f'literature/{note["slug"]}/index.html').read_text(encoding="utf-8")

    def test_exact_ten_sources_match_manifest_and_date(self):
        self.assertEqual(len(self.notes), 10)
        self.assertEqual(len({n["source_work"] for n in self.notes}), 7)
        for index, note in enumerate(self.notes, 6182):
            self.assertEqual(validate_manifest_note(note, index), note)
            saved = json.loads((ROOT / f"content/literature/{index}.json").read_text(encoding="utf-8"))
            self.assertEqual(saved, note)
            self.assertEqual(datetime.fromisoformat(note["published_at"]).strftime("%Y%m%d"), "20260922")
            self.assertEqual(note["source_author"], "이후")
            self.assertEqual(note["content_kind"], "original_reflection")

    def test_original_prose_is_substantial_and_not_duplicated(self):
        for field in ("id", "slug", "title", "quote", "commentary", "closing"):
            self.assertEqual(len({builder.normalize(n[field]) for n in self.notes}), 10, field)
        for key in builder.SEO_SECTION_KEYS:
            self.assertEqual(len({n["seo_sections"][key] for n in self.notes}), 10)
        for note in self.notes:
            self.assertGreaterEqual(len(note["quote"]), 50)
            self.assertLessEqual(len(note["quote"]), 260)
            self.assertLessEqual(builder.prose_sentence_count(note["quote"]), 2)
            self.assertGreaterEqual(len(note["commentary"]), max(220, len(note["quote"]) * 1.25))
            self.assertIn(len(re.findall(r"다\.", note["commentary"])), range(4, 9))
            self.assertTrue(all(len(v) >= 80 for v in note["seo_sections"].values()))
            self.assertIn("직접 인용 없음", note["rights_note"])

    def test_sources_are_on_approved_publisher_or_bookstore_hosts(self):
        for note in self.notes:
            self.assertTrue(builder.is_allowed_https_url(note["source_url"], builder.ORIGINAL_REFLECTION_HOSTS))
            self.assertTrue(builder.is_allowed_https_url(note["related_work"]["url"], builder.COLLECTION_SOURCE_HOSTS))
        self.assertFalse(builder.is_allowed_https_url("https://www.g-world.co.kr@attacker.invalid/x", builder.ORIGINAL_REFLECTION_HOSTS))

    def test_book_identity_matches_visible_work_anchor(self):
        for note in self.notes:
            url = builder.official_work_url(note)
            self.assertEqual(url, builder.ORIGIN + "/works/#" + note["work_anchor"])
            self.assertIn(f'id="{note["work_anchor"]}"', self.works)
            page = self.page(note)
            self.assertIn(f'href="/works/#{note["work_anchor"]}"', page)
            blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
            self.assertEqual(len(blocks), 1)
            article, breadcrumb = json.loads(blocks[0])
            self.assertEqual(article["@type"], "BlogPosting")
            self.assertEqual(article["author"]["@id"], builder.ORIGIN + "/#person")
            self.assertEqual(article["about"]["@id"], url)
            self.assertEqual(article["about"]["@type"], "Book")
            self.assertEqual(article["citation"]["url"], note["source_url"])
            self.assertEqual(breadcrumb["@type"], "BreadcrumbList")

    def test_untrusted_or_mismatched_book_anchors_are_not_linked(self):
        for value in ('"><script>alert(1)</script>', "https://attacker.invalid", "sonagi"):
            note = copy.deepcopy(self.notes[0])
            note["work_anchor"] = value
            self.assertIsNone(builder.official_work_url(note))
            rendered = builder.detail_page(note, None, None)
            self.assertNotIn('href="/works/#', rendered)
        note = {**self.notes[0], "source_author": "다른 작가"}
        self.assertIsNone(builder.official_work_url(note))

    def test_detail_metadata_and_body_match_sources(self):
        for note in self.notes:
            page = self.page(note)
            self.assertIn(f'<title>{html.escape(builder.seo_title(note["title"]))}</title>', page)
            self.assertIn(f'<link rel="canonical" href="{builder.canonical(note)}">', page)
            self.assertIn('<meta name="robots" content="index, follow">', page)
            for text in [note["quote"], note["commentary"], note["closing"], *note["seo_sections"].values()]:
                self.assertIn(html.escape(text, quote=True), page)
            self.assertIn("독서 기록 제안", page)
            body = page.split("</head>", 1)[1]
            self.assertNotRegex(body, r"GitHub|github\.com|SEO|백링크")
            self.assertNotIn("<blockquote>", body)

    def test_pagination_has_every_indexable_note_once(self):
        paths = [ROOT / "literature/index.html", *sorted((ROOT / "literature/page").glob("*/index.html"), key=lambda p: int(p.parent.name))]
        self.assertEqual(len(paths), 268)
        slugs = []
        for index, path in enumerate(paths, 1):
            page = path.read_text(encoding="utf-8")
            found = re.findall(r'<a class="note-card" href="/literature/([a-z0-9-]+)/">', page)
            self.assertEqual(len(found), 25 if index < 268 else 17)
            slugs.extend(found)
            if index > 1:
                self.assertIn('<meta name="robots" content="noindex, follow">', page)
        self.assertEqual(len(slugs), 6692)
        self.assertEqual(len(set(slugs)), 6692)
        self.assertEqual([slug for slug in slugs if slug in {n["slug"] for n in self.notes}],
                         [n["slug"] for n in self.ordered])

    def test_sitemap_and_rss_include_ten_new_urls_exactly_once(self):
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [n.findtext("s:loc", namespaces=ns) for n in ET.parse(ROOT / "sitemap.xml").getroot()]
        items = ET.parse(ROOT / "literature/rss.xml").findall("./channel/item")
        guids = [i.findtext("guid") for i in items]
        self.assertEqual(len(items), 6692)
        self.assertEqual(len(guids), len(set(guids)))
        for note in self.notes:
            url = builder.canonical(note)
            self.assertEqual(locations.count(url), 1)
            self.assertEqual(guids.count(url), 1)
        previous_urls = {builder.canonical(n) for n in self.notes}
        self.assertEqual([guid for guid in guids if guid in previous_urls],
                         [builder.canonical(n) for n in self.ordered])

    def test_homepage_promotes_six_latest_notes(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        block = re.search(r'<!-- LITERATURE_LATEST_ITEMS:START -->(.*?)<!-- LITERATURE_LATEST_ITEMS:END -->', home, re.S).group(1)
        slugs = re.findall(r'href="/literature/([^/]+)/"', block)
        current = json.loads((ROOT / "content/leehu-works-20260923-1000.json").read_text(encoding="utf-8"))
        self.assertEqual(slugs, [n["slug"] for n in builder.sort_for_publication(current)[:6]])

    def test_work_page_has_all_ten_reading_links_and_matching_schema(self):
        block = re.search(r'<section[^>]*id="reading-notes".*?</section>', self.works, re.S).group(0)
        for note in self.notes:
            self.assertIn(f'href="/literature/{note["slug"]}/"', block)
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', self.works, re.S).group(1))
        listing = next(n for n in ld["@graph"] if n.get("@id") == builder.ORIGIN + "/works/#reading-notes")
        self.assertEqual(listing["numberOfItems"], 10)
        self.assertEqual([n["url"] for n in listing["itemListElement"]], [builder.canonical(n) for n in self.notes])

    def test_previous_next_chain_links_new_batch_to_existing_note(self):
        old = json.loads((ROOT / "content/literature/6181.json").read_text(encoding="utf-8"))
        chain = self.ordered + [old]
        for pos, note in enumerate(self.ordered):
            page = self.page(note)
            self.assertIn(f'href="/literature/{chain[pos + 1]["slug"]}/"', page)
            if pos:
                self.assertIn(f'href="/literature/{chain[pos - 1]["slug"]}/"', page)
        self.assertIn(f'href="/literature/{self.ordered[-1]["slug"]}/"', self.page(old))


if __name__ == "__main__":
    unittest.main()
