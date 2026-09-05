# 소설가 이후(李後, Lee Hu) 공식 홈페이지

장편소설 《연》·《데자뷔》·《소나기》와 《Fantasy》를 쓴 소설가 이후의 공식 홈페이지 소스 및 문학노트 아카이브입니다.

## 공식 채널

- [소설가 이후 공식 홈페이지](https://xn--hu5b23z.com/)
- [소설가 이후 공식 작가 프로필](https://xn--hu5b23z.com/author/)
- [소설가 이후 공식 출처 인덱스](https://xn--hu5b23z.com/official-links/)
- [소설가 이후 작품 문학노트](https://xn--hu5b23z.com/literature/)
- [소설가 이후 네이버 블로그](https://blog.naver.com/yesblue0342)
- [소설가 이후 YouTube](https://www.youtube.com/@Yesblue1234)
- [소설가 이후 YouTube Music](https://music.youtube.com/channel/UCQdIJKAOKVI8pKIsvcFBEKA)
- [소설가 이후 Instagram](https://www.instagram.com/12drf52/)
- [소설가 이후 X](https://twitter.com/yesblue0342)
- [교보문고 작가정보](https://store.kyobobook.co.kr/person/detail/1000809404)
- [Wikipedia: 이후 (소설가)](https://ko.wikipedia.org/wiki/%EC%9D%B4%ED%9B%84_(%EC%86%8C%EC%84%A4%EA%B0%80))
- 한글 표시 도메인: [이후.com](https://이후.com/)

## 기존 1,000개 문학노트 재활용

`content/leehu-reflections-20260903-1000.json`의 기존 문학노트 1,000건은 새 페이지로 복제하지 않고 원래 canonical URL을 그대로 유지합니다. 각 문서는 [공식 작가 프로필](https://xn--hu5b23z.com/author/)과 [공식 출처 인덱스](https://xn--hu5b23z.com/official-links/)로 연결되며, sitemap과 구조화 데이터를 통해 네이버·YouTube를 포함한 공개 채널의 동일 인물 관계를 전달합니다.

## 문학노트 정적 발행

문학노트는 GitHub Pages에서 직접 제공하는 정적 HTML입니다. 정기 발행, n8n, API token, 런타임 데이터베이스 없이 한 번의 배치로 공개합니다.

### 구조

```text
content/literature/001.json … NNN.json   원본 데이터
content/literature-index-policy.json    검색 색인 포함·제외 정책
literature_index_policy.py              정적/서버 공용 정책 검증기
scripts/curate_literature.py              기존 공공영역 원문 큐레이션 도구
scripts/literature_batch.py               manifest append·build·verify 범용 CLI
scripts/build_literature.py               검증 및 정적 사이트 생성기
author/index.html                         활동명 기준 공식 작가 프로필
official-links/index.html                 검증된 공식 출처 인덱스
llms.txt                                  AI 검색용 핵심 공개 정보
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
python scripts/literature_batch.py build --expected-count 5131 --test
```

출력 예시:

```text
built 5131 detail pages, 186 list pages, 4632 RSS items, and 4651 sitemap URLs; noindexed 499 detail pages
```

모든 문학노트 원문과 직접 URL은 보존합니다. 다만 `content/literature-index-policy.json`에서 검색 색인 제외로 지정한 반복 형식의 대량 배치는 상세 페이지에 `noindex, follow`를 적용하고 목록·홈페이지·RSS·sitemap·이전/다음 링크에서는 제외합니다. 정책은 버전, 범위 중복, 실제 원본 ID 매칭을 생성 전에 검증하며, 현재 공개 발견 대상은 4,632건입니다. 목록 2쪽 이후는 탐색용 보관 페이지로 유지하되 `noindex, follow`를 적용하고 sitemap에는 넣지 않습니다.

생성기는 다음을 중단 조건으로 검증합니다.

- 설정된 기대 수량의 JSON 및 내부 ID/파일명 대응
- 원문 인용은 Project Gutenberg·위키문헌의 확인된 퍼블릭 도메인 원전만 허용하고, 권리가 남아 있는 작가의 항목은 `original_reflection` 모드에서 직접 인용 없이 공개
- slug·제목·인용문·canonical 중복 및 유사도
- 출처 URL·필수 필드·인용문 대비 해설 길이
- commentary 첫 문장·마지막 문장 중복
- 작가·작품·태그 편중
- 정적 내부 링크, HTML escape, JSON-LD, RSS, sitemap

### 새 문학노트 빠른 배치 추가

완성된 문학노트를 JSON 배열 manifest로 준비합니다. 각 객체는 기존 `content/literature/*.json`과 같은 schema를 사용합니다.

```bash
# 1. 쓰지 않고 schema·ID·slug·기존 충돌·예정 파일명 확인
python scripts/literature_batch.py append batch-manifest.json

# 2. 검토 후에만 연속 번호로 atomic append
python scripts/literature_batch.py append batch-manifest.json --apply

# 3. 정적 생성, 수량 검증, 전체 테스트
python scripts/literature_batch.py build --expected-count <새로운_총수량> --test
```

`append`는 기본적으로 dry-run입니다. `--apply` 중 오류가 발생하면 이번 실행에서 만든 파일만 rollback하며 기존 JSON은 덮어쓰지 않습니다. 생성 후 `literature/`, `literature/rss.xml`, `sitemap.xml`, 홈페이지 최신 카드 변경을 확인하고 `main`에 push합니다.

```bash
git add -A
git commit -m "content: add new literature notes"
git push
```

### 네이버 IndexNow 갱신 알림

공개 소유권 키 파일이 배포된 뒤 변경된 핵심 URL을 네이버에 알립니다. 기본 실행은 홈페이지와 공식 작가 프로필만 제출하며, 외부 호스트·HTTP·userinfo·fragment가 포함된 URL은 거부합니다.

```bash
# 제출 전 JSON 확인
python scripts/submit_indexnow.py --dry-run

# 네이버 IndexNow 제출
python scripts/submit_indexnow.py
```

### 권리 및 출처 처리

원문 인용은 Project Gutenberg와 위키문헌에서 직접 확인한 퍼블릭 도메인 텍스트만 사용합니다. 현대 한국어 번역문을 저장하거나 장문 전재하지 않습니다. 권리가 남아 있는 작가의 작품은 `original_reflection`으로 구분하고, 원문·번역문·대사·상세 줄거리를 인용하지 않은 독창적 감상만 공개합니다.

## 서버 발행 모드

현재 문학노트 공개 기준은 GitHub Pages의 버전 관리된 정적 HTML입니다. `server.py`와 Docker 배포도 기본값인 `LITERATURE_PUBLICATION_MODE=static`에서 같은 정적 홈페이지·공식 프로필·문학노트·RSS·sitemap을 제공합니다. 이 모드에서 API로 저장한 새 문학노트는 다음 정적 빌드 전까지 공개 HTML과 검색 발견 경로에 노출되지 않습니다.

서버의 정적 파일 공개 범위는 홈페이지, 공식 프로필, 공식 출처 인덱스, 문학노트, RSS·sitemap·robots·llms.txt, 검색엔진 소유 확인 파일과 공유 이미지로 제한합니다. Python 소스, 정책 JSON, Docker·저장소 문서는 HTTP로 제공하지 않습니다. 발행 모드 값이 `static` 또는 `dynamic`이 아니면 서버는 묵시적으로 대체하지 않고 시작 단계에서 오류를 냅니다.

기존 즉시 공개 API 동작이 필요한 호환 환경만 `LITERATURE_PUBLICATION_MODE=dynamic`을 사용합니다. 동적 모드에서도 같은 색인 정책을 적용해 목록·RSS·sitemap·이전/다음 링크를 필터링하고, 제외 상세 페이지에는 `noindex, follow`를 표시합니다. 방문자 게시판 API는 두 모드에서 그대로 유지됩니다.
