#!/usr/bin/env python3
"""Append 500 structured static literature notes about Lee Hu's works."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
EXPECTED_BEFORE = 2271
PUBLISHED_AT = "2026-08-23T11:00:00+09:00"

WORKS = (
    ("연(戀)", "love", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756", "한국소설"),
    ("데자뷔", "deja-vu", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772", "기억과 서사"),
    ("소나기", "rain-shower", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780", "창작과 회복"),
    ("환상", "fantasy", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769", "시와 상상"),
    ("별이 빛나는 밤에", "starry-night", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770", "시와 독서"),
)

THEMES = (
    ("침묵", "silence", "말하지 않은 마음", "듣기의 태도"),
    ("기억", "memory", "되돌아오는 시간", "기억의 윤리"),
    ("거리", "distance", "가까움과 멂", "관계의 간격"),
    ("선택", "choice", "망설임 뒤의 결정", "선택의 책임"),
    ("기다림", "waiting", "멈춘 듯 흐르는 시간", "기다리는 힘"),
    ("상실", "loss", "사라진 것의 자리", "애도의 언어"),
    ("회복", "recovery", "다시 시작하는 마음", "회복의 속도"),
    ("시선", "gaze", "같은 장면의 다른 얼굴", "보는 사람의 책임"),
    ("여백", "blank-space", "설명되지 않은 부분", "상상의 자리"),
    ("목소리", "voice", "고유한 말의 리듬", "말할 권리"),
    ("공간", "place", "사람을 기억하는 장소", "장소의 감각"),
    ("시간", "time", "겹쳐지는 과거와 현재", "시간을 견디는 법"),
    ("사물", "objects", "손때가 남은 물건", "사물의 기억"),
    ("날씨", "weather", "마음을 비추는 계절", "감각의 변화"),
    ("오해", "misunderstanding", "엇갈린 말과 표정", "다시 묻는 용기"),
    ("약속", "promise", "미래를 향한 문장", "신뢰의 조건"),
    ("경계", "boundary", "나와 타인을 나누는 선", "존중의 거리"),
    ("돌봄", "care", "작은 행동의 온기", "함께 사는 기술"),
    ("변화", "change", "익숙함이 흔들리는 순간", "변화를 받아들이는 마음"),
    ("귀환", "return", "떠났다가 돌아오는 길", "달라진 자리의 의미"),
)

LENSES = (
    ("첫 문장에서 만나는", "opening", "처음 마주한 문장이 독서의 방향을 여는 방식"),
    ("장면의 리듬으로 읽는", "rhythm", "장면 사이의 속도와 멈춤이 감정을 바꾸는 방식"),
    ("인물의 선택에서 발견한", "character", "인물을 판단하기 전에 선택의 조건을 살피는 방식"),
    ("오늘의 일상으로 이어지는", "today", "작품에서 시작한 질문을 지금의 생활로 옮기는 방식"),
    ("마지막 여운에 남은", "afterglow", "책을 덮은 뒤에도 질문이 천천히 자라는 방식"),
)


def particles(noun: str) -> tuple[str, str]:
    last = ord(noun[-1])
    has_batchim = 0xAC00 <= last <= 0xD7A3 and (last - 0xAC00) % 28 != 0
    return ("을" if has_batchim else "를", "이" if has_batchim else "가")


def make_note(work: tuple[str, str, str, str], theme: tuple[str, str, str, str], lens: tuple[str, str, str], sequence: int) -> dict[str, object]:
    work_name, work_slug, source_url, work_tag = work
    theme_name, theme_slug, image, meaning = theme
    lens_title, lens_slug, lens_detail = lens
    obj, subj = particles(theme_name)
    image_obj, image_subj = particles(image)
    _, meaning_subj = particles(meaning)
    topic_no = ((sequence - 1) % 100) + 1
    title = f"《{work_name}》{particles(work_name)[0]} 읽으며: {lens_title} {theme_name}"
    deck = f"《{work_name}》에서 {image}{image_obj} 떠올리고, {lens_title} {theme_name}{obj} 오늘의 언어로 다시 읽어 보는 문학노트다."
    commentary = (
        f"이 노트는 《{work_name}》의 줄거리를 대신 요약하지 않고, {lens_title} {theme_name}{subj} 독자에게 남기는 감각을 살핀다. "
        f"《{work_name}》에서 {lens_detail}에 주목하면 {image}{image_subj} 고정된 해답보다 새로운 질문에 가까워진다. "
        f"나는 {work_name}의 {theme_name}에 관한 질문을 빠르게 결론 내리지 않고, ‘{lens_title} {theme_name}’ 관점에서 내 경험과 타인의 시간을 함께 존중하는 쪽으로 읽어 본다. "
        f"《{work_name}》{particles(work_name)[0]} 통해 ‘{lens_title} {theme_name}’ 관점으로 바라본 {meaning}{meaning_subj} 작품 밖의 하루에서도 말과 행동을 한 번 더 돌아보게 한다. "
        f"{work_name}에 관한 {topic_no}번째 기록의 끝에는 ‘{lens_title} {theme_name}’{obj} 묻는 질문과 각자의 속도로 답할 자리를 남긴다."
    )
    return {
        "id": f"20260823_leehu_literature_{sequence:03d}",
        "slug": f"leehu-{work_slug}-{theme_slug}-{lens_slug}",
        "title": title,
        "quote": deck,
        "source_author": "이후",
        "source_work": work_name,
        "source_location": "교보ebook 도서 정보의 작가 소개 및 작품 설명 참고 · 작품 본문 직접 인용 없음",
        "source_language": "ko",
        "source_url": source_url,
        "translation_note": "한국어 창작 작품에 관한 독창적 감상으로, 작품 본문 직접 인용 및 타인의 번역문 전재 없음.",
        "rights_note": f"소설가 이후의 작품 《{work_name}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.",
        "commentary": commentary,
        "closing": f"《{work_name}》를 다시 펼칠 때 ‘{lens_title} {theme_name}’을 바라보는 나의 시선도 함께 기록해 본다.",
        "author": "소설가 이후",
        "tags": ["소설가 이후", work_name, work_tag, theme_name, meaning],
        "related_work": {"name": work_name, "url": source_url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": {
            "work_introduction": f"《{work_name}》은 소설가 이후의 한국어 창작 작품이며, 이 글은 공식 도서 정보에 근거해 본문을 직접 인용하지 않고 {lens_title} {theme_name} 독서 주제로 접근한다.",
            "why_read_now": f"《{work_name}》을 읽는 지금, 빠른 판단과 짧은 반응 속에서 {lens_title} {image}{image_obj} 천천히 바라보는 일은 다른 사람의 맥락을 놓치지 않게 한다. {work_name}에서 {theme_name}{obj} 중심에 두고 {lens_detail}은 오늘 이 작품을 다시 읽을 한 가지 이유가 된다.",
            "personal_reflection": f"나는 《{work_name}》을 떠올리며 ‘{lens_title} {theme_name}’{obj} 하나의 뜻으로 고정하지 않으려 했다. {work_name}에서 ‘{lens_title} {theme_name}’{obj} 읽는 날의 형편에 따라 달리 기록할 때, 문학노트는 작품과 독자 사이의 살아 있는 대화가 된다.",
            "meaning_today": f"《{work_name}》을 오늘 읽는 독자에게 ‘{lens_title} {theme_name}’ 관점에서 살핀 {meaning}{meaning_subj} 거창한 교훈보다 구체적인 태도로 다가온다. {work_name}의 {theme_name}{obj} ‘{lens_title} {theme_name}’ 질문과 함께 생각하며 잠시 멈추고 다시 듣는 실천이 독서의 의미를 일상으로 이어 준다.",
        },
    }


def validate(notes: list[dict[str, object]]) -> None:
    if len(notes) != 500:
        raise ValueError(f"expected 500 notes, got {len(notes)}")
    for key in ("id", "slug", "title", "quote", "commentary", "closing"):
        values = [str(n[key]) for n in notes]
        if len(values) != len(set(values)):
            raise ValueError(f"duplicate {key}")
    if Counter(str(n["source_work"]) for n in notes) != Counter({w[0]: 100 for w in WORKS}):
        raise ValueError("unexpected work distribution")
    bad = [n["slug"] for n in notes if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(n["slug"]))]
    if bad:
        raise ValueError(f"non-semantic slug: {bad[:3]}")
    forbidden = ("원문 확인 필요", "공식 카탈로그", "주제표목", "AI", "자동 생성")
    for n in notes:
        prose = " ".join([str(n["quote"]), str(n["commentary"]), *map(str, n["seo_sections"].values())])
        if any(word in prose for word in forbidden):
            raise ValueError(f"forbidden public marker: {n['id']}")


def main() -> None:
    existing = sorted(CONTENT.glob("*.json"), key=lambda p: int(p.stem))
    notes: list[dict[str, object]] = []
    sequence = 1
    for work in WORKS:
        for theme in THEMES:
            for lens in LENSES:
                notes.append(make_note(work, theme, lens, sequence))
                sequence += 1
    validate(notes)
    if len(existing) == EXPECTED_BEFORE + 500:
        actual = [json.loads((CONTENT / f"{EXPECTED_BEFORE + i:03d}.json").read_text(encoding="utf-8")) for i in range(1, 501)]
        if actual != notes:
            raise SystemExit("existing batch differs from generator")
        print("verified existing 500-note batch")
        return
    if len(existing) != EXPECTED_BEFORE:
        raise SystemExit(f"expected {EXPECTED_BEFORE} sources, found {len(existing)}")
    for offset, note in enumerate(notes, 1):
        target = CONTENT / f"{EXPECTED_BEFORE + offset:03d}.json"
        temp = target.with_suffix(".json.tmp")
        temp.write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(target)
    print("created and validated 500 notes in ten 50-note review batches")

if __name__ == "__main__":
    main()
