# 문학노트 정적 시스템 검증 보고서

검증일: 2026-07-28 (Asia/Seoul)

## 최종 산출물

- 원천 JSON: 1,465개 (`content/literature/001.json` … `1465.json`)
- ID 범위:
  - 기존 배치: `20260727_leehu_literature_001` … `_1165`
  - 최신 세계문학 배치: `20260728_leehu_literature_001` … `_300`
- 정적 상세 페이지: 1,465개
- 목록 페이지: 59개 (페이지당 25개)
- RSS item: 1,465개
- sitemap URL: 1,525개

## 최신 300편 구성

| 구분 | 건수 | 출처·권리 처리 |
|---|---:|---|
| Leo Tolstoy · *Anna Karenina* | 35 | Project Gutenberg 퍼블릭 도메인 영어 원전 직접 인용 |
| Emily Brontë · *Wuthering Heights* | 35 | Project Gutenberg 퍼블릭 도메인 영어 원전 직접 인용 |
| Victor Hugo · *Les Misérables* | 35 | Project Gutenberg 퍼블릭 도메인 영어 원전 직접 인용 |
| J. W. von Goethe · *The Sorrows of Young Werther* | 35 | Project Gutenberg 퍼블릭 도메인 영어 원전 직접 인용 |
| Alexandre Dumas fils · *La Dame aux Camélias* | 35 | Project Gutenberg 퍼블릭 도메인 영어 원전 직접 인용 |
| Anton Chekhov · *About Love* | 35 | Project Gutenberg 수록 영어 원전 직접 인용 |
| Gabriel García Márquez · *Love in the Time of Cholera* | 45 | `original_reflection`: 직접 인용·번역문·장면 재현 없음 |
| Antoine de Saint-Exupéry · *The Little Prince* | 45 | `original_reflection`: 직접 인용·번역문·장면 재현 없음 |

마르케스와 생택쥐페리 항목은 권리 상태를 보수적으로 처리했다. 작품 제목과 일반적 사랑 주제를 매개로 한 독창 감상만 사용하며, 해당 작품의 원문·번역문·대사·세부 줄거리를 인용하지 않는다.

## 생성·검증 명령

```bash
cd /c/codex/Leehu
python scripts/append_world_love_literature.py
python scripts/build_literature.py
python -m unittest discover -s tests -v
git diff --check
```

## 자동 검증 범위

- JSON 수, 파일명, ID 날짜와 `published_at` 일치
- 필수 필드, HTTPS 원전/작품 정보 URL, 원문 인용 및 감상형 권리 고지
- slug·title·quote·canonical 중복, 직접 인용 항목의 근접 중복
- commentary 문장 수·길이·시작/끝 문장 중복
- 작가·작품·태그 편중, JSON-LD, RSS, sitemap, 내부 링크
- 목록·RSS·홈페이지 대표 카드의 `published_at DESC → ID DESC` 정렬
- 감상형 상세 페이지가 Project Gutenberg 원문 인용으로 잘못 표기되지 않는지 확인

## 실행 결과

```text
python -m unittest discover -s tests -v
Ran 15 tests
OK

python scripts/build_literature.py
built 1465 detail pages, 59 list pages, 1465 RSS items, and 1525 sitemap URLs
```
