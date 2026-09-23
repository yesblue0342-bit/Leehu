"""2026-09-23 문학 노트 원고 D: 전역 위치 601~800."""

from __future__ import annotations


WORKS = (
    ("연(戀)", "소설"),
    ("데자뷔", "소설"),
    ("소나기", "소설"),
    ("환상", "시집"),
    ("별이 빛나는 밤에", "시집"),
    ("Fantasy", "시집"),
)

WORK_SCHEDULE = tuple(
    work
    for turn in range(33)
    for work, count in zip(WORKS, (15, 13, 13, 13, 13, 33))
    if turn < count
)

FLOWS = ("question", "contrast", "observation", "thought_experiment", "practice")

# 각 씨앗은 독립된 창작 독서 문제를 이룬다.
# slug, 주제명, 핵심 대상, 긴장, 감각 이미지, 구체적 독서 행위
SEEDS = (
    ("blank-margin", "빈 여백의 상상", "적히지 않은 부분", "보충과 절제", "연필이 멈춘 흰 가장자리", "떠오른 가능성 셋 가운데 근거가 약한 둘을 지우기"),
    ("word-temperature", "단어의 온도", "같은 뜻을 가진 말의 체감", "정확성과 온기", "손바닥에 남는 미지근한 음절", "유의어를 바꾸어 읽고 정서의 차이를 적기"),
    ("breath-unit", "숨의 단위", "한 문장을 나누는 호흡", "속도와 이해", "쉼표 앞에서 가늘어지는 숨", "소리 내어 읽으며 편안한 멈춤을 표시하기"),
    ("translation-question", "번역을 향한 독자의 질문", "옮겨진 말 뒤의 선택", "신뢰와 의문", "두 언어 사이에 놓인 작은 물음표", "낯선 표현을 오류로 단정하기 전에 가능한 선택지를 묻기"),
    ("line-drawing", "선으로 읽는 문장", "문장의 진행 방향", "설명과 형상", "종이 위에서 굽어지는 한 줄", "문단의 움직임을 직선과 곡선으로 그리기"),
    ("low-sound", "낮은 소리의 자리", "작게 들리는 표현", "강조와 경청", "큰 박수 뒤에 남는 낮은 울림", "눈에 덜 띈 낱말 하나를 골라 천천히 발음하기"),
    ("misreading-door", "오독이 여는 문", "처음 잘못 짚은 의미", "수정과 발견", "잘못 연 문틈으로 들어온 빛", "첫 해석과 다시 읽은 해석의 차이를 나란히 쓰기"),
    ("metaphor-distance", "은유의 거리", "서로 먼 두 대상의 연결", "비약과 설득", "멀리 떨어진 점을 잇는 실", "닮은 점뿐 아니라 닮지 않은 점도 함께 표시하기"),
    ("punctuation-stage", "문장부호의 무대", "말 사이의 작은 표지", "침묵과 발화", "마침표 뒤에 잠깐 꺼지는 조명", "부호를 달리 놓아 목소리의 변화를 비교하기"),
    ("color-vocabulary", "색채 어휘의 경계", "색을 부르는 이름", "분류와 감각", "이름 붙기 전의 흐린 빛깔", "한 색을 여러 생활어로 묘사해 보기"),
    ("echo-reading", "메아리 독서", "읽고 난 뒤 되돌아오는 말", "반복과 변화", "벽을 돌아 조금 낮아진 목소리", "마지막에 기억난 표현과 처음의 인상을 대조하기"),
    ("rhythm-stumble", "리듬의 걸림", "매끄럽지 않은 박자", "유창함과 주의", "계단 하나에서 달라지는 발걸음", "걸리는 구절을 건너뛰지 않고 세 번 다른 속도로 읽기"),
    ("title-sketch", "제목의 스케치", "제목이 만드는 첫 윤곽", "기대와 유보", "아직 색칠되지 않은 밑그림", "본문을 상상하기보다 제목이 낳은 질문만 그리기"),
    ("silence-grammar", "침묵의 문법", "말하지 않는 간격", "공백과 의미", "대화 사이에 놓인 투명한 괄호", "쉼이 생긴 자리에 성급한 해석 대신 질문을 남기기"),
    ("voice-texture", "목소리의 질감", "글에서 느껴지는 발화 방식", "선명함과 다성성", "거친 종이를 스치는 낮은 음", "한 문장을 속삭임과 평서로 번갈아 읽기"),
    ("reader-caption", "독자의 임시 자막", "이해를 돕는 자기 말", "요약과 축소", "문장 아래 잠깐 켜지는 설명", "자기 요약에 빠진 뉘앙스를 다시 덧붙이기"),
    ("image-sequence", "이미지의 순서", "떠오르는 장면들의 배열", "연속과 도약", "서로 떨어진 세 장의 그림", "이미지를 화살표로 잇되 빈 구간은 비워 두기"),
    ("consonant-sound", "자음의 빗소리", "반복되는 자음의 울림", "뜻과 소리", "창을 두드리는 짧은 음절", "자음이 되풀이되는 부분을 입으로 확인하기"),
    ("vowel-light", "모음의 밝기", "입이 열리는 소리의 폭", "음색과 정서", "입안에서 넓어지는 밝은 공기", "모음이 바뀔 때 문장의 표정을 관찰하기"),
    ("untranslatable-space", "옮기기 어려운 여백", "한 단어로 맞지 않는 의미", "등가와 차이", "사전의 두 항목 사이 빈 칸", "하나의 정답 대신 설명형 번역 질문을 만들기"),
    ("eraser-reading", "지우개 독서", "처음 세운 해석", "확신과 개정", "흑연 자국이 옅어진 종이", "근거가 없는 추측에 줄을 긋고 남은 사실을 읽기"),
    ("page-choreography", "페이지의 안무", "시선이 이동하는 경로", "배치와 속도", "줄 사이를 건너는 눈의 발걸음", "시선의 이동을 번호 없이 화살표로 기록하기"),
    ("whisper-scale", "속삭임의 크기", "작은 목소리가 지닌 힘", "세기와 지속", "귀 가까이 오래 남는 가는 진동", "강조하지 않아도 남는 표현을 따로 모으기"),
    ("creative-rereading", "창조적 재독", "두 번째 읽기의 새 조건", "기억과 갱신", "접힌 자국 위에 놓인 새 책갈피", "첫 독서의 결론을 가리고 질문부터 다시 만들기"),
    ("question-mark-map", "물음표 지도", "읽는 동안 생기는 의문", "해결과 보존", "종이 곳곳에 찍힌 작은 표지", "답할 질문과 오래 둘 질문을 다른 모양으로 표시하기"),
    ("sentence-shadow", "문장의 그림자", "명시된 말 뒤의 영향", "표현과 파장", "글자 옆으로 길어진 저녁 그림자", "문장이 누구에게 어떻게 들릴지 두 방향으로 써 보기"),
    ("tempo-switch", "독서 속도 전환", "빠르게 읽을 곳과 머물 곳", "효율과 음미", "빠른 길 옆의 작은 벤치", "같은 문단을 훑기와 낭독으로 나누어 경험하기"),
    ("soundless-music", "소리 없는 음악", "묵독 속의 박자", "내면음과 침묵", "귀가 아닌 눈에서 시작되는 박동", "행갈이마다 손가락으로 조용히 박을 짚기"),
    ("doodle-argument", "낙서의 논증", "그림으로 정리한 생각", "놀이와 정확성", "여백에 겹쳐진 원과 화살표", "주장과 근거를 간단한 도형으로 분리하기"),
    ("synonym-fork", "유의어의 갈림길", "비슷하지만 같지 않은 말", "선택과 손실", "두 방향으로 갈라지는 표지판", "바꿀 수 있는 말과 바꾸면 잃는 뜻을 적기"),
    ("reader-orchestra", "독자 안의 합주", "서로 다른 해석의 목소리", "통일과 공존", "한 박자 안에서 겹치는 여러 악기", "찬성하는 읽기와 의심하는 읽기를 번갈아 쓰기"),
    ("unfinished-image", "미완의 이미지", "끝까지 채워지지 않은 형상", "완성욕과 개방성", "윤곽만 남은 달의 드로잉", "비어 있는 부분을 결함이라 부르기 전에 역할을 묻기"),
    ("accent-choice", "강세의 선택", "어느 낱말에 힘을 둘지", "의도와 수용", "한 음절 위에 내려앉는 작은 추", "강세 위치를 바꾸어 의미의 중심을 비교하기"),
    ("translation-margin", "번역문 곁의 여백 질문", "독자가 덧붙이는 확인", "판단과 탐색", "옮긴 문장 옆의 가느다란 빈 줄", "왜 이 표현일지 세 가지 가능성을 메모하기"),
    ("imaginary-camera", "상상의 카메라", "독서 중 선택되는 시점", "초점과 배제", "한 곳만 밝히는 조용한 렌즈", "보이는 것 밖에 무엇이 남는지 프레임을 넓혀 그리기"),
    ("onomatopoeia-body", "의성어의 몸", "소리가 몸에 주는 반응", "모방과 체감", "가슴과 혀에서 튀는 짧은 파동", "의성어를 발음하며 몸의 긴장 변화를 살피기"),
    ("line-break-bridge", "행갈이의 다리", "끊어진 줄 사이의 연결", "단절과 지속", "두 줄 사이에 놓인 가느다란 다리", "행 끝과 다음 행 첫말을 한 쌍으로 묶어 보기"),
    ("reader-collage", "독자 콜라주", "서로 다른 인상의 조합", "파편과 구성", "종이 조각 사이로 보이는 바탕", "핵심어와 색과 도형을 한 면에 겹쳐 배치하기"),
    ("ambiguity-hum", "모호함의 잔향", "확정되지 않는 뜻", "불편과 가능성", "문을 닫은 뒤에도 남는 낮은 웅웅거림", "둘 이상의 해석을 서둘러 하나로 합치지 않기"),
    ("dictionary-detour", "사전의 우회로", "정의와 실제 문맥", "지식과 사용", "곧은 길 옆으로 난 단어의 샛길", "사전 뜻을 확인한 뒤 문맥이 더한 결을 적기"),
    ("memory-illustration", "기억의 삽화", "읽은 뒤 남은 시각 흔적", "회상과 왜곡", "책을 덮은 뒤 떠오른 작은 그림", "기억으로 그린 뒤 글을 다시 보며 차이를 표시하기"),
    ("cadence-balance", "운율의 균형", "반복과 변주의 비율", "안정과 놀람", "같은 파도 사이에 섞인 다른 높이", "되풀이되는 박자와 어긋나는 지점을 함께 세기"),
    ("pronoun-window", "대명사의 창", "가리키는 대상의 범위", "친밀함과 불확실성", "누군가를 비추지만 이름은 없는 창", "대명사가 열어 둔 후보를 문맥 안에서만 찾아보기"),
    ("fontless-emphasis", "글꼴 없는 강조", "배치와 반복이 만드는 무게", "장식과 구조", "색 없이도 도드라지는 문장", "반복 위치와 문장 길이로 강조를 확인하기"),
    ("reader-soundtrack", "독자의 배경음", "읽을 때 마음속에 생기는 소리", "집중과 간섭", "페이지 뒤에서 흐르는 느린 선율", "상상한 소리가 문장 근거인지 개인 연상인지 구분하기"),
    ("negative-space", "그리지 않은 형태", "비워 둔 공간이 만든 윤곽", "부재와 구성", "검은 선 사이에서 드러난 흰 모양", "언급되지 않은 것을 사실처럼 채우지 않고 경계를 따라가기"),
    ("homonym-mirror", "동음의 거울", "같은 소리에 담긴 다른 뜻", "유사와 분기", "한 소리를 되비추는 두 표면", "가능한 뜻을 늘어놓고 문맥의 제한을 확인하기"),
    ("pause-ethics", "멈춤의 윤리", "해석을 보류하는 시간", "반응과 숙고", "대답 직전에 내려놓은 연필", "불편한 구절에 즉답 대신 잠정 표시를 남기기"),
    ("texture-sketch", "질감의 스케치", "말이 주는 촉각적 인상", "개념과 감각", "거친 선과 매끈한 면의 대비", "추상어를 선의 굵기와 방향으로 바꾸어 보기"),
    ("chorus-reading", "후렴의 독서", "되풀이가 만드는 공동 감각", "개별성과 합류", "여러 목소리가 만나는 짧은 구절", "반복되는 핵심을 읽되 매번 달라진 주변을 찾기"),
)

MODES = (
    ("경계", "어디까지 허용할지", "읽기 전", "조건을 먼저 세우는"),
    ("관계", "다른 감각과 어떻게 만날지", "읽는 동안", "연결을 시험하는"),
    ("개정", "처음 판단을 어떻게 고칠지", "읽은 뒤", "흔적을 다시 살피는"),
    ("실천", "다음 읽기에 무엇을 남길지", "다시 펼칠 때", "작은 행동으로 옮기는"),
)


def _has_batchim(value: str) -> bool:
    """Return whether the final Korean syllable has a closing consonant."""
    code = ord(value[-1])
    return 0xAC00 <= code <= 0xD7A3 and (code - 0xAC00) % 28 != 0


def _object(value: str) -> str:
    return f"{value}{'을' if _has_batchim(value) else '를'}"


def _topic(value: str) -> str:
    return f"{value}{'은' if _has_batchim(value) else '는'}"


def _nominative(value: str) -> str:
    return f"{value}{'이' if _has_batchim(value) else '가'}"


def _label(value: str) -> str:
    return f"{value}{'이라는' if _has_batchim(value) else '라는'}"


def _and(value: str) -> str:
    return f"{value}{'과' if _has_batchim(value) else '와'}"


def _mode_seed(seed: tuple[str, ...], mode_index: int) -> tuple[str, ...]:
    """Give each angle its own subject, tension, image, and reading practice."""
    slug, theme, subject, tension, image, action = seed
    if mode_index == 0:
        return (
            slug,
            f"{theme}에 적용하는 해석의 경계",
            f"{_object(subject)} 문장 근거로 인정할 조건",
            tension,
            f"{image} 둘레에 가는 테두리를 그은 모습",
            f"{_object(action)} 마친 뒤 근거가 남은 부분에 선 긋기",
        )
    if mode_index == 1:
        return (
            slug,
            f"{_and(theme)} 다른 감각의 연결",
            f"{_nominative(subject)} 시각·청각·촉각 사이에서 달라지는 방식",
            "익숙한 감각과 새로 발견한 감각",
            f"{image} 옆에 다른 색의 선이 겹친 장면",
            f"{_object(action)} 마친 뒤 다른 감각의 표현 하나를 나란히 놓기",
        )
    if mode_index == 2:
        return (
            slug,
            f"{theme}에 남은 수정의 흔적",
            f"{subject}에 대한 첫 판단과 다시 읽은 판단의 차이",
            "처음의 확신과 수정할 용기",
            f"{image} 위에 반투명 종이를 덧댄 모습",
            f"{_object(action)} 마친 뒤 첫 메모와 달라진 이유를 대조하기",
        )
    return (
        slug,
        f"{theme}에서 다음 읽기로 이어지는 습관",
        f"{_object(subject)} 다음 읽기에도 반복하는 방법",
        "즉흥적인 발견과 지속 가능한 기록",
        f"{image} 곁에 다음 쪽을 위한 책갈피가 놓인 장면",
        f"{_object(action)} 마친 뒤 다음에도 반복할 한 줄 규칙을 남기기",
    )


def _entry(position: int, seed: tuple[str, ...], mode: tuple[str, ...]) -> dict[str, object]:
    mode_index = (position - 601) // len(SEEDS)
    slug, theme, subject, tension, image, action = _mode_seed(seed, mode_index)
    mode_slug = ("boundary", "relation", "revision", "practice")[mode_index]
    mode_name, mode_question, reading_time, mode_method = mode
    work, genre = WORK_SCHEDULE[(position - 1) % len(WORK_SCHEDULE)]
    flow = FLOWS[(position - 1) % len(FLOWS)]
    lens = f"{mode_name}: {theme}"
    title = f"{theme}, {mode_question}"
    theme_object = _object(theme)
    theme_topic = _topic(theme)
    theme_label = _label(theme)
    subject_object = _object(subject)
    subject_nominative = _nominative(subject)
    image_object = _object(image)
    image_label = _label(image)
    tension_object = _object(tension)
    mode_object = _object(mode_name)
    action_object = _object(action)
    if mode_index == 0:
        commentary_claim = (
            f"{image_label} 비유는 작품에 적힌 단서와 독자가 보탠 추측 사이에 "
            f"선을 그어야 {tension_object} 함께 지킬 수 있음을 보여 준다."
        )
        commentary_implication = (
            f"{subject_object} 판단할 때 근거를 먼저 표시하면 상상은 금지되는 것이 아니라 "
            f"어디서 시작되었는지 밝힌 채 더 책임 있게 움직인다."
        )
        personal_claim = (
            f"나는 {theme_object} 검토하며 확인한 말과 추정한 말을 두 칸에 나누어 적고, "
            f"그 경계가 흐린 부분만 다시 질문하고 싶다."
        )
        today_claim = (
            f"맥락에서 잘린 문장이 빠르게 퍼지는 환경에서 {theme_topic} 사실과 상상을 "
            f"한 문장 안에서 구분하게 하는 작은 안전장치가 된다."
        )
        today_action = (
            f"{action_object} 독서 과정에서 직접 시도하면 서로 다른 독자도 결론보다 "
            f"어떤 근거를 공유하는지부터 비교할 수 있다."
        )
    elif mode_index == 1:
        commentary_claim = (
            f"{image_label} 비유는 같은 표현도 소리, 선, 촉감으로 옮길 때 "
            f"다른 면을 드러내므로 {tension} 가운데 하나를 표준으로 고정할 수 없음을 보여 준다."
        )
        commentary_implication = (
            f"{subject_object} 한 감각의 번역으로만 묶지 않으면 독자는 서로 다른 반응을 "
            f"오답으로 밀어내지 않고 연결의 자료로 사용할 수 있다."
        )
        personal_claim = (
            f"나는 {theme_object} 살피며 머릿속 장면을 소리나 선으로 한 번 바꾸어 보고, "
            f"매체가 달라질 때 새로 보이는 요소를 기록하고 싶다."
        )
        today_claim = (
            f"읽는 방식과 감각 조건이 다양한 오늘, {theme_topic} 한 가지 표현 방식만으로 "
            f"이해의 깊이를 평가하지 않게 하는 포용의 기준이 된다."
        )
        today_action = (
            f"{action_object} 함께 시도한 독자들은 누가 맞는지만 다투기보다 각 감각이 "
            f"포착한 정보를 합쳐 더 넓은 질문을 만들 수 있다."
        )
    elif mode_index == 2:
        commentary_claim = (
            f"{image_label} 비유는 처음 읽은 흔적을 지우지 않은 채 새 해석을 "
            f"겹쳐 보아야 {tension} 사이의 변화 이유가 드러남을 보여 준다."
        )
        commentary_implication = (
            f"{subject_object} 대조하면 판단을 바꾼 사실보다 어떤 문장 근거가 수정에 "
            f"기여했는지를 설명할 수 있어 개정이 변덕으로 오해되지 않는다."
        )
        personal_claim = (
            f"나는 {theme_object} 돌아보며 첫 메모를 삭제하지 않고 옆에 새 판단과 이유를 "
            f"덧붙여, 생각이 바뀐 경로 자체를 독서 기록으로 남기고 싶다."
        )
        today_claim = (
            f"입장을 빠르게 고정하는 대화 환경에서 {theme_topic} 오류를 숨기는 대신 근거를 "
            f"갱신하는 일을 지적 성실함으로 받아들이게 한다."
        )
        today_action = (
            f"{action_object} 공개적으로 연습하면 서로 다른 독자도 과거의 결론에 매이지 않고 "
            f"새 증거에 따라 의견을 고치는 과정을 존중할 수 있다."
        )
    else:
        commentary_claim = (
            f"{image_label} 비유는 거창한 결심보다 다시 펼칠 때 곧바로 반복할 수 "
            f"있는 행동 하나가 {tension_object} 오래 지킨다는 점을 보여 준다."
        )
        commentary_implication = (
            f"{subject_object} 매번 같은 크기로 수행할 수 있게 줄이면 독서의 성과는 멋진 "
            f"해석의 양이 아니라 질문을 이어 가는 지속성으로 측정된다."
        )
        personal_claim = (
            f"나는 {theme_object} 위해 {action}를 다음 독서의 첫 행동으로 정하고, "
            f"지키기 어려운 날에는 더 작은 단위로 줄여서라도 이어 가고 싶다."
        )
        today_claim = (
            f"주의가 자주 끊기는 생활에서 {theme_topic} 의지의 강도보다 다시 시작하기 쉬운 "
            f"구조를 마련하는 일이 중요하다는 점을 일깨운다."
        )
        today_action = (
            f"{action_object} 실제로 반복하면 서로 다른 독자도 일회성 감탄을 넘어 "
            f"각자의 생활 속에서 읽기를 지속할 발판을 만들 수 있다."
        )
    quote = (
        f"{image_object} 떠올리면 {_topic(subject)} 곧바로 확정되지 않고, "
        f"{tension} 사이에서 독자가 {mode_question} 묻게 하는 살아 있는 단서가 된다."
    )
    commentary = (
        f"{theme_object} {mode_name}의 관점에서 살피면 {subject_object} 이미 확정된 결론이 아니라 독자가 조심스럽게 검토할 대상으로 바라보게 된다. "
        f"{commentary_claim} "
        f"{reading_time} {subject_object} 마주할 때는 {mode_method} 태도가 필요하며, 이는 작품의 확인되지 않은 내용을 상상으로 메우려는 행동과 구별된다. "
        f"구체적으로 {reading_time} {theme_object} 다루며 {action_object} 시도하면 떠오른 인상과 문장에 기대어 말할 수 있는 범위를 {mode_name}의 기준으로 나눌 수 있다. "
        f"{commentary_implication} "
        f"따라서 {theme_object} 중심에 둔 독서는 {mode_question} 스스로 확인하면서 상상력과 책임을 동시에 기르는 창조적 읽기가 된다."
    )
    closing = (
        f"{mode_name}의 방향으로 {theme_object} 오래 붙드는 독자는 {image} 앞에서 답을 서두르지 않고, "
        f"{subject}에 어울리는 다음 질문을 자기 언어로 남긴다."
    )
    work_introduction = (
        f"확인된 서지 정보는 작품명 『{work}』, 저자 이후, 장르 {genre}이며, 이 글은 제목이 연 인상을 {mode_name}의 관점에서 {theme_label} 독서 주제로 살핀다. "
        f"작품 속 인물, 사건, 개별 시의 내용은 가정하지 않고 {subject}에 주의를 두는 독서 행위를 {mode_name}의 방향에서 살핀다. "
        f"{image_label} 이미지는 작품을 설명하기 위한 사실이 아니라 독자가 {mode_name}에 관한 읽기 방식을 점검하도록 마련한 현재의 비유다. "
        f"이처럼 {mode_object} 분명히 하면 독자는 {theme}에 관한 질문을 자유롭게 펼치면서도 확인되지 않은 서사를 대신 만들지 않는다."
    )
    why_read_now = (
        f"짧고 빠른 반응이 익숙한 지금에는 {mode_name}의 문제를 떠올리며 {subject_object} 충분히 살피기 전에 이해했다는 결론부터 내리기 쉽다. "
        f"그러나 {theme}에서 중요하게 보는 {tension}의 균형을 {mode_name}의 관점에서 놓치면 익숙한 말만 남고 낯선 표현이 건네는 질문은 사라질 수 있다. "
        f"지금 {theme_object} 읽기의 중심에 두는 까닭은 속도를 늦추는 행위 자체보다 {mode_question} 숙고할 여백을 되찾기 위해서다. "
        f"‘{action}’라는 작은 시도는 {mode_name}에서 {theme}에 관한 감상에 머물지 않고 자기 언어를 갱신하는 계기를 만든다."
    )
    personal_reflection = (
        f"나는 {mode_name}의 자리에서 {theme_object} 마주할 때 {subject_object} 내 취향의 증거로만 사용하지 않고 질문의 출발점으로 삼고 싶다. "
        f"{reading_time} {action}를 실천하면 처음 떠오른 생각이 문장에 닿아 있는지, 아니면 개인적인 연상이 앞선 것인지 구별할 수 있다. "
        f"{personal_claim} "
        f"이처럼 {theme_object} 돌아보는 일은 경험을 꾸며 말하는 고백이 아니라 앞으로 {mode_question} 스스로 점검하겠다는 구체적인 약속이다."
    )
    meaning_today = (
        f"오늘의 언어 환경에서는 많은 문장이 맥락에서 떨어져 빠르게 공유되므로 {mode_name}의 기준으로 {subject_object} 세밀하게 보는 태도가 더욱 중요하다. "
        f"{today_claim} "
        f"{today_action} "
        f"결국 {theme_object} 두고 {mode_question} 묻는 습관은 문학을 넘어 일상의 말에서도 상상력, 수정 가능성, 타인에 대한 경청을 함께 지키는 방법이 된다."
    )
    return {
        "position": position,
        "work": work,
        "slug": f"{slug}-{mode_slug}",
        "lens": lens,
        "flow": flow,
        "title": title,
        "quote": quote,
        "commentary": commentary,
        "closing": closing,
        "source_location": (
            f"확인된 서지 정보(소설가 이후, {genre}, 『{work}』)만 참고하여 제목에서 출발했으며, "
            f"{theme}에서 {mode_name}의 문제를 다룬 독창적 감상이다."
        ),
        "translation_note": (
            f"{theme}에서 {mode_name}의 관점을 살피는 한국어 독창 감상으로 작성했으며, 번역문이나 작품의 표현을 옮기지 않고 "
            f"{subject}에 대한 독자 질문을 새로 구성했다."
        ),
        "rights_note": (
            f"직접 인용 없음. 확인된 제목과 장르만 바탕으로 {theme}에서 {mode_name}에 관한 질문을 새로 썼다."
        ),
        "work_introduction": work_introduction,
        "why_read_now": why_read_now,
        "personal_reflection": personal_reflection,
        "meaning_today": meaning_today,
    }


def entries() -> list[dict[str, object]]:
    """Return the 200 authored entries assigned to positions 601 through 800."""
    result: list[dict[str, object]] = []
    for mode_index, mode in enumerate(MODES):
        for seed_index, seed in enumerate(SEEDS):
            position = 601 + mode_index * len(SEEDS) + seed_index
            result.append(_entry(position, seed, mode))
    return result


ENTRIES = entries()
