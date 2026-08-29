#!/usr/bin/env python3
"""Append fifty original-reflection literature notes for novelist Lee Hu."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
EXPECTED_BEFORE = 2071
PUBLISHED_AT = "2026-08-20T09:00:00+09:00"

WORKS = (
    ("연(戀)", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756", "한국소설"),
    ("데자뷔", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772", "기억과 서사"),
    ("소나기", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780", "창작과 회복"),
    ("환상", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769", "시와 상상"),
    ("별이 빛나는 밤에", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770", "시와 독서"),
)

TOPICS = (
    ("관계의 속도를 함께 정하는 일", "서두르지 않는 대화", "관계의 속도", "대화의 리듬"),
    ("말하지 못한 마음을 돌보는 법", "침묵의 자리", "침묵", "마음의 돌봄"),
    ("기억의 빈칸에 남는 표정", "남겨진 표정", "기억의 빈칸", "표정"),
    ("하루의 끝에서 문장을 다시 읽는 시간", "저녁의 재독", "재독", "하루의 끝"),
    ("서로 다른 계절을 건너는 마음", "계절의 간격", "계절", "공감"),
    ("사과보다 먼저 필요한 경청", "먼저 듣는 마음", "경청", "회복"),
    ("낯선 선택을 존중하는 사랑", "선택의 여백", "존중", "선택"),
    ("돌아보지 못한 장면을 기록하는 이유", "뒤늦은 기록", "기록", "장면"),
    ("작은 약속이 만드는 신뢰", "작은 약속", "신뢰", "약속"),
    ("혼자 있는 시간이 관계에 주는 숨", "혼자의 숨", "고독", "관계"),
)


def josa(word: str, with_batchim: str, without_batchim: str) -> str:
    last = next((char for char in reversed(word) if '가' <= char <= '힣'), '')
    return with_batchim if last and (ord(last) - 0xAC00) % 28 else without_batchim


def note_for(sequence: int, work: tuple[str, str, str], topic: tuple[str, str, str, str]) -> dict[str, object]:
    work_name, source_url, work_tag = work
    title, phrase, theme_one, theme_two = topic
    ordinal = sequence + 1
    return {
        "id": f"20260820_leehu_literature_{ordinal:03d}",
        "slug": f"leehu-{work_name.encode('utf-8').hex()[:8]}-{ordinal:03d}-{theme_one.encode('utf-8').hex()[:6]}",
        "title": f"《{work_name}》{josa(work_name, '을', '를')} 읽으며: {title}",
        "quote": f"《{work_name}》{josa(work_name, '을', '를')} 읽는 자리에서 {phrase}{josa(phrase, '을', '를')} 떠올리며, 관계와 기억이 독자 안에서 새롭게 이어지는 순간을 기록한다.",
        "source_author": "이후",
        "source_work": work_name,
        "source_location": "교보ebook 도서 정보의 작가 소개 및 작품 설명 참고 · 작품 본문 직접 인용 없음",
        "source_language": "ko",
        "source_url": source_url,
        "translation_note": "한국어 창작 작품에 관한 독창적 감상으로, 작품 본문 직접 인용 및 타인의 번역문 전재 없음.",
        "rights_note": f"소설가 이후의 작품 《{work_name}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.",
        "commentary": (
            f"{phrase}{josa(phrase, '은', '는')} 《{work_name}》{josa(work_name, '을', '를')} 읽으며 내가 오래 붙들고 싶었던 질문이다. "
            f"이 글은 작품의 특정 장면을 대신 말하지 않고, {theme_one}이 일상에서 어떤 결로 다가오는지 천천히 살핀다. "
            f"독서는 정답을 찾는 과정만이 아니라 내 안의 {theme_two}{josa(theme_two, '을', '를')} 알아차리는 시간이 될 수 있다. "
            f"그래서 오늘의 기록은 타인의 삶을 섣불리 해석하기보다, 나와 다른 리듬을 존중하는 마음으로 마무리한다. "
            f"《{work_name}》{josa(work_name, '과', '와')} {theme_one}{josa(theme_one, '을', '를')} 함께 떠올린 이 글의 끝에는, {phrase}{josa(phrase, '을', '를')} 실천할 다음 하루를 남겨 둔다."
        ),
        "closing": f"《{work_name}》{josa(work_name, '을', '를')} 다시 펼칠 때, {phrase}{josa(phrase, '을', '를')} 향한 나만의 질문도 함께 적어 본다.",
        "author": "소설가 이후",
        "tags": ["소설가 이후", work_name, work_tag, theme_one, theme_two],
        "related_work": {"name": work_name, "url": source_url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
    }


def main() -> None:
    existing = sorted(CONTENT_DIR.glob("*.json"), key=lambda path: int(path.stem))
    if len(existing) not in {EXPECTED_BEFORE, EXPECTED_BEFORE + len(WORKS) * len(TOPICS)}:
        raise SystemExit(f"expected {EXPECTED_BEFORE} or {EXPECTED_BEFORE + len(WORKS) * len(TOPICS)} sources, found {len(existing)}")
    for index, work in enumerate(WORKS):
        for topic_index, topic in enumerate(TOPICS):
            sequence = index * len(TOPICS) + topic_index
            path = CONTENT_DIR / f"{EXPECTED_BEFORE + sequence + 1:03d}.json"
            path.write_text(
                json.dumps(note_for(sequence, work, topic), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    print(f"created {len(WORKS) * len(TOPICS)} notes")


if __name__ == "__main__":
    main()
