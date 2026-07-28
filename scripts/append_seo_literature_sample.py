#!/usr/bin/env python3
"""Create one structured SEO literature-note sample based on a verified public source."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "content" / "literature" / "1466.json"

note = {
    "id": "20260728_leehu_literature_301",
    "slug": "gibran-prophet-love-spaces",
    "title": "함께하되 서로의 여백을 지키는 사랑 — Kahlil Gibran의 『예언자』",
    "quote": "You were born together, and together you shall be forevermore. You shall be together when the white wings of death scatter your days.",
    "source_author": "Kahlil Gibran",
    "source_work": "The Prophet",
    "source_location": "Marriage section, Project Gutenberg eBook #58585",
    "source_language": "en",
    "source_url": "https://www.gutenberg.org/cache/epub/58585/pg58585.txt",
    "translation_note": "Project Gutenberg 제공 영어 텍스트의 직접 인용. 현대 한국어 번역문을 저장하거나 전재하지 않음.",
    "rights_note": "Project Gutenberg에서 copyright: false로 제공되는 영어 텍스트를 직접 확인한 문장. 이용 전 관할지별 이용 조건 확인 필요.",
    "commentary": "이 문장은 사랑을 두 사람이 하나가 되는 상태가 아니라, 함께 시간을 지나가는 약속으로 바라보게 합니다. 함께함은 서로의 삶을 대신 결정하는 권리가 아니라, 흔들리는 순간에도 곁을 지키려는 책임에 가깝습니다. 그래서 사랑에는 가까워지는 용기와 함께 상대의 고유한 시간을 침범하지 않는 절제가 필요합니다. 오늘의 관계는 즉각적인 확인을 요구하기 쉽지만, 신뢰는 상대의 침묵과 선택을 견딜 때 더 단단해질 수 있습니다. 이 문학노트는 사랑을 붙드는 말보다 서로의 여백을 존중하는 태도를 먼저 묻습니다.",
    "closing": "소설가 이후 드림",
    "author": "소설가 이후",
    "tags": ["사랑", "관계", "Kahlil Gibran"],
    "related_work": {"name": "연", "url": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756"},
    "published_at": "2026-07-28T12:00:00+09:00",
    "content_kind": "source_quote",
    "seo_sections": {
        "work_introduction": "『예언자(The Prophet)』는 레바논계 미국 시인 Kahlil Gibran이 1923년에 발표한 산문시집으로, 한 인물이 떠나기 전 여러 삶의 주제에 답하는 형식으로 구성된 작품이다. 그 가운데 ‘Marriage’ 장은 사랑, 관계, 책임, 함께함과 거리의 문제를 생각하게 하는 대목이다.",
        "why_read_now": "관계가 빠른 확신과 즉각적인 응답을 요구하는 시대일수록, 함께하되 서로의 삶을 지우지 않는 사랑의 방식은 여전히 유효하다. 이 작품은 사랑을 소유나 동의어로 축소하지 않고, 각자의 자유를 지키는 책임으로 다시 생각하게 한다.",
        "personal_reflection": "나는 이 문장을 읽으며 가까운 사이라도 상대의 시간을 내 기준으로 재단하지 않는 일이 중요하다고 느꼈다. 사랑은 모든 거리를 없애는 일이 아니라, 필요한 순간에 서로가 숨 쉴 자리를 남기는 약속일 수 있다.",
        "meaning_today": "오늘 우리에게 이 문장은 관계의 불안을 통제로 해결하려는 습관을 멈추게 한다. 함께 걷되 서로의 방향을 존중할 때, 사랑은 더 오래 지속될 수 있다는 의미를 남긴다."
    }
}

if __name__ == "__main__":
    TARGET.write_text(json.dumps(note, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(TARGET)
