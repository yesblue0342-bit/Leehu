#!/usr/bin/env python3
"""소설가 이후 자작품 5종 문학노트 1,000편 manifest 생성기."""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
MANIFEST = ROOT / "content" / "leehu-reflections-20260903-1000.json"
EXPECTED_BEFORE = 3631
TARGET_COUNT = 1000
START_SEQUENCE = 1261
PUBLISHED_AT = "2026-09-03T06:30:00+09:00"


@dataclass(frozen=True)
class Work:
    name: str
    slug: str
    theme: str
    url: str
    frame: str
    present: str
    focus: str


WORKS = (
    Work("연(戀)", "love", "관계와 선택", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756",
         "사랑을 완성된 감정보다 거리와 선택을 다시 묻는 과정으로 읽는 일",
         "빠른 호감과 단절이 반복되는 관계의 시대",
         "관계가 깊어질수록 선택의 책임도 함께 커진다는 질문"),
    Work("데자뷔", "deja-vu", "기억과 반복", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772",
         "낯익음을 진실의 증거로 단정하지 않고 기억이 만든 편집을 의심하는 일",
         "추천 화면이 익숙한 장면을 거듭 돌려주는 시대",
         "되풀이되는 감각과 실제 기억을 어떻게 구분할지에 관한 질문"),
    Work("소나기", "rain-shower", "회복과 변화", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780",
         "갑작스러운 변화 뒤 몸과 마음이 제 속도를 되찾는 과정을 바라보는 일",
         "예고 없이 일상이 바뀐 뒤 곧바로 회복하라는 요구가 따르는 시대",
         "회복에는 각자의 시간과 보이지 않는 수고가 필요하다는 질문"),
    Work("환상", "fantasy", "상상과 경계", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769",
         "상상을 현실 회피가 아니라 익숙한 세계의 규칙을 다르게 보는 힘으로 읽는 일",
         "이미지와 현실의 경계가 매일 새롭게 편집되는 시대",
         "상상이 현실을 외면하지 않으면서도 시야를 넓힐 수 있는지에 관한 질문"),
    Work("별이 빛나는 밤에", "starry-night", "밤과 사유", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770",
         "밤의 고요 속에서 멀리 있는 존재와 오늘의 자신을 함께 바라보는 일",
         "잠들기 전까지 화면의 빛이 좀처럼 사라지지 않는 시대",
         "고요가 외로움에 머물지 않고 성찰의 시간이 될 수 있는지에 관한 질문"),
)

TARGET_BY_WORK = {
    "연(戀)": 203,
    "데자뷔": 200,
    "소나기": 197,
    "환상": 200,
    "별이 빛나는 밤에": 200,
}

SETTINGS = tuple(zip(
    "새벽 플랫폼|비 갠 주택가|문 닫기 전 도서관|긴 강변 산책로|막차가 떠난 정류장|바람 센 옥상|불 밝힌 동전 세탁소|상영이 끝난 극장|겨울 바닷가|첫차의 맨 뒷자리|수업 뒤 빈 교실|장날 끝 찻집|조용한 병원 복도|오래된 아파트 계단|산 아래 우체국|항구 대합실|불 꺼진 사무실|이사 전날의 빈방|공원 끝 벤치|달빛이 든 부엌|아침 문 여는 꽃집|아무도 없는 운동장|간이역 대합실|늦은 오후 미술관|불을 낮춘 서점|비 갠 온실".split("|"),
    "dawn-platform|clear-rain-neighborhood|closing-library|long-riverside-path|after-last-bus-stop|windy-rooftop|coin-laundromat|after-screening-theater|winter-seashore|last-seat-first-train|empty-classroom|market-end-teahouse|quiet-hospital-corridor|old-apartment-stairs|mountain-post-office|harbor-waiting-room|dark-office|empty-room-before-moving|park-back-bench|moonlit-kitchen|opening-flower-shop|vacant-playground|small-train-stop|late-afternoon-gallery|dim-bookstore|after-rain-greenhouse".split("|")
))

DETAILS = {
    "연(戀)": tuple(zip(
        "접어 둔 약속 메모|서로 다른 방향을 보는 두 우산|식어 가는 찻잔 사이의 거리|돌려주지 못한 얇은 책|한 칸 비워 둔 의자|보내지 못하고 남긴 안부|따로 이어진 귀갓길|같은 노래 뒤의 침묵".split("|"),
        "folded-promise-note|two-opposite-umbrellas|distance-between-cooling-cups|unreturned-thin-book|one-empty-chair|unsent-greeting|separate-routes-home|silence-after-same-song".split("|"))),
    "데자뷔": tuple(zip(
        "처음인데 익숙한 문손잡이|두 번 적힌 같은 날짜|기억과 다르게 놓인 의자|모르는 번호의 익숙한 말투|되돌아온 오래된 알림|처음 펼친 책의 밑줄|겹쳐 보이는 두 안내 표지|잃어버린 적 없는 열쇠".split("|"),
        "familiar-new-doorknob|same-date-twice|chair-against-memory|familiar-tone-unknown-number|returned-old-notice|underline-in-new-book|overlapping-signs|never-lost-key".split("|"))),
    "소나기": tuple(zip(
        "천천히 마르는 소매|빗물에 번진 장보기 목록|처마 아래 나눈 짧은 자리|젖은 운동화가 남긴 자국|구름 사이로 열린 빛|우산 끝에 남은 마지막 물방울|비 그친 길의 흙냄새|물웅덩이에 흔들린 창문 불빛".split("|"),
        "slow-drying-sleeve|rain-blurred-list|shared-space-under-eaves|wet-shoe-marks|light-between-clouds|last-drop-on-umbrella|earth-scent-after-rain|window-light-in-puddle".split("|"))),
    "환상": tuple(zip(
        "그림자를 빌려주는 작은 가게|시간이 접히는 낡은 시계|문 뒤에서 자라는 푸른 숲|별빛을 담았다는 유리병|거꾸로 이어지는 계단|이름을 바꾸는 골목|새벽을 접어 띄운 종이배|문장 사이에서 날아간 새".split("|"),
        "shadow-rental-shop|time-folding-clock|blue-forest-behind-door|starlight-glass-bottle|backward-stairs|name-changing-alley|dawn-paper-boat|bird-between-sentences".split("|"))),
    "별이 빛나는 밤에": tuple(zip(
        "구름 뒤에서 다시 나타난 별|맨 마지막까지 남은 먼 창의 불빛|새벽 직전 기울어진 달|밤기차가 지나간 뒤의 정적|등대와 배 사이의 어둠|낡은 옥상에서 헤아린 별자리|한밤중 창문에 비친 얼굴|해 뜨기 전에 남은 푸른빛".split("|"),
        "star-after-clouds|last-distant-window-light|tilted-moon-before-dawn|silence-after-night-train|dark-between-lighthouse-and-boat|constellation-on-rooftop|face-in-midnight-window|blue-before-sunrise".split("|"))),
}

LENSES = "기다림의 윤리|관계의 신뢰|침묵의 책임|속도의 회복|거리의 감각|기억의 편집|반복의 의미|변화의 리듬|혼자 있는 시간|상상의 책임|익숙함의 함정|대화의 여백|말하기와 듣기|선택의 무게|다시 시작할 권리|불확실성을 견디는 힘|일상의 작은 용기|타인의 시간을 존중하는 태도|감정의 정확한 이름|보이지 않는 수고|기록과 망각의 균형|우연을 해석하는 방식|경계를 넘는 시야|떠나는 것과 함께 사는 법|마음을 천천히 읽는 습관".split("|")
TENSIONS = "기다림과 단절|믿음과 의심|침묵과 회피|회복과 재촉|친밀함과 거리|사실과 기억|반복과 변화|상실과 회복|고독과 연결|상상과 도피|익숙함과 진실|대화와 단정|표현과 경청|선택과 책임|떠남과 귀환|확신과 질문|두려움과 용기|나의 시간과 타인의 시간|감정과 해석|성과와 돌봄|기록과 망각|우연과 필연|안전과 모험|이별과 동행|속도와 이해".split("|")
ACTIONS = "확인된 사실과 느낌을 나누어 적기|답을 제시하기 전에 한 번 더 묻기|침묵을 곧바로 거절로 단정하지 않기|회복의 속도를 타인과 비교하지 않기|가까운 사이에서도 필요한 자리를 남기기|기억을 미리 정답으로 둔 채 대화하지 않기|선택을 건네기 전에 의사를 확인하기|익숙한 결론을 처음부터 되묻기|혼자 있는 시간을 실패로 부르지 않기|해석 뒤에 다시 보기의 여지를 두기|익숙하다는 이유만으로 옳다고 믿지 않기|대화 마지막에 남은 질문을 확인하기|말한 내용만큼 듣지 못한 부분을 확인하기|좋은 의도로 상대의 의사를 대신하지 않기|떠나는 결정을 실패의 증거로 사용하지 않기|모르는 부분을 억지로 채우지 않기|작은 행동의 의미를 천천히 헤아리기|타인의 시간표를 내 기준으로 재단하지 않기|감정의 크기와 행동의 책임을 구분하기|기대가 만든 요구를 호의와 분리하기|기록되지 않은 마음을 없었다고 여기지 않기|우연을 운명처럼 강요하지 않기|낯선 풍경 앞에서 달라진 감각을 적기|떠난 것을 지우지 않고 다음을 준비하기|빨리 아는 대신 알아갈 시간을 두기".split("|")

TRANSITIONS = (
    "가만히 호흡을 늦추어 보면", "한 걸음 물러서 살피면", "첫인상을 잠시 미루면",
    "눈앞의 장면을 오래 붙들면", "감정의 이름을 서둘러 붙이지 않으면", "문장 사이의 여백을 따라가면",
    "익숙한 판단을 잠시 내려놓으면", "독서의 속도를 한 박자 늦추면", "작은 차이를 놓치지 않으려 하면",
    "대답보다 질문을 먼저 세우면", "그날의 공기를 다시 불러오면", "기억의 순서를 거꾸로 더듬으면",
    "보이는 것과 느끼는 것을 나누어 보면", "선명한 결론에서 조금 벗어나면", "말보다 침묵의 길이를 재어 보면",
    "나의 경험을 유일한 기준으로 삼지 않으면", "장면의 앞뒤를 억지로 채우지 않으면", "작품과 현실 사이에 거리를 남겨 두면",
    "한 문장을 마음속에서 다시 읽으면", "사소한 흔적에 시선을 오래 두면", "처음의 확신을 조심스럽게 의심하면",
    "누군가의 시간을 대신 정하지 않으면", "이해했다는 말을 조금 늦추면", "감상의 방향을 한쪽으로 고정하지 않으면",
    "오늘의 생활과 조용히 겹쳐 보면", "상징을 정답처럼 풀어내지 않으면", "남겨진 감각을 차분히 정리하면",
    "내가 놓친 맥락부터 돌아보면", "끝맺음보다 이어질 질문을 생각하면",
)

ANCHOR_PATTERNS = (
    "{detail_obj} 품은 {setting}", "{detail_subj} 오래 남은 {setting}",
    "{setting}의 정적과 나란히 놓인 {detail}", "{detail_obj} 떠올리게 한 {setting}의 풍경",
    "{setting} 한편에 놓인 {detail}", "{detail_with} 함께 기억된 {setting}",
    "{setting_obj} 지나며 눈에 담은 {detail}", "{detail_subj} 풍경의 중심이 된 {setting}",
    "{setting}의 공기에 겹쳐진 {detail}", "{detail} 너머로 돌아본 {setting}",
    "{setting}에서 천천히 선명해진 {detail}", "{detail_obj} 오래 바라보게 한 {setting}",
    "{setting}의 빛 아래 머문 {detail}", "{detail_subj} 시간을 늦춘 {setting}",
    "{setting_subj} 한 화면에 함께 품은 {detail}", "{detail_obj} 곁에 둔 채 걸어 본 {setting}",
    "{setting}의 소리 사이로 떠오른 {detail}", "{detail_subj} 새로운 표정을 얻은 {setting}",
    "{setting} 끝에서 다시 본 {detail}", "{detail_obj} 쉽게 지나치지 못한 {setting}",
    "{setting}의 빈자리와 맞닿은 {detail}", "{detail_subj} 질문으로 바뀐 {setting}",
    "{setting_obj} 배경으로 천천히 읽은 {detail}",
)

TITLE_PATTERNS = (
    "{work} 문학노트: {motif} 앞에서 천천히 읽은 마음",
    "{motif_obj} 따라 다시 펼친 《{work}》",
    "서두르지 않은 {work}: {motif_subj} 남긴 질문",
    "《{work}》 곁에 놓아 본 {setting}의 {detail}",
    "{setting}의 {detail}, {work_obj} 읽는 새로운 거리",
    "{work} 문학노트: {setting}에서 발견한 {detail_with} 작은 선택",
    "{setting}에서 {detail_obj} 오래 바라보며 읽은 {work}",
    "한 장면의 여백: {work_with} {setting}의 {detail}",
    "{work_obj} 서두르지 않고 읽는 법: {setting}의 {detail}",
    "{setting}에서 시작된 {work}의 질문",
    "{work_with} {setting}의 {detail}, 익숙한 판단을 늦춘 기록",
    "{work} 문학노트: {setting}에 머문 {detail}",
    "{motif_subj} 건넨 《{work}》의 다음 질문",
)

ROLE_TEMPLATES = {
    "quote": (
        "{lead}, {anchor_topic} 평범한 풍경을 독서의 질문으로 바꾸고 이 노트는 {work_obj} 요약하지 않은 채 {lens_obj} 따라 읽는다.",
        "{lead}, {anchor_obj} 바라보는 일은 {work_with} 오늘의 생활 사이에 조용한 통로를 내며 {tension_obj} 성급히 한쪽으로 몰지 않게 한다.",
        "{lead}, {anchor_subj} 남긴 감각은 줄거리의 빈칸을 상상으로 채우기보다 {work_obj} 둘러싼 {focus_obj} 내 자리에서 다시 묻게 한다.",
        "{lead}, {anchor} 앞에서는 익숙한 설명도 잠시 힘을 잃고 {work_topic} {lens_obj} 생활의 언어로 옮겨 생각할 여지를 얻는다.",
        "{lead}, {anchor_with} 마주한 짧은 정적은 {work_obj} 빠르게 판단하지 말라는 신호가 되어 {tension} 사이의 간격을 보여 준다.",
        "{lead}, {anchor_topic} 작품을 대신 설명하는 장면이 아니라 {work_with} 나의 경험이 어디에서 만나는지 확인하는 독서의 출발점이 된다.",
        "{lead}, {anchor_obj} 중심에 둔 이번 기록은 {work_obj} 정답으로 고정하지 않고 {lens_subj} 어떤 태도에서 시작되는지 살펴본다.",
        "{lead}, {anchor_subj} 눈에 들어오는 까닭은 크고 극적인 사건보다 작은 흔적이 {work_with} 현실 사이의 거리를 더 정확히 드러내기 때문이다.",
        "{lead}, {anchor} 곁에서 떠오른 생각은 {focus_obj} 쉽게 끝낼 수 없음을 알리고 {lens_obj} 오래 생각하게 한다.",
        "{lead}, {anchor_obj} 따라가다 보면 {work_topic} 먼 이야기에 머물지 않고 {tension_obj} 대하는 오늘의 말투와 선택으로 다가온다.",
        "{lead}, {anchor_topic} 감상을 장식하기 위한 배경이 아니라 {work_obj} 읽는 속도를 조절하며 {lens_obj} 구체적인 문제로 만든다.",
        "{lead}, {anchor_subj} 만든 여백 안에서 {work_with} 관련한 확신은 잠시 느슨해지고 {focus_topic} 새롭게 들린다.",
        "{lead}, {anchor_obj} 지나치지 않는 일만으로도 {work_obj} 대하는 태도는 달라지며 {lens_topic} 추상적인 구호에서 벗어난다.",
    ),
    "commentary": (
        "{lead}, {anchor_topic} 작품 속 사실로 단정할 수 없는 상상의 장면이지만 {work_obj} 읽고 난 뒤 남은 질문을 정직하게 놓아 볼 자리를 마련한다.",
        "{lead}, {anchor_obj} 통해 나는 {lens_subj} 타인에게 요구할 덕목이기 전에 내 판단의 속도를 조절하는 기준임을 깨닫는다.",
        "{lead}, {anchor_subj} 보여 주는 작은 간격은 {tension_obj} 어느 한쪽의 잘못으로 정리하지 않고 각자의 시간까지 살피게 한다.",
        "{lead}, {anchor} 앞에서 중요한 것은 해답을 얻는 일이 아니라 {focus_obj} 나의 말과 행동 안에서 구체적으로 시험하는 일이다.",
        "{lead}, {anchor_with} 함께 떠오른 기억을 살피니 {work_obj} 내 경험의 증거로 이용하지 않으면서도 감상의 책임을 지킬 수 있었다.",
        "{lead}, {anchor_topic} 익숙한 감정을 낯설게 바라보게 하며 {lens_obj} 거창한 선언보다 작은 습관으로 이해하도록 이끈다.",
        "{lead}, {anchor_obj} 오래 생각할수록 {tension} 사이에는 정답보다 조정이 필요하고 그 조정에는 상대의 목소리가 빠질 수 없다는 점이 선명해진다.",
        "{lead}, {anchor_subj} 남긴 불편함을 지우지 않자 {work_topic} 위로나 교훈 하나로 줄어들지 않고 여러 독해가 공존할 자리를 얻는다.",
        "{lead}, {anchor} 곁에서는 좋은 의도만으로 충분하다는 믿음도 흔들리고 {action_choice_subj} 실제 관계를 돌보는 기준으로 다가온다.",
        "{lead}, {anchor_obj} 따라 되짚은 생각은 {work_obj} 현실의 사례와 같다고 우기지 않으면서도 오늘의 선택을 비추는 거울로 남긴다.",
        "{lead}, {anchor_topic} 내가 놓친 맥락을 먼저 찾게 하고 {lens_obj} 말할 때 필요한 겸손과 확인의 순서를 가르쳐 준다.",
        "{lead}, {anchor_subj} 품은 모호함을 그대로 두니 {tension_topic} 서로를 배제하는 두 답이 아니라 상황에 따라 다시 맞출 균형으로 보인다.",
        "{lead}, {anchor_obj} 한 문장으로 요약하지 않는 태도는 {work_with} 나 사이의 거리를 지키면서도 감상을 구체적인 삶의 문제로 이어 준다.",
    ),
    "work_introduction": (
        "{lead}, {anchor_obj} 중심에 둔 이 글은 교보ebook 공식 도서 정보에서 소설가 이후의 창작 작품 {work_obj} 확인하고 작성한 독립적인 문학노트다.",
        "{lead}, 이 기록은 {anchor_obj} 작품의 실제 장면이라고 주장하지 않으며 확인된 저자와 작품 정보 위에서 {frame}에 초점을 맞춘다.",
        "{lead}, {anchor_with} 연결한 이번 읽기는 작품 본문이나 대사를 옮기지 않고 {work_obj} 둘러싼 감상을 새롭게 구성한다.",
        "{lead}, {anchor_subj} 출발점이 된 까닭은 줄거리를 대신 전달하기 위해서가 아니라 {focus_obj} 구체적인 생활의 언어로 바꾸어 보기 위해서다.",
        "{lead}, {anchor_obj} 바라보는 이 노트는 확인되지 않은 인물과 사건을 보태지 않고 {work_with} 관련한 해석의 범위를 분명히 밝힌다.",
        "{lead}, {anchor_topic} 서지 정보와 감상을 구분하는 표지가 되며 작품 자체의 표현을 복제하지 않는 독서 기록의 경계를 세운다.",
        "{lead}, {anchor} 곁에 {work_obj} 놓는 일은 창작 배경을 임의로 꾸미는 대신 확인 가능한 정보와 개인의 해석을 나누는 방법이다.",
        "{lead}, {anchor_obj} 소재로 삼은 이 글에서 {frame}은 작품의 유일한 의미가 아니라 한 독자가 선택한 읽기 방향으로 제시된다.",
        "{lead}, {anchor_subj} 이끄는 문학노트는 소설가 이후와 《{work}》의 관계를 공식 도서 정보로 확인하되 작품 내용을 재현하지 않는다.",
        "{lead}, {anchor}에서 시작한 소개는 출판 정보의 빈칸을 추측으로 메우지 않고 {lens_obj} 중심으로 독서의 질문을 좁힌다.",
        "{lead}, {anchor_obj} 통해 만나는 {work_topic} 이 노트 안에서 {focus_obj} 살피는 계기가 되며 원문을 대신하는 요약으로 다뤄지지 않는다.",
        "{lead}, {anchor_topic} 확인된 작품명과 저자명 바깥의 사실을 만들어 내지 않겠다는 원칙 아래 마련한 감상의 독립된 무대다.",
        "{lead}, {anchor_subj} 남긴 분위기를 빌리되 이 글은 그것을 실제 작품 장면으로 가장하지 않고 {work_obj} 향한 하나의 해석으로 한정한다.",
    ),
    "why_read_now": (
        "{lead}, {anchor_topic} {present}에 {tension_obj} 짧은 판단으로 끝내지 않을 이유를 보여 주며 {lens_obj} 다시 생각하게 한다.",
        "{lead}, {anchor_obj} 오늘의 생활과 겹쳐 보면 {focus_topic} 오래된 물음이면서도 지금 우리의 대화 방식과 맞닿아 있음을 알 수 있다.",
        "{lead}, {anchor_subj} 요청하는 느린 시선은 {present}에 빠르게 지나친 감정의 맥락을 되찾는 데 필요하다.",
        "{lead}, {anchor} 앞에 잠시 머무는 일은 {tension_obj} 승패처럼 가르려는 습관을 늦추고 {work_obj} 지금 읽을 이유를 마련한다.",
        "{lead}, {anchor_with} 이어진 질문은 {present}에 {lens_topic} 사적인 취향을 넘어 관계를 지키는 기술이 될 수 있음을 보여 준다.",
        "{lead}, {anchor_obj} 다시 보는 동안 {work_topic} 낡은 교훈으로 멀어지지 않고 오늘 선택의 속도와 책임을 묻는 작품으로 가까워진다.",
        "{lead}, {anchor_topic} 정보가 넘치는 시기일수록 맥락을 잃지 않는 독서가 왜 필요한지 보여 주고 {action_choice_obj} 현실적인 응답으로 남긴다.",
        "{lead}, {anchor_subj} 품은 작은 변화는 {present}에 눈에 띄는 성과보다 보이지 않는 회복과 돌봄을 살피게 한다.",
        "{lead}, {anchor_obj} 따라 읽으면 {tension_topic} 개인의 감정에만 머물지 않고 서로 다른 경험이 만나는 사회적 질문으로 넓어진다.",
        "{lead}, {anchor}에서 감지한 여백은 {work_obj} 지금 다시 펼칠 때 과도한 확신을 줄이고 {lens_obj} 생활 속에서 연습하게 한다.",
        "{lead}, {anchor_topic} 오늘의 독자에게 대단한 결심보다 판단을 잠시 늦출 틈을 주며 {focus_obj} 자기 언어로 묻게 한다.",
        "{lead}, {anchor_obj} 바라보는 시간은 {present}에 쉽게 소비되는 감정을 오래 책임지는 법을 찾게 한다.",
        "{lead}, {anchor_subj} 건넨 질문 덕분에 {work_topic} 과거의 작품 정보에 머물지 않고 {tension_obj} 새롭게 조율하는 현재의 독서가 된다.",
    ),
    "personal_reflection": (
        "{lead}, {anchor_obj} 떠올린 나는 선의를 앞세워 상대의 속도를 정했던 순간을 돌아보고 {action_plan}.",
        "{lead}, {anchor_subj} 남긴 감각을 따라가며 나는 {tension_obj} 충분히 구분하지 않은 채 결론부터 냈던 습관을 발견했다.",
        "{lead}, {anchor} 앞에서 나는 {work_obj} 내 경험과 동일시하지 않으면서도 {lens_obj} 실천하지 못한 장면들을 솔직히 마주했다.",
        "{lead}, {anchor_with} 나의 기억을 나란히 두자 오래된 확신은 느슨해졌고 나는 {action_thing_obj} 작은 시작으로 삼을 수 있겠다고 생각했다.",
        "{lead}, {anchor_topic} 내 말이 정확했는지보다 상대가 말할 자리를 남겼는지 먼저 묻게 했으며 그 질문은 쉽게 사라지지 않았다.",
        "{lead}, {anchor_obj} 바라본 뒤 나는 {focus_obj} 남의 문제로 밀어 두지 않고 오늘의 선택 안에서 확인해야겠다고 느꼈다.",
        "{lead}, {anchor_subj} 불러온 기억에는 미안함과 안도감이 함께 있었고 나는 둘 중 하나만 진실이라고 고집하지 않기로 했다.",
        "{lead}, {anchor} 곁에서 내가 아는 것과 짐작하는 것을 나누어 보니 {lens_topic} 생각보다 구체적인 말투와 기다림의 문제였다.",
        "{lead}, {anchor_obj} 오래 붙드는 동안 나는 빠른 해석이 불안을 가릴 수는 있어도 관계를 이해하게 하지는 못한다는 사실을 받아들였다.",
        "{lead}, {anchor_topic} 나 자신에게도 회복할 시간을 허락해야 한다는 점을 일깨웠고 나는 {action_plan}.",
        "{lead}, {anchor_subj} 조용히 남아 있는 모습을 보며 나는 기록되지 않은 마음까지 없었다고 판단한 일을 반성했다.",
        "{lead}, {anchor_obj} 통해 돌아본 하루에는 사소한 선택이 여러 사람의 시간을 바꾼 순간이 있었고 나는 그 책임을 가볍게 넘기지 않기로 했다.",
        "{lead}, {anchor}에서 시작한 감상은 결국 나에게 돌아와 {tension_obj} 대하는 태도를 묻고 {action_choice_obj} 다음 행동으로 남겼다.",
    ),
    "meaning_today": (
        "{lead}, {anchor_topic} 오늘의 독자에게 빠른 확신보다 정확한 이해가 오래 간다는 사실을 전하며 {action_thing_obj} 오늘의 작은 출발로 삼게 한다.",
        "{lead}, {anchor_obj} 통해 얻는 의미는 {tension_obj} 없애는 데 있지 않고 서로의 시간이 다름을 인정하며 균형을 다시 맞추는 데 있다.",
        "{lead}, {anchor_subj} 제안하는 작은 멈춤은 {present}에 {lens_obj} 추상적인 미덕이 아니라 생활의 기술로 바꾼다.",
        "{lead}, {anchor} 앞에서 남겨 둔 여백은 다른 경험을 하나의 답으로 합치지 않으면서도 함께 살아갈 방법을 찾게 한다.",
        "{lead}, {anchor_with} 이어진 {action_choice_topic} 거창한 교훈보다 실행하기 쉬우며 오늘의 대화와 기록을 조금 더 책임 있게 만든다.",
        "{lead}, {anchor_obj} 오래 보는 태도는 {focus_obj} 타인에게만 요구하지 않고 자신의 선택부터 점검하게 한다.",
        "{lead}, {anchor_topic} 보이지 않는 수고를 알아보는 눈을 길러 주며 {work_with} 관련한 독서를 현실의 돌봄으로 이어 준다.",
        "{lead}, {anchor_subj} 남긴 질문은 답을 독점하려는 마음을 낮추고 {tension_obj} 함께 견딜 언어를 찾게 한다.",
        "{lead}, {anchor_obj} 따라 생각한 결과 오늘의 의미는 속도를 늦추는 데서 멈추지 않고 더 정확한 선택을 준비하는 데까지 이어진다.",
        "{lead}, {anchor} 곁에서 배운 거리 감각은 친밀함 속에서도 상대의 의사를 확인하게 하고 {lens_obj} 지속 가능한 관계의 기준으로 세운다.",
        "{lead}, {anchor_topic} 기억과 해석 사이에 필요한 간격을 보여 주며 {action_choice_obj} 누구나 시도할 수 있는 작은 변화로 제안한다.",
        "{lead}, {anchor_obj} 현재의 질문으로 받아들이면 {work_topic} 독서 뒤에 끝나지 않고 말하기와 듣기의 순서를 바꾸는 힘이 된다.",
        "{lead}, {anchor_subj} 일으킨 조용한 변화는 삶을 단번에 고치겠다는 약속보다 {action_thing_from} 출발하는 꾸준한 태도를 권한다.",
    ),
    "closing": (
        "{lead}, {anchor}에서 시작한 질문은 오늘 {action_choice_obj} 남기고 다음 의미는 독자의 시간에 열어 둔다.",
        "{lead}, {anchor_obj} 지나온 이 기록은 {work_obj} 하나의 답으로 닫지 않고 {lens_obj} 이어 갈 작은 약속으로 남긴다.",
        "{lead}, {anchor_subj} 건넨 멈춤을 기억하며 나는 다음 선택에서 {action_plan}.",
        "{lead}, {anchor} 곁에 남은 여백은 {tension_obj} 서둘러 끝내지 말라는 조용한 문장으로 이어진다.",
        "{lead}, {anchor_obj} 다시 떠올릴 때마다 이 노트는 {focus_obj} 삶의 자리에서 새롭게 묻고자 한다.",
        "{lead}, {anchor_topic} 오늘의 결론보다 내일의 태도를 바꾸는 데 의미가 있으며 그 시작은 {action_choice_subj} 될 수 있다.",
        "{lead}, {anchor_with} 함께 머문 독서는 {work_obj} 설명하지 않고도 오래 생각할 한 가지 이유를 남긴다.",
        "{lead}, {anchor_subj} 만든 작은 틈을 닫지 않은 채 나는 {lens_obj} 다음 대화의 기준으로 가져간다.",
        "{lead}, {anchor_obj} 천천히 읽은 시간은 {tension_obj} 다시 조율할 수 있다는 믿음으로 남는다.",
        "{lead}, {anchor} 앞에서 멈춘 오늘의 감상은 {action_choice_obj} 현실로 옮길 때 비로소 다음 장을 얻는다.",
        "{lead}, {anchor_topic} 선명한 답 대신 정확한 질문을 남겼고 나는 그 질문을 서두르지 않고 품어 보기로 했다.",
        "{lead}, {anchor_obj} 중심에 둔 기록은 {work_with} 나 사이의 거리를 지키며 새로운 독해를 기다린다.",
        "{lead}, {anchor_subj} 보여 준 느린 변화처럼 이 글도 작은 선택이 쌓이는 방향으로 조용히 닫힌다.",
    ),
}


def josa(word: str, consonant: str, vowel: str) -> str:
    last = next((char for char in reversed(word) if "\uac00" <= char <= "\ud7a3"), "")
    return consonant if last and (ord(last) - 0xAC00) % 28 else vowel


def attach(word: str, consonant: str, vowel: str) -> str:
    return word + josa(word, consonant, vowel)


def sentence_list(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def make_anchor(setting: str, detail: str, pattern_index: int) -> str:
    values = {
        "setting": setting,
        "setting_obj": attach(setting, "을", "를"),
        "setting_subj": attach(setting, "이", "가"),
        "setting_with": attach(setting, "과", "와"),
        "detail": detail,
        "detail_obj": attach(detail, "을", "를"),
        "detail_subj": attach(detail, "이", "가"),
        "detail_with": attach(detail, "과", "와"),
    }
    return ANCHOR_PATTERNS[pattern_index % len(ANCHOR_PATTERNS)].format(**values)


def render_sentence(role: str, ctx: dict[str, str], index: int, serial: int) -> str:
    role_code = tuple(ROLE_TEMPLATES).index(role)
    anchor_index = (index * 7 + serial * 11 + role_code * 3) % len(ANCHOR_PATTERNS)
    anchor = make_anchor(ctx["setting"], ctx["detail"], anchor_index)
    lead = TRANSITIONS[(index * 17 + serial * 19 + role_code * 5) % len(TRANSITIONS)]
    template = ROLE_TEMPLATES[role][(index + serial * 5 + role_code * 7) % len(ROLE_TEMPLATES[role])]
    values = dict(ctx)
    values.update({
        "lead": lead,
        "anchor": anchor,
        "anchor_obj": attach(anchor, "을", "를"),
        "anchor_subj": attach(anchor, "이", "가"),
        "anchor_topic": attach(anchor, "은", "는"),
        "anchor_with": attach(anchor, "과", "와"),
    })
    return template.format(**values)


def render_paragraph(role: str, count: int, ctx: dict[str, str], index: int) -> str:
    return " ".join(render_sentence(role, ctx, index, serial) for serial in range(count))


def make_note(work: Work, work_index: int, setting_index: int, detail_index: int, sequence: int) -> dict[str, object]:
    setting, setting_slug = SETTINGS[setting_index]
    detail, detail_slug = DETAILS[work.name][detail_index]
    index = sequence - START_SEQUENCE
    lens = LENSES[(index * 7 + work_index) % len(LENSES)]
    tension = TENSIONS[(index * 11 + detail_index) % len(TENSIONS)]
    action = ACTIONS[(index * 13 + setting_index) % len(ACTIONS)]
    motif = f"{setting}에서 마주한 {detail}"
    ctx = {
        "setting": setting,
        "detail": detail,
        "work": work.name,
        "work_obj": attach(f"《{work.name}》", "을", "를"),
        "work_topic": attach(f"《{work.name}》", "은", "는"),
        "work_with": attach(f"《{work.name}》", "과", "와"),
        "lens": lens,
        "lens_obj": attach(lens, "을", "를"),
        "lens_subj": attach(lens, "이", "가"),
        "lens_topic": attach(lens, "은", "는"),
        "tension": tension,
        "tension_obj": attach(tension, "을", "를"),
        "tension_topic": attach(tension, "은", "는"),
        "action": action,
        "action_choice": f"‘{action}’라는 선택",
        "action_choice_subj": f"‘{action}’라는 선택이",
        "action_choice_obj": f"‘{action}’라는 선택을",
        "action_choice_topic": f"‘{action}’라는 선택은",
        "action_thing_obj": f"{action[:-1]}는 것을",
        "action_thing_from": f"{action[:-1]}는 것에서",
        "action_from": f"{action}부터",
        "action_plan": f"{action}로 마음을 정했다",
        "frame": work.frame,
        "present": work.present,
        "focus": work.focus,
        "focus_obj": attach(work.focus, "을", "를"),
        "focus_topic": attach(work.focus, "은", "는"),
    }
    title = TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(
        work=work.name,
        work_obj=attach(f"《{work.name}》", "을", "를"),
        work_with=attach(f"《{work.name}》", "과", "와"),
        setting=setting,
        detail=detail,
        detail_obj=attach(detail, "을", "를"),
        detail_with=attach(detail, "과", "와"),
        motif=motif,
        motif_obj=attach(motif, "을", "를"),
        motif_subj=attach(motif, "이", "가"),
    )
    return {
        "id": f"20260903_leehu_literature_{sequence:04d}",
        "slug": f"leehu-20260903-{work.slug}-{setting_slug}-{detail_slug}-literary-note",
        "title": title,
        "quote": render_paragraph("quote", 1, ctx, index),
        "source_author": "이후",
        "source_work": work.name,
        "source_location": f"교보ebook 공식 도서 정보에서 이후와 《{work.name}》의 관계를 확인함 · {setting}의 {attach(detail, "은", "는")} 독립적인 감상 소재임",
        "source_language": "ko",
        "source_url": work.url,
        "translation_note": f"《{work.name}》에 관한 한국어 독창 감상으로 {setting}의 {attach(detail, "을", "를")} 소재로 구성했으며 제3자의 번역문을 옮기지 않음.",
        "rights_note": f"소설가 이후의 《{work.name}》에 관한 자체 작성 문학노트로 {setting}의 {attach(detail, "을", "를")} 감상 소재로 삼았으며 작품 본문 직접 인용 없음.",
        "commentary": render_paragraph("commentary", 4, ctx, index),
        "closing": render_paragraph("closing", 1, ctx, index),
        "author": "소설가 이후",
        "tags": ["소설가 이후", work.name, work.theme, lens, "독창적 감상"],
        "related_work": {"name": work.name, "url": work.url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": {
            "work_introduction": render_paragraph("work_introduction", 2, ctx, index),
            "why_read_now": render_paragraph("why_read_now", 2, ctx, index),
            "personal_reflection": render_paragraph("personal_reflection", 2, ctx, index),
            "meaning_today": render_paragraph("meaning_today", 2, ctx, index),
        },
    }


def normalize_skeleton(sentence: str) -> str:
    terms: list[str] = []
    for work in WORKS:
        terms.extend((work.name, work.frame, work.present, work.focus))
        terms.extend(detail for detail, _ in DETAILS[work.name])
    terms.extend(setting for setting, _ in SETTINGS)
    terms.extend(LENSES)
    terms.extend(TENSIONS)
    terms.extend(ACTIONS)
    normalized = sentence
    for term in sorted(set(terms), key=len, reverse=True):
        normalized = normalized.replace(term, "<V>")
    normalized = re.sub(r"《?<V>》?(?:이라는|라는|으로|로|에서|부터|을|를|은|는|이|가|과|와)?", "<V>", normalized)
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def review(notes: list[dict[str, object]]) -> None:
    if len(notes) != TARGET_COUNT:
        raise SystemExit(f"expected {TARGET_COUNT}, found {len(notes)}")
    expected_distribution = TARGET_BY_WORK
    if Counter(str(note["source_work"]) for note in notes) != Counter(expected_distribution):
        raise SystemExit("work distribution mismatch")
    for field in ("id", "slug", "title", "quote", "commentary", "closing"):
        values = [re.sub(r"\s+", " ", str(note[field])).casefold() for note in notes]
        if len(values) != len(set(values)):
            raise SystemExit(f"duplicate {field}")
    forbidden = (
        "AI", "인공지능", "자동 생성", "자동화", "에이전트", "검수 도구", "SEO",
        "권리이", "자유을", "과정를", "소나기을", "환상와", "메모은", "윤리을",
        "’이라는", "’이라는", "적기이라는", "묻기이라는", "확인하기이라는",
    )
    all_sentences: list[str] = []
    all_skeletons: list[str] = []
    for note in notes:
        sections = note["seo_sections"]
        if tuple(sections) != ("work_introduction", "why_read_now", "personal_reflection", "meaning_today"):
            raise SystemExit(f"section schema mismatch: {note['id']}")
        if len(str(note["commentary"])) < 300:
            raise SystemExit(f"short commentary: {note['id']}")
        if any(len(str(value)) < 180 for value in sections.values()):
            raise SystemExit(f"short section: {note['id']}")
        prose = " ".join((str(note["quote"]), str(note["commentary"]), str(note["closing"]), *(str(v) for v in sections.values())))
        if any(term in prose for term in forbidden):
            raise SystemExit(f"forbidden prose: {note['id']}")
        if re.search(r"(?:기|하기)\.$", prose):
            raise SystemExit(f"incomplete nominal ending: {note['id']}")
        sentences = [sentence for sentence in sentence_list(prose) if len(sentence) >= 25]
        all_sentences.extend(sentences)
        all_skeletons.extend(normalize_skeleton(sentence) for sentence in sentences)
    repeated = [sentence for sentence, count in Counter(all_sentences).items() if count > 1]
    if repeated:
        raise SystemExit(f"repeated exact sentence: {repeated[0]}")
    skeleton_repeated = [(value, count) for value, count in Counter(all_skeletons).items() if count > 1]
    if skeleton_repeated:
        value, count = max(skeleton_repeated, key=lambda item: item[1])
        raise SystemExit(f"repeated normalized sentence skeleton x{count}: {value}")
    for offset in range(0, TARGET_COUNT, 50):
        batch = notes[offset:offset + 50]
        if len(batch) != 50 or len({str(note["slug"]) for note in batch}) != 50:
            raise SystemExit(f"batch {offset // 50 + 1} uniqueness failure")
        print(f"batch {offset // 50 + 1:02d}: 50 notes reviewed")


def generate() -> list[dict[str, object]]:
    notes: list[dict[str, object]] = []
    sequence = START_SEQUENCE
    for work_index, work in enumerate(WORKS):
        candidates = [
            (setting_index, detail_index)
            for setting_index in range(len(SETTINGS))
            for detail_index in range(len(DETAILS[work.name]))
        ]
        for setting_index, detail_index in candidates[:TARGET_BY_WORK[work.name]]:
            notes.append(make_note(work, work_index, setting_index, detail_index, sequence))
            sequence += 1
    return notes


def main() -> None:
    existing = sorted(CONTENT.glob("*.json"), key=lambda path: int(path.stem))
    if len(existing) not in (EXPECTED_BEFORE, EXPECTED_BEFORE + TARGET_COUNT):
        raise SystemExit(f"expected {EXPECTED_BEFORE} or {EXPECTED_BEFORE + TARGET_COUNT} sources, found {len(existing)}")
    notes = generate()
    review(notes)
    existing_ids = {json.loads(path.read_text(encoding="utf-8"))["id"] for path in existing[:EXPECTED_BEFORE]}
    existing_slugs = {json.loads(path.read_text(encoding="utf-8"))["slug"] for path in existing[:EXPECTED_BEFORE]}
    if existing_ids & {str(note["id"]) for note in notes}:
        raise SystemExit("existing id collision")
    if existing_slugs & {str(note["slug"]) for note in notes}:
        raise SystemExit("existing slug collision")
    if len(existing) == EXPECTED_BEFORE + TARGET_COUNT:
        targets = [CONTENT / f"{number}.json" for number in range(EXPECTED_BEFORE + 1, EXPECTED_BEFORE + TARGET_COUNT + 1)]
        if [json.loads(path.read_text(encoding="utf-8")) for path in targets] != notes:
            raise SystemExit("applied batch differs from regenerated notes")
    MANIFEST.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"reviewed and wrote {len(notes)} notes to {MANIFEST}")


if __name__ == "__main__":
    main()
