#!/usr/bin/env python3
"""Assemble fifty individually authored notes using the established source schema."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

try:
    from . import build_literature
    from .leehu_notes_20260918_a import ENTRIES as A
    from .leehu_notes_20260918_b import ENTRIES as B
    from .leehu_notes_20260918_c import ENTRIES as C
except ImportError:
    import build_literature
    from leehu_notes_20260918_a import ENTRIES as A
    from leehu_notes_20260918_b import ENTRIES as B
    from leehu_notes_20260918_c import ENTRIES as C

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content" / "leehu-works-20260918-50.json"
EXPECTED_BEFORE = 6131
TARGET_COUNT = 50
START_SEQUENCE = 3761
BATCH_DATE = "20260918"
PUBLISHED_AT = "2026-09-18T18:50:00+09:00"
SECTION_KEYS = (
    "work_introduction", "why_read_now", "personal_reflection", "meaning_today",
)
FLOWS = ("question", "contrast", "observation", "thought_experiment", "practice")
# Same verified editions used by the approved September 8 batch and /works/.
WORKS = {
    "연(戀)": ("love", "E000005377756"),
    "데자뷔": ("deja-vu", "E000005377772"),
    "소나기": ("rain-shower", "E000002957780"),
    "환상": ("illusion", "E000005377769"),
    "별이 빛나는 밤에": ("starry-night", "E000005377770"),
    "Fantasy": ("fantasy-poetry", "E000009124008"),
}
TARGET_BY_WORK = dict(zip(WORKS, (9, 9, 8, 8, 8, 8)))


def entries() -> list[dict]:
    return sorted([*A, *B, *C], key=lambda entry: entry["position"])


def generate() -> list[dict]:
    notes = []
    for entry in entries():
        work = entry["work"]
        work_slug, edition = WORKS[work]
        source_url = f"https://ebook-product.kyobobook.co.kr/dig/epd/ebook/{edition}"
        note = {
            "id": f"{BATCH_DATE}_leehu_literature_{START_SEQUENCE + entry['position'] - 1:04d}",
            "slug": f"leehu-{BATCH_DATE}-{work_slug}-{entry['slug']}-literary-note",
            "title": entry["title"],
            "quote": entry["quote"],
            "source_author": "이후",
            "source_work": work,
            "source_location": entry["source_location"],
            "source_language": "ko",
            "source_url": source_url,
            "translation_note": entry["translation_note"],
            "rights_note": entry["rights_note"],
            "commentary": entry["commentary"],
            "closing": entry["closing"],
            "author": "소설가 이후",
            "tags": ["소설가 이후", work, entry["lens"], "독서 기록"],
            "related_work": {"name": work, "url": source_url},
            "published_at": PUBLISHED_AT,
            "content_kind": "original_reflection",
            "seo_sections": {key: entry[key] for key in SECTION_KEYS},
        }
        notes.append(note)
    return notes


def review(notes: list[dict]) -> None:
    authored = entries()
    assert [entry["position"] for entry in authored] == list(range(1, 51))
    assert len({entry["lens"] for entry in authored}) >= 20
    assert Counter(entry["flow"] for entry in authored) == Counter(dict.fromkeys(FLOWS, 10))
    assert all(entry["flow"] == FLOWS[index % 5] for index, entry in enumerate(authored))
    assert len(notes) == TARGET_COUNT
    assert Counter(note["source_work"] for note in notes) == Counter(TARGET_BY_WORK)
    for note in notes:
        assert 50 <= len(note["quote"]) <= 260, note["id"]
        assert build_literature.prose_sentence_count(note["quote"]) <= 2, note["id"]
        assert len(note["commentary"]) >= max(300, int(len(note["quote"]) * 1.25)), note["id"]
        assert 4 <= len(re.findall(r"다\.", note["commentary"])) <= 8, note["id"]
        assert all(len(value) >= 180 for value in note["seo_sections"].values()), note["id"]
        assert "직접 인용 없음" in note["rights_note"], note["id"]
    corpus = ROOT / "content" / "literature"
    existing = [json.loads((corpus / f"{number:03d}.json").read_text(encoding="utf-8"))
                for number in range(1, EXPECTED_BEFORE + 1)]
    unique_fields = ("id", "slug", "title", "quote", "commentary", "closing",
                     "source_location", "translation_note", "rights_note")
    for field in unique_fields:
        values = [build_literature.normalize(note[field]) for note in notes]
        assert len(set(values)) == TARGET_COUNT, f"duplicate {field}"
        previous = {build_literature.normalize(note[field]) for note in existing}
        assert not previous.intersection(values), f"existing {field} collision"
    for key in SECTION_KEYS:
        assert len({note["seo_sections"][key] for note in notes}) == TARGET_COUNT, key
    targets = [corpus / f"{number}.json" for number in range(6132, 6182)]
    if any(path.exists() for path in targets):
        assert all(path.exists() for path in targets), "partially applied batch"
        assert [json.loads(path.read_text(encoding="utf-8")) for path in targets] == notes


def main() -> None:
    notes = generate()
    review(notes)
    build_literature.write_text_atomic(
        MANIFEST, json.dumps(notes, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"reviewed {len(notes)} individually authored notes; wrote {MANIFEST.name}")


if __name__ == "__main__":
    main()
