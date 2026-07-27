# 문학노트 정적 시스템 검증 보고서

검증일: 2026-07-27 (Asia/Seoul)

## 최종 산출물

- 원천 JSON: 665개 (`content/literature/001.json` … `665.json`)
- ID 범위: `20260727_leehu_literature_001` … `_665`
- 공개 시각: 665편 모두 `2026-07-27T12:00:00+09:00`
- 원문 범위: 저자와 작품이 서로 다른 Project Gutenberg 영어 원전 30편
- 상세 HTML: 665개
- 목록 HTML: 27쪽 (25편 × 26쪽, 마지막 15편)
- RSS: 665개 항목
- 사이트맵: 693개 URL
- 홈페이지 대표 카드: 정확히 6개

## 실행 명령과 결과

### 원문 큐레이션

```text
python scripts/curate_literature.py
curated 665 verified notes from 30 public-domain works
```

각 Project Gutenberg plain-text 본문을 `urllib`로 내려받고 `*** START`와 `*** END` 사이에서만 문장을 선별했다. 저장 직전에 공백을 정규화한 원문 본문에 각 인용문이 정확히 존재하는지 665건 모두 확인했다. 닫는 인용부호가 소실되거나 쌍이 맞지 않는 문장은 제외했다.

### 정적 빌드

```text
python scripts/build_literature.py
built 665 detail pages, 27 list pages, 665 RSS items, and 693 sitemap URLs
```

빌드 과정에서 필수 필드, 파일명/ID 대응, slug와 canonical, 중복 및 유사도, 해설 첫·끝 문장, 원문 URL, 인용 대비 해설 길이, 작가·작품·태그 편중, 태그 중복, HTML 이스케이프, JSON-LD JSON, 정적 내부 링크, RSS·사이트맵·홈페이지 개수를 검증했다.

### 전체 회귀 테스트

```text
python -m unittest
Ran 10 tests in 33.223s
OK
```

정적 코퍼스/페이지/SEO/피드/내부 링크 검사와 기존 `server.py` 문학 API 및 방문자 게시판 회귀 테스트를 함께 통과했다. 테스트 안에서 생성기를 한 번 더 실행해 주요 산출물이 바이트 단위로 동일한지도 확인했다.

### 작업 트리 검사

```text
git diff --check
exit code 0
```

- `.github/workflows`, `server.py`, `Dockerfile` 변경 없음
- `.literature-source-cache/`와 모든 `__pycache__/` 제거
- 비밀키, 토큰, 임시 로그 추가 없음
- 기존 미추적 `.omx/` 보존
- 요청에 따라 commit/push 미실행

## 콘텐츠 및 권리 확인

- 인용은 현대 한국어 번역이 아닌 퍼블릭 도메인 영어 원문만 저장했다.
- 30명의 저자에게 12~13편씩 분산하여 한 저자나 작품이 전체의 5%를 넘지 않는다.
- 모든 JSON에 직접 원문 URL, eBook 번호와 원문 줄 근처 위치, 언어, 번역 메모, 권리 메모가 있다.
- 해설은 4~8개의 한국어 문장으로 구성되며 인용문보다 충분히 길다.
- 제목, 인용, 해설, 해설의 첫 문장과 마지막 문장, 태그 조합을 중복·유사도 게이트로 검사했다.
