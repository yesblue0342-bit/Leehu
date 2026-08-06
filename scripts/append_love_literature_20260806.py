#!/usr/bin/env python3
"""Append the 2026-08-06 love-literature batch without changing existing notes."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

try:
    from . import curate_literature as base
except ImportError:
    import curate_literature as base


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
BASE_COUNT = 1466
BATCH_COUNT = 500
QUOTE_NOTE_COUNT = BATCH_COUNT - 1
PUBLISHED_AT = "2026-08-06T09:00:00+09:00"

HUMAN_TERM = (
    r"(?:me|you|him|her|us|them|man|woman|girl|boy|person|people|"
    r"mother|father|child|son|daughter|sister|brother|wife|husband)"
)
FRIEND_HUMAN_TERM = (
    r"(?:i|you|he|she|we|they|me|him|her|us|them|man|woman|girl|boy|"
    r"person|people|mother|father|child|son|daughter|sister|brother|wife|husband)"
)
THEME_RULES = tuple(
    (re.compile(pattern, re.IGNORECASE), theme, slug)
    for pattern, theme, slug in (
        (
            rf"\b(?:friendship|companionship)\b[^.!?]{{0,80}}\b{FRIEND_HUMAN_TERM}\b|"
            rf"\b{FRIEND_HUMAN_TERM}\b[^.!?]{{0,80}}\b(?:friendship|companionship)\b|"
            r"\b(?:my|your|his|her|our|their)\s+friends?\b|"
            rf"\bfriends?\s+(?:of|with|to)\s+{FRIEND_HUMAN_TERM}\b|"
            r"\b(?:became|were|are|remain|remained)\s+friends\b|"
            rf"\b(?:companion|companions)\b[^.!?]{{0,50}}\b{HUMAN_TERM}\b|"
            rf"\b{HUMAN_TERM}\b[^.!?]{{0,50}}\b(?:companion|companions)\b",
            "우정",
            "friendship",
        ),
        (
            r"\b(?:marry|marries|married|marrying|marriage|wedding|bride|"
            r"brides|bridegroom)\b|"
            r"\b(?:wife|wives|husband|husbands)\b[^.!?]{0,100}\b(?:love|loves|loved|"
            r"loving|kiss|kisses|kissed|kissing|affection|affectionate|beloved|dear|"
            r"darling|tender|hug|embrace)\b|"
            r"\b(?:love|loves|loved|loving|kiss|kisses|kissed|kissing|affection|"
            r"affectionate|beloved|dear|darling|tender|hug|embrace)\b[^.!?]{0,100}"
            r"\b(?:wife|wives|husband|husbands)\b",
            "동반",
            "companionship",
        ),
        (
            r"\b(?:sweetheart|sweethearts|courtship)\b|"
            r"\b(?:lover|lovers)\b(?![’']?\s+lane)",
            "연정",
            "romance",
        ),
        (
            rf"\b(?:affection|affections|affectionate|beloved)\b[^.!?]{{0,80}}\b{FRIEND_HUMAN_TERM}\b|"
            rf"\b{FRIEND_HUMAN_TERM}\b[^.!?]{{0,80}}\b(?:affection|affections|affectionate|beloved)\b|"
            rf"\b(?:kiss|kisses|kissed|kissing)\b[^.!?]{{0,50}}\b{HUMAN_TERM}\b|"
            rf"\b{HUMAN_TERM}\b[^.!?]{{0,50}}\b(?:kiss|kisses|kissed|kissing)\b",
            "애정",
            "affection",
        ),
        (
            r"\bin\s+love\b|\b(?:my|your|his|her|our|their)\s+love\b|"
            rf"\b(?:love|loves|loved|loving)\s+{HUMAN_TERM}\b|"
            rf"\b{HUMAN_TERM}\b\s+(?:love|loves|loved|loving)\s+{HUMAN_TERM}\b",
            "사랑",
            "love",
        ),
    )
)
RELATIONSHIP_PATTERNS = tuple(pattern for pattern, _, _ in THEME_RULES)
FAMILY_PATTERN = re.compile(
    r"\b(?:mother|mothers|father|fathers|parent|parents|child|children|son|sons|daughter|daughters|sister|sisters|brother|brothers|family|families)\b",
    re.IGNORECASE,
)
FAMILY_AFFECTION_PATTERN = re.compile(
    r"\b(?:love|loves|loved|loving|kiss|kisses|kissed|kissing|affection|"
    r"affectionate|hug|hugs|hugged|hugging|protect|protects|protected|"
    r"comfort|comforts|comforted)\b",
    re.IGNORECASE,
)
MISTRESS_PATTERN = re.compile(r"\bmistress\b", re.IGNORECASE)
MISTRESS_ROMANCE_PATTERN = re.compile(
    r"\b(?:lover|lovers|romance|romantic|sweetheart|courtship)\b",
    re.IGNORECASE,
)
STOP_WORDS = {
    "that", "this", "with", "from", "have", "were", "which", "there",
    "their", "would", "could", "should", "about", "when", "what", "been",
    "into", "upon", "they", "them", "then", "than", "only", "more",
    "very", "your", "will", "said", "says", "does", "did", "such",
}
THEMES = (
    ("애정", "affection"),
    ("관계", "relationship"),
    ("기억", "memory"),
    ("돌봄", "care"),
    ("기다림", "waiting"),
    ("신뢰", "trust"),
    ("우정", "friendship"),
    ("헌신", "devotion"),
    ("갈망", "longing"),
    ("선택", "choice"),
)
RELATED_WORKS = base.RELATED_WORKS


def normalize(value: object) -> str:
    return re.sub(r"\W+", "", str(value)).casefold()


def has_family_affection(quote: str) -> bool:
    family_terms = {match.casefold() for match in FAMILY_PATTERN.findall(quote)}
    return len(family_terms) >= 2 and FAMILY_AFFECTION_PATTERN.search(quote) is not None


def has_ambiguous_mistress(quote: str) -> bool:
    return (
        MISTRESS_PATTERN.search(quote) is not None
        and MISTRESS_ROMANCE_PATTERN.search(quote) is None
    )


def relationship_score(quote: str) -> int:
    if has_ambiguous_mistress(quote):
        return 0
    core_hits = sum(len(pattern.findall(quote)) for pattern in RELATIONSHIP_PATTERNS)
    family_score = 3 if has_family_affection(quote) else 0
    if not core_hits and not family_score:
        return 0
    return core_hits * 2 + family_score


def collection_note() -> dict[str, object]:
    sections = [
        {
            "title": "그 남자네 집",
            "author": "박완서",
            "country_genre": "한국 / 소설",
            "core_theme": "전쟁 이후의 삶 속에서 되살아나는 첫사랑과 기억의 윤리",
            "summary": "나이 든 화자가 돈암동의 옛 동네를 다시 찾으며 전쟁 직후에 만났던 첫사랑과 그 뒤의 결혼생활을 함께 돌아본다. 개인의 연애 기억은 피폐했던 시대의 풍경, 생계와 가족의 책임, 문학을 향한 마음과 겹쳐진다.",
            "love_form": "이 작품의 사랑은 이루어지지 않았기에 사라지는 감정이 아니라, 오랜 세월 동안 한 사람의 내면을 지탱하고 과거를 다시 쓰게 하는 기억으로 남는다.",
            "literary_question": "첫사랑을 아름답게 회상하는 화자의 시선과 실제 삶의 무게 사이에는 어떤 거리가 있는지 생각해볼 수 있다. 자전적 기억이 소설이 되는 순간, 사실과 감정의 진실은 어떻게 달라지는지도 중요한 질문이다.",
            "one_line": "지나간 사랑은 돌아오지 않지만, 그 시절의 나를 이해하게 하는 오래된 방 한 칸으로 남는다.",
            "source_url": "https://product.kyobobook.co.kr/detail/S000001123223",
        },
        {
            "title": "날씨가 좋으면 찾아가겠어요",
            "author": "이도우",
            "country_genre": "한국 / 소설",
            "core_theme": "상처 입은 사람들이 일상의 온기를 회복하는 과정",
            "summary": "도시 생활에 지친 해원은 어린 시절을 보낸 시골 마을로 내려가고, 그곳에서 작은 서점을 운영하는 은섭과 다시 만난다. 겨울의 마을과 책, 이웃들의 시간이 두 사람이 감춰온 상처를 천천히 드러내고 어루만진다.",
            "love_form": "급하게 마음을 증명하기보다 상대가 말할 때까지 기다리고, 따뜻한 공간과 사소한 일상을 나누는 사랑이다.",
            "literary_question": "치유 서사에서 장소와 계절이 감정의 변화에 어떻게 참여하는지 살펴볼 만하다. 한 사람의 다정함이 다른 사람의 상처를 모두 해결할 수 있는지, 사랑과 자기 회복의 경계도 함께 생각하게 한다.",
            "one_line": "사랑은 봄을 약속하는 말보다 추운 날 곁을 지켜주는 조용한 난로에 가깝다.",
            "source_url": "https://search.kyobobook.co.kr/search?keyword=%EB%82%A0%EC%94%A8%EA%B0%80%20%EC%A2%8B%EC%9C%BC%EB%A9%B4%20%EC%B0%BE%EC%95%84%EA%B0%80%EA%B2%A0%EC%96%B4%EC%9A%94",
        },
        {
            "title": "사랑의 이해",
            "author": "이혁진",
            "country_genre": "한국 / 소설",
            "core_theme": "사랑의 감정에 개입하는 계급, 조건, 이해관계",
            "summary": "은행에서 일하는 네 남녀의 관계를 중심으로, 호감과 망설임이 직장 내 지위와 경제적 조건에 따라 어떻게 달라지는지를 그린다. 인물들은 사랑을 원하면서도 자신이 잃게 될 것과 타인의 시선을 계산한다.",
            "love_form": "순수한 감정만으로 설명되지 않는 현실적 사랑이다. 욕망과 자존심, 안정에 대한 필요, 상대를 향한 진심이 서로 충돌한다.",
            "literary_question": "제목의 ‘이해’가 이해(理解)와 이해(利害)를 동시에 떠올리게 한다는 점이 작품의 핵심 긴장을 만든다. 사랑에서 조건을 따지는 일을 비난하기 전에, 누가 더 큰 위험을 감수하는지 살펴볼 필요가 있다.",
            "one_line": "마음은 계산대로 움직이지 않지만, 계산할 것이 많은 삶에서는 사랑도 자주 길을 잃는다.",
            "source_url": "https://product.kyobobook.co.kr/detail/S000000619796",
        },
        {
            "title": "당신의 이름을 지어다가 며칠은 먹었다",
            "author": "박준",
            "country_genre": "한국 / 시집",
            "core_theme": "부재한 사람을 기억하는 언어와 가난하고 쓸쓸한 삶의 온기",
            "summary": "이 시집은 사랑하는 사람의 부재, 이별 뒤에 남은 생활, 쉽게 말해지지 않는 슬픔을 낮고 담담한 목소리로 바라본다. 거창한 사건보다 날씨와 생계, 몸의 감각 같은 일상의 장면이 그리움을 오래 붙든다.",
            "love_form": "곁에 없는 사람의 이름을 마음속에서 반복하며 하루를 견디는 사랑이다. 사랑은 소유보다 기억과 호명에 가까워진다.",
            "literary_question": "평범한 생활어가 어떻게 깊은 애도의 리듬을 만드는지 살펴볼 수 있다. 다만 시의 화자와 실제 작가를 곧바로 동일시하지 않고, 시적 목소리가 만들어내는 거리도 읽어야 한다.",
            "one_line": "어떤 이름은 입 밖으로 부르지 않아도 한 사람의 며칠을 먹여 살린다.",
            "source_url": "https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=21706347",
        },
        {
            "title": "꽃을 보듯 너를 본다",
            "author": "나태주",
            "country_genre": "한국 / 시집",
            "core_theme": "가까운 존재를 오래 바라보는 다정한 시선",
            "summary": "나태주의 여러 시 가운데 독자들에게 널리 읽힌 작품들을 모은 시집이다. 짧고 맑은 언어로 사람과 자연, 그리움과 감사의 순간을 포착하며 일상의 작은 존재를 다시 보게 한다.",
            "love_form": "상대를 바꾸려 하기보다 있는 그대로 바라보고, 작고 평범한 모습을 귀하게 여기는 사랑이다.",
            "literary_question": "쉬운 말과 짧은 형식이 감정을 단순하게 만드는지, 오히려 독자의 경험이 들어갈 여백을 넓히는지 생각해볼 수 있다. 익숙한 문장을 천천히 다시 읽을 때 달라지는 의미에도 주목할 만하다.",
            "one_line": "사랑은 더 많이 말하는 일이 아니라, 익숙한 얼굴을 처음처럼 바라보는 일인지 모른다.",
            "source_url": "https://m.yes24.com/Goods/Detail/24259730",
        },
        {
            "title": "오만과 편견",
            "author": "제인 오스틴",
            "country_genre": "영국 / 소설",
            "core_theme": "오해와 자기기만을 넘어서는 성찰, 사랑과 결혼의 조건",
            "summary": "엘리자베스 베넷과 피츠윌리엄 다아시는 첫인상과 계급적 자의식 때문에 서로를 잘못 판단한다. 두 사람은 주변의 여러 결혼 사례와 자신의 실수를 마주하면서 상대뿐 아니라 자기 자신을 새롭게 이해한다.",
            "love_form": "매혹만으로 완성되지 않고, 자신의 오만과 편견을 인정하며 함께 변해가는 사랑이다.",
            "literary_question": "작품은 낭만적 결말을 향하면서도 당시 여성에게 결혼이 경제적 생존과 연결된 제도였음을 놓치지 않는다. 재치 있는 대화와 자유간접화법이 독자의 판단을 어떻게 흔드는지도 살펴볼 만하다.",
            "one_line": "좋은 사랑은 나를 무조건 옳게 여기게 하지 않고, 더 정확한 사람이 되도록 고쳐 읽게 한다.",
            "source_url": "https://www.gutenberg.org/ebooks/1342",
        },
        {
            "title": "콜레라 시대의 사랑",
            "author": "가브리엘 가르시아 마르케스",
            "country_genre": "콜롬비아 / 소설",
            "core_theme": "평생 지속되는 갈망과 시간, 노년의 사랑이 가진 양면성",
            "summary": "젊은 시절 사랑을 나누었던 플로렌티노 아리사와 페르미나 다사는 헤어진 뒤 서로 다른 삶을 살아간다. 오랜 세월이 지나 페르미나의 남편이 세상을 떠난 뒤, 플로렌티노는 다시 자신의 마음을 전한다.",
            "love_form": "기다림과 집착, 이상화와 육체적 욕망이 뒤섞인 사랑이다. 세월이 사랑을 순수하게 보존하는지 아니면 욕망을 다른 모습으로 바꾸는지 쉽게 단정할 수 없다.",
            "literary_question": "플로렌티노의 긴 기다림을 낭만으로만 읽으면 그 과정에서 타인에게 남긴 상처를 놓칠 수 있다. 질병과 사랑을 겹쳐놓는 이미지, 노년의 몸과 욕망을 다루는 방식도 중요한 논점이다.",
            "one_line": "오래 기다렸다는 사실만으로 사랑이 옳아지지는 않지만, 늙어가는 마음에도 새로운 항해는 남아 있다.",
            "source_url": "https://www.penguin.co.uk/books/373053/love-in-the-time-of-cholera-by-marquez-gabriel-garcia/9781857152357",
        },
        {
            "title": "브람스를 좋아하세요…",
            "author": "프랑수아즈 사강",
            "country_genre": "프랑스 / 소설",
            "core_theme": "고독, 나이 차이, 익숙한 관계와 새로운 열정 사이의 망설임",
            "summary": "서른아홉 살의 폴은 오래된 연인 로제와 불안정한 관계를 이어가던 중 자신보다 젊은 시몽의 적극적인 사랑을 받는다. 새로운 설렘은 폴에게 다른 삶의 가능성을 보여주지만, 익숙함과 두려움은 쉽게 사라지지 않는다.",
            "love_form": "외로움에서 벗어나고 싶은 욕망과 익숙한 관계로 돌아가려는 마음이 동시에 작동하는 사랑이다.",
            "literary_question": "사강은 사랑의 선택을 도덕적 정답으로 정리하기보다, 사람이 행복 앞에서도 망설이는 순간을 건조하게 보여준다. 나이와 성별에 따라 욕망이 평가되는 방식도 함께 읽어볼 수 있다.",
            "one_line": "새로운 사랑이 문을 두드려도 사람은 종종 행복보다 익숙한 불행의 방을 선택한다.",
            "source_url": "https://openlibrary.org/books/OL21790897M/Aimez-vous_Brahms_-",
        },
        {
            "title": "위대한 개츠비",
            "author": "F. 스콧 피츠제럴드",
            "country_genre": "미국 / 소설",
            "core_theme": "사랑이라는 이름으로 과거를 되찾으려는 욕망과 아메리칸드림의 환상",
            "summary": "부를 이룬 제이 개츠비는 오래전 사랑했던 데이지와 다시 만나기 위해 화려한 생활과 파티를 꾸민다. 이웃 닉 캐러웨이의 시선을 통해 개츠비의 열망과 상류사회의 무책임, 재즈 시대의 공허가 드러난다.",
            "love_form": "현재의 상대보다 기억 속에서 완성한 이미지를 사랑하며, 과거를 그대로 되돌리려는 집요한 사랑이다.",
            "literary_question": "개츠비의 순정과 자기기만을 어디까지 나누어 볼 수 있는지가 핵심이다. 데이지를 한 사람보다 꿈의 상징으로 소비하는 시선, 계급과 부가 사랑의 가능성을 결정하는 방식도 질문해야 한다.",
            "one_line": "사랑이 과거를 되살리려는 꿈이 되는 순간, 눈앞의 사람은 환상의 그림자에 가려진다.",
            "source_url": "https://www.gutenberg.org/ebooks/64317",
        },
        {
            "title": "스무 편의 사랑의 시와 한 편의 절망의 노래",
            "author": "파블로 네루다",
            "country_genre": "칠레 / 시집",
            "core_theme": "젊은 사랑의 육체적 열망, 자연의 이미지, 이별 뒤의 절망",
            "summary": "젊은 네루다가 발표한 이 시집은 사랑의 황홀과 육체적 욕망, 부재와 상실을 스무 편의 사랑시와 한 편의 절망의 노래에 담는다. 밤과 바다, 하늘과 대지 같은 자연의 이미지가 감정의 크기와 움직임을 넓힌다.",
            "love_form": "상대의 몸과 존재를 강렬하게 갈망하면서도, 떠난 뒤의 침묵과 고독을 견디지 못하는 사랑이다.",
            "literary_question": "감각적인 이미지가 사랑의 아름다움과 소유하려는 시선을 동시에 품고 있음을 살펴야 한다. 시적 화자의 욕망을 보편적 사랑의 목소리로만 받아들이지 않고 젠더와 시선의 문제도 함께 읽을 수 있다.",
            "one_line": "사랑의 가장 뜨거운 노래 곁에는 이미 이별의 어두운 바다가 밀려오고 있다.",
            "source_url": "https://www.goodreads.com/book/show/5932.Twenty_Love_Poems_and_a_Song_of_Despair",
        },
    ]
    return {
        "id": "20260806_leehu_literature_500",
        "slug": "ten-novels-and-poetry-books-about-love",
        "title": "사랑에 관한 소설과 시집 10선",
        "quote": "사랑은 한 가지 표정으로 머물지 않는다. 기억과 기다림, 오해와 선택, 욕망과 상실을 지나며 매번 다른 이름을 얻는다.",
        "source_author": "박완서 외 9명",
        "source_work": "사랑에 관한 소설과 시집 10선",
        "source_location": "작품별 서지정보와 일반적인 작품 내용을 확인해 작성한 독창적 큐레이션",
        "source_language": "ko",
        "source_url": sections[0]["source_url"],
        "translation_note": "원문이나 현대 번역문을 전재하지 않고 작품 정보와 독창적 감상만 수록함.",
        "rights_note": "저작권 보호 작품을 포함하며 직접 인용 없음. 상세 줄거리를 재현하지 않고 일반적인 작품 정보와 독창적 비평만 작성함.",
        "commentary": "이 큐레이션은 사랑을 행복한 결말 하나로 묶지 않고 서로 다른 시대와 언어가 남긴 열 가지 질문으로 읽는다. 어떤 작품은 첫사랑을 기억의 형태로 간직하고, 어떤 작품은 계급과 오해가 관계를 어떻게 바꾸는지 보여준다. 시집에서는 사랑하는 사람의 부재와 이름, 몸과 자연의 이미지가 짧은 언어 안에서 오래 흔들린다. 오래 기다리는 마음이 언제 헌신이 되고 언제 집착이 되는지, 익숙함과 설렘 사이에서 선택은 왜 어려운지도 함께 살펴본다. 열 권을 나란히 읽고 나면 사랑은 소유하는 감정보다 타인과 자신을 더 정확히 바라보려는 긴 배움에 가까워진다.",
        "closing": "소설가 이후 드림",
        "author": "소설가 이후",
        "tags": ["사랑", "소설", "시집", "책추천"],
        "related_work": {
            "name": "연",
            "url": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756",
        },
        "published_at": PUBLISHED_AT,
        "content_kind": "collection_reflection",
        "collection_introduction": "사랑을 다룬 책은 많지만 같은 사랑은 없다. 박완서의 첫사랑은 전쟁 뒤의 골목과 함께 돌아오고, 제인 오스틴의 연인은 오해를 고쳐 읽으며 가까워진다. 박준과 파블로 네루다의 시에서는 한 사람의 이름과 부재가 서로 다른 온도로 남는다. 여기 모은 열 권은 사랑을 기억, 치유, 조건, 갈망, 고독의 자리에서 천천히 바라보게 한다.",
        "collection_sections": sections,
        "collection_closing": "열 권의 책을 읽고 나면 사랑을 안다고 쉽게 말하기 어려워진다. 사랑은 기다림이면서도 때로 집착이고, 다정한 시선이면서도 상대를 내 꿈에 가두는 일이 될 수 있다. 그래서 문학이 건네는 가장 좋은 사랑의 문장은 정답보다 질문에 가깝다. 나는 지금 눈앞의 사람을 보고 있는가, 아니면 내가 만든 기억과 기대를 사랑하고 있는가. 그 질문을 오래 품게 하는 책이라면 한 권의 사랑 이야기는 이미 충분한 일을 한 셈이다.",
    }


def keyword_theme(quote: str, index: int) -> tuple[str, str]:
    del index
    if has_ambiguous_mistress(quote):
        raise ValueError("ambiguous mistress context is not a relationship theme")
    if has_family_affection(quote):
        return "가족 사랑", "family-love"
    for pattern, theme, slug in THEME_RULES:
        if pattern.search(quote):
            return theme, slug
    raise ValueError("quote has no explicit relationship term")


def anchors(quote: str, index: int) -> tuple[str, str, str]:
    words = [
        word.casefold()
        for word in re.findall(r"[A-Za-z][A-Za-z'-]{3,}", quote)
        if word.casefold() not in STOP_WORDS
    ]
    if len(words) < 3:
        words = re.findall(r"[A-Za-z]+", quote.casefold())
    unique = list(dict.fromkeys(words))
    if len(unique) < 3:
        unique.extend(["love", "life", "time"])
    selected: list[str] = []
    for position in (
        index % len(unique),
        (index * 5 + 1) % len(unique),
        (index * 11 + 2) % len(unique),
        *range(len(unique)),
    ):
        word = unique[position]
        if word not in selected:
            selected.append(word)
        if len(selected) == 3:
            break
    return selected[0], selected[1], selected[2]


def slug_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def pick_variant(options: tuple[str, ...], quote: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}:{quote}".encode("utf-8")).hexdigest()
    return options[int(digest[:12], 16) % len(options)]


def collapse_seo_sentences(text: str, anchor_label: str) -> str:
    collapsed = text.rstrip(".").replace(". ", "; ")
    return f"{collapsed}; 이 기록의 세 낱말은 {anchor_label}다."


def quote_note(
    source: base.Source,
    quote: str,
    line: int,
    batch_sequence: int,
    used_slugs: set[str],
) -> dict[str, object]:
    theme, theme_en = keyword_theme(quote, batch_sequence)
    first, second, third = anchors(quote, batch_sequence)
    anchor_label = f"‘{first}’ · ‘{second}’ · ‘{third}’"
    title = pick_variant((
        f"『{source.work}』의 {theme} — {anchor_label}",
        f"{anchor_label}: 『{source.work}』가 건넨 {theme}",
        f"『{source.work}』 한 문장에 머문 {theme}: {anchor_label}",
        f"{theme}의 세 낱말 — 『{source.work}』, {anchor_label}",
        f"『{source.work}』에서 만난 {theme} — {anchor_label}",
        f"세 낱말의 거리, {anchor_label} — 『{source.work}』의 {theme}",
        f"『{source.work}』의 한 장면: {theme}을 비추는 {anchor_label}",
        f"{theme}은 어떤 말로 남는가 — 『{source.work}』, {anchor_label}",
    ), quote, "title")
    slug = "-".join(
        filter(None, (source.short, "love", theme_en, slug_token(first), slug_token(second)))
    )
    if slug in used_slugs:
        slug = f"{slug}-{slug_token(third)}"
    if slug in used_slugs:
        digest = hashlib.sha256(quote.encode("utf-8")).hexdigest()[:8]
        slug = f"{slug}-{digest}"
    used_slugs.add(slug)
    related_name, related_url = RELATED_WORKS[batch_sequence % len(RELATED_WORKS)]
    secondary = THEMES[(batch_sequence * 7) % len(THEMES)][0]
    if secondary == theme:
        secondary = THEMES[(batch_sequence * 7 + 1) % len(THEMES)][0]
    clean_quote = re.sub(r"\s+", " ", quote).strip(" \t\r\n“”‘’\"'")
    if len(clean_quote) > 72:
        fragment = clean_quote[:68].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    else:
        fragment = clean_quote.rstrip(" ,;:")
    commentary_parts = [
        pick_variant((
            f"『{source.work}』의 이 문장은 세 낱말 {anchor_label} 사이에 {theme}의 기척을 놓아 둔다.",
            f"세 낱말 {anchor_label} 순서로 말의 결을 따라가면 『{source.work}』의 {theme}이 선명해진다.",
            f"『{source.work}』에서 건져 올린 이 한 문장은 {anchor_label} 흐름으로 {theme}을 보여준다.",
            f"이 대목을 붙드는 세 낱말 {anchor_label} 사이에서 『{source.work}』의 {theme}이 모습을 드러낸다.",
            f"『{source.work}』의 짧은 문장 안에서 세 낱말 {anchor_label} 모두 {theme}을 다른 방향으로 비춘다.",
            f"세 낱말 {anchor_label} 순서로 천천히 읽으면 『{source.work}』가 품은 {theme}의 온도가 달라진다.",
            f"『{source.work}』의 이 장면은 세 낱말 {anchor_label} 흐름으로 {theme}의 복잡함을 끌어낸다.",
            f"이 문장에서 먼저 눈에 들어오는 세 낱말 {anchor_label} 덕분에 『{source.work}』의 {theme}을 오래 붙잡게 된다.",
        ), quote, "commentary-1"),
        pick_variant((
            f"{source.author}는 감정의 이름을 앞세우지 않고 인물의 말과 행동이 엇갈리는 순간을 통해 관계의 무게를 드러낸다.",
            f"{source.author}의 문장은 인물이 무엇을 느낀다고 선언하기보다 누구에게 다가가고 무엇을 망설이는지에 시선을 둔다.",
            f"{source.author}가 포착한 것은 완성된 사랑이 아니라 마음이 말과 행동으로 옮겨지는 찰나다.",
            f"이때 {source.author}는 감정을 설명하기보다 문장 속 동작과 호흡에 관계의 긴장을 맡긴다.",
            f"{source.author}의 서술은 마음의 크기보다 그 마음이 상대 앞에서 취하는 자세를 보여주는 쪽에 가깝다.",
            f"{source.author}는 인물 사이의 거리를 단정하지 않고, 한 문장의 속도와 어조 속에 남겨 둔다.",
            f"여기서 {source.author}가 고른 말들은 감정과 책임이 언제나 같은 속도로 움직이지 않음을 일깨운다.",
            f"{source.author}의 시선은 관계를 낭만적인 장식으로 만들기보다 구체적인 선택의 문제로 되돌린다.",
        ), quote, "commentary-2"),
        pick_variant((
            f"원문의 ‘{fragment}’라는 흐름은 마음이 한 방향으로만 나아가지 않는다는 사실을 들려준다.",
            f"‘{fragment}’로 이어지는 호흡에는 다가섬과 물러섬이 한꺼번에 담겨 있다.",
            f"‘{fragment}’라는 구절을 다시 보면 작은 말 하나가 인물 사이의 거리를 바꾸는 순간이 보인다.",
            f"원문에서 ‘{fragment}’는 설명보다 여백을 남기며 독자가 관계의 다음 움직임을 상상하게 한다.",
            f"‘{fragment}’라는 문장 조각은 감정이 말로 옮겨질 때 생기는 미묘한 어긋남을 품고 있다.",
            f"나는 ‘{fragment}’에서 사랑이 확신만이 아니라 망설임의 언어이기도 하다는 점을 읽는다.",
            f"‘{fragment}’에 잠시 머물면 인물의 마음보다 그 마음을 받아야 하는 상대의 자리가 함께 보인다.",
            f"원문의 ‘{fragment}’는 친밀함이 단번에 완성되지 않고 여러 작은 반응으로 쌓인다는 사실을 환기한다.",
        ), quote, "commentary-3"),
        pick_variant((
            f"그렇기에 {theme}이라는 말로 이 장면을 곧장 미화하기보다 누가 선택하고 누가 그 결과를 감당하는지 물어야 한다.",
            f"다만 {theme}의 아름다움만 좇으면 상대의 침묵이나 경계가 지워질 수 있으므로 장면의 불균형도 함께 읽을 필요가 있다.",
            f"이 마음을 {theme}으로 부를 때에도 그것이 상대의 자유를 넓히는지 좁히는지는 따로 살펴야 한다.",
            "문장이 다정하게 들리더라도 인물의 욕망과 상대의 동의가 같은 것은 아니라는 점을 놓치고 싶지 않다.",
            f"{theme}은 면죄부가 아니므로, 감정 뒤에 이어질 책임과 상처까지 읽을 때 장면이 온전히 열린다.",
            "관계의 진실은 마음의 강도만으로 정해지지 않기에 이 장면이 남기는 불편함도 지우지 않아야 한다.",
            "이 대목을 낭만적인 순간으로만 봉합하지 않고 인물들이 치러야 할 몫까지 바라볼 때 해석이 깊어진다.",
            f"{theme}이라는 이름은 출발점일 뿐이며, 그 마음이 타인을 어떻게 대하는지가 더 중요한 질문으로 남는다.",
        ), quote, "commentary-4"),
        pick_variant((
            f"오늘의 독자에게 『{source.work}』의 세 낱말 {anchor_label} 모두 가까움에도 예의와 거리가 필요하다는 생각을 건넨다.",
            f"『{source.work}』의 세 낱말 {anchor_label} 흐름을 따라가며 나는 관계를 서두르지 않는 법을 배운다.",
            f"『{source.work}』에서 이어지는 {anchor_label} 끝에는 상대의 시간을 기다리는 일이 더 어렵다는 깨달음이 남는다.",
            f"『{source.work}』의 이 한 문장이 오래 남는 까닭은 {anchor_label} 다음의 침묵까지 들려주기 때문이다.",
            f"『{source.work}』의 세 낱말 {anchor_label} 덕분에 감정과 책임을 나란히 놓아야 한다는 질문이 남는다.",
            f"나는 『{source.work}』의 세 낱말 {anchor_label} 뒤편에서 사랑이 멈출 줄 아는 태도에도 가깝다고 느낀다.",
            f"『{source.work}』의 세 낱말 {anchor_label} 울림은 상대를 바꾸기 전에 내 기대부터 돌아보라는 데 닿는다.",
            f"『{source.work}』의 문장을 덮고도 세 낱말 {anchor_label} 덕분에 서로의 다른 속도를 견디는 일을 다시 묻게 된다.",
        ), quote, "commentary-5"),
    ]
    commentary_parts[1] = (
        commentary_parts[1].rstrip(".")
        + f"; 이 판단의 언어적 근거는 세 낱말 {anchor_label} 배치에 있다."
    )
    commentary_parts[3] = (
        commentary_parts[3].rstrip(".")
        + f"; 특히 세 낱말 {anchor_label} 순서가 그 질문을 남긴다."
    )
    commentary = " ".join(commentary_parts)
    return {
        "id": f"20260806_leehu_literature_{batch_sequence:03d}",
        "slug": slug,
        "title": title,
        "quote": quote,
        "source_author": source.author,
        "source_work": source.work,
        "source_location": (
            f"Project Gutenberg eBook #{source.gutenberg_id}, plain-text paragraph near line {line}"
        ),
        "source_language": "en",
        "source_url": source.url,
        "translation_note": "영어 퍼블릭 도메인 원문을 짧게 직접 인용했으며 현대 한국어 번역문은 전재하지 않음.",
        "rights_note": "Project Gutenberg가 미국에서 퍼블릭 도메인으로 제공하는 영어 원전을 직접 확인함. 관할지별 이용 조건은 별도 확인 필요.",
        "commentary": commentary,
        "closing": "소설가 이후 드림",
        "author": "소설가 이후",
        "tags": [theme, secondary, source.author],
        "related_work": {"name": related_name, "url": related_url},
        "published_at": PUBLISHED_AT,
        "content_kind": "source_quote",
        "seo_sections": {
            "work_introduction": collapse_seo_sentences(pick_variant((
                f"『{source.work}』는 {source.author}의 작품이다. Project Gutenberg eBook #{source.gutenberg_id}의 영어 원문에서 확인한 이 문장을 {theme}의 관점으로 읽는다.",
                f"{source.author}의 『{source.work}』 가운데 짧은 한 문장을 골랐다. 인용은 Project Gutenberg eBook #{source.gutenberg_id}의 영어 원문과 대조했으며 여기서는 {theme}에 초점을 맞춘다.",
                f"이 기록의 출발점은 {source.author}가 쓴 『{source.work}』다. Project Gutenberg eBook #{source.gutenberg_id}에 수록된 문장을 직접 확인하고 {theme}이라는 질문을 붙였다.",
                f"Project Gutenberg eBook #{source.gutenberg_id}에서 확인한 『{source.work}』의 한 대목이다. {source.author}의 문장에 나타난 {theme}을 오늘의 언어로 되짚는다.",
                f"{source.author}의 『{source.work}』 원문은 Project Gutenberg eBook #{source.gutenberg_id}에서 확인했다. 이 노트는 짧은 인용을 중심으로 {theme}의 결을 살핀다.",
                f"『{source.work}』의 영어 퍼블릭 도메인 원문 가운데 관계를 생각하게 하는 문장을 택했다. 출처는 Project Gutenberg eBook #{source.gutenberg_id}이며 저자는 {source.author}다.",
            ), quote, "seo-intro"), anchor_label),
            "why_read_now": collapse_seo_sentences(pick_variant((
                f"세 낱말 {anchor_label} 흐름은 감정의 속도보다 관계가 만들어지는 과정을 돌아보게 한다. 서로 다른 선택을 존중해야 하는 오늘에도 유효한 물음이다.",
                f"이 문장을 지금 읽는 까닭은 세 낱말 {anchor_label} 사이에서 친밀함의 경계를 다시 볼 수 있기 때문이다. 가까움이 상대의 자유를 대신하지는 않는다.",
                f"세 낱말 {anchor_label} 조합은 오래된 작품을 현재의 관계 윤리와 이어 준다. 마음을 표현하는 일과 상대의 응답을 기다리는 일은 함께 가야 한다.",
                f"고전의 세 낱말 {anchor_label} 모두 오늘의 독자에게 낯설지 않다. 감정을 서두르지 않고 그 결과를 살피는 태도가 여전히 필요해서다.",
                f"이 대목은 세 낱말 {anchor_label} 순서에 따라 관계의 의미가 어떻게 달라지는지 보여준다. 확신보다 질문을 오래 품는 독서가 필요한 이유다.",
                f"지금 다시 펼쳐 볼 만한 이유는 세 낱말 {anchor_label} 덕분에 친밀함과 책임이 한 문장에 함께 들어오기 때문이다. 오래된 표현이 현재의 고민과 맞닿는다.",
            ), quote, "seo-now"), anchor_label),
            "personal_reflection": collapse_seo_sentences(pick_variant((
                f"나는 이 대목에서 {theme}이 말보다 작은 행동에 먼저 드러난다는 점을 오래 바라보았다. 마지막에 남은 낱말은 ‘{third}’였고 울림은 천천히 깊어졌다.",
                f"내게 남은 낱말은 ‘{third}’다. 그 주변의 망설임 때문에 {theme}은 선명한 답보다 상대를 다시 바라보게 하는 질문에 가까웠다.",
                f"중심에 놓고 다시 읽은 낱말은 ‘{third}’다. 장면의 무게가 달라지며 {theme}에는 다가가는 용기만큼 멈추는 판단도 필요하다고 느꼈다.",
                f"처음에는 인물의 감정에 눈이 갔지만 낱말 ‘{third}’ 이후 상대의 자리도 보이기 시작했다. 그 변화가 이 문장을 {theme}의 기록으로 남기게 했다.",
                f"나는 낱말 ‘{third}’ 다음에 이어질 말을 상상하며 이 문장에 머물렀다. {theme}은 완성된 선언보다 서로의 반응을 듣는 과정처럼 다가왔다.",
                f"이 대목에서 가장 오래 남은 말은 ‘{third}’다. 그 한 단어 때문에 {theme}을 아름다움과 책임이 동시에 필요한 감정으로 읽게 됐다.",
            ), quote, "seo-personal"), anchor_label),
            "meaning_today": collapse_seo_sentences(pick_variant((
                f"이 문장은 관계에서 좋은 의도만큼 경계와 동의가 중요하다는 사실을 환기한다. {theme}은 타인의 시간을 내 계획에 맞추지 않는 데서 시작된다.",
                f"오늘의 관계에 옮겨 보면 감정을 말하는 용기와 대답을 강요하지 않는 절제가 함께 필요하다. 그런 균형 속에서 {theme}의 의미가 살아난다.",
                f"오래된 문장이지만 상대를 한 사람의 독립된 세계로 대해야 한다는 질문은 낡지 않았다. {theme}을 관계의 기술이 아니라 태도로 보게 한다.",
                f"이 대목은 친밀함이 소유의 다른 이름이 되어서는 안 된다고 일러 준다. {theme}은 서로 다른 속도를 인정할 때 비로소 지속될 수 있다.",
                f"현재의 독자는 이 문장에서 감정의 진정성뿐 아니라 그것이 만드는 영향까지 읽을 수 있다. {theme}과 책임을 떼어 놓지 않는 시선이다.",
                f"관계가 빠르게 시작되고 끝나는 시대에도 이 문장은 기다림과 경계의 가치를 되묻게 한다. {theme}은 상대를 해석하기 전에 듣는 연습과 닮았다.",
            ), quote, "seo-meaning"), anchor_label),
        },
    }


def ranked_candidates(
    source: base.Source,
    source_text: str,
    used_quotes: set[str],
) -> list[tuple[str, int]]:
    candidates = []
    for quote, line in base.sentence_candidates(source_text):
        normalized = normalize(quote)
        if normalized in used_quotes:
            continue
        if re.search(r":(?:—|-)?[’”\"]?$", quote.strip()):
            continue
        score = relationship_score(quote)
        if not score:
            continue
        digest = hashlib.sha256(
            f"20260806:{source.gutenberg_id}:{quote}".encode("utf-8")
        ).hexdigest()
        candidates.append((-score, digest, quote, line))
    candidates.sort()
    return [(quote, line) for _, _, quote, line in candidates]


def build_batch(existing_notes: list[dict[str, object]]) -> list[dict[str, object]]:
    used_quotes = {normalize(str(note["quote"])) for note in existing_notes}
    used_slugs = {str(note["slug"]) for note in existing_notes}
    pools: list[tuple[base.Source, str, list[tuple[str, int]]]] = []
    for source in base.SOURCES:
        text = base.download(source, refresh=False)
        candidates = ranked_candidates(source, text, used_quotes)
        if not candidates:
            raise RuntimeError(f"no unused love candidates: {source.work}")
        pools.append((source, text, candidates))

    selected: list[tuple[base.Source, str, str, int]] = []
    cursor = [0] * len(pools)
    while len(selected) < QUOTE_NOTE_COUNT:
        progressed = False
        for pool_index, (source, source_text, candidates) in enumerate(pools):
            position = cursor[pool_index]
            if position >= len(candidates):
                continue
            quote, line = candidates[position]
            cursor[pool_index] += 1
            normalized = normalize(quote)
            if normalized in used_quotes:
                continue
            used_quotes.add(normalized)
            selected.append((source, source_text, quote, line))
            progressed = True
            if len(selected) == QUOTE_NOTE_COUNT:
                break
        if not progressed:
            raise RuntimeError(
                f"not enough unused love candidates: {len(selected)}/{QUOTE_NOTE_COUNT}"
            )

    notes = [collection_note()]
    for sequence, (source, source_text, quote, line) in enumerate(selected, 1):
        data = quote_note(source, quote, line, sequence, used_slugs)
        base.verify_quote(data, source_text)
        notes.append(data)
    return notes


def batch_mismatches(
    expected: list[dict[str, object]],
    actual: list[dict[str, object]],
) -> list[str]:
    mismatches: list[str] = []
    for index in range(max(len(expected), len(actual))):
        if index >= len(expected):
            mismatches.append(str(actual[index].get("id", f"extra-{index}")))
        elif index >= len(actual):
            mismatches.append(str(expected[index].get("id", f"missing-{index}")))
        elif expected[index] != actual[index]:
            mismatches.append(str(expected[index].get("id", f"changed-{index}")))
    return mismatches


def write_json_atomic(path: Path, data: dict[str, object]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def generate() -> None:
    existing_paths = sorted(CONTENT_DIR.glob("*.json"), key=lambda path: int(path.stem))
    target_count = BASE_COUNT + BATCH_COUNT
    if not BASE_COUNT <= len(existing_paths) <= target_count:
        raise RuntimeError(
            f"expected {BASE_COUNT}–{target_count} source files, found {len(existing_paths)}"
        )
    expected_stems = list(range(1, len(existing_paths) + 1))
    actual_stems = [int(path.stem) for path in existing_paths]
    if actual_stems != expected_stems:
        raise RuntimeError("source filenames must remain contiguous before batch recovery")

    base_paths = existing_paths[:BASE_COUNT]
    existing_notes = [
        json.loads(path.read_text(encoding="utf-8-sig")) for path in base_paths
    ]
    expected_batch = build_batch(existing_notes)

    if len(existing_paths) == target_count:
        actual_batch = [
            json.loads(path.read_text(encoding="utf-8-sig"))
            for path in existing_paths[BASE_COUNT:]
        ]
        mismatches = batch_mismatches(expected_batch, actual_batch)
        if mismatches:
            preview = ", ".join(mismatches[:5])
            raise RuntimeError(f"existing 2026-08-06 batch differs from generator: {preview}")
        print(f"batch already exists and fully verified: {BATCH_COUNT} notes")
        return

    partial_paths = existing_paths[BASE_COUNT:]
    for path in partial_paths:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not str(data.get("id", "")).startswith("20260806_leehu_literature_"):
            raise RuntimeError(f"refusing to remove unrelated partial file: {path.name}")
    for path in partial_paths:
        path.unlink()

    for offset, data in enumerate(expected_batch, 1):
        path = CONTENT_DIR / f"{BASE_COUNT + offset:03d}.json"
        if path.exists():
            raise RuntimeError(f"refusing to overwrite {path.name}")
        write_json_atomic(path, data)
    print(
        f"appended {len(expected_batch)} notes: "
        f"{BASE_COUNT + 1:03d}.json–{BASE_COUNT + len(expected_batch):03d}.json"
    )


if __name__ == "__main__":
    generate()
