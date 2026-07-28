#!/usr/bin/env python3
"""Append a 2026-07-28 world-classics love batch without altering prior notes."""
from __future__ import annotations

import hashlib
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

from append_love_literature import english_love_quotes

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
START_FILE_INDEX = 1166
BATCH_SIZE = 300
TARGET_COUNT = 1465
PUBLISHED_AT = "2026-07-28T12:00:00+09:00"
RELATED = {"name": "연", "url": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756"}
LOVE_TAGS = ("사랑", "애정", "연애", "헌신", "기다림", "관계", "신뢰", "기억", "갈망", "돌봄")

DIRECT_SOURCES = (
    (1399, "Leo Tolstoy", "Anna Karenina", "tolstoy-anna-karenina"),
    (768, "Emily Brontë", "Wuthering Heights", "bronte-wuthering-heights"),
    (135, "Victor Hugo", "Les Misérables", "hugo-les-miserables"),
    (2527, "Johann Wolfgang von Goethe", "The Sorrows of Young Werther", "goethe-young-werther"),
    (1608, "Alexandre Dumas fils", "La Dame aux Camélias", "dumas-camelias"),
    (1883, "Anton Chekhov", "About Love", "chekhov-about-love"),
)

REFLECTIONS = (
    ("Gabriel García Márquez 작품 감상", "Love in the Time of Cholera", "marquez-love-time-cholera", "https://www.penguin.co.uk/books/482988/love-in-the-time-of-cholera-by-marquez-gabriel-garcia/9780241968567", "Gabriel García Márquez"),
    ("Antoine de Saint-Exupéry 작품 감상", "The Little Prince", "saint-exupery-little-prince", "https://www.lepetitprince.com/en/the-book/", "Antoine de Saint-Exupéry"),
)
THEMES = (
    "기다림", "재회", "책임", "신뢰", "돌봄", "거리", "침묵", "용기", "상실", "기억",
    "약속", "자유", "선택", "연민", "존중", "안부", "여백", "회복", "고백", "동행",
    "온기", "그리움", "배려", "용서", "희망", "절제", "인내", "상호성", "진심", "평안",
    "이해", "눈빛", "계절", "경계", "공감", "성장", "위로", "결단", "마음", "관계",
    "헌신", "갈망", "공존", "약함", "평생",
)


def token(value: str) -> str:
    return "".join(chr(ord("a") + int(char, 16)) for char in hashlib.sha256(value.encode()).hexdigest()[:10])


def first_word(value: str) -> str:
    words = re.findall(r"[A-Za-z]{4,}", value)
    return (words[0].lower() if words else "love")[:18]


def tags(position: int, author_tag: str) -> list[str]:
    primary = LOVE_TAGS[position % len(LOVE_TAGS)]
    secondary = LOVE_TAGS[(position * 3 + 1) % len(LOVE_TAGS)]
    if primary == secondary:
        secondary = "관계"
    return [primary, secondary, author_tag]


def normalized_quote(value: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", "", value.casefold())


def selected_quotes(book_id: int, required: int, existing: list[str]) -> list[tuple[str, int]]:
    selected: list[tuple[str, int]] = []
    seen = [normalized_quote(value) for value in existing]
    for quote, line in english_love_quotes(book_id, 78):
        cleaned = quote.replace("“", "").replace("”", "")
        if cleaned.count('"') % 2:
            cleaned = cleaned.replace('"', "")
        normalized = normalized_quote(cleaned)
        if any(
            normalized == prior or normalized in prior or prior in normalized
            or SequenceMatcher(None, normalized, prior).ratio() >= 0.97
            for prior in seen
        ):
            continue
        selected.append((cleaned, line))
        seen.append(normalized)
        if len(selected) == required:
            return selected
    raise RuntimeError(f"not enough distinct love quotes for Gutenberg #{book_id}")


def direct_note(sequence: int, position: int, author: str, work: str, short: str, book_id: int, quote: str, line: int) -> dict[str, object]:
    quote = quote.replace("“", "").replace("”", "")
    if quote.count('"') % 2:
        quote = quote.replace('"', "")
    compact = re.sub(r"\s+", " ", quote)
    title = f"{work}의 사랑을 읽는 문장 — {compact[:135]}"
    first = compact[:105].strip(" ,.;:")
    tail = compact[-75:].strip(" ,.;:")
    commentary = " ".join((
        f"『{work}』의 이 문장은 ‘{first}’와 ‘{tail}’ 사이에서 사랑의 긴장을 드러냅니다.",
        f"이 대목은 사랑이 감정의 선언만이 아니라 {tags(position, author)[0]}을 견디는 시간임을 생각하게 합니다.",
        "독자는 인물의 마음을 단정하기보다, 가까워지고 싶은 욕망과 서로의 현실 사이에 생기는 간격을 함께 바라볼 수 있습니다.",
        "그 간격은 관계를 소유하려는 마음보다 상대의 선택을 존중하는 태도가 왜 중요한지 묻습니다.",
        f"그래서 이 기록은 {sequence}번째 새 배치에서도 사랑을 더 책임 있게 읽게 하는 여운으로 남습니다.",
    ))
    return {
        "id": f"20260728_leehu_literature_{sequence:03d}",
        "slug": f"{short}-love-{first_word(quote)}-{token(author + work + quote)}",
        "title": title, "quote": quote, "source_author": author, "source_work": work,
        "source_location": f"Project Gutenberg eBook #{book_id}, plain-text paragraph near line {line}",
        "source_language": "en", "source_url": f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        "translation_note": "퍼블릭 도메인 영어 원문 인용. 현대 한국어 번역문을 저장하거나 전재하지 않음.",
        "rights_note": "퍼블릭 도메인 원전에서 직접 확인한 문장.",
        "commentary": commentary, "closing": "소설가 이후 드림", "author": "소설가 이후",
        "tags": tags(position, author), "related_work": RELATED, "published_at": PUBLISHED_AT,
        "content_kind": "source_quote",
    }


def reflection_note(sequence: int, position: int, source_author: str, work: str, short: str, source_url: str, author_tag: str, theme: str) -> dict[str, object]:
    insight = f"{theme}을 통해 상대의 시간을 함부로 대신 말하지 않는 법을 배운다"
    quote = f"{author_tag}의 『{work}』를 읽으며 사랑은 {theme}의 자리에서 상대를 한 사람으로 존중하려는 태도에서 시작된다고 생각한다. {insight}."
    commentary = " ".join((
        f"이 글은 {author_tag}의 『{work}』를 읽으며 사랑과 {theme}의 관계를 새로 생각해 본 독창적 감상입니다.",
        "원문·번역문·대사·장면의 흐름을 옮기지 않고, 작품 제목이 환기하는 사랑의 질문만을 출발점으로 삼았습니다.",
        f"{theme}은 관계를 소유하려는 마음을 멈추고, 서로 다른 감각이 공존할 자리를 남기는 계기로 읽힙니다.",
        f"그 여백은 사랑이 ‘{insight}’라는 태도로 이어질 수 있음을 생각하게 합니다.",
        f"이 기록은 『{work}』를 매개로 {theme}의 순간에 자신의 관계를 천천히 돌아보게 하는 하나의 질문으로 남습니다.",
    ))
    return {
        "id": f"20260728_leehu_literature_{sequence:03d}",
        "slug": f"{short}-love-{token(source_author + work + theme)}",
        "title": f"{theme}의 자리에서 읽는 사랑: {author_tag}의 『{work}』", "quote": quote,
        "source_author": source_author, "source_work": work,
        "source_location": "직접 인용 없음 · 작품 제목과 일반적 사랑 주제에 대한 독창적 감상",
        "source_language": "en", "source_url": source_url,
        "translation_note": "직접 인용이나 번역문 전재 없음.",
        "rights_note": f"{author_tag} 작품의 직접 인용 없음. 작품 제목과 일반적 사랑 주제를 바탕으로 쓴 독창적 감상.",
        "commentary": commentary, "closing": "소설가 이후 드림", "author": "소설가 이후",
        "tags": tags(position, author_tag), "related_work": RELATED, "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
    }


def main() -> None:
    existing = list(CONTENT_DIR.glob("*.json"))
    if len(existing) != START_FILE_INDEX - 1:
        raise RuntimeError(f"expected {START_FILE_INDEX - 1} existing notes, found {len(existing)}")
    notes: list[dict[str, object]] = []
    existing_quotes = [json.loads(path.read_text(encoding="utf-8"))["quote"] for path in existing]
    for book_id, author, work, short in DIRECT_SOURCES:
        for quote, line in selected_quotes(book_id, 35, existing_quotes + [str(note["quote"]) for note in notes]):
            sequence = len(notes) + 1
            notes.append(direct_note(sequence, len(notes), author, work, short, book_id, quote, line))
    for source_author, work, short, source_url, author_tag in REFLECTIONS:
        for theme in THEMES:
            sequence = len(notes) + 1
            notes.append(reflection_note(sequence, len(notes), source_author, work, short, source_url, author_tag, theme))
    if len(notes) != BATCH_SIZE:
        raise RuntimeError(f"expected {BATCH_SIZE} notes, got {len(notes)}")
    for position, note in enumerate(notes, START_FILE_INDEX):
        (CONTENT_DIR / f"{position:03d}.json").write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if len(list(CONTENT_DIR.glob("*.json"))) != TARGET_COUNT:
        raise RuntimeError("final source count mismatch")
    print("appended 300 world love notes: six public-domain authors 35 each, two no-quote reflection groups 45 each")


if __name__ == "__main__":
    main()
