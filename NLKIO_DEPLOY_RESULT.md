# nlkio 런처 배포 결과

## 탐지(작업 0)
- GITHUB_OWNER: `yesblue0342-bit`
- REPO: **`yesblue0342-bit/leehu`** (자동 탐지) — `CNAME = xn--hu5b23z.com`(= 이후.com), 구글/네이버 사이트 인증 파일·sitemap 존재로 확정.
- HOMEPAGE_FILE: **`index.html`** (유일한 메인 HTML, 77KB)
- 배포 방식: **GitHub Pages**(CNAME 커스텀 도메인) — `main` 브랜치 푸시 시 자동 배포.

## 삽입 위젯(작업 1~4)
- 위치: `index.html` `</body>` 직전(footer/레이아웃 무간섭, 자기완결 블록).
- 형태: 우측 하단 고정(`position:fixed; right/bottom:16px`, 모바일 12px), 지름 40px 원형(모바일 38px), 배경 `#16A34A`(BRAND_GREEN), 흰색 **N·L 겹친 모노그램 SVG**.
- 가시성: 평소 `opacity:.42`(은은), hover/focus 시 `opacity:1` + 살짝 떠오름.
- id/주석: `nlkio-mark` / `nlkio-style` / `nlkio-script` (PROGRAM_ID 사용).

## 라벨링(작업 2)
- `title` / `aria-label` = **"이후 李後"** (중립·장식 마크). 원격/VPS/login/콘솔/서버 등 기능 노출 문구 **없음**(grep 검증).

## 클릭 동작(작업 3)
- 클릭 → `window.open("https://wenexer.xn--hu5b23z.com", "_blank", "noopener,noreferrer")`.
- `wenexer.xn--hu5b23z.com` = `wenexer.이후.com`의 punycode(브라우저 호환·인코딩 안전).
- **프록시 한 단계 경유**: 위젯은 직접 원격 콘솔/VPS가 아니라 **wenexer 프록시 게이트웨이(단일 홉)** 로 이동하고, 실제 콘솔은 그 뒤에 위치. 브라우저에는 프록시 도메인만 노출.

## 검증(작업 5)
| 항목 | 결과 |
|------|------|
| nlkio 인라인 JS `new Function` 파싱 | ✅ |
| 위젯 버튼/녹색/고정위치/40px 원형 | ✅ |
| 게이트웨이 URL(punycode) + window.open noopener | ✅ |
| 중립 라벨(원격/VPS/login 문구 0) | ✅ |
| N·L 2-path 모노그램 SVG | ✅ |
| `</body>`·`</html>` 각 1개(구조 무손상), footer 보존 | ✅ |
| 모바일 미디어쿼리(위치·크기) | ✅ |

## 배포 상태(작업 6)
- 변경 파일: `index.html`(위젯 삽입), `NLKIO_DEPLOY_RESULT.md`(신규).
- 커밋 → **`main` 푸시** → GitHub Pages 자동 재배포(보통 1~2분).
- PWA/Service Worker·캐시 버전 없음 → bump 불필요(GitHub Pages 정적 서빙).

## 남은 수동 작업(작업 7)
- **프록시 구축 확인**: `https://wenexer.이후.com`(= wenexer.xn--hu5b23z.com)에 **프록시 게이트웨이(리버스 프록시 + 인증)** 가 실제로 떠 있어야 클릭이 의미 있음. 이 wenexer 가 한 단계 프록시 홉으로 동작하며 실제 원격 콘솔/VPS는 그 뒤에 둔다. 미구축 시 DNS(wenexer 서브도메인 A/CNAME) + 리버스프록시(예: Cloudflare/Nginx) + 인증부터 세울 것. **VPS 직접 노출 금지(반드시 wenexer 프록시 경유).**
- 배포 확인은 KH 브라우저에서: 이후.com 우측 하단 녹색 마크 렌더 → 클릭 시 새 탭으로 게이트웨이 오픈.
- (한계) 샌드박스는 라이브 URL 직접 접근 불가 → 정적 검증까지 수행.
