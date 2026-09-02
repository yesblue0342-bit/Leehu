#!/usr/bin/env python3
"""2026-09-03 소설가 이후 문학노트 1,000편 독립 품질 게이트."""
from __future__ import annotations

import argparse
import json
import re
import runpy
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "content" / "leehu-reflections-20260903-1000.json"
GENERATOR = ROOT / "scripts" / "append_leehu_reflections_20260903_1000.py"
EXPECTED = 1000
START_SEQUENCE = 1261
PUBLISHED_AT = "2026-09-03T06:30:00+09:00"
SECTION_KEYS = ("work_introduction", "why_read_now", "personal_reflection", "meaning_today")
REQUIRED = {
    "id", "slug", "title", "quote", "source_author", "source_work",
    "source_location", "source_language", "source_url", "translation_note",
    "rights_note", "commentary", "closing", "author", "tags",
    "related_work", "published_at", "content_kind", "seo_sections",
}
FORBIDDEN = (
    "AI", "인공지능", "자동 생성", "자동화", "에이전트", "검수 도구",
    "SEO", "원문 확인 필요", "공식 카탈로그", "blockquote",
)
UNSUPPORTED_STORY = (
    "주인공은", "주인공이", "결말에서", "마지막 장면에서",
    "작가는 의도", "작가가 의도", "실제 사건은", "등장인물은",
)
KNOWN_BAD = (
    "권리이", "자유을", "과정를", "소나기을", "환상와", "환상를",
    "데자뷔을", "밤에를", "메모은", "윤리을", "거리이라는",
    "소유을", "적기이라는", "묻기이라는", "확인하기이라는",
)


def sentences(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", item).strip().casefold()
        for item in re.split(r"(?<=[.!?])\s+", text)
        if len(item.strip()) >= 25
    ]


def has_batchim(word: str) -> bool:
    last = next((char for char in reversed(word) if "\uac00" <= char <= "\ud7a3"), "")
    return bool(last and (ord(last) - 0xAC00) % 28)


def invalid_particle_hits(text: str, terms: set[str]) -> list[str]:
    groups = (("이라는", "라는"), ("을", "를"), ("은", "는"), ("이", "가"), ("과", "와"))
    hits: list[str] = []
    for term in sorted(terms, key=len, reverse=True):
        invalid = [vowel if has_batchim(term) else consonant for consonant, vowel in groups]
        for particle in invalid:
            token = term + particle
            if token in text:
                hits.append(token)
                if len(hits) >= 20:
                    return hits
    return hits


def fail(errors: list[str], message: str) -> None:
    if len(errors) < 50:
        errors.append(message)


def load_generator() -> dict[str, object]:
    return runpy.run_path(str(GENERATOR), run_name="leehu_generator_review")


def review(path: Path) -> dict[str, object]:
    notes = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if not isinstance(notes, list) or len(notes) != EXPECTED:
        fail(errors, f"manifest count must be {EXPECTED}")
        notes = notes if isinstance(notes, list) else []

    module = load_generator()
    regenerated = module["generate"]()
    generator_match = regenerated == notes
    if not generator_match:
        fail(errors, "generator output differs from manifest")

    works = Counter(str(note.get("source_work")) for note in notes)
    expected_works = {"연(戀)": 203, "데자뷔": 200, "소나기": 197, "환상": 200, "별이 빛나는 밤에": 200}
    if works != Counter(expected_works):
        fail(errors, f"invalid work distribution: {dict(works)}")

    particle_terms: set[str] = set()
    for work in module["WORKS"]:
        particle_terms.update((work.name, f"《{work.name}》", work.frame, work.present, work.focus))
        particle_terms.update(detail for detail, _ in module["DETAILS"][work.name])
    particle_terms.update(setting for setting, _ in module["SETTINGS"])
    particle_terms.update(module["LENSES"])
    particle_terms.update(module["TENSIONS"])
    particle_terms.update(module["ACTIONS"])

    public_sentences: list[str] = []
    metadata_phrases: list[str] = []
    skeletons: list[str] = []
    grammar_hits: list[str] = []
    for position, note in enumerate(notes):
        missing = REQUIRED - set(note)
        if missing:
            fail(errors, f"item {position + 1} missing {sorted(missing)}")
            continue
        expected_id = f"20260903_leehu_literature_{START_SEQUENCE + position:04d}"
        if note["id"] != expected_id:
            fail(errors, f"unexpected id at {position + 1}: {note['id']}")
        if note["published_at"] != PUBLISHED_AT:
            fail(errors, f"wrong published_at: {note['id']}")
        if note["source_author"] != "이후" or note["author"] != "소설가 이후":
            fail(errors, f"wrong author: {note['id']}")
        if note["content_kind"] != "original_reflection":
            fail(errors, f"wrong content kind: {note['id']}")
        sections = note["seo_sections"]
        if not isinstance(sections, dict) or tuple(sections) != SECTION_KEYS:
            fail(errors, f"invalid section keys: {note['id']}")
            continue
        if any(len(str(value)) < 180 for value in sections.values()):
            fail(errors, f"short section: {note['id']}")
        if len(str(note["commentary"])) < 300:
            fail(errors, f"short commentary: {note['id']}")

        public_fields = [
            str(note["title"]), str(note["quote"]), str(note["commentary"]),
            str(note["closing"]), *map(str, sections.values()),
            str(note["source_location"]), str(note["translation_note"]),
            str(note["rights_note"]),
        ]
        public = " ".join(public_fields)
        for term in FORBIDDEN:
            if term.casefold() in public.casefold():
                fail(errors, f"forbidden term {term}: {note['id']}")
        for term in KNOWN_BAD:
            if term in public:
                fail(errors, f"known bad Korean {term}: {note['id']}")
        for phrase in UNSUPPORTED_STORY:
            if phrase in public:
                fail(errors, f"unsupported story claim {phrase}: {note['id']}")
        if "직접 인용 없음" not in str(note["rights_note"]):
            fail(errors, f"rights note missing quote boundary: {note['id']}")
        if not str(note["source_url"]).startswith("https://ebook-product.kyobobook.co.kr/"):
            fail(errors, f"unapproved source URL: {note['id']}")

        bad_particles = invalid_particle_hits(public, particle_terms)
        if bad_particles:
            grammar_hits.extend(f"{note['id']}:{value}" for value in bad_particles)
            fail(errors, f"invalid particle {bad_particles[0]}: {note['id']}")
        note_sentences = sentences(" ".join(public_fields[:7]))
        for sentence in note_sentences:
            if re.search(r"(?:기|하기)[”’']?\.$", sentence):
                fail(errors, f"incomplete nominal ending: {note['id']}")
        public_sentences.extend(note_sentences)
        skeletons.extend(module["normalize_skeleton"](sentence) for sentence in note_sentences)
        metadata_phrases.extend(
            re.sub(r"\s+", " ", str(note[field])).strip().casefold()
            for field in ("source_location", "translation_note", "rights_note")
        )

    for field in (
        "id", "slug", "title", "quote", "commentary", "closing",
        "source_location", "translation_note", "rights_note",
    ):
        values = [re.sub(r"\s+", " ", str(note.get(field, ""))).casefold() for note in notes]
        if len(values) != len(set(values)):
            fail(errors, f"duplicate {field}: {len(values) - len(set(values))}")

    duplicate_sentences = [
        sentence for sentence, count in Counter(public_sentences).items() if count > 1
    ]
    if duplicate_sentences:
        fail(errors, f"duplicate sentence: {duplicate_sentences[0]}")
    duplicate_metadata = [
        value for value, count in Counter(metadata_phrases).items() if count > 1
    ]
    if duplicate_metadata:
        fail(errors, f"duplicate public metadata: {duplicate_metadata[0]}")
    duplicate_skeletons = [
        (value, count) for value, count in Counter(skeletons).items() if count > 1
    ]
    if duplicate_skeletons:
        value, count = max(duplicate_skeletons, key=lambda item: item[1])
        fail(errors, f"duplicate normalized skeleton x{count}: {value}")

    for offset in range(0, len(notes), 50):
        batch = notes[offset:offset + 50]
        if len(batch) != 50:
            fail(errors, f"incomplete batch {offset // 50 + 1}")
        if len({str(note["title"]) for note in batch}) != len(batch):
            fail(errors, f"duplicate title in batch {offset // 50 + 1}")

    return {
        "ok": not errors,
        "count": len(notes),
        "works": dict(works),
        "generator_match": generator_match,
        "exact_sentence_duplicates": len(duplicate_sentences),
        "normalized_skeleton_duplicates": len(duplicate_skeletons),
        "metadata_duplicates": len(duplicate_metadata),
        "particle_errors": len(grammar_hits),
        "errors": errors,
        "samples": [
            {
                "position": index + 1,
                "id": notes[index]["id"],
                "title": notes[index]["title"],
                "slug": notes[index]["slug"],
                "quote": notes[index]["quote"],
                "commentary": notes[index]["commentary"],
            }
            for index in (0, len(notes) // 2, len(notes) - 1)
        ] if notes else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    result = review(args.manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
