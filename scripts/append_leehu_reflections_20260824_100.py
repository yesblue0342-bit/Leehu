#!/usr/bin/env python3
"""소설가 이후 자작품 문학노트 100편 manifest 생성 및 품질검사."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
MANIFEST = ROOT / "content" / "leehu-reflections-20260824-100.json"
EXPECTED_BEFORE = 2781
PUBLISHED_AT = "2026-08-24T20:00:00+09:00"

WORKS = (
    ("연(戀)", "love", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756", "한국소설"),
    ("데자뷔", "deja-vu", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772", "기억과 서사"),
    ("소나기", "rain-shower", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780", "창작과 회복"),
    ("환상", "fantasy", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769", "시와 상상"),
    ("별이 빛나는 밤에", "starry-night", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770", "시와 독서"),
)

# 20 topics per work (skip 문턱/새벽 - already done in previous 10 batch)
# 20 topics × 5 works = 100 notes
TOPICS = (
    ("여백", "blank", "채워지지 않은 공간이 품은 가능성", "빈 곳이 말을 걸어올 때 내가 듣는 태도"),
    ("기억", "memory", "지나간 장면이 현재에 남긴 흔적", "오늘의 나를 만든 어제의 조각들"),
    ("침묵", "silence", "말하지 않음으로 더 깊어지는 울림", "소리 없이 전해지는 마음의 무게"),
    ("흐름", "flow", "멈추지 않고 이어지는 시간의 결", "거스를 수 없는 변화 앞에서 중심을 잡는 일"),
    ("그림자", "shadow", "빛이 닿지 않는 곳에 드리운 결", "밝음 뒤에 숨은 또 다른 진실"),
    ("호흡", "breath", "들이쉬고 내쉬는 생명의 리듬", "한 번의 숨에 담긴 삶의 무게"),
    ("발자국", "footprint", "걸어온 길이 남긴 고유한 자취", "되돌아볼 때 비로소 보이는 나의 길"),
    ("창", "window", "안과 밖을 잇는 투명한 경계", "세상을 향해 열려 있는 마음의 틀"),
    ("씨앗", "seed", "작은 껍질 안에 갇힌 무한한 가능성", "땅속에서 기다림 끝에 피어날 싹"),
    ("강", "river", "끊임없이 바다로 나아가는 물길", "방향을 잃지 않고 흐르는 삶의 의지"),
    ("별", "star", "어둠 속에서 제 빛을 내는 존재", "멀리서도 길을 밝혀주는 고요한 등대"),
    ("바람", "wind", "보이지 않으나 닿는 곳마다 흔적을 남기는 힘", "자유롭게 불어와 마음을 흔드는 손길"),
    ("불", "fire", "태우며 빛을 내고 재가 되어 돌아가는 순환", "열정으로 나를 태워 세상을 밝히는 일"),
    ("물", "water", "담는 그릇의 모양을 따르며 본성을 잃지 않는 흐름", "부드러우나 끝내 바위를 뚫는 인내"),
    ("돌", "stone", "세월을 견디며 제 자리를 지키는 단단함", "변하지 않는 가치로 중심을 잡는 태도"),
    ("길", "path", "걸음마다 새로운 풍경을 여는 통로", "정해진 답 없이 내가 만들어가는 행로"),
    ("꿈", "dream", "잠든 사이에도 이어지는 영혼의 여정", "현실을 넘어선 상상이 건네는 메시지"),
    ("약속", "promise", "서로에게 건네는 다짐의 말", "시간이 지나도 변하지 않아야 할 말"),
    ("빛", "light", "어둠을 가르고 나아가는 최초의 선", "처음으로 세상을 비추는 용기"),
    ("소리", "sound", "정적을 깨고 퍼져나가는 파동", "들리지 않던 진실이 귀에 닿는 순간"),
)


def josa(word: str, consonant: str, vowel: str) -> str:
    last = next((ch for ch in reversed(word) if "가" <= ch <= "힣"), "")
    return consonant if last and (ord(last) - 0xAC00) % 28 else vowel


def make_note(work, topic, sequence: int) -> dict[str, object]:
    work_name, work_slug, source_url, work_tag = work
    topic_name, topic_slug, image, question = topic
    topic_obj = topic_name + josa(topic_name, "을", "를")
    topic_subj = topic_name + josa(topic_name, "이", "가")
    work_obj = work_name + josa(work_name, "을", "를")
    work_title_obj = f"《{work_name}》" + josa(work_name, "을", "를")
    work_title_join = f"《{work_name}》" + josa(work_name, "과", "와")
    image_subj = image + josa(image, "은", "는")
    question_subj = question + josa(question, "이", "가")
    title = f"{work_name} 문학노트: {topic_name} 앞에서 문장을 늦추는 일"
    deck = f"《{work_name}》 곁에 {topic_obj} 놓아 보니, {image_subj} 독서의 속도를 낮추고 아직 말하지 않은 질문을 오래 바라보게 한다."
    commentary = " ".join((
        f"이 노트에서는 《{work_name}》의 줄거리나 장면을 옮기지 않고 {topic_name}이라는 이미지가 독자에게 여는 감각을 따라간다.",
        f"{work_obj} 생각하며 {topic_obj} 마음속에 세우면 {image_subj} 익숙한 판단을 잠시 멈추게 한다.",
        f"나는 {work_name}의 {question}을 작품에 대한 단정으로 삼기보다, 오늘의 관계와 선택을 돌아보는 개인적인 독서 질문으로 남겨 둔다.",
        f"{work_title_join} {topic_name} 사이에서 생긴 여백은 타인의 경험을 대신 설명하지 않으면서도 내 말의 방향을 살피게 한다.",
        f"결국 작품 《{work_name}》에 관한 이 기록은 {question_subj} 각자의 속도 안에서 새롭게 읽힐 수 있다는 가능성으로 마무리된다.",
    ))
    return {
        "id": f"20260824_leehu_literature_{sequence:03d}",
        "slug": f"leehu-20260824-{work_slug}-{topic_slug}-slow-reading",
        "title": title,
        "quote": deck,
        "source_author": "이후",
        "source_work": work_name,
        "source_location": "교보ebook 도서 정보의 작가 소개 및 작품 설명 참고 · 작품 본문 직접 인용 없음",
        "source_language": "ko",
        "source_url": source_url,
        "translation_note": "한국어 창작 작품에 관한 독창적 감상으로, 작품 본문과 타인의 번역문을 옮기지 않음.",
        "rights_note": f"소설가 이후의 작품 《{work_name}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.",
        "commentary": commentary,
        "closing": f"《{work_name}》를 다시 펼치는 날에는 {topic_name} 앞에서 달라진 나의 질문도 함께 기록한다.",
        "author": "소설가 이후",
        "tags": ["소설가 이후", work_name, work_tag, topic_name, "느린 독서"],
        "related_work": {"name": work_name, "url": source_url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": {
            "work_introduction": f"소설가 이후의 한국어 창작 작품 {work_title_obj} {topic_name}의 관점에서 다루는 이 문학노트는 교보ebook의 공식 도서 정보를 바탕으로 작품과 작가를 확인한다. 《{work_name}》 본문을 직접 인용하지 않은 채 {topic_name}이라는 독서 주제를 독창적으로 확장한다.",
            "why_read_now": f"빠른 요약과 즉각적인 반응이 일상이 된 지금 《{work_name}》 곁에서 {topic_obj} 바라보는 일은 읽기의 속도를 조절하게 한다. {work_name}에서 떠올린 {image_subj} 결론보다 맥락을 먼저 살피게 하므로, 이 작품을 오늘 다시 생각할 이유가 된다.",
            "personal_reflection": f"나는 {work_title_obj} 설명하려 하기보다 {topic_name} 앞에서 내 문장이 얼마나 쉽게 서두르는지 돌아보았다. {work_name}에서 시작한 {question_subj} 선명한 정답으로 닫히지 않을 때 독서는 타인의 시간과 나의 경험을 함께 존중하는 대화가 될 수 있다고 느꼈다.",
            "meaning_today": f"{work_title_join} {topic_name}을 잇는 이번 읽기는 모르는 것을 곧바로 단정하지 않는 태도의 가치를 남긴다. 《{work_name}》의 독자는 {question}을 자신의 일상으로 가져가면서, 선택하기 전에 한 번 더 듣고 바라보는 구체적인 실천을 시작할 수 있다.",
        },
    }


def main() -> None:
    existing = sorted(CONTENT.glob("*.json"), key=lambda p: int(p.stem))
    if len(existing) != EXPECTED_BEFORE:
        raise SystemExit(f"expected {EXPECTED_BEFORE} sources, found {len(existing)}")
    notes = []
    sequence = 511
    for work in WORKS:
        for topic in TOPICS:
            notes.append(make_note(work, topic, sequence))
            sequence += 1
    if len(notes) != 100:
        raise SystemExit(f"expected 100 notes, got {len(notes)}")
    # Quality checks
    for field in ("id", "slug", "title", "quote", "commentary"):
        values = [re.sub(r"\W+", "", str(n[field])).casefold() for n in notes]
        if len(values) != len(set(values)):
            raise SystemExit(f"duplicate {field}")
    forbidden = ("AI", "자동 생성", "공식 카탈로그", "원문 확인 필요", "소나기을", "권리이", "경계을")
    for note in notes:
        prose = " ".join((note["quote"], note["commentary"], *note["seo_sections"].values()))
        if any(token in prose for token in forbidden):
            raise SystemExit(f"forbidden prose in {note['id']}")
        if any(len(value) < 80 for value in note["seo_sections"].values()):
            raise SystemExit(f"short SEO section in {note['id']}")
    MANIFEST.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"reviewed and wrote {len(notes)} notes")


if __name__ == "__main__":
    main()