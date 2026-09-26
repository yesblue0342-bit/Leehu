"""Protect work identity when linking older literature notes to official books."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_literature import ORIGIN, detail_page, official_work_url


class OfficialWorkLinksTests(unittest.TestCase):
    def test_known_names_and_verified_alias_share_existing_book_ids(self):
        names = {
            "연(戀)": "yeon", "연(戀)": "yeon", "데자뷔": "deja-vu",
            "소나기": "sonagi", "환상": "illusion",
            "별이 빛나는 밤에": "starry-night", "처음처럼": "like-the-first-time",
            "Fantasy": "fantasy",
        }
        for name, anchor in names.items():
            with self.subTest(name=name):
                self.assertEqual(
                    official_work_url({"source_author": "이후", "source_work": name}),
                    f"{ORIGIN}/works/#{anchor}",
                )

    def test_existing_matching_anchor_remains_valid(self):
        self.assertEqual(
            official_work_url({
                "source_author": "이후", "source_work": "소나기", "work_anchor": "sonagi",
            }),
            f"{ORIGIN}/works/#sonagi",
        )

    def test_explicit_invalid_anchor_never_falls_back(self):
        for anchor in ["yeon", "", None, False, [], "sonagi/", "https://example.com/"]:
            with self.subTest(anchor=anchor):
                self.assertIsNone(official_work_url({
                    "source_author": "이후", "source_work": "소나기", "work_anchor": anchor,
                }))

    def test_other_authors_cannot_match_on_title_alone(self):
        for author in ["황순원", "Vincent van Gogh", "소설가 이후", "이후 ", None]:
            for explicit_anchor in [False, True]:
                with self.subTest(author=author, explicit_anchor=explicit_anchor):
                    note = {"source_author": author, "source_work": "소나기"}
                    if explicit_anchor:
                        note["work_anchor"] = "sonagi"
                    self.assertIsNone(official_work_url(note))

    def test_unreviewed_titles_and_similar_names_do_not_match(self):
        for name in ["연", "연 (戀)", "소나기 해설", "fantasy", "Fantasy 2", "", None]:
            with self.subTest(name=name):
                self.assertIsNone(official_work_url({
                    "source_author": "이후", "source_work": name,
                }))

    def test_legacy_note_renders_link_and_book_identity_without_changing_prose(self):
        note = self.note()
        before = json.dumps(note, ensure_ascii=False, sort_keys=True)
        rendered = detail_page(note, None, None, indexable=False)
        self.assertIn('href="/works/#sonagi"', rendered)
        self.assertIn('<h2>왜 지금도 읽히는가</h2>', rendered)
        self.assertIn('<h2>나의 감상</h2>', rendered)
        self.assertIn('<h2>오늘 우리에게 주는 의미</h2>', rendered)
        self.assertIn('<meta name="robots" content="noindex, follow">', rendered)
        self.assertIn(f'<link rel="canonical" href="{ORIGIN}/literature/legacy-note/">', rendered)
        for value in [note["commentary"], note["quote"], *note["seo_sections"].values()]:
            self.assertIn(value, rendered)
        structured = json.loads(re.search(
            r'<script type="application/ld\+json">(.*?)</script>', rendered, re.S,
        ).group(1))
        self.assertEqual(structured[0]["about"]["@id"], f"{ORIGIN}/works/#sonagi")
        self.assertEqual(structured[0]["datePublished"], note["published_at"])
        self.assertEqual(before, json.dumps(note, ensure_ascii=False, sort_keys=True))

    def test_explicit_reviewed_note_keeps_existing_headings(self):
        note = self.note()
        note["work_anchor"] = "sonagi"
        rendered = detail_page(note, None, None)
        self.assertIn('<h2>지금 떠오르는 질문</h2>', rendered)
        self.assertIn('<h2>독자로서 생각해 볼 거리</h2>', rendered)
        self.assertIn('<h2>독서 기록 제안</h2>', rendered)

    @staticmethod
    def note():
        return {
            "id": "20260727_leehu_literature_001", "slug": "legacy-note",
            "title": "기존 문학노트", "quote": "기존 요약 문장입니다.",
            "source_author": "이후", "source_work": "소나기",
            "source_location": "작품 정보", "source_url": "https://example.com/book",
            "translation_note": "기존 안내", "rights_note": "기존 권리 안내",
            "commentary": "기존 독서 기록의 본문입니다.", "author": "소설가 이후",
            "closing": "소설가 이후 드림", "tags": ["문학"],
            "related_work": {"name": "소나기", "url": "https://example.com/book"},
            "published_at": "2026-07-27T12:00:00+09:00",
            "content_kind": "original_reflection",
            "seo_sections": {
                "work_introduction": "기존 작품 소개입니다.",
                "why_read_now": "기존 읽기 이유입니다.",
                "personal_reflection": "기존 감상입니다.",
                "meaning_today": "기존 의미입니다.",
            },
        }


if __name__ == "__main__":
    unittest.main()
