import html
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

from scripts import build_literature


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
LITERATURE = ROOT / "literature"
ORIGIN = "https://xn--hu5b23z.com"
TARGET_COUNT = 1466
PAGE_SIZE = 25
TARGET_LIST_PAGES = 59
TARGET_SITEMAP_URLS = 1526
REQUIRED = {
    "id", "slug", "title", "quote", "source_author", "source_work",
    "source_location", "source_language", "source_url", "translation_note",
    "rights_note", "commentary", "closing", "author", "tags",
    "related_work", "published_at",
}


class StaticLiteratureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(CONTENT.glob("*.json"), key=lambda item: int(item.stem))
        cls.notes = [
            json.loads(path.read_text(encoding="utf-8")) for path in cls.paths
        ]

    def test_exact_source_count_names_ids_and_publication_dates(self):
        self.assertEqual(len(self.paths), TARGET_COUNT)
        self.assertEqual(len(self.notes), TARGET_COUNT)
        for index, (path, note) in enumerate(zip(self.paths, self.notes), 1):
            self.assertEqual(path.name, f"{index:03d}.json")
            self.assertRegex(note["id"], r"^\d{8}_leehu_literature_\d{3,}$")
            self.assertEqual(
                note["id"][:8],
                note["published_at"][:10].replace("-", ""),
            )
            self.assertTrue(REQUIRED <= set(note))

    def test_love_batch_author_mix_and_hwang_reflection_rights(self) -> None:
        batch = self.notes[665:1165]
        self.assertEqual(len(batch), 500)
        self.assertEqual(
            Counter(note["source_author"] for note in batch),
            Counter({
                "Guy de Maupassant": 125,
                "William Shakespeare": 125,
                "이상": 60,
                "이상 작품 감상": 65,
                "황순원 작품 감상": 125,
            }),
        )
        reflection_notes = [note for note in batch if note.get("content_kind") == "original_reflection"]
        self.assertEqual(len(reflection_notes), 190)
        self.assertTrue(all("직접 인용 없음" in note["rights_note"] for note in reflection_notes))
        self.assertTrue(all("사랑" in note["tags"] for note in batch))

    def test_world_love_batch_author_mix_and_rights_modes(self) -> None:
        batch = self.notes[1165:1465]
        self.assertEqual(len(batch), 300)
        self.assertEqual(
            Counter(note["source_author"] for note in batch),
            Counter({
                "Leo Tolstoy": 35, "Emily Brontë": 35, "Victor Hugo": 35,
                "Johann Wolfgang von Goethe": 35, "Alexandre Dumas fils": 35,
                "Anton Chekhov": 35, "Gabriel García Márquez 작품 감상": 45,
                "Antoine de Saint-Exupéry 작품 감상": 45,
            }),
        )
        self.assertEqual(sum(note.get("content_kind") == "original_reflection" for note in batch), 90)
        self.assertTrue(all(set(note["tags"]) & {"사랑", "애정", "연애", "헌신", "기다림", "관계", "신뢰", "기억", "갈망", "돌봄"} for note in batch))

    def test_reflection_pages_do_not_claim_project_gutenberg_source(self) -> None:
        reflection = next(note for note in self.notes if note.get("content_kind") == "original_reflection")
        page = (LITERATURE / reflection["slug"] / "index.html").read_text(encoding="utf-8")
        self.assertIn("작품 정보 확인", page)
        self.assertNotIn("Project Gutenberg 원문 확인", page)

    def test_structured_seo_sample_has_semantic_sections(self) -> None:
        sample = next(note for note in self.notes if note["id"] == "20260728_leehu_literature_301")
        page = (LITERATURE / sample["slug"] / "index.html").read_text(encoding="utf-8")
        for heading in ("작품 소개", "왜 지금도 읽히는가", "나의 감상", "오늘 우리에게 주는 의미"):
            self.assertIn(f"<h2>{heading}</h2>", page)
        self.assertIn("『예언자(The Prophet)』", page)

    def test_search_component_waits_for_document_and_indexes_author_work(self) -> None:
        page = (LITERATURE / "index.html").read_text(encoding="utf-8")
        self.assertIn('document.addEventListener("DOMContentLoaded"', page)
        self.assertIn('author:text("author")', page)
        self.assertIn('work:text("source")', page)

    def test_publication_order_places_newer_batch_and_higher_sequence_first(self) -> None:
        notes = [
            {"id": "20260728_leehu_literature_002", "published_at": "2026-07-28T12:00:00+09:00"},
            {"id": "20260727_leehu_literature_365", "published_at": "2026-07-27T12:00:00+09:00"},
            {"id": "20260728_leehu_literature_001", "published_at": "2026-07-28T12:00:00+09:00"},
        ]
        ordered = build_literature.sort_for_publication(notes)
        self.assertEqual(
            [note["id"] for note in ordered],
            [
                "20260728_leehu_literature_002",
                "20260728_leehu_literature_001",
                "20260727_leehu_literature_365",
            ],
        )

    def test_content_integrity_metrics(self) -> None:
        for field in ("id", "slug", "title", "quote"):
            values = [re.sub(r"\W+", "", str(note[field])).casefold() for note in self.notes]
            self.assertEqual(len(values), len(set(values)), field)
        canonicals = {
            f"{ORIGIN}/literature/{note['slug']}/" for note in self.notes
        }
        self.assertEqual(len(canonicals), TARGET_COUNT)
        openings = []
        closings = []
        for note in self.notes:
            self.assertGreaterEqual(len(note["commentary"]), max(220, int(len(note["quote"]) * 1.25)))
            self.assertGreaterEqual(len(re.findall(r"다\.", note["commentary"])), 4)
            self.assertLessEqual(len(re.findall(r"다\.", note["commentary"])), 8)
            self.assertLessEqual(len(re.split(r"(?<=[.!?])\s+", note["quote"])), 2)
            self.assertEqual(note["quote"].count("“"), note["quote"].count("”"))
            self.assertEqual(note["quote"].count('"') % 2, 0)
            self.assertEqual(
                len(note["tags"]),
                len({re.sub(r"\W+", "", tag).casefold() for tag in note["tags"]}),
            )
            sentences = re.split(r"(?<=다\.)\s+", note["commentary"])
            openings.append(re.sub(r"\W+", "", sentences[0]).casefold())
            closings.append(re.sub(r"\W+", "", sentences[-1]).casefold())
            parsed = urlparse(note["source_url"])
            if note.get("content_kind", "source_quote") == "source_quote":
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.netloc, {"www.gutenberg.org", "ko.wikisource.org"})
                self.assertIn(note["source_language"], {"en", "ko"})
                self.assertTrue("퍼블릭 도메인" in note["rights_note"] or "copyright: false" in note["rights_note"])
            else:
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.netloc, {"library.ltikorea.or.kr", "ko.wikisource.org", "www.penguin.co.uk", "www.lepetitprince.com"})
                self.assertIn("직접 인용 없음", note["rights_note"])
            self.assertNotIn("번역:", note["quote"])
        self.assertEqual(len(openings), len(set(openings)))
        self.assertEqual(len(closings), len(set(closings)))

        authors = Counter(note["source_author"] for note in self.notes)
        works = Counter(note["source_work"] for note in self.notes)
        tags = Counter(tag for note in self.notes for tag in note["tags"])
        self.assertLessEqual(authors.most_common(1)[0][1] / TARGET_COUNT, 0.12)
        self.assertLessEqual(works.most_common(1)[0][1] / TARGET_COUNT, 0.12)
        self.assertLessEqual(tags.most_common(1)[0][1] / sum(tags.values()), 0.18)
        self.assertGreaterEqual(len(authors), 30)
        self.assertGreaterEqual(len(works), 30)

    def test_generated_page_counts_pagination_and_seo(self):
        detail_paths = [
            LITERATURE / note["slug"] / "index.html" for note in self.notes
        ]
        self.assertTrue(all(path.is_file() for path in detail_paths))
        list_paths = [LITERATURE / "index.html"] + [
            LITERATURE / "page" / str(page) / "index.html"
            for page in range(2, TARGET_LIST_PAGES + 1)
        ]
        self.assertTrue(all(path.is_file() for path in list_paths))
        self.assertIn('id="literatureSearch"', list_paths[0].read_text(encoding="utf-8"))
        last_page_cards = TARGET_COUNT % PAGE_SIZE or PAGE_SIZE
        expected_cards = [PAGE_SIZE] * (TARGET_LIST_PAGES - 1) + [last_page_cards]
        for path, expected in zip(list_paths, expected_cards):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count('class="note-card"'), expected)

        json_ld_re = re.compile(
            r'<script type="application/ld\+json">(.*?)</script>', re.S
        )
        for note, path in zip(self.notes, detail_paths):
            text = path.read_text(encoding="utf-8")
            canonical = f"{ORIGIN}/literature/{note['slug']}/"
            self.assertIn(f'<link rel="canonical" href="{canonical}">', text)
            self.assertIn('<meta property="og:type" content="article">', text)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', text)
            self.assertIn('property="article:published_time"', text)
            self.assertIn('property="article:author"', text)
            self.assertIn("전체 목록", text)
            self.assertIn('href="/"', text)
            if isinstance(note.get("seo_sections"), dict):
                for section_text in note["seo_sections"].values():
                    self.assertIn(html.escape(section_text, quote=True), text)
            else:
                self.assertIn(html.escape(note["commentary"], quote=True), text)
            blocks = json_ld_re.findall(text)
            self.assertEqual(len(blocks), 1)
            graph = json.loads(blocks[0].replace("<\\/", "</"))
            self.assertEqual(
                {entry["@type"] for entry in graph},
                {"BlogPosting", "BreadcrumbList"},
            )
            self.assertIn(html.escape(note["quote"], quote=True), text)

    def test_sitemap_rss_and_static_links(self):
        sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in sitemap.findall("s:url/s:loc", namespace)]
        self.assertEqual(len(locations), TARGET_SITEMAP_URLS)
        self.assertEqual(len(locations), len(set(locations)))
        self.assertEqual(
            sum(url == f"{ORIGIN}/literature/{note['slug']}/" for url in locations for note in self.notes),
            TARGET_COUNT,
        )

        rss = ET.parse(LITERATURE / "rss.xml")
        items = rss.findall("./channel/item")
        self.assertEqual(len(items), TARGET_COUNT)
        latest_note = build_literature.sort_for_publication(self.notes)[0]
        self.assertEqual(
            items[0].findtext("link"),
            f"{ORIGIN}/literature/{latest_note['slug']}/",
        )
        self.assertEqual(
            len({item.findtext("guid") for item in items}),
            TARGET_COUNT,
        )
        rss_descriptions = {
            item.findtext("guid"): item.findtext("description") for item in items
        }
        for note in self.notes:
            self.assertEqual(
                rss_descriptions[f"{ORIGIN}/literature/{note['slug']}/"],
                note["commentary"],
            )

        href_re = re.compile(r'href="([^"]+)"')
        html_paths = [LITERATURE / "index.html"]
        html_paths += list((LITERATURE / "page").glob("*/index.html"))
        html_paths += [LITERATURE / note["slug"] / "index.html" for note in self.notes]
        for source_path in html_paths:
            for href in href_re.findall(source_path.read_text(encoding="utf-8")):
                if not href.startswith("/") or href.startswith("//"):
                    continue
                local = href.split("#", 1)[0].split("?", 1)[0]
                target = ROOT / local.lstrip("/")
                if local.endswith("/"):
                    target /= "index.html"
                self.assertTrue(target.exists(), f"{source_path}: {href}")

    def test_homepage_six_notes_and_board_regression(self):
        homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        cards = re.search(
            r"<!-- LITERATURE_LATEST_ITEMS:START -->(.*?)"
            r"<!-- LITERATURE_LATEST_ITEMS:END -->",
            homepage,
            re.S,
        )
        self.assertIsNotNone(cards)
        self.assertEqual(cards.group(1).count('class="note-card"'), 6)
        self.assertIn('href="/literature/"', homepage)
        self.assertIn('id="board"', homepage)
        self.assertIn('id="publicBoardForm"', homepage)
        self.assertIn('id="publicPostList"', homepage)
        self.assertIn('href="#board"', homepage)
        server_text = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn('"/api/board/posts"', server_text)
        self.assertTrue((ROOT / "Dockerfile").is_file())

    def test_z_generator_is_idempotent(self):
        tracked_outputs = [ROOT / "index.html", ROOT / "sitemap.xml", LITERATURE / "rss.xml"]
        tracked_outputs += [LITERATURE / note["slug"] / "index.html" for note in self.notes]
        before = {path: path.read_bytes() for path in tracked_outputs}
        completed = subprocess.run(
            [sys.executable, "scripts/build_literature.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"built {TARGET_COUNT} detail pages", completed.stdout)
        after = {path: path.read_bytes() for path in tracked_outputs}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
