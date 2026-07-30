import html
import json
import re
import subprocess
import sys
import unittest
from collections import Counter
from html.parser import HTMLParser
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


class HomepageContractParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.links = []
        self.images = []
        self.scripts = []
        self._json_ld = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        element_id = attributes.get("id")
        if element_id:
            self.ids[element_id] += 1
        if tag == "a":
            self.links.append(attributes)
        if tag == "img":
            self.images.append(attributes)
        if tag == "script":
            self._json_ld = (
                [] if attributes.get("type") == "application/ld+json" else None
            )

    def handle_data(self, data):
        if self._json_ld is not None:
            self._json_ld.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._json_ld is not None:
            self.scripts.append("".join(self._json_ld))
            self._json_ld = None


class StaticLiteratureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(CONTENT.glob("*.json"), key=lambda item: int(item.stem))
        cls.notes = [
            json.loads(path.read_text(encoding="utf-8")) for path in cls.paths
        ]
        cls.homepage = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.homepage_parser = HomepageContractParser()
        cls.homepage_parser.feed(cls.homepage)

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
        self.assertNotIn("이후 홈페이지에 남기고 싶은 글", homepage)
        compact_homepage = re.sub(r"\s+", "", homepage)
        self.assertRegex(
            compact_homepage,
            r"\.board-copyh2\{[^}]*white-space:nowrap",
        )
        server_text = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn('"/api/board/posts"', server_text)
        self.assertTrue((ROOT / "Dockerfile").is_file())

    def test_homepage_sources_hide_structured_data_description_and_seo_card(self):
        homepage = self.homepage
        self.assertIn("소설가 이후에 대한 공개 정보를 백과·포털 전반에서 확인할 수 있습니다.", homepage)
        self.assertNotIn("각 소스는 구조화 데이터", homepage)
        self.assertNotIn("SEO · 색인 지표", homepage)
        self.assertNotIn("검색엔진 노출 상태", homepage)
        self.assertIn('<script type="application/ld+json">', homepage)
        self.assertIn('"sameAs": [', homepage)
        self.assertIn('<meta property="og:title"', homepage)
        self.assertTrue((ROOT / "sitemap.xml").is_file())
        self.assertTrue((ROOT / "robots.txt").is_file())

    def test_homepage_preserves_seo_json_ld_canonical_and_open_graph(self):
        homepage = self.homepage
        self.assertIn(
            '<link rel="canonical" href="https://xn--hu5b23z.com/">',
            homepage,
        )
        for property_name in (
            "og:type", "og:site_name", "og:title", "og:description",
            "og:url", "og:image", "og:locale",
        ):
            self.assertRegex(
                homepage,
                rf'<meta\s+property="{re.escape(property_name)}"\s+content="[^"]+">',
            )
        self.assertEqual(len(self.homepage_parser.scripts), 1)
        graph = json.loads(self.homepage_parser.scripts[0])["@graph"]
        graph_types = [entry["@type"] for entry in graph]
        self.assertIn("Person", graph_types)
        self.assertIn("WebSite", graph_types)
        self.assertGreaterEqual(graph_types.count("Book"), 3)

    def test_homepage_generator_markers_remain_unique_and_ordered(self):
        homepage = self.homepage
        marker_pairs = (
            ("LITERATURE_LATEST_ITEMS:START", "LITERATURE_LATEST_ITEMS:END"),
            ("BOARD_LITERATURE_ITEMS:START", "BOARD_LITERATURE_ITEMS:END"),
        )
        for start, end in marker_pairs:
            start_marker = f"<!-- {start} -->"
            end_marker = f"<!-- {end} -->"
            self.assertEqual(homepage.count(start_marker), 1)
            self.assertEqual(homepage.count(end_marker), 1)
            self.assertLess(homepage.index(start_marker), homepage.index(end_marker))

    def test_homepage_literal_javascript_ids_exist_exactly_once(self):
        javascript_ids = set(re.findall(
            r'(?:getElementById\(|\$\()\s*["\']([A-Za-z][\w:-]*)["\']\s*\)',
            self.homepage,
        ))
        self.assertGreaterEqual(len(javascript_ids), 20)
        for element_id in sorted(javascript_ids):
            self.assertEqual(
                self.homepage_parser.ids[element_id],
                1,
                f"JavaScript-consumed id must exist exactly once: {element_id}",
            )

    def test_homepage_stella_storage_keys_and_api_contract_are_unchanged(self):
        homepage = self.homepage
        expected_keys = {
            "users": "stella_users_v3",
            "current": "stella_current_user_v3",
            "rooms": "stella_rooms_v3",
            "projects": "stella_projects_v1",
            "posts": "stella_posts_v3",
        }
        store_keys_match = re.search(
            r"const\s+storeKeys\s*=\s*\{(?P<body>[^}]+)\}",
            homepage,
        )
        self.assertIsNotNone(store_keys_match)
        parsed_keys = dict(re.findall(
            r'(\w+)\s*:\s*["\']([^"\']+)["\']',
            store_keys_match.group("body"),
        ))
        self.assertEqual(parsed_keys, expected_keys)
        self.assertIn('const STELLA_API_URL = "/api/chat";', homepage)
        self.assertIn('const BOARD_API_URL = "/api/board/posts";', homepage)
        self.assertIn("passwordHashCandidates", homepage)
        self.assertIn('crypto.subtle.digest("SHA-256"', homepage)

    def test_homepage_blank_links_are_isolated_from_opener(self):
        blank_links = [
            link for link in self.homepage_parser.links
            if link.get("target", "").casefold() == "_blank"
        ]
        self.assertGreater(len(blank_links), 10)
        for link in blank_links:
            rel_tokens = set(link.get("rel", "").casefold().split())
            self.assertIn("noopener", rel_tokens, link.get("href"))

    def test_homepage_contains_no_person_image_or_person_placeholder(self):
        self.assertEqual(
            self.homepage_parser.images,
            [],
            "The homepage must express the author brand without static images.",
        )
        forbidden_copy = (
            "인물사진", "인물 사진", "개인사진", "개인 사진", "프로필 사진",
            "ai 인물", "인물 실루엣", "얼굴 이미지", "portrait placeholder",
        )
        homepage_casefold = self.homepage.casefold()
        for phrase in forbidden_copy:
            self.assertNotIn(phrase.casefold(), homepage_casefold)

    def test_homepage_editorial_design_tokens_match_approved_palette(self):
        token_blocks = re.findall(r":root\s*\{(?P<body>[^}]+)\}", self.homepage)
        self.assertGreaterEqual(len(token_blocks), 1)
        normalized = re.sub(r"\s+", "", "".join(token_blocks)).casefold()
        expected_tokens = {
            "--paper": "#f4f0e8",
            "--paper-light": "#faf8f3",
            "--ink": "#151a24",
            "--body-ink": "#45413c",
            "--brass": "#9c7a45",
        }
        for name, value in expected_tokens.items():
            self.assertIn(f"{name}:{value}", normalized)
        self.assertIn("--font-serif:", normalized)
        self.assertIn("--font-sans:", normalized)

    def test_homepage_has_keyboard_focus_and_reduced_motion_contracts(self):
        compact = re.sub(r"\s+", "", self.homepage)
        self.assertIn(":focus-visible", self.homepage)
        self.assertRegex(
            compact,
            r":focus-visible\{[^}]*outline:(?:[^;}]*\s)?(?:2px|3px)",
        )
        self.assertIn("@media(prefers-reduced-motion:reduce)", compact)
        reduced_motion = re.search(
            r"@media\(prefers-reduced-motion:reduce\)\{(?P<body>.*?)\}\}",
            compact,
            re.S,
        )
        self.assertIsNotNone(reduced_motion)
        self.assertRegex(
            reduced_motion.group("body"),
            r"(animation-duration:\.01ms|animation:none)",
        )

    def test_homepage_mobile_navigation_and_hero_ctas_are_explicit(self):
        homepage = self.homepage
        self.assertEqual(self.homepage_parser.ids["mobileNavToggle"], 1)
        self.assertEqual(self.homepage_parser.ids["primaryNav"], 1)
        self.assertRegex(
            homepage,
            r'id="mobileNavToggle"[^>]*aria-controls="primaryNav"'
            r'[^>]*aria-expanded="false"',
        )
        self.assertIn('class="hero-actions"', homepage)
        hero_actions = re.search(
            r'<div class="hero-actions">(?P<body>.*?)</div>',
            homepage,
            re.S,
        )
        self.assertIsNotNone(hero_actions)
        self.assertIn('href="#works"', hero_actions.group("body"))
        self.assertIn('href="#about"', hero_actions.group("body"))
        self.assertIn('getElementById("mobileNavToggle")', homepage)
        self.assertIn('getElementById("primaryNav")', homepage)

    def test_homepage_stella_entry_open_close_and_auth_contract(self):
        homepage = self.homepage
        for element_id in (
            "stellaButton", "stella", "authScreen", "loginTab", "signupTab",
            "authForm", "stellaApp", "closeStellaBtn", "closeStellaAuthBtn",
            "stellaDialogTitle",
        ):
            self.assertEqual(self.homepage_parser.ids[element_id], 1)
        self.assertRegex(
            homepage,
            r'id="stellaButton"[^>]*aria-controls="stella"'
            r'[^>]*aria-expanded="false"',
        )
        self.assertIn('<body data-stella-ui="dormant">', homepage)
        compact = re.sub(r"\s+", "", homepage)
        self.assertIn(
            'body[data-stella-ui="dormant"]#stellaButton#stellaButton',
            compact,
        )
        self.assertRegex(
            compact,
            r'body\[data-stella-ui="dormant"\]#stella#stella\{'
            r'[^}]*display:none!important',
        )
        self.assertRegex(
            homepage,
            r'<button[^>]*id="closeStellaBtn"[^>]*aria-label="[^"]+"',
        )
        self.assertRegex(
            homepage,
            r'id="stella"[^>]*role="dialog"[^>]*aria-modal="true"'
            r'[^>]*aria-labelledby="stellaDialogTitle"',
        )
        self.assertIn('setAttribute("inert", "")', homepage)
        self.assertIn('removeAttribute("inert")', homepage)
        self.assertIn('event.key === "Escape"', homepage)
        self.assertNotIn('id="stella-icon-disabled-css"', homepage)
        self.assertNotIn('id="stella-icon-disabled-runtime"', homepage)
        self.assertIn('stellaBtn.focus()', homepage)
        self.assertRegex(
            homepage,
            r'setAttribute\(["\']aria-expanded["\'],\s*["\']true["\']\)',
        )
        self.assertRegex(
            homepage,
            r'setAttribute\(["\']aria-expanded["\'],\s*["\']false["\']\)',
        )

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
