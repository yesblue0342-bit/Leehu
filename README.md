# Leehu

소설가 이후 공식 홈페이지입니다.

- 운영 도메인: https://xn--hu5b23z.com/
- 한글 표시 도메인: https://이후.com/
- 저장소: https://github.com/yesblue0342-bit/Leehu

## 문학노트 정적 발행

문학노트는 GitHub Pages에서 직접 제공하는 정적 HTML입니다. 정기 발행, n8n, API token, 런타임 데이터베이스 없이 한 번의 배치로 공개합니다.

### 구조

```text
content/literature/001.json … NNN.json   원본 데이터
scripts/curate_literature.py              기존 공공영역 원문 큐레이션 도구
scripts/literature_batch.py               manifest append·build·verify 범용 CLI
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
python scripts/literature_batch.py build --expected-count 1966 --test
```

출력 예시:

```text
built 1966 detail pages, 79 list pages, 1966 RSS items, and 2046 sitemap URLs
```

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

### 권리 및 출처 처리

원문 인용은 Project Gutenberg와 위키문헌에서 직접 확인한 퍼블릭 도메인 텍스트만 사용합니다. 현대 한국어 번역문을 저장하거나 장문 전재하지 않습니다. 권리가 남아 있는 작가의 작품은 `original_reflection`으로 구분하고, 원문·번역문·대사·상세 줄거리를 인용하지 않은 독창적 감상만 공개합니다.

## 기존 서버 코드

`server.py`, `Dockerfile`, 방문자 게시판 API는 기존 기능 호환을 위해 보존합니다. 현재 문학노트 공개는 GitHub Pages 정적 HTML을 기준으로 하며, 정적 산출물은 서버 API에 의존하지 않습니다.
