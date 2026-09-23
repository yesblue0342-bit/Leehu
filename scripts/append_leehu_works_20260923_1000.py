#!/usr/bin/env python3
"""Assemble the September 23 title-inspired reading notes without applying them."""
from __future__ import annotations

import importlib
import json
from collections import Counter
from pathlib import Path

try:
    from . import build_literature
except ImportError:
    import build_literature

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "content" / "leehu-works-20260923-1000.json"
EXPECTED_BEFORE = 6191
TARGET_COUNT = 1000
START_SEQUENCE = 3821
BATCH_DATE = "20260923"
PUBLISHED_AT = "2026-09-23T18:00:00+09:00"
SECTION_KEYS = ("work_introduction", "why_read_now", "personal_reflection", "meaning_today")
FLOWS = ("question", "contrast", "observation", "thought_experiment", "practice")
WORKS = {
    "연(戀)": ("love", "E000005377756", "yeon"),
    "데자뷔": ("deja-vu", "E000005377772", "deja-vu"),
    "소나기": ("rain-shower", "E000002957780", "sonagi"),
    "환상": ("illusion", "E000005377769", "illusion"),
    "별이 빛나는 밤에": ("starry-night", "E000005377770", "starry-night"),
    "Fantasy": ("fantasy-poetry", "E000009124008", "fantasy"),
}
TARGET_BY_WORK = dict(zip(WORKS, (150, 130, 130, 130, 130, 330)))
WORK_SEQUENCE = tuple(work for turn in range(33) for work, count in TARGET_BY_WORK.items() if turn < count // 10)


def entries() -> list[dict]:
    """Read the five independently authored topic collections in publication order."""
    result = []
    for suffix in "abcde":
        name = f"leehu_notes_20260923_{suffix}"
        module = importlib.import_module(f"{__package__}.{name}" if __package__ else name)
        result.extend(module.entries() if hasattr(module, "entries") else module.ENTRIES)
    return sorted(result, key=lambda entry: entry["position"])


def generate() -> list[dict]:
    """Map authored prose to the established public source schema."""
    authored = entries()
    if [entry["position"] for entry in authored] != list(range(1, TARGET_COUNT + 1)):
        raise ValueError("authored positions must be exactly 1..1000")
    notes = []
    for entry in authored:
        work = entry["work"]
        if work != WORK_SEQUENCE[(entry["position"] - 1) % len(WORK_SEQUENCE)]:
            raise ValueError("work order differs from the reviewed publication schedule")
        work_slug, edition, anchor = WORKS[work]
        url = f"https://ebook-product.kyobobook.co.kr/dig/epd/ebook/{edition}"
        notes.append({
            "id": f"{BATCH_DATE}_leehu_literature_{START_SEQUENCE + entry['position'] - 1:04d}",
            "slug": f"leehu-{BATCH_DATE}-{work_slug}-{entry['slug']}-literary-note",
            "title": f"《{work}》 문학노트: {entry['title']}",
            "quote": entry["quote"],
            "source_author": "이후",
            "source_work": work,
            "source_location": entry["source_location"],
            "source_language": "ko",
            "source_url": url,
            "translation_note": entry["translation_note"],
            "rights_note": entry["rights_note"],
            "commentary": entry["commentary"],
            "closing": entry["closing"],
            "author": "소설가 이후",
            "tags": ["소설가 이후", work, entry["lens"], "독서 기록"],
            "related_work": {"name": work, "url": url},
            "published_at": PUBLISHED_AT,
            "content_kind": "original_reflection",
            "work_anchor": anchor,
            "seo_sections": {key: entry[key] for key in SECTION_KEYS},
        })
    if Counter(note["source_work"] for note in notes) != Counter(TARGET_BY_WORK):
        raise ValueError("work distribution differs from the reviewed publication plan")
    return notes


def main() -> None:
    notes = generate()
    build_literature.write_text_atomic(MANIFEST, json.dumps(notes, ensure_ascii=False, indent=2) + "\n")
    print(f"Assembled {len(notes)} notes: {MANIFEST.name}; source corpus unchanged")


if __name__ == "__main__":
    main()
