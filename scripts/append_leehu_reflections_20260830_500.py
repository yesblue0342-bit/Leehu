#!/usr/bin/env python3
"""소설가 이후 자작품 5종 문학노트 500편 manifest generator."""
from __future__ import annotations
import importlib.util
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / "tmp" / "Leehu-50-final"
CONTENT = ROOT / "content" / "literature"
MANIFEST = ROOT / "content" / "leehu-reflections-20260830-500.json"
EXPECTED_BEFORE = 3131
PUBLISHED_AT = "2026-08-30T11:00:00+09:00"
START_SEQUENCE = 761

spec = importlib.util.spec_from_file_location("approved", ROOT / "scripts" / "append_leehu_reflections_20260829_100_2.py")
approved = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(approved)

WORKS = (
    ("연(戀)", "love", "관계와 선택", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756", "사랑을 완성된 감정보다 거리와 선택을 다시 묻는 과정으로 읽는다", "빠른 호감과 단절이 반복되는 관계의 시대", ("에서 다시 본 접힌 승차권", "에서 식어 간 차 한 잔", "에서 기다린 늦은 편지", "에서 나란히 이어진 발자국", "에서 오래 열린 창"), ("folded-ticket", "cold-tea", "late-letter", "side-by-side-footsteps", "unclosed-window")),
    ("데자뷔", "deja-vu", "기억과 반복", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772", "낯익음이 진실의 증거인지 기억이 만든 편집인지 의심해 본다", "추천 알고리즘이 익숙한 장면을 되돌려 주는 시대", ("에서 두 번 울린 벨", "에서 다시 받은 낯익은 영수증", "에서 되찾은 열쇠", "에서 겹쳐 읽힌 날짜", "에서 발견한 처음 보는 사진"), ("bell-rang-twice", "familiar-receipt", "returned-key", "overlapped-date", "first-seen-photo")),
    ("소나기", "rain-shower", "회복과 변화", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780", "갑작스러운 변화 뒤 몸과 마음이 회복되는 작은 과정을 바라본다", "예고 없이 일상이 바뀌고 곧바로 회복하라는 요구가 따르는 시대", ("에서 비를 맞은 종이봉투", "에서 마르지 않은 소매", "에서 빗방울 맺힌 손잡이", "에서 흐려진 약속 메모", "에서 흔들린 물웅덩이 불빛"), ("wet-paper-bag", "undried-sleeve", "raindrop-handle", "blurred-promise-note", "puddle-light")),
    ("환상", "fantasy", "상상과 경계", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769", "현실을 피하는 장식이 아니라 익숙한 세계의 규칙을 바꾸는 상상으로 접근한다", "이미지와 현실의 경계가 매일 새롭게 편집되는 시대", ("에서 말을 건넨 그림자", "에서 시간을 접은 시계", "에서 열린 문 너머 작은 숲", "에서 별을 담은 유리병", "에서 거꾸로 흐른 계단"), ("speaking-shadow", "time-folding-clock", "forest-behind-door", "star-glass-bottle", "backward-stairs")),
    ("별이 빛나는 밤에", "starry-night", "밤과 사유", "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770", "밤의 고요를 통해 멀리 있는 존재와 오늘의 자신을 함께 바라본다", "잠들기 전까지 화면의 빛이 사라지지 않는 시대", ("에서 지켜본 새벽 전 마지막 별", "에서 찾은 구름 너머 북극성", "에서 바라본 먼 창의 불빛", "에서 올려다본 옥상 위 얇은 달", "에서 들은 밤기차가 남긴 정적"), ("last-star-before-dawn", "north-star-behind-clouds", "distant-window-light", "thin-rooftop-moon", "silence-after-night-train")),
)
SETTINGS = ("새벽 역", "비 그친 골목", "오래된 도서관", "강변 산책로", "늦은 버스 정류장", "옥상 정원", "작은 세탁소", "문 닫은 극장", "겨울 바닷가", "첫차 안", "빈 교실", "시장 끝 찻집", "병원 복도", "오래된 아파트 계단", "산 아래 우체국", "항구 대합실", "불 꺼진 사무실", "이사 전 빈방", "공원 뒤편 벤치", "달빛 든 부엌")
SETTING_SLUGS = ("dawn-station", "after-rain-alley", "old-library", "riverside-path", "late-bus-stop", "rooftop-garden", "small-laundromat", "closed-theater", "winter-seashore", "first-train", "empty-classroom", "market-end-teahouse", "hospital-corridor", "old-apartment-stairs", "mountain-post-office", "harbor-waiting-room", "dark-office", "empty-room-before-moving", "park-back-bench", "moonlit-kitchen")

josa = approved.josa

def make_note(work_data, work_index: int, setting_index: int, detail_index: int, sequence: int):
    work, wslug, tag, url, frame, now, details, detail_slugs = work_data
    motif = f"{SETTINGS[setting_index]}{details[detail_index]}"
    motif_slug = f"{SETTING_SLUGS[setting_index]}-{detail_slugs[detail_index]}"
    local_index = setting_index * 5 + detail_index
    global_index = work_index * 100 + local_index
    scene = approved.SCENES[(local_index + work_index * 3) % 20] + "에서 " + motif + "의 의미가 새로 보이는 순간"
    tension = approved.TENSIONS[(local_index * 3 + work_index * 5) % 20]
    action = approved.ACTIONS[(local_index * 7 + work_index * 2) % 20]
    title, deck, commentary = approved.prose(work, motif, scene, tension, action, global_index)
    obj = motif + josa(motif, "을", "를")
    subj = motif + josa(motif, "이", "가")
    join = "《" + work + "》" + josa(work, "과", "와")
    work_obj = "《" + work + "》" + josa(work, "을", "를")
    scene_obj = scene + josa(scene, "을", "를")
    seo = {
        "work_introduction": f"소설가 이후의 한국어 창작 작품 《{work}》에 관한 {motif} 중심의 독창적 문학노트다. 이 기록은 교보ebook 공식 도서 정보로 작품과 작가를 확인했으며 본문이나 대사를 직접 인용하지 않는다. 이번 글은 {obj} 독립적인 소재로 삼아 {frame}.",
        "why_read_now": f"{motif}에 관한 이번 독서에서, {now}에는 ‘{tension}’이라는 문제를 한쪽 답으로 밀어붙이기 쉽다. 오늘 떠올린 풍경은 {scene}이다. 이는 {work_obj} 오늘 다시 생각하면서 {obj} 통해 즉각적인 요약보다 맥락을 먼저 살피게 한다.",
        "personal_reflection": f"나는 {scene_obj} 떠올리며 판단이 얼마나 빨리 결론을 만드는지 돌아보았다. {join} {motif} 사이의 연결은 작품의 내용을 대신 설명하지 않는다. {motif}에서 출발하면, 대신 {tension} 앞에서 내가 취한 거리와 말투를 점검하게 한다.",
        "meaning_today": f"{motif} 앞에 잠시 멈추면, 오늘의 의미는 거창한 교훈보다 {action}에 있다. {motif}의 관점에서는 이 행동이 ‘{tension}’이라는 문제를 지워 버리지 않으면서도 현실에서 선택할 작은 기준을 제공한다. {subj} 남긴 질문은 그렇게 일상의 윤리로 이어진다.",
    }
    note = {
        "id": f"20260830_leehu_literature_{sequence:04d}",
        "slug": f"leehu-20260830-{wslug}-{motif_slug}-reflection",
        "title": title,
        "quote": approved.vary_sentences(deck, motif, global_index),
        "source_author": "이후",
        "source_work": work,
        "source_location": "교보ebook 도서 정보의 작가 소개 및 작품 설명 참고 · 작품 본문 직접 인용 없음",
        "source_language": "ko",
        "source_url": url,
        "translation_note": "한국어 창작 작품에 관한 독창적 감상으로 작품 본문과 타인의 번역문을 옮기지 않음.",
        "rights_note": f"소설가 이후의 작품 《{work}》에 관한 자체 작성 문학노트이며 작품 본문 직접 인용 없음.",
        "commentary": approved.vary_sentences(commentary, motif, global_index) + f" {obj} 살피는 동안 나는 {work_obj} 대신 설명하기보다 이 소재가 오늘의 판단과 태도에 남기는 미세한 변화를 끝까지 관찰해야 한다고 느꼈다.",
        "closing": approved.vary_sentences(f"오늘의 기록은 “{action}”라는 실천을 남기고 {motif}의 다음 의미는 독자에게 열어 둔다.", motif, global_index),
        "author": "소설가 이후",
        "tags": ["소설가 이후", work, tag, motif, "독창적 감상"],
        "related_work": {"name": work, "url": url},
        "published_at": PUBLISHED_AT,
        "content_kind": "original_reflection",
        "seo_sections": {key: approved.vary_sentences(value, motif, global_index + pos) for pos, (key, value) in enumerate(seo.items())},
    }
    return note

def review(notes):
    if len(notes) != 500:
        raise SystemExit("expected 500 notes")
    for field in ("id", "slug", "title", "quote", "commentary", "closing"):
        values = [re.sub(r"\s+", " ", str(note[field])).casefold() for note in notes]
        if len(values) != len(set(values)):
            raise SystemExit("duplicate " + field)
    if len({note["tags"][3] for note in notes}) != 500:
        raise SystemExit("motifs not unique")
    forbidden = ("AI", "자동 생성", "공식 카탈로그", "원문 확인 필요", "권리이", "자유을", "과정를", "소나기을", "경계을", "연(戀)를", "환상를", "별이 빛나는 밤에를", "독서을", "자리을", "변화을", "이미지을", "대화을", "《데자뷔》을", "《소나기》을", "《별이 빛나는 밤에》을")
    sentences = []
    for note in notes:
        prose = " ".join((note["quote"], note["commentary"], note["closing"], *note["seo_sections"].values()))
        if any(term in prose for term in forbidden):
            raise SystemExit("forbidden prose " + note["id"])
        if any(len(value) < 100 for value in note["seo_sections"].values()):
            raise SystemExit("short SEO " + note["id"])
        sentences.extend(part.strip() for part in re.split(r"(?<=[.!?])\s+", prose) if len(part.strip()) >= 25)
    duplicate = [sentence for sentence, count in Counter(sentences).items() if count > 1]
    if duplicate:
        raise SystemExit("repeated sentence: " + duplicate[0])
    for offset in range(0, 500, 50):
        batch = notes[offset:offset + 50]
        if len({note["slug"] for note in batch}) != 50 or len({note["title"] for note in batch}) != 50:
            raise SystemExit(f"batch {offset // 50 + 1} uniqueness failure")
        print(f"batch {offset // 50 + 1}: 50 notes reviewed")

def main():
    existing = sorted(CONTENT.glob("*.json"), key=lambda p: int(p.stem))
    if len(existing) not in (EXPECTED_BEFORE, EXPECTED_BEFORE + 500):
        raise SystemExit(f"expected 3131 or 3631 sources, found {len(existing)}")
    notes = []
    for work_index, work in enumerate(WORKS):
        for setting_index in range(20):
            for detail_index in range(5):
                local_index = setting_index * 5 + detail_index
                notes.append(make_note(work, work_index, setting_index, detail_index, START_SEQUENCE + work_index * 100 + local_index))
    review(notes)
    targets = [CONTENT / f"{number}.json" for number in range(3132, 3632)]
    if len(existing) == 3631 and [json.loads(path.read_text()) for path in targets] != notes:
        raise SystemExit("existing batch differs; replace explicitly")
    MANIFEST.write_text(json.dumps(notes, ensure_ascii=False, indent=2) + "\n")
    print("reviewed and wrote 500 notes with 500 unique motifs")

if __name__ == "__main__":
    main()
