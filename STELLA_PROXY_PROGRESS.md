# 이후.com — GitHub 차단망 우회 점검 (Task C)

## 결과: 변경 없음 (N/A)
이후.com(이 repo)은 **정적 사이트**다. `index.html`·`stella_cloudflare_worker.js`에
**GitHub 런타임 호출(api.github.com / raw.githubusercontent.com)이나 외부 fetch가 0건**(grep 확인).
자기 콘텐츠를 같은 호스트에서 직접 서빙하므로 GitHub를 경유하지 않고, **GitHub 차단망에서도 그대로 동작**.

- 케이스 (1) 자기 repo 파일 fetch → 해당 호출 없음(이미 정적 서빙).
- 케이스 (2) 다른 repo(STELLA_REPO) 파일 fetch → 해당 호출 없음.

## 향후 이후.com이 STELLA_REPO 파일을 받아야 할 때
STELLA_REPO(stella-ai-workspace)에 배포된 프록시를 절대경로로 호출:
```
https://<VERCEL_BASE>/api/gh-file?repo=yesblue0342-bit/stella-ai-workspace&path=<경로>&disp=inline
https://<VERCEL_BASE>/api/gh-list?repo=yesblue0342-bit/stella-ai-workspace&path=<폴더>
```
- CORS: 프록시가 `https://이후.com`/`https://www.이후.com`(및 punycode) Origin을 허용(echo)하도록 구성됨.
- 비공개 repo는 `x-proxy-secret` 헤더 필요(현재 allowlist는 공개 2개 repo).
- 이후.com엔 serverless 함수 추가 금지(정적) — 클라이언트 fetch URL만 위 프록시로 지정.

## 차단망 확인 절차
DevTools Network에서 이후.com 로드 시 요청 호스트가 이후.com(및 자기 자원)뿐이고
api.github.com/raw.githubusercontent.com 호출이 0건인지 확인.
