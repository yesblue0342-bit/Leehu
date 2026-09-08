#!/usr/bin/env python3
"""Append the 2026-09-08 batch through the established literature pipeline."""
from pathlib import Path
import append_leehu_reflections_20260903_1000 as base

ROOT = Path(__file__).resolve().parents[1]
base.MANIFEST = ROOT / "content" / "leehu-works-20260908-1000.json"
base.BATCH_DATE = "20260908"
base.EXPECTED_BEFORE = 5131
base.TARGET_COUNT = 1000
base.START_SEQUENCE = 2761
base.PUBLISHED_AT = "2026-09-08T12:50:00+09:00"

base.SETTINGS = (
    ("가을비가 지나간 책방 테라스", "autumn-bookshop-terrace"),
    ("첫 햇살이 닿은 동네 빵집", "morning-neighborhood-bakery"),
    ("저녁 무렵 강가의 자전거 쉼터", "evening-river-cycle-stop"),
    ("문을 열기 전 작은 사진관", "photo-studio-before-opening"),
    ("기차 소리가 멀어진 건널목", "crossing-after-train"),
    ("가을 볕이 머문 마을회관", "autumn-village-hall"),
    ("점심시간이 지난 옥상 정원", "rooftop-garden-after-lunch"),
    ("커튼을 걷은 오래된 음악실", "old-music-room-open-curtains"),
    ("바닷바람이 스치는 버스 종점", "sea-breeze-bus-terminal"),
    ("수확이 끝난 과수원 입구", "orchard-after-harvest"),
    ("불을 켜기 전 동네 수선집", "repair-shop-before-lights"),
    ("책을 반납한 뒤의 도서관 현관", "library-return-entrance"),
    ("오후 햇빛이 비친 지하 서점", "sunlit-basement-bookshop"),
    ("여름이 지난 해수욕장 탈의실", "seaside-changing-room-offseason"),
    ("가을 운동회가 끝난 학교 복도", "school-corridor-after-field-day"),
    ("야간 근무를 마친 휴게실", "break-room-after-night-shift"),
    ("마지막 손님이 떠난 식당 창가", "restaurant-window-after-guests"),
    ("첫 낙엽이 쌓인 돌계단", "stone-stairs-first-leaves"),
    ("이른 아침 마을 공동 빨래터", "early-village-wash-place"),
    ("늦은 오후 등산로 안내소", "late-trail-information-hut"),
    ("비를 피해 들어선 공방 처마", "workshop-eaves-in-rain"),
    ("공연 준비가 끝난 빈 연습실", "rehearsal-room-after-preparation"),
    ("물안개가 걷힌 작은 저수지", "small-reservoir-after-mist"),
    ("문 닫는 시간이 다가온 기록관", "archive-near-closing"),
    ("낮과 밤이 교차하는 나루터", "ferry-landing-at-dusk"),
)

base.DETAILS = {
    "연(戀)": (
        ("따로 접어 놓은 두 장의 손수건", "two-separately-folded-handkerchiefs"),
        ("날짜를 고쳐 쓴 작은 약속장", "promise-book-corrected-date"),
        ("손잡이의 온도가 다른 두 찻잔", "two-cups-different-warmth"),
        ("절반만 채운 여행 준비 목록", "half-filled-travel-list"),
        ("서로의 이름이 적힌 책갈피", "bookmarks-with-two-names"),
        ("나란히 놓되 맞닿지 않은 장갑", "gloves-side-by-side"),
        ("한 줄을 비워 둔 안부 카드", "greeting-card-empty-line"),
        ("기다리는 동안 풀어 놓은 목도리", "scarf-unwrapped-while-waiting"),
    ),
    "데자뷔": (
        ("기억보다 낮게 걸린 액자", "frame-lower-than-remembered"),
        ("어제와 다른 잉크의 같은 주소", "same-address-different-ink"),
        ("두 번 접힌 접수증 모서리", "twice-folded-receipt-corner"),
        ("처음 들었는데 익숙한 종소리", "unfamiliar-familiar-bell"),
        ("지워진 길이 남은 손그림 지도", "hand-map-erased-road"),
        ("연도를 가린 기념사진 한 장", "anniversary-photo-hidden-year"),
        ("다른 책에서 발견한 같은 얼룩", "same-stain-another-book"),
        ("순서를 다시 매긴 일기 묶음", "renumbered-diary-bundle"),
    ),
    "소나기": (
        ("빛을 통과시키는 젖은 나뭇잎", "wet-leaf-transmitting-light"),
        ("바람에 조금씩 마르는 천 가방", "cloth-bag-drying-in-wind"),
        ("물기를 털어 낸 접이식 의자", "folding-chair-shaken-dry"),
        ("빗방울 자국이 남은 유리문", "glass-door-with-raindrop-marks"),
        ("흙탕물이 가라앉은 작은 화분", "small-pot-settled-mud"),
        ("비를 건너온 종이봉투의 주름", "rain-traveled-paper-bag"),
        ("한쪽부터 마르기 시작한 돗자리", "mat-drying-from-one-side"),
        ("물웅덩이를 비켜 놓은 징검돌", "stepping-stone-beside-puddle"),
    ),
    "환상": (
        ("아직 쓰지 않은 계절의 달력", "calendar-unwritten-season"),
        ("발자국을 기억하는 푸른 바닥", "blue-floor-remembering-footsteps"),
        ("문을 열 때마다 색이 바뀌는 손잡이", "color-changing-door-handle"),
        ("바람의 이름을 모은 작은 수첩", "notebook-of-wind-names"),
        ("지평선을 접어 넣은 종이 상자", "paper-box-folded-horizon"),
        ("잊은 목소리만 들리는 조개껍데기", "shell-of-forgotten-voices"),
        ("발신인이 내일로 적힌 우편물", "mail-from-tomorrow"),
        ("그늘의 길이를 재는 투명한 자", "clear-ruler-measuring-shade"),
    ),
    "별이 빛나는 밤에": (
        ("불을 낮춘 뒤 드러난 먼 능선", "distant-ridge-after-dimming"),
        ("천천히 움직이는 관측창의 별", "star-in-observation-window"),
        ("달빛이 반쯤 닿은 나무 난간", "wooden-rail-half-moonlit"),
        ("잠든 마을 위로 이어진 전깃줄", "wires-over-sleeping-village"),
        ("늦은 안부를 적어 둔 메모지", "note-with-late-greeting"),
        ("새벽바람에 한 장 넘어간 시집", "poetry-page-turned-by-dawn-wind"),
        ("멀리 돌아가는 마지막 자전거 불빛", "last-bicycle-light-in-distance"),
        ("구름의 이동을 적은 관찰 수첩", "notebook-of-moving-clouds"),
    ),
}


base.WORKS += (
    base.Work("Fantasy", "fantasy-poetry", "꿈과 현실",
              "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000009124008",
              "꿈과 현실 사이에서 떠오르는 감각을 시의 여백과 함께 살피는 일",
              "선명한 설명과 빠른 결론을 요구하는 화면이 일상을 채우는 시대",
              "꿈에서 얻은 감각을 현실의 언어로 어떻게 옮길지에 관한 질문"),
)
base.TARGET_BY_WORK = {
    "연(戀)": 200, "데자뷔": 100, "소나기": 100, "환상": 100,
    "별이 빛나는 밤에": 100, "Fantasy": 400,
}
base.DETAILS["Fantasy"] = (
    ("꿈의 색을 적은 연습장", "notebook-of-dream-colors"),
    ("행 사이에 끼운 반투명 종이", "translucent-paper-between-lines"),
    ("눈을 감을 때 떠오르는 푸른 점", "blue-dot-behind-closed-eyes"),
    ("소리 없이 흔들리는 종이 꽃", "silently-moving-paper-flower"),
    ("낮잠 뒤에도 남은 바람의 감각", "wind-sensation-after-nap"),
    ("빛의 방향을 표시한 빈 악보", "blank-score-marked-with-light"),
    ("물 위에서 접히는 창의 그림자", "window-shadow-folding-on-water"),
    ("한 음절만 남겨 둔 작은 쪽지", "small-note-with-one-syllable"),
    ("잊은 꿈을 대신 그린 동그라미", "circle-in-place-of-forgotten-dream"),
    ("잠에서 깬 뒤 뒤집어 놓은 모래시계", "hourglass-turned-after-waking"),
    ("낯선 향기를 붙여 둔 종이표", "paper-tag-with-unfamiliar-scent"),
    ("공백이 더 넓은 짧은 편지", "short-letter-with-wide-blanks"),
    ("손끝에 남은 마른 꽃잎의 무게", "dry-petal-weight-on-fingers"),
    ("새벽빛을 받아 흐려진 글자", "letters-fading-in-dawn-light"),
    ("방향 없이 이어진 점선의 지도", "directionless-dotted-map"),
    ("물결마다 길이가 달라지는 선", "line-changing-with-ripples"),
)

base.TITLE_PATTERNS = tuple(pattern.replace("{setting}에서 시작된 {work}의 질문", "{setting}의 {detail}에서 시작된 {work}의 질문") for pattern in base.TITLE_PATTERNS)

if __name__ == "__main__":
    base.main()
