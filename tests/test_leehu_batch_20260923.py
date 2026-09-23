"""Independent regression tests for the 1,000-note 2026-09-23 batch."""
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

import build_literature  # noqa: E402
import review_leehu_works_20260923_1000 as checker  # noqa: E402


GENERATOR = SCRIPTS / "append_leehu_works_20260923_1000.py"
MANIFEST = ROOT / "content" / "leehu-works-20260923-1000.json"
SMALL_SPEC = checker.BatchSpec(
    expected_before=0,
    expected=6,
    start_sequence=3821,
    batch_date="20260923",
    expected_works=tuple((work, 1) for work in checker.APPROVED_SOURCES),
)


def load_generator():
    spec = importlib.util.spec_from_file_location("leehu_batch_20260923_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("generator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_note(position: int = 1, *, work: str = "연(戀)") -> dict[str, object]:
    source = checker.APPROVED_SOURCES[work]
    marker = chr(0xAC00 + position)
    sentence = f"관찰의 결을 {marker} 방향으로 충분히 따라가며 성급한 결론 대신 지금의 선택을 오래 살피는 문장이다."
    return {
        "id": f"20260923_leehu_literature_{checker.START_SEQUENCE + position - 1:04d}",
        "slug": f"leehu-20260923-unit-{position}-literary-note",
        "title": f"단위 검사를 위한 고유 제목 {marker}",
        "quote": f"관찰은 {marker} 지점의 익숙한 판단을 잠시 멈추고 관계에 남은 미세한 차이를 다시 읽게 한다.",
        "source_author": "이후",
        "source_work": work,
        "source_location": f"단위 검사 위치 {marker}",
        "source_language": "ko",
        "source_url": source,
        "translation_note": f"단위 검사 번역 메모 {marker}이며 원문의 직접 번역이 아니다.",
        "rights_note": f"직접 인용 없음. 작품을 읽고 쓴 독립 감상 기록 {marker}이다.",
        "commentary": " ".join(
            sentence.replace("문장이다.", ending)
            for ending in (
                "첫 판단이다.",
                "둘째 관찰이다.",
                "셋째 질문이다.",
                "넷째 선택이다.",
                "다섯째 기록이다.",
            )
        ),
        "closing": f"오늘의 읽기는 판단보다 관찰을 한 걸음 앞세우는 고유한 마침표 {marker}를 남긴다.",
        "author": "소설가 이후",
        "tags": ["소설가 이후", work, f"관점 {marker}", "독서 기록"],
        "related_work": {"name": work, "url": source},
        "published_at": "2026-09-23T18:50:00+09:00",
        "content_kind": "original_reflection",
        "seo_sections": {
            key: f"{key} {marker} " + sentence * 4 for key in checker.SECTION_KEYS
        },
    }


def valid_entries() -> list[dict[str, object]]:
    return [
        {"position": index, "flow": checker.FLOWS[index - 1], "lens": f"관점 {index}"}
        for index in range(1, 6)
    ] + [{"position": 6, "flow": checker.FLOWS[0], "lens": "관점 6"}]


def six_notes() -> list[dict[str, object]]:
    return [
        valid_note(index, work=work)
        for index, work in enumerate(checker.APPROVED_SOURCES, 1)
    ]


class PureReviewerTests(unittest.TestCase):
    def validate(self, notes, entries=None, **kwargs):
        return checker.validate_batch(
            notes,
            valid_entries() if entries is None else entries,
            generated_notes=notes,
            spec=SMALL_SPEC,
            **kwargs,
        )

    def test_default_boundaries_and_distribution(self) -> None:
        self.assertEqual(checker.EXPECTED, 1000)
        self.assertEqual(checker.EXPECTED_BEFORE, 6191)
        self.assertEqual(checker.START_SEQUENCE, 3821)
        self.assertEqual(sum(checker.EXPECTED_WORKS.values()), 1000)
        self.assertEqual(list(checker.EXPECTED_WORKS.values()), [150, 130, 130, 130, 130, 330])
        self.assertEqual(len(checker.expected_work_sequence()), 100)

    def test_author_module_partition_requires_equal_contiguous_ranges(self) -> None:
        spec = checker.BatchSpec(expected=10)
        modules = [
            [{"position": first}, {"position": first + 1}]
            for first in range(1, 11, 2)
        ]
        self.assertEqual(checker.author_module_errors(modules, spec), [])
        modules[2][1]["position"] = 99
        self.assertTrue(any("module 3 positions" in error for error in checker.author_module_errors(modules, spec)))

    def test_rejects_malformed_note_without_crashing(self) -> None:
        notes = six_notes()
        notes[0]["tags"] = 42
        del notes[0]["quote"]
        result = self.validate(notes)
        self.assertFalse(result["ok"])
        self.assertTrue(any("schema keys differ" in error for error in result["errors"]))
        self.assertTrue(any("invalid tags" in error for error in result["errors"]))

    def test_rejects_wrong_date_and_id(self) -> None:
        notes = six_notes()
        notes[0]["id"] = "20260922_leehu_literature_3821"
        notes[0]["published_at"] = "2026-09-22T18:50:00+09:00"
        result = self.validate(notes)
        self.assertTrue(any("unexpected id" in error for error in result["errors"]))
        self.assertTrue(any("wrong published_at" in error for error in result["errors"]))

    def test_rejects_filler_and_unsupported_story_claim(self) -> None:
        notes = six_notes()
        notes[0]["quote"] = "메움 " * 80
        notes[0]["closing"] = "주인공은 마지막 장면에서 작가의 의도를 독자에게 분명히 전한다."
        result = self.validate(notes)
        self.assertTrue(any("meaningless padding" in error for error in result["errors"]))
        self.assertTrue(any("unsupported claim" in error for error in result["errors"]))

    def test_rejects_evidenced_korean_particle_errors(self) -> None:
        for bad in checker.LOCAL_KNOWN_BAD:
            note = valid_note()
            note["closing"] = f"이 문장은 {bad} 같은 잘못된 조사를 포함한다."
            self.assertTrue(any(bad in error for error in checker.text_rule_errors(note)))

    def test_rejects_editorial_scaffolding_in_public_prose(self) -> None:
        note = valid_note()
        note["closing"] = "사회적 의미는 이 결론을 책임의 기준으로 다시 분류한다."
        self.assertTrue(any("editorial scaffold" in error for error in checker.text_rule_errors(note)))

    def test_rejects_repeated_long_sentence_within_batch(self) -> None:
        notes = six_notes()
        repeated = "이 문장은 충분히 길어서 서로 다른 기록에 그대로 반복되면 독립적인 산문이라는 검증 기준을 통과할 수 없다."
        notes[0]["closing"] = repeated
        notes[1]["closing"] = repeated
        result = self.validate(notes)
        self.assertGreater(result["exact_sentence_duplicates"], 0)
        self.assertTrue(any("duplicate exact sentence" in error for error in result["errors"]))

    def test_rejects_repeated_long_sentence_inside_one_note(self) -> None:
        notes = six_notes()
        repeated = "한 기록 안에서도 충분히 긴 문장을 그대로 되풀이하면 산문의 독립성과 밀도가 함께 무너진다."
        notes[0]["closing"] = f"{repeated} {repeated}"
        result = self.validate(notes)
        self.assertGreater(result["exact_sentence_duplicates"], 0)

    def test_title_boundary_does_not_hide_reused_first_quote_sentence(self) -> None:
        notes = six_notes()
        repeated = "제목과 붙여 읽더라도 이 충분히 긴 첫 문장의 재사용은 반드시 독립적으로 발견되어야 한다."
        notes[0]["quote"] = f"{repeated} 첫 번째 기록만의 다음 문장이다."
        notes[1]["quote"] = f"{repeated} 두 번째 기록만의 다음 문장이다."
        result = self.validate(notes)
        self.assertGreater(result["exact_sentence_duplicates"], 0)

    def test_rejects_normalized_skeleton_collision_with_existing_corpus(self) -> None:
        notes = six_notes()
        existing = copy.deepcopy(notes[0])
        existing["id"] = "20260918_leehu_literature_3761"
        existing["closing"] = "《연(戀)》을 관점 1이라는 렌즈로 읽으면 오늘의 선택을 다시 오래 살피게 된다."
        notes[0]["closing"] = "『데자뷔』를 관점 2이라는 렌즈로 읽으면 오늘의 선택을 다시 오래 살피게 된다."
        result = self.validate(notes, existing_notes=[existing])
        self.assertGreater(result["normalized_skeleton_duplicates"], 0)
        self.assertTrue(any("duplicate normalized skeleton" in error for error in result["errors"]))

    def test_flow_order_is_flexible_but_three_consecutive_is_rejected(self) -> None:
        entries = valid_entries()
        entries[0]["flow"], entries[1]["flow"] = entries[1]["flow"], entries[0]["flow"]
        flexible = self.validate(six_notes(), entries=entries)
        self.assertFalse(any("cycle" in error for error in flexible["errors"]))

        entries[0]["flow"] = entries[1]["flow"] = entries[2]["flow"] = "question"
        rejected = self.validate(six_notes(), entries=entries)
        self.assertTrue(any("three consecutive" in error for error in rejected["errors"]))

    def test_optional_work_anchor_is_accepted_by_schema(self) -> None:
        notes = six_notes()
        notes[0]["work_anchor"] = "yeon"
        result = self.validate(notes)
        self.assertFalse(any("schema keys differ" in error for error in result["errors"]))
        self.assertFalse(any("work_anchor differs" in error for error in result["errors"]))
        notes[0]["work_anchor"] = "wrong-work"
        result = self.validate(notes)
        self.assertTrue(any("work_anchor differs" in error for error in result["errors"]))

    def test_diagnostics_are_bounded(self) -> None:
        notes = six_notes()
        for note in notes:
            note["closing"] = "주인공은 결말에서 작가의 의도를 전하려 한다."
        result = self.validate(notes)
        unsupported = [error for error in result["errors"] if error.startswith("unsupported claim")]
        self.assertLessEqual(len(unsupported), checker.MAX_EXAMPLES_PER_RULE)
        self.assertGreater(result["error_count"], 0)


@unittest.skipUnless(GENERATOR.is_file() and MANIFEST.is_file(), "1,000-note batch is still being authored")
class BatchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.generator = load_generator()
        cls.generated = cls.generator.generate()
        cls.entries = cls.generator.entries()
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_is_generator_output_and_full_review_passes(self) -> None:
        self.assertEqual(checker.canonical_json(self.generated), checker.canonical_json(self.manifest))
        result = checker.review(MANIFEST)
        self.assertTrue(result["ok"], result["errors"])
        self.assertTrue(result["generator_match"])
        self.assertEqual(result["exact_sentence_duplicates"], 0)
        self.assertEqual(result["normalized_skeleton_duplicates"], 0)

    def test_positions_lenses_flows_and_work_distribution(self) -> None:
        self.assertEqual([entry["position"] for entry in self.entries], list(range(1, 1001)))
        self.assertEqual(
            [entry["work"] for entry in self.entries],
            list(self.generator.WORK_SEQUENCE) * 10,
        )
        self.assertGreaterEqual(len({entry["lens"] for entry in self.entries}), 20)
        self.assertEqual({entry["flow"] for entry in self.entries}, set(checker.FLOWS))
        self.assertFalse(any(
            self.entries[index]["flow"] == self.entries[index + 1]["flow"] == self.entries[index + 2]["flow"]
            for index in range(998)
        ))
        self.assertEqual(
            {work: sum(note["source_work"] == work for note in self.manifest) for work in checker.EXPECTED_WORKS},
            checker.EXPECTED_WORKS,
        )

    def test_applied_sources_and_detail_rendering_when_present(self) -> None:
        paths = [ROOT / "content" / "literature" / f"{number:03d}.json" for number in range(6192, 7192)]
        present = [path.is_file() for path in paths]
        if not any(present):
            self.skipTest("batch has not been applied")
        self.assertTrue(all(present), "batch source application must not be partial")
        source = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        self.assertEqual(checker.canonical_json(source), checker.canonical_json(self.manifest))
        rendered = {
            build_literature.detail_page(note, None, None)
            for note in self.manifest
        }
        self.assertEqual(len(rendered), 1000)


if __name__ == "__main__":
    unittest.main()
