# Leehu

소설가 이후 공식 홈페이지입니다.

- 운영 도메인: https://xn--hu5b23z.com/
- 한글 표시 도메인: https://이후.com/
- 저장소: https://github.com/yesblue0342-bit/Leehu

## 문학노트

`이후의 문학노트`는 Hermes 또는 n8n이 매일 1회 고전문학/한국문학의 짧은 인용문과 출처, 그리고 “소설가 이후의 생각”을 API로 발행하는 정식 콘텐츠 영역입니다.

새 문학노트는 `/data/literature-posts/{slug}.json`에 저장됩니다. 코드나 HTML 파일을 매일 생성하지 않으므로 새 글 등록만으로 Git commit, GitHub Actions, Docker image rebuild, OCI 재배포가 필요하지 않습니다.

## URL과 ID 규칙

내부 ID:

```text
YYYYMMDD_leehu_literature_NN
```

공개 slug:

```text
YYYYMMDD-leehu-literature-NN-{topic-slug}
```

예:

```text
20260727_leehu_literature_01
20260727-leehu-literature-01-shakespeare-love
```

날짜는 Asia/Seoul 기준입니다. 같은 날짜의 두 번째 글은 `02`, 다음 날짜는 다시 `01`부터 시작합니다. `topic-slug`는 영문 소문자, 숫자, 하이픈만 허용됩니다. slug가 없으면 서버가 제목, 인용 작가, 작품명을 기반으로 자동 생성합니다.

## 환경변수

```text
BOARD_POSTS_DIR=/data/board-posts
LITERATURE_POSTS_DIR=/data/literature-posts
LITERATURE_API_TOKEN=긴_임의_토큰
LITERATURE_ALLOWED_ORIGINS=https://example.com,https://n8n.example.com
```

`LITERATURE_API_TOKEN`은 문학노트 POST, PUT, DELETE에 필요합니다. 토큰은 코드나 프런트엔드에 노출하지 않습니다.

## 로컬 실행

```bash
set PORT=8765
set BOARD_POSTS_DIR=%TEMP%\leehu-board-posts
set LITERATURE_POSTS_DIR=%TEMP%\leehu-literature-posts
set LITERATURE_API_TOKEN=dev-token
python server.py
```

확인:

```bash
curl http://127.0.0.1:8765/
curl http://127.0.0.1:8765/literature/
```

## Docker 실행

```bash
docker build -t leehu .
docker run -p 8080:80 ^
  -e LITERATURE_API_TOKEN=change-me ^
  -e BOARD_POSTS_DIR=/data/board-posts ^
  -e LITERATURE_POSTS_DIR=/data/literature-posts ^
  -v leehu-data:/data ^
  leehu
```

`/data` 볼륨 아래에 방문자 게시판과 문학노트가 분리 저장됩니다.

```text
/data/board-posts
/data/literature-posts
```

컨테이너 재시작, Docker 이미지 교체, GitHub Actions 배포 후에도 같은 `/data` 볼륨을 유지하면 기존 게시글과 문학노트가 유지됩니다.

## n8n / Hermes 발행 예시

POST:

```bash
curl -X POST https://xn--hu5b23z.com/api/literature/posts \
  -H "Authorization: Bearer $LITERATURE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"셰익스피어가 바라본 사랑의 맹목성",
    "quote":"짧은 인용문 한두 문장",
    "source_author":"William Shakespeare",
    "source_work":"A Midsummer Night'\''s Dream",
    "source_location":"Act 1, Scene 1",
    "source_language":"en",
    "translation_note":"영문 원전 기반 자체 번역",
    "rights_note":"원전 및 번역 사용 조건 확인",
    "commentary":"사랑은 상대를 있는 그대로 보는 일이라기보다, 때로는 보고 싶은 모습으로 바라보는 일인지도 모릅니다. 소설 『연』을 쓰던 때에도 사랑이 사람의 기억을 어떻게 바꾸는지 오래 생각했습니다. 오늘은 이 문장을 함께 나누고 싶습니다.",
    "closing":"소설가 이후 드림",
    "author":"소설가 이후",
    "published_at":"2026-07-27T09:00:00+09:00",
    "tags":["사랑","셰익스피어","고전문학","소설가 이후"],
    "status":"published"
  }'
```

PUT:

```bash
curl -X PUT https://xn--hu5b23z.com/api/literature/posts/20260727-leehu-literature-01-shakespeare-love \
  -H "Authorization: Bearer $LITERATURE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commentary":"수정된 이후의 생각 본문입니다. 인용문보다 충분히 긴 해설을 유지해야 합니다.","status":"published"}'
```

DELETE 또는 archive:

```bash
curl -X DELETE https://xn--hu5b23z.com/api/literature/posts/20260727-leehu-literature-01-shakespeare-love \
  -H "Authorization: Bearer $LITERATURE_API_TOKEN"
```

성공 응답:

```json
{
  "id": "20260727_leehu_literature_01",
  "slug": "20260727-leehu-literature-01-shakespeare-love",
  "canonical_url": "https://xn--hu5b23z.com/literature/20260727-leehu-literature-01-shakespeare-love"
}
```

오류 응답:

```json
{"error":"unauthorized"}
{"error":"validation_failed","details":["commentary_too_short"]}
{"error":"duplicate_id_or_slug"}
```

## 공개 URL

- 문학노트 목록: `/literature/`
- 문학노트 상세: `/literature/{slug}`
- 문학노트 JSON 목록: `/api/literature/posts`
- 문학노트 JSON 상세: `/api/literature/posts/{slug}`
- RSS: `/literature/rss.xml`
- 동적 사이트맵: `/sitemap.xml`

## 데이터 백업

백업 대상:

```text
/data/board-posts
/data/literature-posts
```

파일 단위 JSON 저장이므로 폴더 전체를 복사하면 됩니다.
