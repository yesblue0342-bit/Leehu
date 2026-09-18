"""Independent regression tests for the fifty-note 2026-09-18 batch."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_literature  # noqa: E402 - repository scripts require the path above
import review_leehu_works_20260918_50 as checker  # noqa: E402


GENERATOR = SCRIPTS / "append_leehu_works_20260918_50.py"
MANIFEST = ROOT / "content" / "leehu-works-20260918-50.json"


def load_generator():
    spec = importlib.util.spec_from_file_location("leehu_batch_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("generator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_note(position: int = 1) -> dict[str, object]:
    work = "연(戀)"
    source = checker.APPROVED_SOURCES[work]
    sentence = "관찰의 결을 충분히 따라가며 성급한 결론 대신 지금의 선택을 오래 살피는 문장이다."
    return {
        "id": f"20260918_leehu_literature_{checker.START_SEQUENCE + position - 1:04d}",
        "slug": f"leehu-20260918-love-unit-{position}-literary-note",
        "title": f"단위 검사를 위한 고유 제목 {position}",
        "quote": "관찰은 익숙한 판단을 잠시 멈추고 관계에 남은 미세한 차이를 다시 읽게 한다.",
        "source_author": "이후",
        "source_work": work,
        "source_location": f"단위 검사 위치 {position}",
        "source_language": "ko",
        "source_url": source,
        "translation_note": f"단위 검사 번역 메모 {position}이며 원문의 직접 번역이 아니다.",
        "rights_note": f"직접 인용 없음. 작품을 읽고 쓴 독립 감상 기록 {position}이다.",
        "commentary": " ".join(sentence.replace("문장이다.", ending) for ending in (
            "첫 문장이다.", "둘째 문장이다.", "셋째 문장이다.", "넷째 문장이다.", "다섯째 문장이다."
        )),
        "closing": f"오늘의 읽기는 판단보다 관찰을 한 걸음 앞세우는 고유한 마침표 {position}를 남긴다.",
        "author": "소설가 이후",
        "tags": ["소설가 이후", work, f"관점 {position}", "독서 기록"],
        "related_work": {"name": work, "url": source},
        "published_at": checker.PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": {
            key: (f"{key} {position} ") + sentence * 4 for key in checker.SECTION_KEYS
        },
    }


class PureCheckerTests(unittest.TestCase):
    def test_skeleton_replaces_only_known_lenses_and_both_title_brackets(self) -> None:
        lenses = {"기억의 출처", "주의의 분배"}
        left = checker.normalize_skeleton(
            "《데자뷔》를 기억의 출처라는 관점에서 다시 읽는다.", lenses
        )
        right = checker.normalize_skeleton(
            "『데자뷔』를 주의의 분배라는 관점에서 다시 읽는다.", lenses
        )
        self.assertEqual(left, right)
        self.assertNotEqual(
            checker.normalize_skeleton("질문은 어디에서 시작되는가?", lenses),
            checker.normalize_skeleton("질문을 오래 남겨 두는 태도다.", lenses),
        )

    def test_detects_duplicate_and_short_text(self) -> None:
        first = valid_note(1)
        second = valid_note(2)
        second["quote"] = first["quote"]
        second["commentary"] = "짧다."
        notes = [first, second]
        result = checker.validate_batch(notes, [], generated_notes=notes)
        self.assertTrue(any("duplicate quote" in error for error in result["errors"]))
        self.assertTrue(any("commentary too short" in error for error in result["errors"]))
        self.assertIsNotNone(checker.meaningless_padding_reason("메움 " * 80))

    def test_malformed_tags_and_slug_report_errors_without_crashing(self) -> None:
        note = valid_note()
        note["tags"] = 42
        note["slug"] = "Invalid Slug"
        result = checker.validate_batch([note], [], generated_notes=[note])
        self.assertTrue(any("invalid tags" in error for error in result["errors"]))
        self.assertTrue(any("invalid slug" in error for error in result["errors"]))

    def test_detects_wrong_date_and_unsupported_claim(self) -> None:
        note = valid_note()
        note["published_at"] = "2026-09-17T18:50:00+09:00"
        note["closing"] = "작가는 이 결말에서 독자에게 자신의 의도를 분명히 전하려 한다."
        result = checker.validate_batch([note], [], generated_notes=[note])
        errors = result["errors"]
        self.assertTrue(any("wrong published_at" in error for error in errors))
        self.assertTrue(any("unsupported claim" in error for error in errors))

    def test_unsupported_claim_filter_allows_explicit_boundary_disclaimer(self) -> None:
        note = valid_note()
        note["closing"] = "이 글은 작품의 결말이나 작가의 의도를 추정하지 않는다."
        self.assertFalse(
            any("unsupported claim" in error for error in checker.text_rule_errors(note))
        )

    def test_autobiographical_past_claim_rejects_fact_but_allows_hypothetical(self) -> None:
        self.assertTrue(checker.autobiographical_claims("나는 비슷한 이별을 겪은 적이 있다."))
        self.assertFalse(
            checker.autobiographical_claims(
                "내가 비슷한 이별을 겪은 적이 있다면 무엇을 먼저 물을지 생각해 보자."
            )
        )
        self.assertFalse(
            checker.autobiographical_claims(
                "내가 비슷한 이별을 겪었다고 가정해 보자."
            )
        )

    def test_title_only_uses_punctuation_normalization(self) -> None:
        notes = [valid_note(1), valid_note(2)]
        notes[0]["title"] = "같은 제목!"
        notes[1]["title"] = "같은-제목"
        notes[0]["quote"] = "공백은 그대로 보존한다."
        notes[1]["quote"] = "공백은  그대로 보존한다."
        self.assertTrue(checker.duplicate_values(notes, "title"))
        self.assertFalse(checker.duplicate_values(notes, "quote"))


class BatchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        if not MANIFEST.is_file():
            raise FileNotFoundError(f"required batch manifest is missing: {MANIFEST}")
        cls.generated = cls.generator.generate()
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_canonical_generator_output(self) -> None:
        self.assertEqual(
            checker.canonical_json(self.generated),
            checker.canonical_json(self.manifest),
        )

    def test_source_equality_gate_accepts_canonical_equal_payload(self) -> None:
        result = checker.validate_batch(
            self.manifest,
            self.generator.entries(),
            generated_notes=self.generated,
            source_notes=copy.deepcopy(self.manifest),
        )
        self.assertTrue(result["generator_match"])
        self.assertTrue(result["source_match"])

    def test_applied_sources_equal_manifest_when_present(self) -> None:
        paths = [ROOT / "content" / "literature" / f"{number:03d}.json" for number in range(6132, 6182)]
        present = [path.is_file() for path in paths]
        if not any(present):
            self.skipTest("batch has not been applied")
        self.assertTrue(all(present), "batch source application must not be partial")
        source = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        self.assertEqual(checker.canonical_json(source), checker.canonical_json(self.manifest))

    def test_all_fifty_notes_render_to_distinct_detail_html(self) -> None:
        rendered = []
        for index, note in enumerate(self.manifest):
            previous = self.manifest[index - 1] if index else None
            following = self.manifest[index + 1] if index + 1 < len(self.manifest) else None
            page = build_literature.detail_page(note, previous, following, True)
            rendered.append(page)
            self.assertIn(build_literature.canonical(note), page)
            self.assertIn(str(note["title"]), page)
        self.assertEqual(len(rendered), 50)
        self.assertEqual(len(set(rendered)), 50)

    def test_full_independent_review_passes(self) -> None:
        result = checker.review(MANIFEST)
        self.assertTrue(result["ok"], result["errors"][:10])
        self.assertTrue(result["generator_match"])
        self.assertEqual(result["exact_sentence_duplicates"], 0)
        self.assertEqual(result["normalized_skeleton_duplicates"], 0)
        self.assertRegex(result["manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(len(result["input_sha256"]), 5)
        self.assertTrue(all(len(value) == 64 for value in result["input_sha256"].values()))


if __name__ == "__main__":
    unittest.main()
