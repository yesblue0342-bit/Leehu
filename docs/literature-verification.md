# 문학노트 정적 시스템 검증 보고서

검증일: 2026-07-28 (Asia/Seoul)

## 최종 산출물

- 원천 JSON: 1,165개 (`content/literature/001.json` … `1165.json`)
- ID 범위: `20260727_leehu_literature_001` … `_1165`
- 공개 시각: 모두 `2026-07-27T12:00:00+09:00`
- 상세 HTML: 1,165개
- 목록 HTML: 47쪽 (25편 × 46쪽, 마지막 15편)
- RSS: 1,165개 항목
- 사이트맵: 1,213개 URL
- 홈페이지 대표 카드: 정확히 6개

## 사랑 주제 확장 배치

기존 665편에 500편을 추가했다.

| 구분 | 수량 | 공개 방식 |
|---|---:|---|
| Guy de Maupassant | 125 | Project Gutenberg 퍼블릭 도메인 원전 직접 인용 |
| William Shakespeare | 125 | Project Gutenberg 퍼블릭 도메인 원전 직접 인용 |
| 이상 | 60 | 위키문헌에서 `PD-old-70` 표지가 확인된 고정 원문 버전 직접 인용 |
| 이상 작품 감상 | 65 | 원문·번역문·장면을 인용하지 않은 독창적 감상 |
| 황순원 작품 감상 | 125 | 원문·번역문·대사·상세 줄거리를 인용하지 않은 독창적 감상 |

`original_reflection` 항목에는 `직접 인용 없음` 권리 고지를 강제했다. 황순원 항목은 작품 제목과 일반적인 사랑의 질문만을 출발점으로 하며, 원문 재현이나 줄거리 대체를 포함하지 않는다.

## 정적 빌드

```text
python scripts/build_literature.py
built 1165 detail pages, 47 list pages, 1165 RSS items, and 1213 sitemap URLs
```

빌드는 필수 필드, 숫자 파일명/ID 대응, ID와 공개일 일치, slug·제목·인용·canonical 중복, 출처 도메인과 콘텐츠 모드, 해설 길이, 태그 중복, HTML escape, JSON-LD, RSS, sitemap, 정적 내부 링크를 검증한다.

정렬은 다음 규칙을 적용한다.

```text
published_at DESC → 같은 공개일은 ID sequence DESC
```

## 전체 회귀 테스트

```text
python -m unittest discover -s tests -v
Ran 13 tests in 159.420s
OK
```

정적 코퍼스/검색/페이지네이션/SEO/피드/내부 링크 검사와 기존 `server.py` 문학 API 및 방문자 게시판 회귀 테스트를 함께 통과했다. 테스트 안에서 생성기를 다시 실행해 주요 산출물이 바이트 단위로 동일한지도 확인했다.

## 작업 트리 검사

```text
git diff --check
exit code 0
```

- `.github/workflows`, `server.py`, `Dockerfile` 변경 없음
- `.omx/`는 기존 미추적 로컬 항목으로 제외
- 비밀키, 토큰, 임시 로그 추가 없음
