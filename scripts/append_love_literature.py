#!/usr/bin/env python3
"""Append a copyright-safe love literature batch to the Leehu static corpus."""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
BATCH_PUBLISHED_AT = "2026-07-27T12:00:00+09:00"
START_INDEX = 666
TARGET_COUNT = 1165
BATCH_SIZE = 500
HEADERS = {"User-Agent": "LeehuLiteratureBot/1.0"}
LOVE_WORDS_EN = ("love", "heart", "beloved", "affection", "dear")
LOVE_WORDS_KO = ("사랑", "애정", "연애", "아내", "연인", "님")
RELATED = {
    "name": "연",
    "url": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756",
}


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def pg_text(book_id: int) -> str:
    return fetch(f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt")


def pg_body(text: str) -> str:
    start = re.search(r"\*\*\* START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I | re.S)
    end = re.search(r"\*\*\* END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I | re.S)
    return text[start.end():end.start()] if start and end else text


def english_love_quotes(book_id: int, count: int) -> list[tuple[str, int]]:
    text = pg_body(pg_text(book_id))
    selected: list[tuple[str, int]] = []
    seen: set[str] = set()
    paragraphs = re.split(r"\n\s*\n", text)
    candidates: list[tuple[str, int]] = []
    line = 1
    for paragraph in paragraphs:
        compact = re.sub(r"\s+", " ", paragraph).strip()
        for sentence in re.split(r"(?<=[.!?])\s+", compact):
            quote = sentence.strip(" \t\r\n“”\"")
            if not 50 <= len(quote) <= 260:
                continue
            if sum(ch.isalpha() for ch in quote) < 60:
                continue
            if quote.count(".") + quote.count("!") + quote.count("?") > 2:
                continue
            if not any(word in quote.casefold() for word in LOVE_WORDS_EN):
                continue
            if re.search(r"\b(illustration|chapter|project gutenberg|http|www\.)\b", quote, re.I):
                continue
            candidates.append((quote, line))
        line += paragraph.count("\n") + 2
    for quote, line in sorted(candidates, key=lambda item: hashlib.sha256(f"{book_id}:{item[0]}".encode()).hexdigest()):
        normalized = re.sub(r"\W+", "", quote).casefold()
        if normalized not in seen:
            seen.add(normalized)
            selected.append((quote, line))
        if len(selected) == count:
            return selected
    raise RuntimeError(f"Project Gutenberg #{book_id}: love quotes {len(selected)}/{count}")


def wiki_api(params: dict[str, str]) -> dict[str, object]:
    url = "https://ko.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    return json.loads(fetch(url))


def clean_wikitext(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\{\{[^{}]*\}\}", " ", value)
    value = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", lambda match: match.group(2), value)
    value = re.sub(r"'{2,}", "", value)
    return re.sub(r"\s+", " ", value).strip()


YI_PUBLIC_DOMAIN_SOURCES = (
    ("동해", 221319), ("단발", 221332), ("혈서삼태", 221336),
    ("I WED A TOY BRIDE", 221285), ("불행한 계승", 291722),
    ("날개", 221326), ("공포의 기록", 221329), ("봉별기", 321170),
    ("EPIGRAM", 221343), ("19세기식", 369829),
)


def yi_love_quotes(count: int) -> list[tuple[str, str, int]]:
    candidates: list[tuple[str, str, int]] = []
    for title, oldid in YI_PUBLIC_DOMAIN_SOURCES:
        try:
            raw = wiki_api({"action": "parse", "oldid": str(oldid), "prop": "wikitext", "format": "json", "origin": "*"})["parse"]["wikitext"]["*"]
        except Exception:
            continue
        source = clean_wikitext(raw)
        chunks = [chunk.strip(" ·-—:;\t\r\n") for chunk in re.split(r"[\n。.!?]+", source)]
        for position, chunk in enumerate(chunks):
            if 12 <= len(chunk) <= 240 and any(word in chunk for word in LOVE_WORDS_KO):
                variants = [chunk]
            elif position + 1 < len(chunks):
                variants = [f"{chunk} {chunks[position + 1]}"]
            else:
                variants = []
            for quote in variants:
                if not 12 <= len(quote) <= 240 or not any(word in quote for word in LOVE_WORDS_KO):
                    continue
                candidates.append((quote, title, oldid))
    selected: list[tuple[str, str, int]] = []
    seen: set[str] = set()
    selected_normalized: list[str] = []
    for quote, title, oldid in sorted(candidates, key=lambda item: hashlib.sha256((item[1] + item[0]).encode()).hexdigest()):
        normalized = re.sub(r"\W+", "", quote)
        if normalized in seen or any(
            normalized in prior or prior in normalized or SequenceMatcher(None, normalized, prior).ratio() >= 0.90
            for prior in selected_normalized
        ):
            continue
        seen.add(normalized)
        selected_normalized.append(normalized)
        selected.append((quote, title, oldid))
        if len(selected) == count:
            return selected
    raise RuntimeError(f"Yi Sang: verified public-domain love quotes {len(selected)}/{count}")


def slug_token(value: str) -> str:
    return "".join(chr(ord("a") + int(char, 16)) for char in hashlib.sha256(value.encode()).hexdigest()[:10])


def first_word(value: str) -> str:
    words = re.findall(r"[A-Za-z]{4,}", value)
    return (words[0].lower() if words else "love")[:20]


def direct_note(index: int, author: str, work: str, short: str, quote: str, location: str, source_url: str, language: str) -> dict[str, object]:
    quote = quote.replace("“", "").replace("”", "")
    if quote.count('"') % 2:
        quote = quote.replace('"', "")
    anchor = first_word(quote)
    title_fragment = re.sub(r"\s+", " ", quote)[:140]
    title = f"{work}에서 사랑을 다시 읽는 문장 — {title_fragment}"
    token = slug_token(f"{author}|{work}|{quote}")
    compact_quote = re.sub(r"\s+", " ", quote)
    fragment = compact_quote[:110].strip(" ,.;:")
    tail_fragment = compact_quote[-78:].strip(" ,.;:")
    commentary = " ".join((
        f"『{work}』의 이 사랑에 관한 문장은 ‘{fragment}’와 ‘{tail_fragment}’라는 감각을 함께 남깁니다.",
        f"이 문장에 이어지는 ‘{re.sub(r'[^A-Za-z가-힣 ]', ' ', quote)[46:118].strip()}’의 결은 사랑을 관계의 시간으로 읽게 합니다.",
        f"특히 ‘{re.sub(r'[^A-Za-z가-힣 ]', ' ', quote)[118:190].strip()}’라는 대목은 가까워지고 싶은 마음과 쉽게 닿을 수 없는 거리의 긴장을 함께 바라보게 합니다.",
        "독자는 인물의 선택을 서둘러 판정하기보다, 사랑이 요구하는 책임과 망설임을 나란히 읽을 수 있습니다.",
        f"그래서 이 문장은 {index}번째 기록에서도 관계를 더 조심스럽게 생각하게 하는 여운으로 남습니다.",
    ))
    return {
        "id": f"20260727_leehu_literature_{index:03d}", "slug": f"{short}-love-{anchor}-{token}", "title": title,
        "quote": quote, "source_author": author, "source_work": work, "source_location": location,
        "source_language": language, "source_url": source_url,
        "translation_note": "공공영역 원문 인용. 현대 한국어 번역문을 저장하거나 전재하지 않음.",
        "rights_note": "퍼블릭 도메인 원전에서 직접 확인한 문장.", "commentary": commentary,
        "closing": "소설가 이후 드림", "author": "소설가 이후", "tags": ["사랑", "관계", author],
        "related_work": RELATED, "published_at": BATCH_PUBLISHED_AT, "content_kind": "source_quote",
    }


HWANG_WORKS = ("소나기", "별", "카인의 후예", "나무들 비탈에 서다", "움직이는 성")
HWANG_FOCUSES = (
    "기다림", "침묵", "거리", "약속", "기억", "눈빛", "계절", "용기", "배려", "상실",
    "재회", "망설임", "신뢰", "이해", "돌봄", "안부", "여백", "선택", "존중", "회복",
    "고백", "연민", "동행", "온기", "작별",
)
REFLECTION_INSIGHTS = {
    "기다림": "서두르지 않는 약속을 배운다", "침묵": "말하지 않은 마음의 결을 살핀다", "거리": "서로의 경계를 다정하게 인정한다",
    "약속": "내일을 함께 견디는 책임을 생각한다", "기억": "지나간 시간을 돌봄으로 바꾼다", "눈빛": "설명보다 먼저 도착하는 신호를 읽는다",
    "계절": "변화 속에서도 관계의 온도를 지킨다", "용기": "두려움 곁에서 진심을 선택한다", "배려": "상대의 리듬을 기다려 준다",
    "상실": "없어진 자리에도 존중을 남긴다", "재회": "다시 만남의 낯섦을 받아들인다", "망설임": "결정을 늦추는 마음을 함부로 재단하지 않는다",
    "신뢰": "확신보다 꾸준한 행동을 믿는다", "이해": "모르겠다는 고백에서 대화를 시작한다", "돌봄": "작은 안부를 오래 지속한다",
    "안부": "평범한 하루를 함께 확인한다", "여백": "말 사이에 숨 쉴 자리를 남긴다", "선택": "서로의 자유를 관계 안에 세운다",
    "존중": "다름을 고치려 들지 않는다", "회복": "상처 이후의 시간을 재촉하지 않는다", "고백": "진심을 상대의 부담으로 만들지 않는다",
    "연민": "약함을 판단 대신 곁에 둔다", "동행": "같은 속도가 아니어도 함께 걷는다", "온기": "사소한 친절을 잊지 않는다",
    "작별": "떠나는 마음에도 평안을 건넨다", "낯섦": "서로의 미지에 머무는 법을 배운다", "고독": "혼자 있는 시간을 관계의 적으로 삼지 않는다",
    "상호성": "주고받음의 균형을 돌아본다",
}
WORK_LENSES = {
    "소나기": "비가 지난 자리의 조심스러운 마음", "별": "먼 빛을 바라보는 기다림", "카인의 후예": "상처와 책임 사이의 관계",
    "나무들 비탈에 서다": "서로를 지지하는 느린 용기", "움직이는 성": "변화 속에서 지키는 약속",
}


def hwang_reflection(index: int, work: str, focus: str) -> dict[str, object]:
    token = slug_token(f"hwang|{work}|{focus}")
    insight = REFLECTION_INSIGHTS[focus]
    quote = f"『{work}』를 읽으며 사랑은 {focus}의 순간에도 상대를 한 사람으로 존중하려는 마음에서 시작된다고 생각한다. {insight}."
    commentary = " ".join((
        f"이 글은 황순원의 『{work}』를 읽으며 사랑과 {focus}의 관계를 새로 생각해 본 독창적 감상입니다.",
        "작품의 문장이나 줄거리를 옮기지 않고, 제목이 불러오는 정서와 사랑의 보편적 질문만을 출발점으로 삼았습니다.",
        "사랑은 상대를 내 감정의 증거로 바꾸는 일이 아니라, 그의 선택과 침묵을 함부로 대신 말하지 않는 태도에 가깝습니다.",
        f"그 태도는 관계가 불확실할수록 더 필요한 배려와 책임을 요청합니다. 그때 {insight}는 생각이 남습니다.",
        f"『{work}』의 {focus}을 생각하는 이 기록은 독자가 자신의 관계를 천천히 돌아보게 하는 하나의 질문으로 남습니다.",
    ))
    return {
        "id": f"20260727_leehu_literature_{index:03d}", "slug": f"hwang-love-{token}",
        "title": f"{insight}: 황순원의 『{work}』를 읽고", "quote": quote,
        "source_author": "황순원 작품 감상", "source_work": work,
        "source_location": "직접 인용 없음 · 작품 제목과 일반적 사랑 주제에 대한 독창적 감상",
        "source_language": "ko", "source_url": "https://library.ltikorea.or.kr/writer/200068",
        "translation_note": "직접 인용이나 번역문 전재 없음.",
        "rights_note": "황순원 작품의 직접 인용 없음. 작품 제목과 일반적 주제를 바탕으로 쓴 독창적 감상.",
        "commentary": commentary, "closing": "소설가 이후 드림", "author": "소설가 이후",
        "tags": ["사랑", "관계", "황순원"], "related_work": RELATED,
        "published_at": BATCH_PUBLISHED_AT, "content_kind": "original_reflection",
    }


YI_REFLECTION_WORKS = ("동해", "단발", "혈서삼태", "I WED A TOY BRIDE", "불행한 계승")
YI_REFLECTION_FOCUSES = ("낯섦", "기다림", "고독", "망설임", "상호성", "침묵", "거리", "기억", "연민", "약속", "선택", "돌봄", "작별")


def yi_reflection(index: int, work: str, focus: str) -> dict[str, object]:
    token = slug_token(f"yi-reflection|{work}|{focus}")
    insight = REFLECTION_INSIGHTS[focus]
    quote = f"이상의 『{work}』를 읽으며 사랑은 {focus}을 견디는 감각 속에서 상대의 낯선 시간을 인정하는 일이라고 생각한다. {insight}."
    commentary = " ".join((
        f"이 글은 이상의 『{work}』를 읽으며 사랑과 {focus}의 관계를 새로 생각해 본 독창적 감상입니다.",
        f"작품의 문장과 번역문, 장면의 흐름을 옮기지 않고 {focus}이 던지는 사랑의 질문만을 독자적인 언어로 풀어 봅니다.",
        f"상대를 쉽게 해석하려는 충동을 멈추는 순간, 사랑은 ‘{insight}’라는 태도로 이어질 수 있습니다.",
        f"이 글에서 {focus}은 소유의 감정이 아니라 서로 다른 감각이 공존할 자리를 남기는 계기로 읽힙니다.",
        f"『{work}』의 {focus}을 생각하는 이 기록은 독자가 자신의 사랑을 천천히 돌아보게 하는 질문으로 남습니다.",
    ))
    return {
        "id": f"20260727_leehu_literature_{index:03d}", "slug": f"yi-sang-love-{token}",
        "title": f"{insight}: 이상의 『{work}』를 읽고", "quote": quote,
        "source_author": "이상 작품 감상", "source_work": work,
        "source_location": "직접 인용 없음 · 작품 제목과 일반적 사랑 주제에 대한 독창적 감상",
        "source_language": "ko", "source_url": "https://ko.wikisource.org/wiki/저자:이상",
        "translation_note": "직접 인용이나 번역문 전재 없음.",
        "rights_note": "이상 작품의 직접 인용 없음. 작품 제목과 일반적 주제를 바탕으로 쓴 독창적 감상.",
        "commentary": commentary, "closing": "소설가 이후 드림", "author": "소설가 이후",
        "tags": ["사랑", "관계", "이상"], "related_work": RELATED,
        "published_at": BATCH_PUBLISHED_AT, "content_kind": "original_reflection",
    }


def write_batch(notes: list[dict[str, object]]) -> None:
    if len(notes) != BATCH_SIZE:
        raise RuntimeError(f"expected {BATCH_SIZE} notes, got {len(notes)}")
    existing = sorted(CONTENT_DIR.glob("*.json"))
    if len(existing) != START_INDEX - 1:
        raise RuntimeError(f"expected {START_INDEX - 1} existing notes, found {len(existing)}")
    for offset, note in enumerate(notes, START_INDEX):
        (CONTENT_DIR / f"{offset:03d}.json").write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if len(list(CONTENT_DIR.glob("*.json"))) != TARGET_COUNT:
        raise RuntimeError("final source count mismatch")


def main() -> None:
    notes: list[dict[str, object]] = []
    for author, work, short, book_id in (
        ("Guy de Maupassant", "Complete Original Short Stories", "maupassant", 3090),
        ("William Shakespeare", "The Complete Works of William Shakespeare", "shakespeare", 100),
    ):
        source_url = f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
        for quote, line in english_love_quotes(book_id, 125):
            notes.append(direct_note(START_INDEX + len(notes), author, work, short, quote, f"Project Gutenberg eBook #{book_id}, plain-text paragraph near line {line}", source_url, "en"))
    for quote, work, oldid in yi_love_quotes(60):
        source_url = f"https://ko.wikisource.org/w/index.php?title={urllib.parse.quote(work.replace(' ', '_'))}&oldid={oldid}"
        notes.append(direct_note(START_INDEX + len(notes), "이상", work, "yi-sang", quote, f"위키문헌 『{work}』 원문 (PD-old-70, oldid={oldid})", source_url, "ko"))
    for work in YI_REFLECTION_WORKS:
        for focus in YI_REFLECTION_FOCUSES:
            notes.append(yi_reflection(START_INDEX + len(notes), work, focus))
    for work in HWANG_WORKS:
        for focus in HWANG_FOCUSES:
            notes.append(hwang_reflection(START_INDEX + len(notes), work, focus))
    write_batch(notes)
    print("appended 500 love literature notes: Maupassant 125, Shakespeare 125, Yi Sang 60 quotes + 65 reflections, Hwang 125 reflections")


if __name__ == "__main__":
    main()
