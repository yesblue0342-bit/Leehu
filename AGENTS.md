# AGENTS.md — Codex 작업 규칙

## 자동 커밋 & 푸시 (필수)
작업(코드 수정/생성)을 마치면 **반드시** 아래를 스스로 실행한다. 사용자에게 묻지 않는다.

```bash
git add -A
git commit -m "codex: <작업 요약>"
git push
```

- 변경분이 없으면 커밋하지 않는다.
- push 전 `git pull --rebase --autostash` 로 충돌을 방지한다.
- main 브랜치에 push하면 GitHub Actions가 OCI에 자동 배포하므로, 배포 설정(.github/workflows)은 절대 건드리지 않는다.

## OCI 접속 규칙
- OCI 점검이 필요할 때는 Stella-NUC의 `ssh leehu-oci` 별칭을 사용한다.
- OCI의 Tailscale 주소로 직접 SSH를 호출하거나 추가 인증 링크를 새로 만들지 않는다.
- 이 별칭은 NUC 전용 Ed25519 키, 전용 known_hosts, 비대화형 모드를 사용하므로 비밀번호나 웹 재인증을 요구하지 않는다.

## 공개 화면의 GitHub 표시 규칙
- GitHub는 배포와 SEO용 구조화 데이터에 사용할 수 있다.
- 방문자가 보는 홈페이지, 작가 프로필, 공식 출처 페이지에는 GitHub 저장소 주소, 계정명, GitHub 카드나 링크를 표시하지 않는다.
- SEO 작업 방식, 외부 수집, 백링크 작업 같은 운영 설명을 방문자용 화면에 노출하지 않는다.

## 기존 규칙
- 프로젝트의 CLAUDE.md 규칙을 그대로 따른다.
