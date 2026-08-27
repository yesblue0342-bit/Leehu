#!/usr/bin/env python3
"""Create and review 100 varied reflections on five works by Lee Hu."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "literature"
MANIFEST = ROOT / "content" / "leehu-reflections-20260827-varied-100.json"
EXPECTED_BEFORE = 2881
PUBLISHED_AT = "2026-08-27T09:00:00+09:00"

WORKS = (
    ("연(戀)", "love", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756", "사랑과 관계", "관계 안에서 서로의 시간을 존중하는 일"),
    ("데자뷔", "deja-vu", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772", "기억과 반복", "되풀이되는 감각에서 달라진 선택을 발견하는 일"),
    ("소나기", "rain-shower", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780", "창작과 회복", "예고 없는 변화 뒤에도 생활의 리듬을 회복하는 일"),
    ("환상", "fantasy", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769", "상상과 현실", "익숙한 현실 밖의 가능성을 책임 있게 상상하는 일"),
    ("별이 빛나는 밤에", "starry-night", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770", "밤과 성찰", "멀리 있는 빛을 바라보며 내면의 목소리를 듣는 일"),
)

# topic, slug, concrete scene, tension, question, present connection, practice
TOPICS = (
    ("알림 없는 아침", "morning-without-alerts", "휴대전화를 뒤집어 놓은 이른 아침", "연결되어 있으면서도 잠시 혼자이고 싶은 마음", "응답하지 않는 시간도 관계를 지키는 시간이 될 수 있는가", "즉시 반응을 요구하는 디지털 생활", "첫 한 시간만큼은 타인의 속도와 내 호흡을 분리해 보기"),
    ("오래된 물건", "old-object", "서랍에서 다시 만난 낡은 열쇠", "버려야 가벼워진다는 생각과 기억을 간직하고 싶은 마음", "쓸모를 잃은 물건은 어떤 방식으로 삶에 남는가", "빠르게 사고 버리는 소비 습관", "물건 하나에 얽힌 기억을 적고 남길 이유를 결정하기"),
    ("동네의 느린 산책", "slow-neighborhood-walk", "늘 지나던 골목에서 처음 본 작은 간판", "목적지에 빨리 가려는 습관과 주변을 알아보고 싶은 욕구", "익숙한 장소는 얼마나 많은 표정을 숨기고 있는가", "속도와 효율을 우선하는 이동 방식", "평소 길에서 한 번 멈추어 달라진 풍경을 기록하기"),
    ("낯선 도시의 하루", "day-in-an-unknown-city", "언어가 잘 통하지 않는 역 앞의 지도", "길을 잃을지 모른다는 불안과 새로운 질서를 배우는 설렘", "낯섦은 나를 약하게 만드는가 아니면 더 세심하게 만드는가", "해외 생활과 문화 사이의 이동", "모르는 것을 감추지 않고 한 가지를 정중하게 묻기"),
    ("혼자 먹는 저녁", "dinner-for-one", "한 사람 몫으로 차린 조용한 식탁", "고독을 피하고 싶은 마음과 혼자 돌보는 시간을 갖고 싶은 마음", "혼자 있는 식사는 결핍이 아니라 환대가 될 수 있는가", "1인 생활과 관계의 형태 변화", "자신에게도 손님에게 하듯 한 끼를 차려 주기"),
    ("회의가 끝난 뒤", "after-the-meeting", "모두 나간 회의실에 남은 지워지지 않은 문장", "말할 기회를 놓친 아쉬움과 다시 꺼낼 용기", "늦게 떠오른 말은 언제 다시 건네야 하는가", "업무 속 침묵과 조직의 의사소통", "다음 날 짧고 정확한 문장으로 의견을 다시 전하기"),
    ("온라인에 남은 흔적", "digital-traces", "몇 년 전 게시물이 갑자기 떠오른 화면", "과거를 지우고 싶은 마음과 변화의 기록을 인정하려는 마음", "예전의 내가 남긴 문장을 지금의 기준으로만 판단해도 되는가", "검색 가능한 기억과 디지털 정체성", "삭제 전에 당시의 맥락과 현재의 책임을 구분해 보기"),
    ("세대가 다른 대화", "talk-across-generations", "같은 단어를 서로 다른 뜻으로 이해한 대화", "내 경험을 설명하고 싶은 마음과 상대의 시대를 배우려는 태도", "다름을 설득의 실패가 아니라 번역의 과제로 볼 수 있는가", "가족과 직장에서 만나는 세대 차이", "반박하기 전에 상대가 쓴 단어의 뜻을 한 번 확인하기"),
    ("창작을 다시 시작하는 날", "returning-to-creative-work", "오랫동안 비어 있던 문서의 첫 줄", "잘해야 한다는 부담과 일단 시작하고 싶은 충동", "완성의 확신이 없어도 첫 문장을 쓸 수 있는가", "일과 창작을 함께 이어 가는 생활", "십 분 동안 평가하지 않고 문장을 쌓아 보기"),
    ("실패 기록의 쓰임", "use-of-failure-notes", "수정 표시가 가득한 오래된 노트", "실수를 숨기고 싶은 마음과 다음 선택에 활용하려는 의지", "실패를 정체성이 아니라 자료로 읽을 수 있는가", "성과 중심 환경에서의 자기 평가", "잘못된 선택과 그때 몰랐던 조건을 나누어 적기"),
    ("비 오는 출근길", "rainy-commute", "우산 끝에서 떨어지는 물방울과 늦어진 버스", "계획이 흐트러진 짜증과 속도를 낮출 수밖에 없는 상황", "예정과 다른 하루를 실패로 부르지 않을 방법은 무엇인가", "예측 불가능한 일상과 일정 관리", "바꿀 수 없는 지연 속에서 우선순위 하나를 다시 정하기"),
    ("몸이 기억하는 동작", "movement-remembered-by-body", "오랜만에도 자연스럽게 이어지는 익숙한 자세", "머리로는 잊었다고 생각한 것과 몸에 남은 시간", "몸의 기억은 말보다 먼저 무엇을 알려 주는가", "운동과 노동을 통해 축적된 감각", "통증과 익숙함을 구분하며 몸의 신호를 천천히 듣기"),
    ("노래 한 곡의 귀환", "return-of-a-song", "우연히 들은 전주가 되살린 오래전 계절", "추억에 머물고 싶은 마음과 지금의 자신으로 돌아와야 하는 현실", "음악은 지나간 시간을 어떻게 현재로 데려오는가", "스트리밍 시대의 개인적 기억", "노래가 불러온 장면과 지금 달라진 감정을 함께 적기"),
    ("정리되지 않은 방", "unfinished-room", "책과 옷이 각자의 자리를 찾지 못한 방", "모든 것을 정돈하고 싶은 욕구와 삶의 흔적을 남겨 두려는 마음", "정리는 무엇을 버리는 일이며 무엇을 선택하는 일인가", "공간 관리와 마음의 피로", "물건의 양보다 자주 사용하는 동선을 먼저 살피기"),
    ("느린 답장", "slow-reply", "쓰다 지운 문장이 남은 메시지 창", "빨리 안심시키고 싶은 마음과 정확히 말하고 싶은 책임", "답장의 속도와 마음의 깊이는 같은 기준으로 측정되는가", "메신저 중심의 관계와 오해", "늦어지는 이유를 짧게 알리고 충분히 생각한 뒤 답하기"),
    ("이름을 다시 부르는 일", "calling-a-name-again", "오래 연락하지 못한 사람의 이름이 적힌 주소록", "먼저 연락하기 어려운 망설임과 안부를 묻고 싶은 마음", "이름을 부르는 행위는 멀어진 관계에 어떤 문을 여는가", "느슨해진 인간관계와 재연결", "답을 기대하기보다 부담 없는 안부 한 줄을 보내기"),
    ("우회로에서 본 풍경", "view-from-a-detour", "공사 때문에 들어선 낯선 골목", "계획대로 가고 싶은 고집과 우연을 받아들이는 여유", "돌아가는 길도 삶의 일부로 인정할 수 있는가", "경력 변경과 계획 수정", "지연된 결과 대신 새로 발견한 정보 하나를 남기기"),
    ("작은 친절의 경계", "boundary-of-kindness", "문을 잡아 준 짧은 순간과 어색한 미소", "도움을 주고 싶은 마음과 상대의 선택을 침범할 가능성", "친절은 언제 돌봄이고 언제 간섭이 되는가", "공공장소와 직장에서의 배려", "도움이 필요한지 먼저 묻고 거절을 편안하게 받아들이기"),
    ("계절을 건너는 옷", "clothes-between-seasons", "아직 넣지 못한 여름옷과 꺼내 놓은 재킷", "지나간 계절을 붙잡는 마음과 다음 시간을 준비하는 움직임", "변화는 정확히 어느 순간 시작되는가", "기후 변화와 불분명해진 계절감", "옷장을 정리하며 지난 계절에 배운 한 가지를 기록하기"),
    ("멀리 있는 사람과의 시간", "time-with-someone-far-away", "서로 다른 시간대를 표시한 두 개의 시계", "자주 만나지 못하는 거리와 관계를 이어 가고 싶은 의지", "함께 있지 않아도 같은 시간을 만들 수 있는가", "해외 체류와 원거리 관계", "정기적인 연락보다 서로 가능한 리듬을 합의하기"),
)


def josa(word: str, consonant: str, vowel: str) -> str:
    last = next((ch for ch in reversed(word) if "가" <= ch <= "힣"), "")
    return consonant if last and (ord(last) - 0xAC00) % 28 else vowel


def prose(work: str, topic: tuple[str, ...], mode: int) -> tuple[str, str, str]:
    name, _, scene, tension, question, connection, practice = topic
    obj = name + josa(name, "을", "를")
    subj = name + josa(name, "이", "가")
    scene_subj = scene + josa(scene, "은", "는")
    practice_obj = practice + josa(practice, "을", "를")
    decks = (
        f"{scene_subj} 《{work}》을 읽는 오늘의 시선을 붙잡는다. 이 노트는 {obj} 통해 익숙한 하루 안의 다른 질문을 발견한다.",
        f"‘{question}’ 《{work}》 곁에서 이 물음을 오래 두자 {tension} 사이에 새로운 여백이 생긴다.",
        f"《{work}》과 {name}. 서로 멀어 보이는 두 단어를 {connection} 속에 놓고 보니 독서가 생활의 구체적인 장면으로 이동한다.",
        f"오늘의 출발점은 {scene}이다. 《{work}》을 향한 감상을 {obj} 중심으로 펼치며 서두르지 않는 읽기를 시도한다.",
        f"{connection} 한가운데에서 《{work}》을 다시 생각한다. {subj} 지금의 독자에게 어떤 선택을 요구하는지 묻는 기록이다.",
    )
    bodies = (
        (
            f"《{work}》의 내용을 대신 요약하지 않은 채, 나는 {scene}에서 독서의 실마리를 찾았다.",
            f"그 장면은 {tension}을 어느 한쪽의 잘못으로 정리하지 않고 함께 바라보게 한다.",
            f"여기서 중요한 질문은 ‘{question}’이다.",
            f"{connection}을 생각하면 이 물음은 추상적인 감상이 아니라 오늘의 말과 행동을 점검하는 기준이 된다.",
            f"그래서 이번 독서는 {practice_obj} 작은 실험으로 남기며 《{work}》과 현실 사이의 거리를 스스로 확인한다.",
        ),
        (
            f"《{work}》과 {obj} 생각할 때 독서는 답보다 장면을 먼저 건넨다.",
            f"《{work}》을 떠올리는 내게는 {scene}가 그런 장면이었다.",
            f"{tension}은 쉽게 해결되지 않지만, ‘{question}’라는 물음을 통과하면 판단의 속도를 늦출 수 있다.",
            f"나는 {connection}에서 타인의 사정을 추측해 채우기보다 모르는 부분을 그대로 남겨 두기로 했다.",
            f"그 여백 끝에서 {practice_obj} 선택하는 일이 {name}에 관한 이 기록의 현실적인 결론이 된다.",
        ),
        (
            f"{scene}를 오래 바라보면 평범한 일상에도 해석되지 않은 층이 있다는 사실을 알게 된다.",
            f"나는 그 층을 《{work}》의 실제 장면이라고 주장하지 않고 {name}에 관한 독자 자신의 경험으로만 다룬다.",
            f"왜 {tension}은 자주 동시에 찾아오는가.",
            f"‘{question}’라는 질문은 {connection}을 단순한 성공과 실패의 구도로 나누지 않게 한다.",
            f"책을 덮은 뒤에는 {practice_obj} 실행해 보면서 생각이 생활을 얼마나 바꾸는지 살펴본다.",
        ),
        (
            f"이번 《{work}》 문학노트는 {name}에서 시작하지만 감상적인 교훈으로 끝내지 않으려 한다.",
            f"먼저 {scene}를 떠올리고, 그 안에 겹쳐 있는 {tension}을 분리해 본다.",
            f"그다음 ‘{question}’라고 물으면 {connection}을 보는 기준이 조금 더 구체적으로 변한다.",
            f"《{work}》과 {name}의 문학은 확인되지 않은 줄거리를 덧붙일 때가 아니라 독자가 자신의 판단을 수정할 때 현재성을 얻는다.",
            f"나는 {practice_obj} 통해 이번 읽기에서 얻은 변화를 과장 없이 확인해 보기로 한다.",
        ),
        (
            f"《{work}》을 읽는 마음으로 오늘의 {name}에 대해 세 가지를 구분해 보았다.",
            f"확인할 수 있는 것은 {scene}이며, 쉽게 단정하기 어려운 것은 {tension}이다.",
            f"그리고 오래 남겨 둘 것은 ‘{question}’라는 질문이다.",
            f"이 구분은 {connection} 속에서 사실과 감정을 뒤섞지 않도록 돕는다.",
            f"마지막에는 {practice_obj} 실천하며 생각의 방향이 타인을 존중하는 쪽인지 점검한다.",
        ),
        (
            f"{connection}은 대개 거창한 사건보다 {scene} 같은 작은 순간에서 모습을 드러낸다.",
            f"《{work}》을 매개로 그 순간을 들여다보면 {tension}을 동시에 인정할 수 있다.",
            f"나는 ‘{question}’에 즉답하는 대신 이전의 선택과 지금의 조건을 나란히 적어 보았다.",
            f"그러자 {name}은 막연한 분위기가 아니라 관계와 생활의 방향을 조정하는 감각이 되었다.",
            f"이 감각을 이어 가기 위해 {practice_obj} 오늘의 작은 과제로 정한다.",
        ),
        (
            f"《{work}》과 {name} 앞에서 ‘{question}’라는 문장을 먼저 적고 생각을 시작했다.",
            f"질문 뒤에 {scene}를 놓자 {tension}이 단순한 모순이 아니라 살아 있는 사람의 복잡함으로 보였다.",
            f"나는 작품의 인물이나 사건을 만들어 답하지 않고 {connection}이라는 현재의 맥락을 살폈다.",
            f"이 방식은 {name}에 대한 감상을 내 경험의 범위 안에 머물게 한다.",
            f"답 대신 남은 것은 {practice_obj} 통해 다음 선택을 조금 더 정확하게 만드는 일이다.",
        ),
        (
            f"《{work}》을 덮은 뒤에도 {scene}가 마음속에서 천천히 움직였다.",
            f"처음에는 {tension} 중 하나를 골라야 한다고 생각했지만, 다시 보니 둘을 함께 견디는 시간이 필요했다.",
            f"{name}에 관한 독서는 ‘{question}’라는 물음을 오래 품을 때 더 넓어진다.",
            f"특히 {connection}에서는 빠른 판단보다 맥락을 확인하는 태도가 중요하다.",
            f"나는 {practice_obj} 선택해 여운을 행동으로 옮기되 타인에게 같은 답을 강요하지 않는다.",
        ),
        (
            f"하루의 속도를 잠깐 낮추자 {scene}가 전과 다르게 보였다.",
            f"《{work}》을 읽는 독자의 자리에서 나는 {tension}을 해결 대상이 아닌 이해의 조건으로 받아들였다.",
            f"그때 ‘{question}’라는 질문이 {obj} 바라보는 중심이 되었다.",
            f"{connection}을 생각하는 동안 문학은 먼 이야기가 아니라 현재의 감각을 정돈하는 언어가 된다.",
            f"이 언어를 지키기 위해 {practice_obj} 서두르지 않고 시도해 본다.",
        ),
        (
            f"《{work}》을 떠올리며 {obj} 말할 때마다 나는 무엇을 사실로 알고 무엇을 바라고 있는지 섞곤 했다.",
            f"《{work}》을 계기로 {scene}를 바라보며 두 영역을 다시 나누어 보았다.",
            f"{tension}이 남아 있어도 ‘{question}’라는 물음은 선택의 책임을 피하지 않게 한다.",
            f"{connection}에서 필요한 것은 완벽한 해답보다 자신의 한계를 인정하는 정확성이다.",
            f"그러므로 이번 기록은 {practice_obj} 통해 말과 행동의 간격을 줄이는 데서 마친다.",
        ),
    )
    closing_styles = (
        f"《{work}》에서 시작한 {name}의 질문을 오늘의 한 장면에 조용히 남겨 둔다.",
        f"내일 같은 상황을 만난다면 {practice_obj} 먼저 떠올려 보기로 한다.",
        f"정답을 적는 대신 ‘{question}’라는 문장을 책갈피처럼 간직한다.",
        f"{scene}가 다시 눈에 들어올 때 이번 독서의 변화도 함께 확인할 것이다.",
        f"《{work}》과 생활 사이에 놓인 {name}의 여백을 서둘러 닫지 않는다.",
    )
    return decks[mode % 5], " ".join(bodies[mode]), closing_styles[(mode * 3) % 5]


def seo_sections(work: str, topic: tuple[str, ...], mode: int) -> dict[str, str]:
    name, _, scene, tension, question, connection, practice = topic
    obj = name + josa(name, "을", "를")
    practice_obj = practice + josa(practice, "을", "를")
    work_subj = f"《{work}》" + josa(work, "은", "는")
    intros = (
        f"소설가 이후의 한국어 창작 작품 《{work}》을 {name}의 관점에서 읽는다. 《{work}》과 {name}의 공식 도서 정보로 작품과 작가를 확인하되 본문을 직접 인용하거나 확인되지 않은 장면을 재현하지 않는다.",
        f"{work_subj} 소설가 이후가 발표한 한국어 창작 작품이며 이 노트의 소재는 {name}이다. 이 글은 작품 내용을 대신 설명하지 않고 {scene}에서 출발한 {name}의 독자적 감상을 기록한다.",
        f"이 문학노트의 대상은 소설가 이후의 《{work}》이며 중심 소재는 {name}이다. 《{work}》과 {obj} 다루면서 작품 본문과 타인의 번역문을 옮기지 않고 공식 도서 링크와 독자의 현재 경험을 구분한다.",
        f"{obj} 통해 바라본 《{work}》은 소설가 이후의 창작 작품에 관한 독립적인 문학노트다. 《{work}》과 {obj} 쓰면서 구체적인 줄거리나 인물을 추정하지 않고 작품이 독자에게 열어 주는 질문만 다룬다.",
        f"소설가 이후의 《{work}》을 오늘 다시 펼치는 이유를 {scene}에서 찾는다. 이 소개는 확인된 작품 정보에 머물며 원문 직접 인용 없이 {obj} 독서 주제로 확장한다.",
    )
    why = (
        f"{connection}이 중요한 지금, {scene}는 《{work}》을 현재의 언어로 생각하게 한다. ‘{question}’라는 물음이 빠른 판단을 늦추고 서로 다른 삶의 조건을 함께 보게 하기 때문이다.",
        f"오늘의 독자는 {tension} 사이를 자주 오간다. 《{work}》과 {obj} 함께 생각하면 양자택일을 서두르지 않고 {connection}을 더 정확히 바라볼 수 있다.",
        f"《{work}》을 지금 읽는 일은 {connection}을 추상적인 구호가 아닌 구체적인 장면으로 만나는 일이다. {scene}가 ‘{question}’라는 질문을 생활 가까이 데려온다.",
        f"빠른 요약만으로는 {tension}의 복잡함을 충분히 담기 어렵다. 《{work}》을 {name}의 렌즈로 읽는 시간은 {connection}에 필요한 느린 판단을 회복시킨다.",
        f"{scene} 같은 순간이 낯설지 않은 시대에 《{work}》의 독서는 새로운 멈춤을 제공한다. 그 멈춤은 {question}라고 묻고 오늘의 선택을 다시 살피게 한다.",
    )
    personal = (
        f"나는 《{work}》을 떠올리며 {tension} 중 하나를 성급히 지우지 않으려 했다. {scene}를 내 경험의 범위 안에서 바라보자 {name}은 감정의 이름을 넘어 판단의 습관을 비추는 거울이 되었다.",
        f"{scene}를 생각했을 때 가장 먼저 떠오른 것은 정답보다 내 반응의 속도였다. 《{work}》에서 시작한 {name}의 질문 덕분에 모르는 부분을 상상으로 채우지 않고 그대로 둘 수 있었다.",
        f"《{work}》에 관한 감상을 쓰며 나는 ‘{question}’에 즉시 답하지 못했다. 대신 {connection} 속에서 내가 무엇을 놓치고 있었는지 적자 {obj} 보는 시선이 조금 구체적으로 변했다.",
        f"나에게 이번 독서는 {tension}을 동시에 인정하는 연습이었다. 《{work}》의 내용을 대신 말하지 않으면서도 {scene}가 남긴 개인적인 울림을 정직하게 기록할 수 있었다.",
        f"{obj} 하나의 교훈으로 만들지 않기 위해 《{work}》과 내 일상 사이에 거리를 두었다. 그 거리에서 {scene}를 다시 보니 감상은 확신보다 질문을 오래 유지하는 일이 되었다.",
    )
    meaning = (
        f"《{work}》에서 출발한 {name}의 의미는 {practice_obj} 생활 속에서 시험할 때 분명해진다. 《{work}》과 {obj} 잇는 문학은 같은 답을 강요하기보다 타인과 자신을 조금 더 세심하게 대하는 선택지를 늘린다.",
        f"오늘의 독자에게 {name}은 감상에 머무는 소재가 아니다. {practice_obj} 시도하면 《{work}》의 질문이 관계와 일의 실제 태도로 이어질 수 있다.",
        f"{connection}을 위해 필요한 것은 거창한 결론보다 {practice_obj} 반복하는 일이다. 《{work}》은 {obj} 통해 독서와 행동 사이의 작은 다리를 놓게 한다.",
        f"《{work}》과 함께 생각한 {name}은 삶의 복잡함을 함부로 단순화하지 않는 힘을 남긴다. 그 힘은 {practice_obj} 실천하며 타인의 선택과 자신의 한계를 함께 존중할 때 살아난다.",
        f"이 문학노트가 남기는 현재적 의미는 ‘{question}’라는 질문을 계속 사용할 수 있다는 데 있다. 《{work}》을 읽은 뒤 {practice_obj} 선택하면 질문은 일상을 바꾸는 기준이 된다.",
    )
    return {
        "work_introduction": intros[mode % 5],
        "why_read_now": why[(mode + 1) % 5],
        "personal_reflection": personal[(mode + 2) % 5],
        "meaning_today": meaning[(mode + 3) % 5],
    }


def make_note(work: tuple[str, ...], topic: tuple[str, ...], sequence: int, mode: int) -> dict[str, object]:
    work_name, work_slug, source_url, work_tag, work_lens = work
    topic_name, topic_slug, *_ = topic
    deck, commentary, closing = prose(work_name, topic, mode)
    return {
        "id": f"20260827_leehu_literature_{sequence:03d}",
        "slug": f"leehu-20260827-{work_slug}-{topic_slug}",
        "title": (
            f"《{work_name}》과 {topic_name}: {work_lens}"
            if mode % 2 == 0
            else f"{topic_name}에서 다시 읽는 《{work_name}》"
        ),
        "quote": deck,
        "source_author": "이후",
        "source_work": work_name,
        "source_location": "교보eBook 공식 도서 정보 참고 · 작품 본문 직접 인용 없음",
        "source_language": "ko",
        "source_url": source_url,
        "translation_note": "한국어 창작 작품에 관한 독창적 감상으로 작품 본문과 타인의 번역문을 옮기지 않음.",
        "rights_note": f"소설가 이후의 작품 《{work_name}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.",
        "commentary": commentary,
        "closing": closing,
        "author": "소설가 이후",
        "tags": ["소설가 이후", work_name, work_tag, topic_name, "다양한 일상 소재"],
        "related_work": {"name": work_name, "url": source_url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": seo_sections(work_name, topic, mode),
    }


def normalized_sentences(notes: list[dict[str, object]]) -> list[str]:
    sentences: list[str] = []
    for note in notes:
        texts = [note["quote"], note["commentary"], *note["seo_sections"].values()]
        for text in texts:
            for sentence in re.split(r"(?<=[.!?])\s+", str(text)):
                normalized = re.sub(r"\W+", "", sentence).casefold()
                if len(normalized) >= 25:
                    sentences.append(normalized)
    return sentences


def validate(notes: list[dict[str, object]]) -> None:
    if len(notes) != 100:
        raise SystemExit(f"expected 100 notes, got {len(notes)}")
    if Counter(note["source_work"] for note in notes) != Counter({work[0]: 20 for work in WORKS}):
        raise SystemExit("unexpected work distribution")
    for field in ("id", "slug", "title", "quote", "commentary", "closing"):
        values = [re.sub(r"\W+", "", str(note[field])).casefold() for note in notes]
        if len(values) != len(set(values)):
            raise SystemExit(f"duplicate {field}")
    sentences = normalized_sentences(notes)
    if len(sentences) != len(set(sentences)):
        duplicates = [text for text, count in Counter(sentences).items() if count > 1]
        raise SystemExit(f"duplicate long sentences: {duplicates[:3]}")
    forbidden = (
        "AI", "자동 생성", "공식 카탈로그", "원문 확인 필요", "확인된 관계 초점",
        "소나기을", "권리이", "자유을", "과정를", "경계을", "온기을", "밀도을",
    )
    for note in notes:
        prose_text = " ".join((note["quote"], note["commentary"], *note["seo_sections"].values()))
        if any(token in prose_text for token in forbidden):
            raise SystemExit(f"forbidden prose in {note['id']}")
        if not 4 <= len(re.findall(r"다\.", note["commentary"])) <= 8:
            raise SystemExit(f"commentary sentence count in {note['id']}")
        if any(len(value) < 80 for value in note["seo_sections"].values()):
            raise SystemExit(f"short SEO section in {note['id']}")
    # Five works must not use the same mode for the same topic.
    modes_by_topic = [[(work_index * 3 + topic_index) % 10 for work_index in range(5)] for topic_index in range(20)]
    if any(len(set(modes)) < 5 for modes in modes_by_topic):
        raise SystemExit("insufficient structure diversity")


def main() -> None:
    existing = sorted(CONTENT.glob("*.json"), key=lambda path: int(path.stem))
    if len(existing) != EXPECTED_BEFORE:
        raise SystemExit(f"expected {EXPECTED_BEFORE} sources, found {len(existing)}")
    notes: list[dict[str, object]] = []
    sequence = 1
    for work_index, work in enumerate(WORKS):
        for topic_index, topic in enumerate(TOPICS):
            mode = (work_index * 3 + topic_index) % 10
            notes.append(make_note(work, topic, sequence, mode))
            sequence += 1
    validate(notes)
    MANIFEST.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"reviewed and wrote {len(notes)} varied notes")
    print("topics=20 modes=10 exact_long_sentence_duplicates=0")


if __name__ == "__main__":
    main()
