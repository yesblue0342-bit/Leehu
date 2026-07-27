# Leehu

소설가 이후 공식 홈페이지입니다.

- 운영 도메인: https://xn--hu5b23z.com/
- 한글 표시 도메인: https://이후.com/
- 저장소: https://github.com/yesblue0342-bit/Leehu

## 문학노트 정적 발행

문학노트는 GitHub Pages에서 직접 제공하는 정적 HTML입니다. 정기 발행, n8n, API token, 런타임 데이터베이스 없이 한 번의 배치로 공개합니다.

### 구조

```text
content/literature/001.json … 365.json   원본 데이터
scripts/curate_literature.py              공공영역 원문 큐레이션 도구
scripts/build_literature.py               검증 및 정적 사이트 생성기
literature/index.html                     목록 첫 페이지
literature/page/N/index.html              페이지네이션
literature/{slug}/index.html              개별 문학노트
literature/rss.xml                        RSS 피드
sitemap.xml                               전체 사이트맵
```

문학노트 데이터에는 내부 관리 ID, 공개 slug, 짧은 원문 인용, 작가·작품·위치·원문 언어·직접 출처 URL·번역 및 권리 메모·해설·태그·관련 작품 링크를 저장합니다. 내부 ID는 배치 관리용이며 공개 URL에는 사용하지 않습니다.

### 정적 생성

```bash
cd C:\codex\Leehu
python scripts/build_literature.py
python -m unittest
```

출력 예시:

```text
built 365 detail pages, 15 list pages, 365 RSS items, and 381 sitemap URLs
```

생성기는 다음을 중단 조건으로 검증합니다.

- 정확히 365개 JSON 및 내부 ID/파일명 대응
- slug·제목·인용문·canonical 중복 및 유사도
- 출처 URL·필수 필드·인용문 대비 해설 길이
- commentary 첫 문장·마지막 문장 중복
- 작가·작품·태그 편중
- 정적 내부 링크, HTML escape, JSON-LD, RSS, sitemap

### 새 문학노트 추가 또는 코퍼스 재생성

1. `content/literature/`에 필수 필드를 갖춘 새 JSON을 추가하거나, 공공영역 원문을 다시 큐레이션합니다.
2. `python scripts/build_literature.py`를 실행합니다.
3. `python -m unittest`로 전체 정적·기존 게시판 회귀 테스트를 실행합니다.
4. 생성된 `literature/`, `literature/rss.xml`, `sitemap.xml`, 홈페이지 카드 변경을 확인합니다.
5. 커밋하고 `main`에 push합니다.

```bash
git add -A
git commit -m "content: add new literature notes"
git push
```

### 권리 및 출처 처리

원문은 Project Gutenberg가 제공하는 공공영역 영어 텍스트에서 짧게 인용합니다. 현대 한국어 번역문을 저장하거나 장문 전재하지 않습니다. `scripts/curate_literature.py`는 직접 원문을 내려받아 인용문이 원문 본문에 존재하는지 확인한 후 JSON을 생성합니다.

## 기존 서버 코드

`server.py`, `Dockerfile`, 방문자 게시판 API는 기존 기능 호환을 위해 보존합니다. 현재 문학노트 공개는 GitHub Pages 정적 HTML을 기준으로 하며, 정적 산출물은 서버 API에 의존하지 않습니다.
