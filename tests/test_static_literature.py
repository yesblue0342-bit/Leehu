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

from scripts import append_love_literature_20260806 as append_love_batch
from scripts import build_literature
from literature_index_policy import is_note_indexable, load_index_policy


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
LITERATURE = ROOT / "literature"
ORIGIN = "https://xn--hu5b23z.com"
TARGET_COUNT = 2781
TARGET_INDEXABLE_COUNT = 2282
TARGET_NOINDEX_COUNT = 499
PAGE_SIZE = 25
TARGET_LIST_PAGES = 92
TARGET_SITEMAP_URLS = 2292
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
    def test_collection_url_allowlist_rejects_userinfo_and_unknown_hosts(self) -> None:
        hosts = build_literature.COLLECTION_SOURCE_HOSTS
        self.assertTrue(
            build_literature.is_allowed_https_url(
                "https://product.kyobobook.co.kr/detail/example", hosts
            )
        )
        self.assertFalse(
            build_literature.is_allowed_https_url(
                "https://trusted.example@attacker.example/x", hosts
            )
        )
        self.assertFalse(
            build_literature.is_allowed_https_url("https://attacker.example/x", hosts)
        )

    @classmethod
    def setUpClass(cls):
        cls.paths = sorted(CONTENT.glob("*.json"), key=lambda item: int(item.stem))
        cls.notes = [
            json.loads(path.read_text(encoding="utf-8")) for path in cls.paths
        ]
        cls.index_policy = load_index_policy(build_literature.INDEX_POLICY_PATH, cls.notes)
        cls.indexable_notes = [
            note for note in cls.notes if is_note_indexable(note, cls.index_policy)
        ]
        cls.noindex_notes = [
            note for note in cls.notes if not is_note_indexable(note, cls.index_policy)
        ]
        cls.indexable_ids = {note["id"] for note in cls.indexable_notes}
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

    def test_20260806_love_batch_count_ids_and_collection(self) -> None:
        batch = self.notes[1466:1966]
        self.assertEqual(len(batch), 500)
        self.assertEqual(
            {note["id"] for note in batch},
            {f"20260806_leehu_literature_{sequence:03d}" for sequence in range(1, 501)},
        )
        collection = next(
            note for note in batch if note["title"] == "사랑에 관한 소설과 시집 10선"
        )
        self.assertEqual(collection["id"], "20260806_leehu_literature_500")
        self.assertEqual(collection["content_kind"], "collection_reflection")
        self.assertEqual(len(collection["collection_sections"]), 10)
        self.assertEqual(
            sum(note.get("content_kind") == "source_quote" for note in batch),
            499,
        )

    def test_20260819_leehu_own_work_batch_is_complete_and_structured(self) -> None:
        batch = self.notes[1971:2071]
        self.assertEqual(len(batch), 100)
        self.assertEqual(
            {note["id"] for note in batch},
            {
                f"20260819_leehu_literature_{sequence:03d}"
                for sequence in range(1, 101)
            },
        )
        self.assertEqual(
            Counter(note["source_work"] for note in batch),
            Counter(
                {
                    "연(戀)": 20,
                    "데자뷔": 20,
                    "소나기": 20,
                    "환상": 20,
                    "별이 빛나는 밤에": 20,
                }
            ),
        )
        self.assertTrue(all(note["source_author"] == "이후" for note in batch))
        self.assertTrue(all(note["author"] == "소설가 이후" for note in batch))
        self.assertTrue(
            all(note.get("content_kind") == "original_reflection" for note in batch)
        )
        self.assertTrue(
            all("직접 인용 없음" in note["rights_note"] for note in batch)
        )
        self.assertTrue(
            all(set(note.get("seo_sections", {})) == build_literature.SEO_SECTION_KEYS for note in batch)
        )
        long_sentences = []
        for note in batch:
            public_prose = [
                note["quote"],
                note["commentary"],
                *note["seo_sections"].values(),
            ]
            self.assertTrue(
                all(
                    marker not in " ".join(public_prose)
                    for marker in (
                        "공식 카탈로그",
                        "주제표목",
                        "확인된 관계 초점",
                        "원문 확인 필요",
                    )
                )
            )
            for prose in public_prose:
                long_sentences.extend(
                    normalized
                    for sentence in build_literature.prose_sentences(prose)
                    if len(
                        normalized := re.sub(r"\W+", "", sentence).casefold()
                    ) >= 25
                )
        self.assertEqual(len(long_sentences), len(set(long_sentences)))

    def test_20260823_leehu_500_batch_is_structured_and_unique(self) -> None:
        batch = self.notes[2271:2771]
        self.assertEqual(len(batch), 500)
        self.assertEqual(
            {note["id"] for note in batch},
            {f"20260823_leehu_literature_{sequence:03d}" for sequence in range(1, 501)},
        )
        self.assertEqual(
            Counter(note["source_work"] for note in batch),
            Counter({"연(戀)": 100, "데자뷔": 100, "소나기": 100, "환상": 100, "별이 빛나는 밤에": 100}),
        )
        self.assertTrue(all(note["source_author"] == "이후" for note in batch))
        self.assertTrue(all(note["author"] == "소설가 이후" for note in batch))
        self.assertTrue(all(note.get("content_kind") == "original_reflection" for note in batch))
        self.assertTrue(all("직접 인용 없음" in note["rights_note"] for note in batch))
        self.assertTrue(all(set(note.get("seo_sections", {})) == build_literature.SEO_SECTION_KEYS for note in batch))
        self.assertEqual(len({note["slug"] for note in batch}), 500)
        self.assertTrue(all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", note["slug"]) for note in batch))
        long_sentences = []
        for note in batch:
            for prose in [note["quote"], note["commentary"], *note["seo_sections"].values()]:
                long_sentences.extend(
                    normalized
                    for sentence in build_literature.prose_sentences(prose)
                    if len(normalized := re.sub(r"\W+", "", sentence).casefold()) >= 25
                )
        self.assertEqual(len(long_sentences), len(set(long_sentences)))

    def test_versioned_index_policy_keeps_collection_and_excludes_repetitive_batch(self) -> None:
        self.assertEqual(self.index_policy.version, 1)
        self.assertTrue(self.index_policy.default_indexable)
        self.assertEqual(len(self.indexable_notes), TARGET_INDEXABLE_COUNT)
        self.assertEqual(len(self.noindex_notes), TARGET_NOINDEX_COUNT)
        self.assertEqual(
            {note["id"] for note in self.noindex_notes},
            {
                f"20260806_leehu_literature_{sequence:03d}"
                for sequence in range(1, 500)
            },
        )
        self.assertIn("20260806_leehu_literature_500", self.indexable_ids)

    def test_20260806_batch_avoids_repeated_boilerplate_and_raw_anchor_titles(self) -> None:
        batch = [
            note for note in self.notes[1466:1966]
            if note.get("content_kind") == "source_quote"
        ]
        forbidden_phrases = (
            "사랑을 추상적인 선언으로 밀어 올리기보다",
            "가까워지고 싶은 마음과 자기 자리를 지키려는 마음",
            "사랑을 소유가 아니라 타인의 시간과 선택을 존중하는 태도",
            "빠른 확신보다 관계의 맥락을 살피게 한다",
        )
        for note in batch:
            combined = note["commentary"] + " " + " ".join(note["seo_sections"].values())
            self.assertTrue(all(phrase not in combined for phrase in forbidden_phrases))
            self.assertNotRegex(note["title"], r"에서 [A-Za-z'-]+와 [A-Za-z'-]+로 읽는")
            self.assertNotRegex(note["quote"].strip(), r":(?:—|-)?[’”\"]?$")

    def test_append_batch_verifier_rejects_any_changed_note(self) -> None:
        expected = [
            {"id": "20260806_leehu_literature_500", "title": "collection"},
            {"id": "20260806_leehu_literature_001", "title": "quote"},
        ]
        changed = [dict(note) for note in expected]
        changed[1]["title"] = "tampered"
        errors = append_love_batch.batch_mismatches(expected, changed)
        self.assertEqual(errors, ["20260806_leehu_literature_001"])

    def test_relationship_theme_rejects_ambiguous_general_words(self) -> None:
        for sentence in (
            "The shoal was very long and uninterrupted.",
            "Take care to close the door.",
            "I remember the old road.",
            "I hope the weather improves.",
            "The criminal had a child-brain.",
            "The mistress ordered the household to work.",
            "I remembered my once affectionate old mistress.",
            "The officer's wife took the children to school.",
        ):
            with self.assertRaises(ValueError):
                append_love_batch.keyword_theme(sentence, 1)
        self.assertEqual(
            append_love_batch.keyword_theme("They protected their friendship through winter.", 1),
            ("우정", "friendship"),
        )
        self.assertEqual(
            append_love_batch.keyword_theme("He married her in spring.", 1),
            ("동반", "companionship"),
        )
        self.assertEqual(
            append_love_batch.keyword_theme("Her father loved her mother.", 1),
            ("가족 사랑", "family-love"),
        )
        with self.assertRaises(ValueError):
            append_love_batch.keyword_theme("Her father and mother waited at home.", 1)

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

    def test_collection_detail_page_renders_ten_work_sections(self) -> None:
        note = dict(self.notes[-1])
        note.update({
            "content_kind": "collection_reflection",
            "title": "사랑에 관한 소설과 시집 10선",
            "quote": "사랑을 서로 다른 열 개의 목소리로 읽어 보는 큐레이션입니다.",
            "rights_note": "모든 보호 작품에 대해 원문과 번역문을 직접 인용하지 않음.",
            "collection_introduction": "사랑은 기억과 선택, 기다림과 상실 속에서 다른 얼굴을 드러냅니다.",
            "collection_closing": "열 권의 책은 사랑을 하나의 정답 대신 오래 남는 질문으로 돌려줍니다.",
            "collection_sections": [
                {
                    "title": f"작품 {index}",
                    "author": f"작가 {index}",
                    "country_genre": "국가 / 소설",
                    "core_theme": f"핵심 주제 {index}",
                    "summary": f"주요 내용 {index}",
                    "love_form": f"사랑의 형태 {index}",
                    "literary_question": f"문학적으로 생각할 점 {index}",
                    "one_line": f"한 줄 감상 {index}",
                    "source_url": "https://www.penguin.co.uk/",
                }
                for index in range(1, 11)
            ],
        })

        page = build_literature.detail_page(note, None, None)

        self.assertEqual(page.count('class="collection-work"'), 10)
        self.assertIn("<h2>1. 작품 1</h2>", page)
        self.assertIn("<dt>작품의 핵심 주제</dt>", page)
        self.assertIn("<dt>문학노트 한 줄 감상</dt>", page)
        self.assertIn("열 권의 책은 사랑을 하나의 정답", page)
        self.assertIn("저작권 안내", page)
        self.assertIn("모든 보호 작품에 대해 원문과 번역문을 직접 인용하지 않음", page)
        self.assertIn('class="collection-deck"', page)

    def test_collection_validation_accepts_complete_ten_work_payload(self) -> None:
        note = {
            "collection_introduction": "사랑을 읽는 열 가지 길을 소개합니다.",
            "collection_closing": "열 권의 책이 남긴 질문을 오래 기억합니다.",
            "collection_sections": [
                {
                    "title": f"작품 {index}",
                    "author": f"작가 {index}",
                    "country_genre": "국가 / 소설",
                    "core_theme": f"주제 {index}",
                    "summary": f"내용 {index}",
                    "love_form": f"사랑 {index}",
                    "literary_question": f"생각 {index}",
                    "one_line": f"감상 {index}",
                    "source_url": "https://www.penguin.co.uk/",
                }
                for index in range(1, 11)
            ],
        }
        errors = []

        build_literature.validate_collection_note(note, "sample.json", errors)

        self.assertEqual(errors, [])

        note["collection_sections"][0]["source_url"] = "https://attacker.example/phish"
        errors = []
        build_literature.validate_collection_note(note, "sample.json", errors)
        self.assertTrue(any("approved host" in error for error in errors))

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
            content_kind = note.get("content_kind", "source_quote")
            if content_kind == "source_quote":
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(parsed.netloc, {"www.gutenberg.org", "ko.wikisource.org"})
                self.assertIn(note["source_language"], {"en", "ko"})
                self.assertTrue("퍼블릭 도메인" in note["rights_note"] or "copyright: false" in note["rights_note"])
            elif content_kind == "collection_reflection":
                self.assertEqual(parsed.scheme, "https")
                self.assertIn("직접 인용 없음", note["rights_note"])
                self.assertEqual(len(note["collection_sections"]), 10)
                self.assertTrue(all(urlparse(work["source_url"]).scheme == "https" for work in note["collection_sections"]))
            else:
                self.assertEqual(parsed.scheme, "https")
                self.assertIn(
                    parsed.netloc,
                    {
                        "ebook-product.kyobobook.co.kr",
                        "library.ltikorea.or.kr",
                        "ko.wikisource.org",
                        "www.penguin.co.uk",
                        "www.lepetitprince.com",
                    },
                )
                self.assertIn("직접 인용 없음", note["rights_note"])
            self.assertNotIn("번역:", note["quote"])
        self.assertEqual(len(openings), len(set(openings)))
        self.assertEqual(len(closings), len(set(closings)))

        authors = Counter(note["source_author"] for note in self.notes)
        works = Counter(note["source_work"] for note in self.notes)
        tags = Counter(tag for note in self.notes for tag in note["tags"])
        self.assertLessEqual(authors.most_common(1)[0][1] / TARGET_COUNT, 0.30)
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
        last_page_cards = TARGET_INDEXABLE_COUNT % PAGE_SIZE or PAGE_SIZE
        expected_cards = [PAGE_SIZE] * (TARGET_LIST_PAGES - 1) + [last_page_cards]
        for page_number, (path, expected) in enumerate(
            zip(list_paths, expected_cards), 1
        ):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count('class="note-card"'), expected)
            expected_robots = "index, follow" if page_number == 1 else "noindex, follow"
            self.assertIn(
                f'<meta name="robots" content="{expected_robots}">', text
            )
            self.assertIn('<meta name="twitter:image" content="https://xn--hu5b23z.com/og-image.jpg">', text)
            self.assertIn('<meta name="twitter:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">', text)
        card_slugs = []
        for path in list_paths:
            card_slugs.extend(
                re.findall(
                    r'<a class="note-card" href="/literature/([^/]+)/">',
                    path.read_text(encoding="utf-8"),
                )
            )
        self.assertEqual(len(card_slugs), TARGET_INDEXABLE_COUNT)
        self.assertEqual(len(card_slugs), len(set(card_slugs)))
        self.assertEqual(
            set(card_slugs), {note["slug"] for note in self.indexable_notes}
        )

        json_ld_re = re.compile(
            r'<script type="application/ld\+json">(.*?)</script>', re.S
        )
        for note, path in zip(self.notes, detail_paths):
            text = path.read_text(encoding="utf-8")
            canonical = f"{ORIGIN}/literature/{note['slug']}/"
            search_title = build_literature.seo_title(note["title"])
            self.assertIn(f"<title>{html.escape(search_title)}</title>", text)
            self.assertLessEqual(len(search_title), 60)
            self.assertIn(
                f'<meta property="og:title" content="{html.escape(search_title)}">',
                text,
            )
            self.assertIn(
                f'<meta name="twitter:title" content="{html.escape(search_title)}">',
                text,
            )
            self.assertIn(f'<link rel="canonical" href="{canonical}">', text)
            self.assertIn('<meta property="og:type" content="article">', text)
            self.assertIn('<meta name="twitter:card" content="summary_large_image">', text)
            self.assertIn('<meta property="og:image:width" content="1200">', text)
            self.assertIn('<meta property="og:image:height" content="630">', text)
            self.assertIn('<meta property="og:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">', text)
            self.assertIn('<meta name="twitter:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">', text)
            self.assertIn('property="article:published_time"', text)
            self.assertIn('property="article:author"', text)
            expected_robots = (
                "index, follow"
                if note["id"] in self.indexable_ids
                else "noindex, follow"
            )
            self.assertIn(
                f'<meta name="robots" content="{expected_robots}">', text
            )
            self.assertIn("전체 목록", text)
            self.assertIn('href="/"', text)
            if note.get("content_kind") == "collection_reflection":
                self.assertIn(html.escape(note["collection_introduction"], quote=True), text)
                self.assertIn(html.escape(note["collection_closing"], quote=True), text)
                self.assertEqual(text.count('class="collection-work"'), 10)
                for work in note["collection_sections"]:
                    self.assertIn(html.escape(work["one_line"], quote=True), text)
            elif isinstance(note.get("seo_sections"), dict):
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
            article = next(entry for entry in graph if entry["@type"] == "BlogPosting")
            self.assertEqual(article["author"]["@id"], f"{ORIGIN}/#person")
            self.assertEqual(article["author"]["url"], f"{ORIGIN}/author/")
            self.assertEqual(
                article["image"],
                {
                    "@type": "ImageObject",
                    "url": f"{ORIGIN}/og-image.jpg",
                    "width": 1200,
                    "height": 630,
                },
            )
            self.assertIn(
                'href="/author/">소설가 이후 공식 프로필</a>', text
            )
            self.assertIn(html.escape(note["quote"], quote=True), text)
            if note["id"] not in self.indexable_ids:
                post_nav = re.search(
                    r'<nav class="post-nav".*?</nav>', text, re.S
                )
                self.assertIsNotNone(post_nav)
                self.assertNotIn('href="/literature/', post_nav.group(0))

    def test_generated_detail_directories_match_source_slugs(self) -> None:
        expected = {note["slug"] for note in self.notes}
        actual = {
            path.parent.name
            for path in LITERATURE.glob("*/index.html")
            if path.parent.name != "page"
        }
        self.assertEqual(actual, expected)

    def test_seo_update_pages_are_preserved_in_generated_sitemap(self):
        self.assertEqual(
            build_literature.additional_sitemap_urls(),
            [
                (f"{ORIGIN}/seo-updates/", "2026-08-26"),
                (
                    f"{ORIGIN}/seo-updates/2026-08-18-leehu-dadb7cfc/",
                    "2026-08-18",
                ),
                (
                    f"{ORIGIN}/seo-updates/2026-08-19-leehu-44b78db6/",
                    "2026-08-19",
                ),
                (
                    f"{ORIGIN}/seo-updates/2026-08-23-leehu-80c783be/",
                    "2026-08-23",
                ),
                (
                    f"{ORIGIN}/seo-updates/2026-08-24-leehu-ef782845/",
                    "2026-08-24",
                ),
                (
                    f"{ORIGIN}/seo-updates/2026-08-25-leehu-1cf75bdb/",
                    "2026-08-25",
                ),
                (
                    f"{ORIGIN}/seo-updates/2026-08-26-leehu-022406d5/",
                    "2026-08-26",
                ),
            ],
        )

    def test_sitemap_rss_and_static_links(self):
        sitemap = ET.parse(ROOT / "sitemap.xml").getroot()
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in sitemap.findall("s:url/s:loc", namespace)]
        self.assertEqual(len(locations), TARGET_SITEMAP_URLS)
        self.assertEqual(len(locations), len(set(locations)))
        sitemap_dates = {
            node.findtext("s:loc", namespaces=namespace): node.findtext(
                "s:lastmod", namespaces=namespace
            )
            for node in sitemap.findall("s:url", namespace)
        }
        latest_date = max(note["published_at"][:10] for note in self.notes)
        latest_note = build_literature.sort_for_publication(self.indexable_notes)[0]
        self.assertEqual(sitemap_dates[f"{ORIGIN}/"], latest_date)
        self.assertIn(f"{ORIGIN}/author/", locations)
        self.assertEqual(
            sitemap_dates[f"{ORIGIN}/literature/{latest_note['slug']}/"],
            latest_note["published_at"][:10],
        )
        self.assertEqual(
            {
                url
                for url in locations
                if url.startswith(f"{ORIGIN}/literature/")
                and url != f"{ORIGIN}/literature/"
            },
            {
                f"{ORIGIN}/literature/{note['slug']}/"
                for note in self.indexable_notes
            },
        )
        self.assertFalse(any("/literature/page/" in url for url in locations))

        rss = ET.parse(LITERATURE / "rss.xml")
        items = rss.findall("./channel/item")
        self.assertEqual(len(items), TARGET_INDEXABLE_COUNT)
        latest_note = build_literature.sort_for_publication(self.indexable_notes)[0]
        self.assertEqual(
            items[0].findtext("link"),
            f"{ORIGIN}/literature/{latest_note['slug']}/",
        )
        self.assertEqual(
            len({item.findtext("guid") for item in items}),
            TARGET_INDEXABLE_COUNT,
        )
        rss_descriptions = {
            item.findtext("guid"): item.findtext("description") for item in items
        }
        for note in self.indexable_notes:
            self.assertEqual(
                rss_descriptions[f"{ORIGIN}/literature/{note['slug']}/"],
                note["commentary"],
            )
        for note in self.noindex_notes:
            self.assertNotIn(
                f"{ORIGIN}/literature/{note['slug']}/", rss_descriptions
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

    def test_noindex_notes_are_absent_from_every_indexable_discovery_surface(self) -> None:
        discovery_paths = [
            ROOT / "index.html",
            ROOT / "sitemap.xml",
            LITERATURE / "rss.xml",
            LITERATURE / "index.html",
        ]
        discovery_paths.extend((LITERATURE / "page").glob("*/index.html"))
        discovery_paths.extend(
            LITERATURE / note["slug"] / "index.html"
            for note in self.indexable_notes
        )
        discovered = "\n".join(
            path.read_text(encoding="utf-8") for path in discovery_paths
        )
        for note in self.noindex_notes:
            self.assertNotIn(f"/literature/{note['slug']}/", discovered)

    def test_filtered_detail_navigation_uses_only_immediate_indexable_neighbors(self) -> None:
        ordered = build_literature.sort_for_publication(self.indexable_notes)
        for position, note in enumerate(ordered):
            page = (LITERATURE / note["slug"] / "index.html").read_text(
                encoding="utf-8"
            )
            navigation = re.search(
                r'<nav class="post-nav".*?</nav>', page, re.S
            )
            self.assertIsNotNone(navigation)
            actual = re.findall(
                r'href="/literature/([^/]+)/"', navigation.group(0)
            )
            expected = []
            if position > 0:
                expected.append(ordered[position - 1]["slug"])
            if position + 1 < len(ordered):
                expected.append(ordered[position + 1]["slug"])
            self.assertEqual(actual, expected, note["id"])

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
        self.assertIn("공식 작가 프로필", homepage)
        self.assertIn("https://blog.naver.com/yesblue0342", homepage)
        self.assertIn("https://www.youtube.com/@Yesblue1234", homepage)
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
            "og:url", "og:image", "og:image:secure_url", "og:image:type",
            "og:image:width", "og:image:height", "og:image:alt", "og:locale",
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
        self.assertIn('<meta name="twitter:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">', homepage)
        person = next(entry for entry in graph if entry["@type"] == "Person")
        self.assertEqual(person["@id"], f"{ORIGIN}/#person")
        self.assertEqual(person["url"], f"{ORIGIN}/author/")
        self.assertEqual(
            person["identifier"],
            {
                "@type": "PropertyValue",
                "propertyID": "Naver Person ID",
                "value": "215161",
            },
        )
        self.assertEqual(
            set(person["sameAs"]),
            {
                "https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&pkid=1&os=215161&query=%EC%9D%B4%ED%9B%84",
                "https://blog.naver.com/yesblue0342",
                "https://www.youtube.com/@Yesblue1234",
                "https://github.com/yesblue0342-bit/Leehu",
                "https://store.kyobobook.co.kr/person/detail/1000809404",
                "https://ko.wikipedia.org/wiki/%EC%9D%B4%ED%9B%84_(%EC%86%8C%EC%84%A4%EA%B0%80)",
                "https://namu.wiki/w/%EC%9D%B4%ED%9B%84(%EC%86%8C%EC%84%A4%EA%B0%80)",
            },
        )
        for forbidden_property in (
            "legalName", "birthName", "givenName", "familyName"
        ):
            self.assertNotIn(forbidden_property, self.homepage)
        self.assertNotIn("mailto:", self.homepage)
        self.assertNotRegex(
            self.homepage,
            r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
        )

    def test_author_profile_is_canonical_pseudonym_only_and_linked(self) -> None:
        author_page = (ROOT / "author" / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            f'<link rel="canonical" href="{ORIGIN}/author/">', author_page
        )
        self.assertIn('<meta name="robots" content="index, follow">', author_page)
        self.assertIn(f'"@id": "{ORIGIN}/#person"', author_page)
        self.assertIn('"propertyID": "Naver Person ID"', author_page)
        self.assertIn('"value": "215161"', author_page)
        self.assertIn(
            '<link rel="alternate" type="application/rss+xml" '
            'title="이후의 문학노트 RSS" '
            f'href="{ORIGIN}/literature/rss.xml">',
            author_page,
        )
        self.assertIn(
            '<link rel="alternate" type="application/rss+xml" '
            'title="이후의 문학노트 RSS" '
            f'href="{ORIGIN}/literature/rss.xml">',
            self.homepage,
        )
        self.assertIn('href="/author/"', self.homepage)
        self.assertNotIn("mailto:", author_page)
        self.assertNotRegex(author_page, r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
        for forbidden_property in (
            "legalName", "birthName", "givenName", "familyName"
        ):
            self.assertNotIn(forbidden_property, author_page)

        sitemap = ET.parse(ROOT / "sitemap.xml")
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        lastmods = {
            node.findtext("sm:loc", namespaces=namespace):
            node.findtext("sm:lastmod", namespaces=namespace)
            for node in sitemap.getroot().findall("sm:url", namespace)
        }
        self.assertEqual(lastmods[f"{ORIGIN}/"], "2026-08-23")
        self.assertEqual(lastmods[f"{ORIGIN}/author/"], "2026-08-23")

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
        self.assertIn('const LOCAL_BOARD_KEY = "leehu_public_board_posts_v1";', homepage)
        self.assertIn('publicBoardMode = "local"', homepage)
        self.assertIn("boardApiUnavailable(response.status)", homepage)
        self.assertIn("saveLocalBoardPosts", homepage)
        self.assertIn("게시판 서버에 연결할 수 없을 때에는 글이 현재 브라우저에만 저장됩니다.", homepage)
        self.assertIn('response.status === 404', homepage)
        self.assertIn('setBoardStatus("이미 삭제된 게시글입니다.")', homepage)
        self.assertIn('if (publicBoardMode === "api") await loadPublicPosts();', homepage)
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

    def test_primary_navigation_has_one_official_youtube_link(self):
        primary_nav = re.search(
            r'<ul id="primaryNav" class="nav-links">(?P<body>.*?)</ul>',
            self.homepage,
            re.S,
        )
        self.assertIsNotNone(primary_nav)
        nav_body = primary_nav.group("body")
        self.assertEqual(nav_body.count("https://www.youtube.com/@Yesblue1234"), 1)
        self.assertEqual(nav_body.count(">공식 YouTube</a>"), 1)
        self.assertNotIn('class="mini-link"', nav_body)

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
        self.assertNotIn("시인 김경의 아들로", self.homepage)

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
        self.assertNotIn(".quote::before", self.homepage)

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
        self.assertIn('href="/author/"', hero_actions.group("body"))
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
        tracked_outputs += [LITERATURE / "index.html"]
        tracked_outputs += list((LITERATURE / "page").glob("*/index.html"))
        tracked_outputs += [LITERATURE / note["slug"] / "index.html" for note in self.notes]
        before = {path: path.read_bytes() for path in tracked_outputs}
        completed = subprocess.run(
            [sys.executable, "scripts/build_literature.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=600,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(f"built {TARGET_COUNT} detail pages", completed.stdout)
        after = {path: path.read_bytes() for path in tracked_outputs}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
