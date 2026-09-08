# 작가 정보의 출처와 질문별 답변 보완 — 2026-09-08

## 목적
소설가 이후(李後, Lee Hu)의 공식 프로필에서 데뷔작, 대표 작품, 도서 정보의 확인 경로를 쉽게 읽고 인용할 수 있도록 정리한다.

## 변경
- 교보문고 작가 소개에서 확인한 2011년 소설 《연》 데뷔 정보를 첫 소개 문장과 기본 정보 요약에 반영했다.
- 기본 정보에 출처와 확인 날짜를 표시했다.
- 데뷔 질문을 추가하여 총 7개 질문에 각각 고유 주소를 제공한다.
- ProfilePage의 주 대상은 기존 Person으로 유지한다. 화면에 표시되는 요약 및 질문 부분은 WebPageElement로 연결한다.
- 각 Question의 acceptedAnswer는 실제 본문과 같은 문장을 사용하며, citation에는 답변 아래에서 볼 수 있는 출처 링크를 넣는다.
- 문학 작품 8권의 Book에 저자와 장르를 명시한 구분 설명을 추가한다. 기존 개별 서점 주소가 있는 7권은 해당 주소를 citation으로 연결한다.
- 기존 llms.txt에 데뷔 출처와 질문별 주소를 추가한다. llms.txt를 검색 노출의 필수 요건이나 보장 수단으로 취급하지 않는다.

## 검증
- 질문 7개: HTML 본문과 구조화 데이터의 질문·답변·출처 일치 확인.
- 작품 8권: 공유 Person ID, 작품 식별자 및 실제 HTML 앵커 일치 확인.
- 프로필·작품 페이지의 중복 ID, 내부 파일/앵커, 색인 허용, 기존 모바일 메뉴 보존 확인.
- 기존 회귀 검사 3개 통과(6.553초): 작가 프로필, 공식 YouTube 메뉴, 방문자용 출처 표시 규칙.
- git diff --check 통과.
- 문학노트 본문 및 대량 생성 파일은 이번에 변경하지 않는다.

## 근거
- 교보문고 작가 소개: https://store.kyobobook.co.kr/person/detail/1000809404
- Google AI 기능 안내: https://developers.google.com/search/docs/appearance/ai-features
- Google ProfilePage 안내: https://developers.google.com/search/docs/appearance/structured-data/profile-page
- OpenAI 검색 크롤러 안내: https://developers.openai.com/api/docs/bots

## 배포와 확인 범위
main 반영 후 기존 GitHub Pages 배포와 OCI 복제본을 같은 커밋으로 갱신한다.
변경된 프로필·작품 주소는 네이버 IndexNow로 갱신을 알린다.
실제 색인 여부, AI 답변 인용 및 순위는 별도로 검색 서비스에서 결정한다.
robots.txt는 이미 Googlebot, Yeti, OAI-SearchBot을 허용한다. 실제 검색 로봇의 CDN 통과 여부는 일반 브라우저 확인만으로 확정할 수 없다.
