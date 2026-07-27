#!/usr/bin/env python3
"""Reproducibly curate 365 literature notes from public-domain source texts.

The script downloads plain-text Project Gutenberg editions with urllib, selects
short complete sentences deterministically, and writes the source JSON consumed
by build_literature.py. No translated Korean source text is stored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
CACHE_DIR = ROOT / ".literature-source-cache"
BATCH_PUBLISHED_AT = "2026-07-27T12:00:00+09:00"
TOTAL_NOTES = 365


@dataclass(frozen=True)
class Source:
    gutenberg_id: int
    author: str
    work: str
    short: str

    @property
    def url(self) -> str:
        return (
            f"https://www.gutenberg.org/cache/epub/{self.gutenberg_id}/"
            f"pg{self.gutenberg_id}.txt"
        )


SOURCES = (
    Source(1342, "Jane Austen", "Pride and Prejudice", "austen"),
    Source(84, "Mary Wollstonecraft Shelley", "Frankenstein", "shelley"),
    Source(1661, "Arthur Conan Doyle", "The Adventures of Sherlock Holmes", "doyle"),
    Source(11, "Lewis Carroll", "Alice's Adventures in Wonderland", "carroll"),
    Source(2701, "Herman Melville", "Moby-Dick", "melville"),
    Source(98, "Charles Dickens", "A Tale of Two Cities", "dickens"),
    Source(74, "Mark Twain", "The Adventures of Tom Sawyer", "twain"),
    Source(345, "Bram Stoker", "Dracula", "stoker"),
    Source(1260, "Charlotte Brontë", "Jane Eyre", "charlotte-bronte"),
    Source(768, "Emily Brontë", "Wuthering Heights", "emily-bronte"),
    Source(43, "Robert Louis Stevenson", "Strange Case of Dr Jekyll and Mr Hyde", "stevenson"),
    Source(174, "Oscar Wilde", "The Picture of Dorian Gray", "wilde"),
    Source(219, "Joseph Conrad", "Heart of Darkness", "conrad"),
    Source(521, "Daniel Defoe", "Robinson Crusoe", "defoe"),
    Source(35, "H. G. Wells", "The Time Machine", "wells"),
    Source(55, "L. Frank Baum", "The Wonderful Wizard of Oz", "baum"),
    Source(1952, "Charlotte Perkins Gilman", "The Yellow Wallpaper", "gilman"),
    Source(514, "Louisa May Alcott", "Little Women", "alcott"),
    Source(23, "Frederick Douglass", "Narrative of the Life of Frederick Douglass", "douglass"),
    Source(45, "L. M. Montgomery", "Anne of Green Gables", "montgomery"),
    Source(289, "Kenneth Grahame", "The Wind in the Willows", "grahame"),
    Source(113, "Frances Hodgson Burnett", "The Secret Garden", "burnett"),
    Source(145, "George Eliot", "Middlemarch", "eliot"),
    Source(209, "Henry James", "The Turn of the Screw", "james"),
    Source(215, "Jack London", "The Call of the Wild", "london"),
    Source(236, "Rudyard Kipling", "The Jungle Book", "kipling"),
    Source(33, "Nathaniel Hawthorne", "The Scarlet Letter", "hawthorne"),
    Source(829, "Jonathan Swift", "Gulliver's Travels", "swift"),
    Source(160, "Kate Chopin", "The Awakening", "chopin"),
    Source(308, "Jerome K. Jerome", "Three Men in a Boat", "jerome"),
)

THEMES = (
    ("기억", "memory", ("memory", "remember", "forgot", "past")),
    ("사랑", "love", ("love", "heart", "affection", "beloved")),
    ("자유", "freedom", ("free", "liberty", "escape", "prison")),
    ("시간", "time", ("time", "hour", "day", "night", "years")),
    ("선택", "choice", ("choose", "choice", "decide", "will")),
    ("두려움", "fear", ("fear", "afraid", "terror", "dread")),
    ("관계", "relation", ("friend", "family", "mother", "father", "companion")),
    ("자연", "nature", ("sea", "wind", "garden", "earth", "sky", "tree")),
    ("정체성", "identity", ("self", "soul", "name", "face", "man", "woman")),
    ("진실", "truth", ("truth", "know", "secret", "real")),
    ("용기", "courage", ("courage", "brave", "fight", "strong")),
    ("고독", "solitude", ("alone", "lonely", "silence", "solitary")),
    ("욕망", "desire", ("want", "wish", "desire", "hope")),
    ("책임", "responsibility", ("duty", "must", "ought", "responsible")),
    ("변화", "change", ("change", "become", "new", "different")),
)

RELATED_WORKS = (
    ("연", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756"),
    ("데자뷔", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772"),
    ("소나기", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780"),
    ("어느 날 문득", "https://store.kyobobook.co.kr/person/detail/1000809404"),
    ("환상", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769"),
    ("별이 빛나는 밤에", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770"),
    ("처음처럼", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377771"),
    ("Fantasy", "https://product.kyobobook.co.kr/detail/S000214458787"),
)

TITLE_FORMS = (
    "{work}에서 발견한 {theme}의 방향",
    "{anchor} 뒤에 남는 {theme}의 질문",
    "{theme}은 어디에서 시작되는가",
    "{work}의 한 문장, {theme}의 두 얼굴",
    "{anchor}라는 말과 {theme}의 거리",
    "{theme}을 다시 읽게 하는 문장",
    "{author}가 비춘 {theme}의 가장자리",
    "{work} 속 {theme}의 작은 전환",
    "{anchor} 앞에서 멈춰 선 까닭",
    "{theme}을 견디는 문장의 방식",
    "{author}의 문장으로 생각한 {theme}",
    "{work}가 건네는 {theme}의 단서",
    "{anchor}에서 시작된 오래된 물음",
    "{theme}의 표정을 바꾸는 한 문장",
    "{work}와 함께 걷는 {theme}의 길",
)

OPENINGS = (
    "『{work}』의 이 문장은 ‘{anchor}’라는 낱말을 중심에 두고 {theme}의 결을 천천히 드러냅니다.",
    "‘{anchor}’가 놓인 순간, 『{work}』의 장면은 사건보다 {theme}에 관한 질문으로 가까워집니다.",
    "{author}의 문장 가운데 이 대목은 {theme}을 설명하지 않고 독자가 직접 헤아리게 합니다.",
    "『{work}』에서 만난 ‘{anchor}’는 익숙한 {theme}을 낯선 각도에서 바라보게 합니다.",
    "이 문장의 힘은 ‘{anchor}’를 말하면서도 {theme}의 답을 쉽게 닫지 않는 데 있습니다.",
    "{author}는 이 짧은 문장 안에서 {theme}이 움직이는 순간을 조용히 붙잡습니다.",
    "처음에는 ‘{anchor}’가 눈에 들어오지만, 다시 읽으면 그 뒤의 {theme}이 더 오래 남습니다.",
    "『{work}』의 이 구절은 {theme}이 관념이 아니라 한 사람의 구체적인 감각임을 보여 줍니다.",
)

ARGUMENTS = (
    "사람은 대개 결론을 먼저 찾지만, 문학은 결론에 이르기 전 마음이 흔들리는 시간을 보여 줍니다.",
    "겉으로 드러난 행동만 보면 단순해 보이지만, 그 행동을 낳은 내면에는 서로 다른 이유가 겹쳐 있습니다.",
    "한 인물의 판단은 옳고 그름만으로 정리되지 않으며, 무엇을 잃을까 두려워했는지까지 살필 때 선명해집니다.",
    "문장이 남기는 여백은 독자에게 해석의 권한을 돌려주고, 그 권한은 읽는 사람의 경험에 따라 달라집니다.",
    "여기서 중요한 것은 감정의 크기보다 감정을 대하는 태도이며, 태도는 결국 삶의 방향을 만듭니다.",
    "말해진 내용과 말해지지 않은 사정 사이의 틈이 넓을수록 인물의 진심은 오히려 더 또렷해집니다.",
    "우리가 타인을 이해한다고 믿는 순간에도 이해되지 않은 부분은 남고, 그 나머지가 관계의 윤리를 요구합니다.",
    "과거의 장면은 그대로 돌아오지 않지만, 현재의 선택을 바꾸는 방식으로 계속 살아 움직입니다.",
    "문학 속 갈등은 승패를 가르는 문제가 아니라 서로 양립하기 어려운 가치가 부딪치는 자리로 읽을 수 있습니다.",
    "작은 표현 하나가 장면 전체의 온도를 바꾸듯, 삶에서도 사소한 말이 오래된 생각의 방향을 틀곤 합니다.",
    "인물은 완성된 답을 가진 존재가 아니라 망설임 속에서 스스로를 만들어 가는 존재로 보입니다.",
    "이 대목을 개인의 감정에만 가두지 않으면, 시대와 공동체가 한 사람에게 요구한 몫도 함께 보입니다.",
)

COUNTERPOINTS = (
    "다만 아름다운 문장이라는 이유로 인물의 선택까지 미화해서는 안 되며, 결과를 감당한 사람들의 자리도 보아야 합니다.",
    "그렇다고 모든 망설임을 깊이라고 부를 수는 없고, 때로는 결정하지 않는 태도 역시 하나의 결정이 됩니다.",
    "반대로 독자의 경험을 작품에 너무 빠르게 겹치면 원문의 낯섦이 사라질 수 있으므로 장면 자체의 목소리도 지켜야 합니다.",
    "그러나 공감은 동의와 다르며, 인물을 이해하는 일은 그의 행동을 면책하는 일과 구분되어야 합니다.",
    "한편 이 문장을 보편적인 교훈으로만 읽으면 작품이 품은 시대적 조건과 구체적인 갈등을 놓치기 쉽습니다.",
    "그럼에도 해석을 하나로 고정하지 않을 때, 서로 다른 독자가 같은 문장 앞에서 대화를 시작할 수 있습니다.",
    "다른 각도에서 보면 이 대목의 침묵은 평온이 아니라 말할 권리를 얻지 못한 상태일 수도 있습니다.",
    "하지만 감정의 진실성이 언제나 사실의 정확성을 보장하지는 않는다는 점도 함께 기억해야 합니다.",
    "이 장면을 운명으로만 부르면 인물의 책임이 흐려지고, 의지로만 부르면 그를 둘러싼 조건이 지워집니다.",
    "따라서 문장의 빛나는 부분뿐 아니라 그 빛이 만들고 있는 그림자도 같은 무게로 읽을 필요가 있습니다.",
)

APPLICATIONS = (
    "오늘의 독자는 이 질문을 빠른 판단을 요구하는 화면 밖으로 가져와, 한 번 더 듣고 늦게 대답하는 연습으로 바꿀 수 있습니다.",
    "글을 쓰는 사람에게 이 대목은 인물을 설명하기보다 행동과 침묵을 배치해 독자가 발견하도록 하라는 조언이 됩니다.",
    "일상의 관계에서도 상대의 한마디를 성격 전체로 확대하지 않고, 그 말이 나온 맥락을 묻는 태도가 필요합니다.",
    "기억을 기록할 때에는 사실을 붙드는 일과 그때의 감정을 인정하는 일을 분리해야 더 정직한 문장에 가까워집니다.",
    "공동체의 문제로 옮겨 보면, 개인의 용기만 요구하기 전에 안전하게 말할 수 있는 조건부터 마련해야 한다는 뜻이 됩니다.",
    "창작에서는 바로 이 모순을 없애기보다 끝까지 유지할 때, 인물이 예측 가능한 표어를 넘어 살아 있는 존재가 됩니다.",
    "지금 내린 판단이 누구의 목소리를 크게 하고 누구를 보이지 않게 하는지 점검하는 질문으로 이 문장을 이어 읽어 봅니다.",
    "속도를 늦추어 원문을 다시 소리 내 읽으면, 처음에는 지나쳤던 리듬과 시선의 이동이 새로운 의미를 열어 줍니다.",
    "이 문장은 답을 외우게 하기보다 자신의 경험에서 비슷한 장면을 찾아 그때와 다른 선택을 상상하게 합니다.",
    "결국 독서는 오래된 문장을 현재의 책임으로 번역하는 일이며, 그 번역은 각자의 행동에서 비로소 완성됩니다.",
)

OBSERVATIONS = (
    "“{fragment}”의 어순을 따라가면 ‘{second}’가 앞선 ‘{anchor}’를 단순히 반복하지 않고 장면의 무게를 옮기는 것이 보입니다.",
    "이 구절에서 ‘{anchor}’와 ‘{second}’ 사이에 놓인 말들은 인물의 감정이 한 방향으로만 흐르지 않는다는 증거가 됩니다.",
    "특히 “{fragment}”라는 호흡은 독자를 잠시 멈추게 하고, ‘{second}’에 이르러 처음의 인상을 고쳐 읽게 합니다.",
    "‘{anchor}’를 중심으로 읽을 때와 ‘{second}’를 중심으로 읽을 때 장면의 주인이 달라진다는 점이 이 문장의 흥미로운 부분입니다.",
    "“{fragment}”에는 설명보다 움직임이 먼저 나오며, 그 움직임이 ‘{anchor}’에서 ‘{second}’로 시선을 데려갑니다.",
    "이 문장은 ‘{anchor}’를 크게 외치지 않지만 ‘{second}’와 나란히 놓음으로써 두 말 사이의 긴장을 오래 유지합니다.",
    "인용문의 앞부분은 ‘{anchor}’를 향해 열리고 뒷부분은 ‘{second}’에서 멈추므로, 문장의 구조 자체가 해석의 순서를 제안합니다.",
    "“{fragment}”를 소리 내 읽으면 ‘{anchor}’ 뒤의 리듬이 달라지고, 그 변화가 ‘{second}’에 새로운 표정을 부여합니다.",
    "‘{anchor}’와 ‘{second}’를 따로 떼어 보면 평범한 말이지만, 이 문장 안에서는 서로를 비추며 감정의 깊이를 만듭니다.",
    "이 대목은 ‘{anchor}’에서 기대를 세운 뒤 ‘{second}’에서 그것을 비틀어, 독자가 인물을 한 번 더 살피게 합니다.",
    "“{fragment}”라는 배열에는 원인과 결과가 깔끔히 나뉘지 않으며, ‘{anchor}’와 ‘{second}’가 그 모호함을 함께 떠받칩니다.",
    "문장 끝까지 따라가야 ‘{anchor}’의 뜻이 정해지는 까닭은 ‘{second}’가 앞선 장면에 다른 맥락을 보태기 때문입니다.",
)

CLOSINGS = (
    "그래서 이번 기록에는 ‘{anchor}’를 정답이 아니라 {theme}을 다시 묻는 표시로 남겨 둡니다.",
    "오늘은 ‘{anchor}’가 만든 여백을 따라가며 {theme}에 대한 내 판단을 조금 늦춰 봅니다.",
    "이 문장을 덮은 뒤에도 ‘{anchor}’와 {theme} 사이의 긴장은 다음 장면을 바라보는 기준으로 남습니다.",
    "마지막에는 ‘{anchor}’가 가리킨 {theme}을 내 삶의 구체적인 선택 하나와 연결해 보고 싶습니다.",
    "그리하여 ‘{anchor}’를 둘러싼 질문은 책 속에 머물지 않고 {theme}을 대하는 오늘의 태도로 이어집니다.",
    "이번 노트의 끝에는 ‘{anchor}’를 기억하며 {theme} 앞에서 서두르지 않겠다는 다짐을 적습니다.",
    "다 읽고 나면 ‘{anchor}’보다 더 크게 들리는 것은 {theme}을 외면하지 말라는 문장의 낮은 목소리입니다.",
    "결국 ‘{anchor}’는 {theme}의 결론이 아니라 더 정직한 질문으로 들어가는 작은 문이 됩니다.",
)


def download(source: Source, refresh: bool) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"pg{source.gutenberg_id}.txt"
    if refresh or not cache_path.exists():
        request = urllib.request.Request(
            source.url,
            headers={"User-Agent": "LeehuLiteratureCurator/1.0 (+https://xn--hu5b23z.com/)"},
        )
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        cache_path.write_bytes(data)
    return cache_path.read_text(encoding="utf-8-sig", errors="replace")


def body_only(text: str) -> str:
    start = re.search(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I)
    end = re.search(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK.*?\*\*\*", text, re.I)
    left = start.end() if start else 0
    right = end.start() if end else len(text)
    return text[left:right]


def sentence_candidates(text: str) -> list[tuple[str, int]]:
    candidates: list[tuple[str, int]] = []
    line_number = 1
    for paragraph in re.split(r"\n\s*\n", body_only(text)):
        paragraph_line = line_number
        line_number += paragraph.count("\n") + 2
        clean = re.sub(r"\s+", " ", paragraph).strip()
        if not clean or clean.isupper() or clean.startswith(("CHAPTER ", "Chapter ")):
            continue
        for sentence in re.split(
            r"(?:(?<=[.!?])|(?<=[.!?][\"'”’)]))\s+(?=[\"'“‘(]*[A-Z])",
            clean,
        ):
            quote = sentence.strip(" \t\r\n")
            if not 85 <= len(quote) <= 230:
                continue
            if quote.count(".") + quote.count("!") + quote.count("?") > 2:
                continue
            if re.search(r"\b(illustration|chapter|project gutenberg|http|www\.)\b", quote, re.I):
                continue
            if any(ch in quote for ch in ("_", "[", "]", "{", "}")):
                continue
            if quote.count("“") != quote.count("”"):
                continue
            if quote.count('"') % 2:
                continue
            if sum(ch.isalpha() for ch in quote) < 60:
                continue
            candidates.append((quote, paragraph_line))
    return candidates


def choose_quotes(source: Source, text: str, count: int) -> list[tuple[str, int]]:
    ranked = sorted(
        sentence_candidates(text),
        key=lambda item: hashlib.sha256(
            f"{source.gutenberg_id}:{item[0]}".encode("utf-8")
        ).hexdigest(),
    )
    selected: list[tuple[str, int]] = []
    seen: set[str] = set()
    for quote, line in ranked:
        normalized = re.sub(r"\W+", "", quote).casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        selected.append((quote, line))
        if len(selected) == count:
            return selected
    raise RuntimeError(f"not enough usable sentences in {source.work}: {len(selected)}/{count}")


def theme_for(quote: str, index: int) -> tuple[str, str]:
    lowered = quote.casefold()
    scored = [
        (sum(lowered.count(word) for word in words), position, ko, en)
        for position, (ko, en, words) in enumerate(THEMES)
    ]
    best = max(scored)
    if best[0] == 0:
        return THEMES[index % len(THEMES)][:2]
    return best[2], best[3]


def anchors_for(quote: str, index: int) -> tuple[str, str]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", quote)
    stop = {
        "that", "this", "with", "from", "have", "were", "which", "there",
        "their", "would", "could", "should", "about", "when", "what", "been",
        "into", "upon", "they", "them", "then", "than", "only", "more",
    }
    useful = [word for word in words if word.casefold() not in stop]
    pool = useful if useful else words
    first = pool[index % len(pool)].lower()
    second = pool[(index * 7 + 3) % len(pool)].lower()
    if second == first and len(pool) > 1:
        second = pool[(index + 1) % len(pool)].lower()
    return first, second


def commentary_for(
    source: Source,
    quote: str,
    index: int,
    theme: str,
    anchor: str,
    second_anchor: str,
    title: str,
) -> str:
    selector = int(hashlib.sha256(quote.encode("utf-8")).hexdigest(), 16)
    values = {
        "work": source.work,
        "author": source.author,
        "theme": theme,
        "anchor": anchor,
    }
    # Keep the embedded source fragment within one Korean commentary sentence.
    quoted_fragment = re.sub(
        r"[.!?]+", "", re.sub(r"\s+", " ", quote)
    ).strip(" \t\r\n“”\"'")[:58].rstrip(" ,;:")
    unique_observation = OBSERVATIONS[
        (selector >> 16) % len(OBSERVATIONS)
    ].format(fragment=quoted_fragment, second=second_anchor, anchor=anchor)
    opening = (
        f"“{quoted_fragment}”의 흐름을 따라가며 "
        f"‘{second_anchor}’를 먼저 표시해 둡니다. "
        + OPENINGS[selector % len(OPENINGS)].format(**values)
    )
    sentences = (
        opening,
        ARGUMENTS[(selector >> 8) % len(ARGUMENTS)],
        unique_observation,
        COUNTERPOINTS[(selector >> 24) % len(COUNTERPOINTS)],
        APPLICATIONS[(selector >> 32) % len(APPLICATIONS)],
        CLOSINGS[(selector >> 40) % len(CLOSINGS)].format(**values)
        + f" ‘{title}’에서 시작한 생각은 ‘{second_anchor}’의 여운 덕분에 한 방향으로 닫히지 않습니다.",
    )
    return " ".join(sentences)


def note(source: Source, quote: str, line: int, index: int) -> dict[str, object]:
    theme, theme_en = theme_for(quote, index)
    anchor, second_anchor = anchors_for(quote, index)
    base_title = TITLE_FORMS[index % len(TITLE_FORMS)].format(
        work=source.work,
        author=source.author,
        theme=theme,
        anchor=anchor,
    )
    title = f"{base_title} — {anchor}에서 {second_anchor}까지"
    slug_anchor = re.sub(r"[^a-z0-9]+", "-", anchor.casefold()).strip("-") or "word"
    slug = f"{source.short}-{theme_en}-{slug_anchor[:24]}"
    related_name, related_url = RELATED_WORKS[(index + source.gutenberg_id) % len(RELATED_WORKS)]
    secondary_theme = THEMES[(index * 7) % len(THEMES)][0]
    if secondary_theme == theme:
        secondary_theme = THEMES[(index * 7 + 1) % len(THEMES)][0]
    return {
        "id": f"20260727_leehu_literature_{index:03d}",
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
        "translation_note": "영어 원문 인용. 현대 한국어 번역문을 저장하거나 전재하지 않음.",
        "rights_note": (
            "Project Gutenberg가 미국에서 퍼블릭 도메인으로 배포하는 영어 원전. "
            "저자 사후 70년이 지난 작품만 선별함."
        ),
        "commentary": commentary_for(
            source, quote, index, theme, anchor, second_anchor, title
        ),
        "closing": "소설가 이후 드림",
        "author": "소설가 이후",
        "tags": [theme, secondary_theme, source.author],
        "related_work": {"name": related_name, "url": related_url},
        "published_at": BATCH_PUBLISHED_AT,
    }


def verify_quote(note_data: dict[str, object], source_text: str) -> None:
    quote = str(note_data["quote"])
    normalized_text = re.sub(r"\s+", " ", body_only(source_text))
    if quote not in normalized_text:
        raise RuntimeError(f"quote not found in source: {note_data['id']}")


def generate(refresh: bool = False) -> None:
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    texts = {source: download(source, refresh) for source in SOURCES}
    notes: list[dict[str, object]] = []
    index = 1
    for source_position, source in enumerate(SOURCES):
        count = 13 if source_position < 5 else 12
        for quote, line in choose_quotes(source, texts[source], count):
            data = note(source, quote, line, index)
            verify_quote(data, texts[source])
            notes.append(data)
            index += 1
    if len(notes) != TOTAL_NOTES:
        raise RuntimeError(f"expected {TOTAL_NOTES} notes, got {len(notes)}")
    for old_path in CONTENT_DIR.glob("*.json"):
        old_path.unlink()
    for position, data in enumerate(notes, 1):
        path = CONTENT_DIR / f"{position:03d}.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"curated {len(notes)} verified notes from {len(SOURCES)} public-domain works")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="redownload source texts")
    args = parser.parse_args()
    generate(refresh=args.refresh)


if __name__ == "__main__":
    main()
