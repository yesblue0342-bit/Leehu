#!/usr/bin/env python3
"""소설가 이후 작품 5편의 고유 문학노트 500건 manifest 생성기."""
from pathlib import Path

import append_leehu_reflections_20260903_1000 as base

ROOT = Path(__file__).resolve().parents[1]
base.MANIFEST = ROOT / "content" / "leehu-works-20260905-500.json"
base.BATCH_DATE = "20260905"
base.EXPECTED_BEFORE = 4631
base.TARGET_COUNT = 500
base.START_SEQUENCE = 2261
base.PUBLISHED_AT = "2026-09-05T00:05:00+09:00"
TARGET_BY_SLUG = {"love": 194, "deja-vu": 82, "rain-shower": 60, "fantasy": 82, "starry-night": 82}
base.TARGET_BY_WORK = {work.name: TARGET_BY_SLUG[work.slug] for work in base.WORKS}

base.SETTINGS = (
    ("첫차가 떠난 버스 차고지", "after-first-bus-depot"),
    ("눈 내린 골목 끝", "snowy-alley-end"),
    ("해 질 무렵 방파제", "sunset-breakwater"),
    ("비어 있는 기차 승강장", "empty-rail-platform"),
    ("오래된 시장의 뒷길", "old-market-backstreet"),
    ("창가가 넓은 작은 카페", "wide-window-cafe"),
    ("불 꺼진 체육관", "dark-gymnasium"),
    ("서늘한 지하 통로", "cool-underground-passage"),
    ("강 건너 불빛이 보이는 다리", "bridge-over-river-lights"),
    ("비 오는 박물관 뜰", "rainy-museum-courtyard"),
    ("첫눈 뒤 산책길", "walk-after-first-snow"),
    ("늦은 밤 편의점 앞", "late-night-storefront"),
    ("파도 잦아든 포구", "calm-wave-harbor"),
    ("종소리 멎은 성당 앞", "quiet-cathedral-square"),
    ("가을 끝 은행나무길", "late-autumn-ginkgo-road"),
    ("새 책 냄새가 남은 서가", "new-book-shelf"),
    ("도시 외곽의 작은 호수", "small-suburban-lake"),
    ("안개 낀 새벽 골목", "foggy-dawn-alley"),
    ("해 뜨기 전 공항 대합실", "airport-before-sunrise"),
    ("저녁바람 부는 학교 운동장", "windy-schoolyard-evening"),
)

base.DETAILS = {
    "연(戀)": (
        ("오래 접어 둔 편지", "long-folded-letter"),
        ("서로 다른 시각을 가리키는 두 시계", "two-clocks-different-times"),
        ("비워 둔 창가 자리", "empty-window-seat"),
        ("반쯤 식은 국 한 그릇", "half-cooled-bowl"),
        ("문턱 앞에 놓인 신발 한 켤레", "shoes-by-threshold"),
        ("약속을 표시한 빈 달력", "empty-calendar-with-promise"),
        ("서로 다른 방향으로 놓인 두 잔", "two-cups-facing-away"),
        ("돌려주지 못한 작은 열쇠", "small-unreturned-key"),
        ("한쪽만 켜진 현관등", "single-porch-light"),
        ("답장을 기다리는 우편함", "mailbox-waiting-reply"),
    ),
    "데자뷔": (
        ("낯익은 필체의 새 엽서", "new-postcard-familiar-hand"),
        ("한 번 더 울린 현관종", "doorbell-ringing-again"),
        ("순서가 바뀐 가족사진", "reordered-family-photo"),
        ("처음 걷는데 기억나는 모퉁이", "remembered-unknown-corner"),
        ("두 겹으로 찍힌 오래된 사진", "double-exposed-old-photo"),
    ),
    "소나기": (
        ("빗소리 멎은 처마", "quiet-eaves-after-rain"),
        ("젖은 가방 속 마른 종이", "dry-paper-in-wet-bag"),
        ("물기 남은 버스 창문", "wet-bus-window"),
        ("구름 밖으로 나온 낮은 햇빛", "low-sun-after-clouds"),
        ("빗물 따라 흐른 낙엽", "leaf-carried-by-rain"),
    ),
    "환상": (
        ("밤마다 위치가 달라지는 문", "door-moving-each-night"),
        ("목소리를 간직한 빈 상자", "empty-box-holding-voice"),
        ("달빛 아래 떠오른 투명한 계단", "clear-stairs-in-moonlight"),
        ("계절을 건너는 작은 창", "window-across-seasons"),
        ("이름 없는 지도가 펼쳐진 탁자", "nameless-map-on-table"),
    ),
    "별이 빛나는 밤에": (
        ("구름 사이 작은 별무리", "small-stars-between-clouds"),
        ("멀리 깜박이는 항구 불빛", "distant-harbor-light"),
        ("새벽 하늘에 남은 초승달", "crescent-before-dawn"),
        ("옥상 난간에 걸린 바람", "wind-on-rooftop-rail"),
        ("밤이 깊어질수록 선명한 북쪽 하늘", "clear-northern-night"),
    ),
}


def main() -> None:
    base.main()


if __name__ == "__main__":
    main()
