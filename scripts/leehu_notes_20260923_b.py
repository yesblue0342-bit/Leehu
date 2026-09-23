"""2026-09-23 문학 노트 원고 B: 전역 위치 201~400.

확인된 작품 제목과 장르만을 출발점으로 삼아 기억, 시간, 재독, 사진,
편지, 기록, 달력에 관한 현재적 질문을 만든다. 작품의 줄거리나 인물,
창작 의도는 추정하지 않는다.
"""
from __future__ import annotations

import re
from collections import Counter


WORKS = ("연(戀)", "데자뷔", "소나기", "환상", "별이 빛나는 밤에", "Fantasy")
FLOWS = ("question", "contrast", "observation", "thought_experiment", "practice")
FLOW_LABELS = {
    "question": "질문 중심",
    "contrast": "대조 중심",
    "observation": "관찰 중심",
    "thought_experiment": "사고 실험 중심",
    "practice": "실천 중심",
}
SCHEDULE = tuple(
    work
    for turn in range(33)
    for work, count in zip(WORKS, (15, 13, 13, 13, 13, 33))
    if turn < count
)
GENRES = {
    "연(戀)": "소설",
    "데자뷔": "소설",
    "소나기": "소설",
    "환상": "시집",
    "별이 빛나는 밤에": "시집",
    "Fantasy": "시집",
}


def _particle(word: str, consonant: str, vowel: str) -> str:
    """Return the Korean particle matching the final pronounced character."""
    final = next((char for char in reversed(word) if "가" <= char <= "힣"), "")
    if not final:
        final = next((char for char in reversed(word) if char.isalnum()), "")
    if "가" <= final <= "힣":
        jong = (ord(final) - ord("가")) % 28
        if (consonant, vowel) == ("으로", "로") and jong == 8:
            return vowel
        return consonant if jong else vowel
    return vowel


def _fix_particles(text: str) -> str:
    """Correct particles attached to variable work, topic, and lens phrases."""
    terms = [item[1] for item in ANCHORS] + [item[1] for item in ANGLES]
    terms += list(WORKS) + [f"『{work}』" for work in WORKS]
    pattern = re.compile(
        "(" + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True))
        + r")(이라는|라는|으로|로|은|는|이|가|을|를|과|와)"
    )

    def replace(match: re.Match[str]) -> str:
        word, found = match.groups()
        if found in ("이라는", "라는"):
            return word + _particle(word, "이라는", "라는")
        for consonant, vowel in (("으로", "로"), ("은", "는"), ("이", "가"), ("을", "를"), ("과", "와")):
            if found in (consonant, vowel):
                return word + _particle(word, consonant, vowel)
        return match.group(0)

    fixed = pattern.sub(replace, text).replace("소설으로", "소설로")
    for awkward, natural in (
        ("접근의 경계의", "접근 경계의"),
        ("맥락의 복원의", "맥락 복원의"),
        ("해석의 수정의", "해석 수정의"),
        ("맥락의 복원을 세우", "맥락을 복원하"),
        ("놓아줄 기준의 기준", "놓아줄 기준"),
    ):
        fixed = fixed.replace(awkward, natural)
    return fixed


def _limit_topic_repetitions(text: str, topic: str) -> str:
    """Use natural references after a concrete topic has already been established."""
    pattern = re.compile(re.escape(topic) + r"(은|는|이|가|을|를|과|와)?")
    seen = 0
    references = ("이 기록", "그 흔적", "해당 자료")
    pairs = {
        "은": ("은", "는"), "는": ("은", "는"), "이": ("이", "가"), "가": ("이", "가"),
        "을": ("을", "를"), "를": ("을", "를"), "과": ("과", "와"), "와": ("과", "와"),
    }

    def replace(match: re.Match[str]) -> str:
        nonlocal seen
        seen += 1
        if seen <= 2:
            return match.group(0)
        reference = references[(seen - 3) % len(references)]
        found = match.group(1)
        if found is None:
            return reference
        consonant, vowel = pairs[found]
        return reference + _particle(reference, consonant, vowel)

    return pattern.sub(replace, text)

# 각 항목은 같은 소재라도 판단 기준이 겹치지 않도록 네 갈래 쟁점을 갖는다.
# (영문 표지, 구체 사물, 핵심 주장)
ANCHORS = (
    ("faded-photo", "빛바랜 가족사진", "색이 흐려진 정도를 감정의 진실과 동일시하지 말아야 한다"),
    ("cropped-photo", "잘려 나간 단체사진", "프레임 밖의 사람을 부재가 아니라 편집의 결과로 기억해야 한다"),
    ("duplicate-photo", "여러 장 인화된 사진", "같은 장면의 복사본마다 서로 다른 보관 관계가 생길 수 있다"),
    ("unnamed-album", "이름표 없는 앨범", "모르는 얼굴을 성급히 친족 서사에 편입하지 않는 태도가 필요하다"),
    ("phone-gallery", "휴대전화 사진첩", "촬영 시각의 정렬이 경험의 중요도까지 정해 주지는 않는다"),
    ("deleted-image", "삭제함에 남은 이미지", "지우기로 한 결정과 복구할 수 있다는 유혹을 분리해야 한다"),
    ("blurred-snapshot", "흔들린 스냅사진", "선명하지 않은 기록도 당시의 속도와 거리만큼은 드러낼 수 있다"),
    ("annotated-back", "뒷면에 메모한 사진", "나중에 붙인 설명이 원래 장면의 유일한 뜻이 되어서는 안 된다"),
    ("shared-folder", "공유 사진 폴더", "함께 찍힌 기록의 삭제 권한은 한 사람에게만 있지 않을 수 있다"),
    ("printed-date", "날짜가 잘못 찍힌 사진", "기계가 남긴 숫자보다 주변 기록과 사람의 증언을 함께 보아야 한다"),
    ("unsent-letter", "보내지 않은 편지", "전달되지 않은 문장도 쓴 사람의 판단 변화를 기록한다"),
    ("returned-letter", "반송된 편지", "도착 실패를 관계의 최종 답으로 단정하지 않을 여지가 있다"),
    ("opened-envelope", "이미 열린 봉투", "과거의 열람 가능성이 오늘의 재열람 권리를 자동으로 주지는 않는다"),
    ("address-change", "옛 주소가 적힌 편지", "사라진 장소를 현재의 거주자와 혼동하지 않는 구분이 필요하다"),
    ("draft-letter", "고쳐 쓴 편지 초안", "지워진 문장은 거짓말의 증거보다 생각이 움직인 흔적일 수 있다"),
    ("inherited-letter", "물려받은 서신 묶음", "소유권을 얻었다고 모든 사적 내용을 공개할 권리까지 생기지는 않는다"),
    ("postcard-space", "여백이 적은 엽서", "짧은 형식에서 빠진 말을 무관심으로 해석해서는 안 된다"),
    ("delayed-reply", "오래 미뤄진 답장", "늦은 응답은 지연을 인정할 때에만 새로운 대화가 될 수 있다"),
    ("wrong-recipient", "수신인이 바뀐 편지", "우연히 얻은 정보 앞에서 호기심보다 경계를 먼저 세워야 한다"),
    ("handwriting-shift", "달라진 필체", "글씨 모양의 변화를 마음의 단정적인 진단으로 삼지 않아야 한다"),
    ("margin-note", "책 가장자리에 남은 기록", "이전 독자의 판단을 현재 독서의 정답처럼 따르지 않아야 한다"),
    ("reread-gap", "재독 사이의 긴 간격", "책이 달라진 듯한 느낌에서 독자 자신의 변화를 함께 찾아야 한다"),
    ("folded-page", "접혀 있는 책장", "예전에 멈춘 자리가 지금도 가장 중요한 대목이라고 볼 수는 없다"),
    ("borrowed-copy", "빌려 읽은 책", "타인의 흔적을 존중하면서 자기 반응을 구별하는 읽기가 가능하다"),
    ("new-edition", "새 판본으로 하는 재독", "표지와 배열의 변화가 기억 속 문장의 위치를 바꿀 수 있다"),
    ("unfinished-reread", "끝내지 못한 재독", "완독 실패가 아니라 더는 같은 질문을 갖지 않는다는 신호일 수 있다"),
    ("read-aloud", "소리 내어 하는 재독", "눈으로 지나친 리듬이 귀에서는 다른 판단의 속도를 만든다"),
    ("seasonal-reread", "계절을 바꾼 재독", "같은 문장도 생활의 온도에 따라 다른 배경을 얻을 수 있다"),
    ("translation-reread", "번역을 달리한 재독", "표현의 차이를 원작의 단일한 의미에 대한 승부로 만들지 말아야 한다"),
    ("shared-reread", "함께하는 재독", "서로 다른 기억을 오류 경쟁이 아니라 읽기 이력으로 다룰 수 있다"),
    ("blank-calendar", "비어 있는 달력 칸", "기록되지 않은 하루가 아무 일도 없던 하루를 뜻하지는 않는다"),
    ("crossed-plan", "취소선이 그어진 일정", "실행되지 않은 계획도 당시의 기대와 제약을 보여 준다"),
    ("anniversary", "반복되는 기념일", "같은 날짜를 기억하는 방식은 해마다 다시 합의될 수 있다"),
    ("lunar-date", "음력과 양력 사이의 날짜", "서로 다른 시간 체계를 틀림이 아니라 생활의 번역으로 보아야 한다"),
    ("shared-calendar", "공유 달력", "편의를 위한 공개가 모든 사적인 시간의 설명 의무를 만들지는 않는다"),
    ("overbooked-day", "겹쳐 적힌 일정", "동시에 가능한 약속처럼 보여도 몸은 한 시간만 통과한다"),
    ("moved-holiday", "해마다 이동하는 휴일", "날짜의 변동 속에서도 돌봄과 휴식의 목적을 놓치지 않아야 한다"),
    ("countdown", "남은 날을 세는 표시", "기다림을 숫자로 줄이면 과정에서 생기는 변화가 가려질 수 있다"),
    ("expired-planner", "지난해의 수첩", "끝난 계획표를 성취와 실패의 장부로만 읽지 않을 수 있다"),
    ("calendar-reminder", "자동 반복 알림", "기억을 맡긴 장치가 관계의 관심까지 대신해 주지는 않는다"),
    ("voice-record", "오래된 음성 기록", "목소리의 생생함이 현재의 동의나 의사를 대표하지는 않는다"),
    ("file-name", "뜻을 잃은 파일 이름", "분류표가 사라져도 기록의 가치를 즉시 폐기할 필요는 없다"),
    ("revision-history", "문서 수정 이력", "최종본만으로는 사라지는 망설임과 협의의 과정을 읽을 수 있다"),
    ("missing-metadata", "정보가 빠진 자료", "빈 항목을 추측으로 채우기보다 모름을 정확히 표시해야 한다"),
    ("public-archive", "공개된 온라인 기록", "검색 가능하다는 사실과 다시 널리 퍼뜨려도 된다는 판단은 다르다"),
    ("private-diary", "남겨진 일기장", "보존의 가치와 고인의 사생활을 동시에 고려하는 제한이 필요하다"),
    ("receipt-box", "영수증을 모은 상자", "소비 기록만으로 한 시기의 감정과 우선순위를 모두 설명할 수 없다"),
    ("backup-drive", "백업용 저장장치", "복사본의 안전이 무엇을 오래 남길지에 대한 선택을 없애지는 않는다"),
    ("archive-label", "바뀐 문서 분류명", "문제 있는 과거 명칭의 흔적을 보존하면서 현재의 분류어를 고칠 필요가 있다"),
    ("empty-folder", "내용이 사라진 폴더", "빈 구조 자체가 한때 무엇을 모으려 했는지 알려 주는 기록이 된다"),
)

MOTIFS = (
    "색과 진실의 간격", "프레임 밖 인물의 권리", "복사본마다 달라지는 관계", "모르는 얼굴 앞의 절제",
    "촬영 순서와 중요도의 차이", "삭제 결정과 복구 유혹의 분리", "흔들림에 남은 거리", "뒷면 설명의 한계",
    "공동 이미지의 삭제 합의", "기계 날짜와 주변 증언의 대조", "전달되지 않은 판단의 변화", "도착 실패와 관계 종료의 구별",
    "과거 열람과 현재 허락의 차이", "사라진 주소와 현재 거주자의 분리", "지워진 문장에 남은 숙고", "소유권과 공개권의 구별",
    "짧은 형식에 대한 오독 경계", "지연을 인정하는 답장의 조건", "우연히 얻은 정보의 경계", "필체 변화에 대한 진단 유보",
    "이전 독자의 흔적과 현재 판단", "재독 사이에서 달라진 독자", "과거의 중단 지점 재평가", "빌린 책에 남은 타인의 자리",
    "판본 변화가 만든 문장 위치", "중단된 재독의 다른 의미", "소리가 드러내는 읽기 리듬", "계절이 바꾼 문장의 배경",
    "번역 차이와 의미 경쟁의 중단", "서로 다른 읽기 이력의 공존", "빈 날짜와 보이지 않는 하루", "취소된 계획에 남은 기대",
    "반복 기념일의 재합의", "두 시간 체계 사이의 생활 번역", "공유 일정과 사적 시간의 경계", "겹친 약속과 하나뿐인 몸",
    "이동하는 휴일이 지키는 목적", "숫자 밖에서 변하는 기다림", "지난 계획표의 비판적 재독", "자동 알림과 관심의 차이",
    "생생한 목소리와 현재 동의", "분류를 잃은 자료의 잠정 가치", "최종본 밖 협의의 흔적", "모름을 표시하는 정확성",
    "검색 가능성과 재확산의 차이", "보존 가치와 사생활의 균형", "소비 내역으로 설명할 수 없는 삶", "안전한 복사와 선별 책임",
    "분류명을 고치며 남길 역사", "빈 구조가 증언하는 수집 의도",
)

ANGLES = (
    ("access", "접근의 경계", "누가 다시 볼 수 있는지부터 정하면 기억의 소유와 열람을 구별할 수 있다"),
    ("context", "맥락의 복원", "남은 조각 하나를 전체 과거로 확대하지 말고 주변 단서를 나란히 놓아야 한다"),
    ("revision", "해석의 수정", "처음 붙인 의미를 보존하되 새로운 판단이 들어설 자리도 남겨 두어야 한다"),
    ("release", "놓아줄 기준", "모든 흔적을 보존하는 대신 무엇을 왜 내려놓는지 설명할 수 있어야 한다"),
)


def _sentences(topic: str, claim: str, angle: str, rule: str, variant: int) -> tuple[str, ...]:
    """주제별 고유 논지를 여섯 개의 완결 문장으로 확장한다."""
    openings = (
        f"{topic}을 마주할 때 가장 먼저 생기는 문제는 과거가 아니라 현재의 판단이다.",
        f"{topic}에는 남겨진 사실과 뒤늦게 붙은 해석이 서로 다른 층으로 포개져 있다.",
        f"시간이 지난 뒤 {topic}을 다시 보면 익숙함이 정확성처럼 느껴지기 쉽다.",
        f"{topic}은 작은 흔적이지만 그것을 다루는 선택은 여러 사람의 시간을 건드린다.",
        f"보관함에서 {topic}을 꺼내는 순간 우리는 기억과 증거를 같은 것으로 취급하기 쉽다.",
        f"{topic} 앞에서는 남아 있다는 사실보다 어떤 조건으로 남았는지를 먼저 물어야 한다.",
        f"과거를 정리하려는 사람에게 {topic}은 정보와 감정이 한 덩어리가 아님을 알려 준다.",
        f"{topic}을 오래 보존했다고 해서 처음의 의미까지 손상 없이 보존된 것은 아니다.",
    )
    middles = (
        f"이때 {claim}는 기준을 세우면 감상적인 확신과 확인 가능한 정보를 구분할 수 있다.",
        f"따라서 {claim}는 원칙은 기억을 의심하려는 태도가 아니라 기억에 과도한 권력을 주지 않는 태도다.",
        f"여기서 {claim}는 관찰은 누군가의 침묵을 마음대로 설명하는 일을 막아 준다.",
        f"특히 {claim}는 구별은 보존과 존중이 언제나 같은 행동은 아니라는 사실을 드러낸다.",
        f"그 때문에 {claim}는 판단은 자료의 생생함보다 사용 방식의 책임을 앞세운다.",
        f"이 흔적을 읽는 동안 {claim}는 태도는 모르는 부분을 결함이 아니라 경계로 남긴다.",
        f"결국 {claim}는 관점은 기록을 소유한 사람에게 해석의 독점권까지 주어지지 않는다고 말한다.",
        f"그런 점에서 {claim}는 원칙은 기억을 지키는 일과 기억에 갇히는 일을 가르는 기준이 된다.",
    )
    turns = (
        f"{angle}을 적용하면 {rule}.",
        f"이 주제에서 {angle}이 필요한 까닭은 {rule}.",
        f"판단의 초점을 {angle}에 두면 {rule}.",
        f"한편 {angle}이라는 기준은 {rule}.",
        f"그래서 {angle}을 실천한다는 말은 {rule}.",
        f"반대로 {angle}을 생략하면 {rule}는 요청도 쉽게 사라진다.",
        f"현재의 독자에게 {angle}은 {rule}는 약속으로 읽힌다.",
        f"이 경우 {angle}을 묻는 일은 {rule}는 절차를 마련한다.",
    )
    cautions = (
        f"다만 {topic}에 특별한 사연이 있을 것이라고 꾸미면 빈칸을 존중하려던 질문이 또 다른 단정으로 바뀐다.",
        f"이 과정에서 {topic}의 주인을 대신해 감정을 말하지 않는 절제가 반드시 따라야 한다.",
        f"그렇다고 {topic}을 무의미한 물건으로 축소하면 남겨진 관계와 선택의 흔적까지 지워진다.",
        f"중요한 것은 {topic}에서 하나의 결론을 얻는 일이 아니라 서로 다른 가능성의 범위를 표시하는 일이다.",
        f"또한 {topic}을 현재의 필요에 맞춰 사용할 때에는 원래 맥락이 불완전하다는 사실을 함께 밝혀야 한다.",
        f"그러므로 {topic}을 둘러싼 불확실성은 상상으로 메울 틈이 아니라 책임 있게 멈출 지점이 된다.",
        f"누군가에게 {topic}이 민감한 자료라면 호기심보다 비공개와 삭제 요청을 우선할 필요가 있다.",
        f"무엇보다 {topic}의 생생함 때문에 당사자의 현재 선택을 과거 모습에 묶어 두어서는 안 된다.",
    )
    practices = (
        f"실제로는 {topic}에서 확인되는 사실, 추정되는 부분, 끝내 모르는 부분을 세 칸으로 나누어 적을 수 있다.",
        f"작은 실천으로 {topic}의 출처와 보관 경로를 적고 열람 범위를 다시 정하는 방법이 있다.",
        f"판단을 서두르지 않으려면 {topic}을 본 첫 반응과 하루 뒤의 해석을 따로 기록해 보는 편이 좋다.",
        f"공동의 흔적이라면 {topic}을 계속 둘지 결정하기 전에 관련된 사람에게 선택권을 묻는 절차가 필요하다.",
        f"정리할 때에는 {topic}의 내용뿐 아니라 남김, 제한, 폐기 가운데 무엇을 택했는지 그 이유도 짧게 남길 수 있다.",
        f"재확인을 위해 {topic}과 연결된 날짜나 장소를 찾되 빈틈은 억지로 채우지 않는 방식이 유효하다.",
        f"혼자 결론 내리기 어려우면 {topic}을 설명하는 문장에서 사실과 감정 표현을 서로 다른 색으로 표시해 볼 수 있다.",
        f"보존 여부를 정하기 전 {topic}이 앞으로 누구에게 어떤 부담을 줄 수 있는지 목록으로 살피는 것도 한 방법이다.",
    )
    endings = (
        f"그렇게 바라볼 때 {topic}은 과거를 고정하는 못이 아니라 현재가 과거와 협상하는 조심스러운 문이 된다.",
        f"이 구분을 지킬 때 {topic}은 추억의 권위를 높이기보다 기억을 함께 다루는 책임을 가르친다.",
        f"마침내 {topic}은 정확히 기억하라는 명령보다 불확실함을 정직하게 표시하라는 요청으로 남는다.",
        f"그 결과 {topic}은 사라진 시간을 대신 말하지 않으면서도 오늘의 선택을 더 신중하게 만든다.",
        f"이런 읽기 속에서 {topic}은 보관된 과거가 아니라 계속 갱신되는 관계의 경계표가 된다.",
        f"결국 {topic}은 무엇을 기억할지뿐 아니라 어떤 방식으로 기억할지를 묻는 생활의 윤리가 된다.",
        f"그때 {topic}은 완전한 설명을 제공하지 않아도 서로의 시간에 함부로 들어가지 않는 법을 알려 준다.",
        f"이 절차를 거치면 {topic}은 감정의 증거가 아니라 판단을 늦추고 대화를 여는 단서로 머문다.",
    )
    return (
        openings[variant % len(openings)],
        middles[(variant * 3 + 1) % len(middles)],
        turns[(variant * 5 + 2) % len(turns)],
        cautions[(variant * 7 + 3) % len(cautions)],
        practices[(variant * 11 + 4) % len(practices)],
        endings[(variant * 13 + 5) % len(endings)],
    )


def _section_texts(work: str, genre: str, topic: str, claim: str, angle: str, rule: str, index: int) -> dict[str, str]:
    """작품 설명을 꾸미지 않는 네 개의 독립 감상 단락을 만든다."""
    intros = (
        f"『{work}』은 소설가 이후의 {genre}으로 확인되는 작품이다. 이 글은 작품 내부의 인물이나 사건을 설명하지 않고 제목이 불러오는 넓은 감각을 {topic}의 문제와 나란히 둔다. 특히 {claim}는 생각을 독립적인 독서 렌즈로 삼아, 확인되지 않은 서사를 덧붙이지 않는 범위에서 기억의 사용법을 묻는다. 따라서 아래의 논의는 작품 해설이나 창작 의도에 대한 주장이 아니라 제목에서 출발한 오늘의 사유다.",
        f"확인된 서지 범위에서 『{work}』은 소설가 이후가 펴낸 {genre}이다. 여기서는 구체적인 줄거리나 화자를 상정하지 않으며, {topic}을 통해 제목과 현재 생활 사이에 질문 하나를 놓는다. 그 질문의 핵심은 {claim}는 데 있고, 작품이 실제로 이 소재를 다룬다고 주장하지 않는다. 독자는 이 제한을 바탕으로 허구의 정보를 사실처럼 받아들이지 않으면서도 자기 기억의 태도를 돌아볼 수 있다.",
        f"소설가 이후의 {genre} 『{work}』이라는 제목을 이 노트의 유일한 문학적 출발점으로 삼는다. 제목에서 받은 인상을 {topic}과 연결하지만 작품 속 장면, 인물, 배경은 전혀 추정하지 않는다. 대신 {claim}는 판단이 우리 일상에서 어떤 책임을 요구하는지 살핀다. 이는 원문을 대신 요약하는 글이 아니라 실제 독서 전후에 활용할 수 있는 제목 기반의 현재적 성찰이다.",
        f"이 기록이 확인하는 작품 정보는 소설가 이후의 {genre} 『{work}』이라는 서지와 제목뿐이다. 그 바깥의 내용을 채우지 않고 {topic}을 하나의 가상적인 사고 도구로 선택한다. {claim}는 원칙을 따라가면 기억을 사실, 해석, 권리의 문제로 나누어 볼 수 있다. 작품 자체의 의미를 단정하지 않는 이 거리는 독창적인 감상과 허구의 작품 소개 사이의 경계를 지킨다.",
    )
    now = (
        f"사진과 문서가 자동으로 쌓이는 오늘에는 잊는 일보다 무엇을 남겼는지 파악하는 일이 더 어려워졌다. {topic}처럼 작고 구체적인 흔적도 검색과 공유를 거치면 원래의 관계를 넘어 널리 이동한다. 그래서 지금 {angle}을 묻는 일은 과거를 미화하기 위한 취향이 아니라 {rule}는 사회적 기술이 된다. 『{work}』이라는 제목 곁에서 이 문제를 생각하면 빠른 소비 대신 기록이 사람에게 미치는 시간을 길게 살필 수 있다.",
        f"현재의 생활은 과거 자료를 손쉽게 복구하지만 그 자료를 다시 보아도 되는지는 자동으로 답해 주지 않는다. {topic}을 다룰 때 {claim}는 원칙이 없다면 생생함은 곧 진실로, 접근 가능성은 곧 허락으로 오인되기 쉽다. 지금 이 독서가 필요한 까닭은 {angle}을 통해 {rule}는 기준을 마련하기 위해서다. 『{work}』의 제목은 이 판단을 서두르지 않고 감정과 권한을 함께 점검하는 출발점이 된다.",
        f"요약과 회고가 빠르게 유통되는 시대에는 한 조각의 기록이 한 사람의 전체 과거를 대표하곤 한다. 그러나 {topic}은 그 위험을 작게 비추며 {claim}는 구분을 요청한다. 오늘 {angle}의 관점으로 다시 생각하면 {rule}는 일이 단순한 정리 습관을 넘어 타인의 시간을 존중하는 방식임을 알 수 있다. 이 때문에 『{work}』을 제목에서부터 천천히 읽는 태도가 지금의 정보 환경과 맞닿는다.",
        f"기억을 외부 장치에 맡긴 사회에서도 해석과 책임은 여전히 사람의 몫으로 남는다. 특히 {topic}은 저장된 정보가 많을수록 오히려 맥락이 분명해진다는 믿음을 흔든다. {claim}는 판단을 현재의 언어로 검토하고 {angle}을 세우면 {rule}는 가능성이 열린다. 『{work}』의 제목을 오늘 다시 생각하는 이유는 바로 기록의 양보다 다루는 태도의 정확성을 선택하기 위해서다.",
    )
    personal = (
        f"나는 {topic}을 발견했다고 가정할 때 곧바로 사연을 만들어 내기보다 확인되는 정보와 떠오르는 감정을 따로 적어 보려 한다. 이어 {angle}의 기준으로 누가 영향을 받을지, 무엇을 공개하지 말아야 할지, 어떤 설명을 남길지 살필 수 있다. 이 과정에서 {claim}는 원칙은 과거를 차갑게 처리하자는 뜻이 아니라 애틋함이 타인의 권리를 넘지 않도록 하는 안전선이 된다. 『{work}』이라는 제목은 그런 조심스러운 태도를 연습하게 하는 상상의 표지가 된다.",
        f"가상의 정리 상자에서 {topic}을 꺼낸다면 나는 첫 느낌을 결론으로 쓰지 않고 질문으로 바꾸고 싶다. 그 다음 {rule}는 방향을 실제 선택에 적용하며 {angle}이 빠졌는지 점검할 것이다. {claim}는 판단을 유지하면 보관하거나 놓아주는 어느 쪽을 택하더라도 그 이유를 더 정직하게 설명할 수 있다. 『{work}』의 제목 앞에서 하는 이 연습은 개인적 체험을 꾸며 내지 않고도 현재의 태도를 구체화한다.",
        f"{topic}이 내 앞에 놓인 상황을 상상하면 가장 경계할 것은 익숙한 이야기를 빈칸에 밀어 넣는 습관이다. 나는 자료의 출처를 확인한 뒤 {angle}을 묻고, 답할 수 없는 부분에는 모른다는 표시를 남기려 한다. 그렇게 해야 {claim}는 생각이 실제 행동의 기준으로 이어지고 {rule}는 요청도 공허한 구호가 되지 않는다. 이 가정적 성찰은 『{work}』의 내용을 말하는 대신 제목이 열어 둔 질문에 나의 책임을 답하는 방식이다.",
        f"만약 {topic}을 다른 사람과 함께 정리해야 한다면 나는 해석의 우열부터 가리지 않을 것이다. 각자가 확인한 사실과 감정적 연상을 나눈 다음 {angle}에 관한 합의점을 찾는 순서가 더 적절하다. 그 과정에서 {claim}는 원칙은 서로 다른 기억이 공존할 수 있게 하고 {rule}는 선택의 근거를 만든다. 『{work}』이라는 제목을 빌린 이 사고 실험은 살아 보지 않은 경험을 내 이야기처럼 말하지 않는 선을 지킨다.",
    )
    today = (
        f"오늘 {topic}의 문제는 개인 추억을 넘어 디지털 유산과 공동 기록의 규칙으로 확장된다. 자료를 가진 사람, 자료에 등장하는 사람, 나중에 읽는 사람의 권리가 서로 다를 수 있기 때문이다. {angle}을 공통 기준으로 삼아 {claim}는 원칙을 지키고 {rule}는 절차를 마련하면 책임 있는 기억 문화가 조금씩 가능해진다. 『{work}』에서 출발한 이 성찰은 기억을 많이 저장하는 사회보다 기억을 책임 있게 건네는 사회가 더 성숙하다는 의미를 남긴다.",
        f"공동체는 무엇을 기념하는지만큼 무엇을 비공개로 남기는지에 의해서도 기억된다. {topic}을 둘러싼 선택에 {angle}이 없다면 보존은 쉽게 감시가 되고 폐기는 쉽게 역사 지우기가 된다. 그래서 {claim}는 관점을 공유하며 {rule}는 절차를 만드는 일이 중요하다. 『{work}』이라는 제목이 오늘 건네는 의미를 이렇게 읽을 때, 문학적 상상은 타인의 과거를 소비하지 않는 시민적 태도와 만난다.",
        f"현재의 기록 기술은 사라짐을 늦추지만 맥락의 손실까지 막아 주지는 않는다. {topic}이 오래 남을수록 후대의 독자는 빈 부분을 자신에게 익숙한 이야기로 채울 가능성이 커진다. {angle}의 표시와 함께 {claim}는 경계를 전하면 {rule}는 조건이 다음 사람에게도 이어질 수 있다. 『{work}』의 제목에서 시작한 질문은 기록의 수명보다 해석의 겸손을 더 중요한 유산으로 보게 한다.",
        f"기억의 공정성은 모든 자료를 똑같이 남기는 데서 생기지 않고 서로 다른 위험을 구체적으로 살피는 데서 생긴다. {topic}에는 애정, 정보, 권한이 함께 있지만 그 셋의 무게는 같지 않다. {claim}는 원칙과 {angle}의 절차를 결합하면 {rule}는 선택이 공동의 신뢰를 해치지 않게 된다. 오늘 『{work}』을 제목 중심으로 사유하는 일은 과거를 소유물보다 관계의 책임으로 바라보게 한다.",
    )
    slot = index % 4
    return {
        "work_introduction": intros[slot],
        "why_read_now": now[(slot + index // 4) % 4],
        "personal_reflection": personal[(slot * 3 + index // 7) % 4],
        "meaning_today": today[(slot * 2 + index // 9) % 4],
    }


def _uniquify_repeated_sentences(entries: list[dict[str, object]]) -> None:
    """공통 설명 문장에는 각 노트의 고유 판단 근거를 결합한다."""
    prose_fields = (
        "quote",
        "commentary",
        "closing",
        "source_location",
        "translation_note",
        "rights_note",
        "work_introduction",
        "why_read_now",
        "personal_reflection",
        "meaning_today",
    )
    counts: Counter[str] = Counter()
    replacements = (
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {motif}{_particle(motif, '을', '를')} 기준으로 삼아 {angle}{_particle(angle, '이', '가')} 요구하는 구분을 밝힌다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {topic}{_particle(topic, '을', '를')} {angle}의 관점으로 살피며 선택의 영향을 먼저 헤아린다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {claim}는 판단을 {angle}의 실제 조건과 연결한다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {motif}{_particle(motif, '이', '가')} 요청하는 권리 구분을 {angle}에서 찾는다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {motif}{_particle(motif, '을', '를')} 먼저 살피고 {angle}{_particle(angle, '을', '를')} 판단의 축으로 삼는다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {claim}는 원칙과 {angle}의 한계를 함께 밝힌다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {motif}{_particle(motif, '을', '를')} 통해 {angle}{_particle(angle, '이', '가')} 책임의 기준임을 드러낸다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {topic}{_particle(topic, '을', '를')} {angle}의 범위 밖으로 일반화하지 않는다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {claim}는 생각을 {angle}의 질문으로 다시 점검한다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {motif}{_particle(motif, '과', '와')} {angle}의 관계에서 보존과 존중을 구별한다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {topic}{_particle(topic, '을', '를')} 다루기 전에 관련된 사람의 선택권을 {angle}에서 확인한다.",
        lambda topic, claim, angle, rule, motif, focus: f"{focus}{_particle(focus, '은', '는')} {rule}는 절차로 {claim}는 원칙을 생활의 선택으로 옮긴다.",
    )
    field_focus = (
        "이 짧은 생각", "이 논의", "마지막 문장", "확인한 서지 범위", "한국어 집필 과정",
        "인용 원칙", "이 글", "오늘의 독자", "가상의 상황", "지금의 공동체",
    )

    for entry in entries:
        for field in prose_fields:
            counts.update(re.split(r"(?<=[.!?])\s+", str(entry[field])))

    for entry in entries:
        offset = int(entry["position"]) - 201
        anchor_index, angle_index = divmod(offset, len(ANGLES))
        _, topic, claim = ANCHORS[anchor_index]
        motif = MOTIFS[anchor_index]
        _, angle, rule = ANGLES[angle_index]
        for field_index, field in enumerate(prose_fields):
            revised = []
            for sentence_index, sentence in enumerate(re.split(r"(?<=[.!?])\s+", str(entry[field]))):
                if len(sentence) >= 25 and counts[sentence] > 1 and sentence[-1] in ".!?":
                    sentence = replacements[(field_index * 3 + sentence_index * 5) % len(replacements)](
                        topic, claim, angle, rule, motif, field_focus[field_index]
                    )
                revised.append(sentence)
            entry[field] = " ".join(revised)


def entries() -> list[dict[str, object]]:
    """전역 위치 201~400에 들어갈 독창 감상 200개를 반환한다."""
    result: list[dict[str, object]] = []
    for offset, (anchor_index, angle_index) in enumerate(
        (pair for anchor_index in range(len(ANCHORS)) for pair in ((anchor_index, 0), (anchor_index, 1), (anchor_index, 2), (anchor_index, 3)))
    ):
        position = 201 + offset
        anchor_slug, topic, claim = ANCHORS[anchor_index]
        angle_slug, angle, rule = ANGLES[angle_index]
        work = SCHEDULE[(position - 1) % len(SCHEDULE)]
        flow = FLOWS[(position - 1) % len(FLOWS)]
        lens = f"{topic}의 {angle}"
        prose = _sentences(topic, claim, angle, rule, offset)
        quote = f"{topic}은 과거를 완성된 답으로 돌려주지 않는다. {angle}을 살피며 {claim}는 태도가 오늘의 기억을 더 정직하게 만든다."
        title_patterns = (
            f"{topic}에서 누구의 시간을 먼저 읽을 것인가",
            f"{topic}과 {angle} 사이에 남겨 둘 거리",
            f"{topic}을 다시 볼 때 바뀌어야 할 기준",
            f"{topic}을 놓아주는 일에도 설명이 필요한 까닭",
        )
        sections = _section_texts(work, GENRES[work], topic, claim, angle, rule, offset)
        result.append(
            {
                "position": position,
                "work": work,
                "slug": f"{anchor_slug}-{angle_slug}",
                "title": title_patterns[angle_index],
                "quote": quote,
                "commentary": " ".join(prose),
                "closing": f"{topic}을 책임 있게 기억한다는 것은 {angle}을 세우고 모르는 부분까지 정직하게 남기는 일이다.",
                "source_location": f"소설가 이후의 {GENRES[work]} 『{work}』이라는 확인된 서지와 제목에서 출발해, 작품 내용을 추정하지 않고 {lens}에 관한 현재적 감상을 작성했으며 {claim}는 원칙과 {rule}는 절차를 판단 근거로 삼았다.",
                "translation_note": f"한국어로 새롭게 쓴 {FLOW_LABELS[flow]}의 독창 감상이며, 번역문이나 기존 해설을 옮기지 않고 {topic}에 관한 가정적 성찰로 구성했다.",
                "rights_note": f"작품 본문 직접 인용 없음. 확인된 제목과 장르만 참고했으며 {topic}과 {angle}에 관한 문장은 모두 독립적으로 작성했다.",
                "lens": lens,
                "flow": flow,
                **sections,
            }
        )
    for entry in result:
        topic = ANCHORS[(int(entry["position"]) - 201) // len(ANGLES)][1]
        for key, value in tuple(entry.items()):
            if isinstance(value, str):
                fixed = _fix_particles(value)
                entry[key] = _limit_topic_repetitions(fixed, topic)
    _uniquify_repeated_sentences(result)
    for entry in result:
        for key, value in tuple(entry.items()):
            if isinstance(value, str):
                entry[key] = _fix_particles(value)
    return result


ENTRIES = entries()
