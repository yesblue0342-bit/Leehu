# OpenSEO 에이전트 스킬 스냅샷

이 폴더는 오픈소스 SEO 도구 [OpenSEO](https://github.com/every-app/open-seo)(Semrush·Ahrefs 대체, MIT 라이선스)의
에이전트 스킬을 소설가 이후 공식 홈페이지 저장소 안에서 바로 쓰기 위해 복제한 스냅샷입니다.

- 원본 저장소: https://github.com/every-app/open-seo
- 복제 기준 커밋: `95c4d10c1c1d7bf57ad7328a682a86e16eec2f06` (release v0.1.10, 2026-09-30), 플러그인 버전 1.0.6 (`plugins/openseo/.claude-plugin/plugin.json`)
- 원본 경로: `plugins/openseo/skills/*` → `skills/openseo/<skill>/SKILL.md`(바이트 동일 복사, 로컬 수정 없음), `plugins/openseo/README.md`, `plugins/openseo/mcp.json`, `LICENSE`
- 원본에서 스킬의 원천은 `.agents/skills/`이고 `plugins/openseo/skills/`는 CI가 검증하는 생성 사본이므로, 릴리스 커밋의 플러그인 사본을 스냅샷하는 것으로 충분합니다.
- 라이선스: MIT (`LICENSE` 원문 동봉). 저작권 표시와 라이선스 고지를 유지하면 수정·재배포할 수 있습니다.
- 원본 안내문: `UPSTREAM-README.md`

## 무엇을 위한 것인가

OpenSEO 자체는 Cloudflare/Docker에 올리는 웹 앱 + MCP 서버이고, 키워드·백링크·순위 데이터는 DataForSEO 유료 API를
사용합니다. 이 저장소는 정적 사이트이므로 앱을 돌리지 않고, 다음 두 가지만 가져옵니다.

1. **감사 방법론** — `seo-audit`(사이트 감사 → 기회 목록 → 1~3개 권장 조치 → 정직한 효과 추정 → 검토 → 보고서),
   `seo-report`(한 장짜리 보고서 작성 규칙), `seo-coach`(초보자용 다음 단계 안내). 이 세 스킬은 MCP 없이도
   "어떤 순서로 무엇을 확인하고 어떻게 보고하는가"의 기준으로 쓸 수 있습니다.
2. **크롤러 점검 항목** — OpenSEO 사이트 감사가 페이지마다 검사하는 항목(제목·설명 누락/중복/길이, H1, 제목 단계 건너뜀,
   noindex, canonical, 얇은 본문, alt 없는 이미지, 발신 링크 없음, 깨진 내부 링크, 고아 페이지 등)을
   `scripts/naver_seo_audit.py`가 표준 라이브러리만으로 재현하고, 네이버 서치어드바이저 가이드 항목을 추가했습니다.

## 스킬별 MCP 의존도

| 스킬 | OpenSEO MCP 없이 사용 | 비고 |
|------|------------------------|------|
| `seo-audit` | 방법론은 가능, 데이터 호출은 불가 | 순위·검색량 호출(`get_serp_results` 등)은 MCP 필요. 로컬 점검은 `scripts/naver_seo_audit.py`로 대체. 순위는 날짜를 적은 실제 네이버 검색으로만 확인 |
| `seo-report` | 가능 (보고서 작성 규칙) | `save_report`/`list_reports`는 MCP 전용. 이 저장소에서는 `docs/`에 마크다운으로 저장 |
| `seo-coach` | 가능 | 프로젝트 컨텍스트 도구만 MCP |
| `seo-project-setup` | 부분 | Search Console 연결·프로젝트 저장은 MCP |
| `keyword-research` | 불가 | DataForSEO 검색량·난이도 필요 |
| `keyword-clustering` | 불가 | 동일 |
| `competitor-analysis` | 불가 | 동일 |
| `competitive-landscape` | 불가 | 동일 |
| `link-prospecting` | 불가 | 백링크 데이터 필요 |
| `local-seo` | 불가 | Google Maps 데이터 필요. 이 사이트와 무관 |

MCP를 연결하려면 OpenSEO 계정(호스팅 또는 자체 호스팅)과 `mcp.json`의 서버 주소를 사용합니다.
이 저장소는 OpenSEO 계정·API 키를 포함하지 않으며, 연결 여부는 운영자가 결정합니다.

## 이 저장소 전용 스킬

네이버 검색을 대상으로 이 사이트에 맞게 다듬은 절차는 `skills/leehu-naver-seo/SKILL.md`에 있습니다.
그 스킬이 위 방법론과 `scripts/naver_seo_audit.py`를 결합해 "점검 → 핵심 페이지 수정 → 재생성 → 테스트 → 운영자 제출 안내"
순서로 작업하도록 안내합니다.

## 갱신 방법

```bash
git clone --depth 1 https://github.com/every-app/open-seo /tmp/open-seo
diff -r /tmp/open-seo/plugins/openseo/skills skills/openseo --exclude='LICENSE' --exclude='README.md' --exclude='UPSTREAM-README.md' --exclude='mcp.json'   # 먼저 변경점을 읽는다
cp -r /tmp/open-seo/plugins/openseo/skills/. skills/openseo/
cp /tmp/open-seo/LICENSE skills/openseo/LICENSE
cp /tmp/open-seo/plugins/openseo/README.md skills/openseo/UPSTREAM-README.md
cp /tmp/open-seo/plugins/openseo/mcp.json skills/openseo/mcp.json
git -C /tmp/open-seo rev-parse HEAD   # 이 README의 복제 기준 커밋과 플러그인 버전을 갱신
```

갱신은 원본 `plugins/openseo/.claude-plugin/plugin.json`의 버전이 올라갔을 때만 하고, 덮어쓰기 전에 `seo-audit`·`seo-report`·`seo-coach`의 방법 변경을 다시 읽습니다.
여기의 스킬은 참고용 방법론이며 슬래시 명령으로 직접 호출하지 않습니다(원본 `seo-audit`은 OpenSEO가 연결되지 않으면 멈추도록 쓰여 있습니다).

원본의 `AGENTS.md`는 스킬을 바꿀 때 플러그인 버전을 올리도록 요구하지만, 여기서는 스냅샷만 보관하므로
버전 파일(`.claude-plugin/plugin.json` 등)은 복제하지 않습니다.
