---
name: leehu-naver-seo
description: Audit and improve the Naver search presence of novelist Lee Hu's official static site (xn--hu5b23z.com) using the vendored OpenSEO methodology and the credit-free local audit script. Use when the user asks to check or improve SEO, Naver exposure, same-name (동명이인) disambiguation, structured data, sitemap/RSS health or Search Advisor readiness for this repository. Not for literature batch publishing (use leehu-literature-publisher) and not for IndexNow-only work.
---

# Lee Hu Naver SEO

Apply the OpenSEO audit discipline (`skills/openseo/seo-audit/SKILL.md`: orient → investigate → shortlist → choose 1–3 changes → size the benefit honestly → review → report) to this static site, with Naver Search Advisor rules as the checklist. OpenSEO's MCP data tools are not available here; `scripts/naver_seo_audit.py` replaces the crawler, and ranking claims must come from a live Naver search the user or a remote browser performs, dated.

## Goal and honesty

- The owner's goal is that novelist 이후 (李後, Lee Hu) stays the representative person for the name 이후 on Naver and that the official site ranks for 소설가 이후 / 이후 작가 / 이후 소설 queries.
- Naver orders same-name people by aggregated searches and clicks (help.naver.com/service/30003/contents/1174). Nothing in this repository can set that order. Report what files say, what a dated search showed, and what the owner must do in Search Advisor or 인물정보.
- Never promise a rank, never fabricate biographical facts, never add visitor-facing text about GitHub, SEO operations, backlinks or crawling (AGENTS.md; tests reject `GitHub|github.com|SEO|백링크` in note bodies).
- Any new `sameAs` or channel URL must be confirmed by the owner or an already-public source the owner controls (for example the links the owner registered in Naver 인물정보) before it is added. A wrong `sameAs` is worse than none.

## Workflow

1. **Baseline.** `git status` must be clean. Run `python3 -m unittest discover -s tests` and record the failure set; the rule is "no new failures". Count expectations in `tests/test_static_literature.py` and `tests/test_leehu_batch_*.py` must match `content/literature-index-policy.json`; if they do not, fix them in a separate commit together with the README numbers.
2. **Rebuild before auditing.** `python3 scripts/literature_batch.py build --expected-count <number of content/literature/*.json>` is idempotent: afterwards `git status` may show only `sitemap.xml`/`literature/feed.xml`/`literature/rss.xml` and files you edited on purpose. If note pages changed, stop and find out why before going on. The audit must read builder output, not stale committed artifacts.
3. **Audit.** `python3 scripts/naver_seo_audit.py --full --out <path outside the public tree, or docs/naver-seo-audit-YYYYMMDD.md> --json /tmp/audit.json` (about 20 seconds for 7,400 pages; `--sample 200` for iteration). Exit 2 means a critical issue; `--fail-on warning` makes warnings fail too; `--baseline previous.json` fails only on issues that were not in the previous run. Read 점검 결과 요약 and 그 밖에 확인한 항목. Network-only checks (crawl status, redirects, response time, live rankings) are listed as not verifiable offline; do not report them as passed.
4. **Live check (optional, dated).** If a remote browser tool is available, fetch `https://search.naver.com/search.naver?query=이후` and `…query=소설가+이후` and record: who the 인물 panel shows, the 같은 이름 다른 인물 list, whether the official site appears in the web section, and the date. These are observations, not causes.
5. **Shortlist and choose.** Write the opportunity table (page | observed problem | evidence | proposed change | who searches | benefit | effort | uncertainty) in `docs/`. Prefer bounded changes to the core pages (`index.html`, `author/index.html`, `works/index.html`, `official-links/index.html`, `seo-updates/`) over anything that rewrites the 7,000+ literature notes. The agent, not the tool, writes 다음 조치.
6. **Apply.** Typical safe changes: unique titles/descriptions, disambiguation facts already verified on the site (1982 성남 출생, 2011 소설 《연》 데뷔, 李後, 네이버 인물정보 ID 215161, 아버지 시인 김경), Person `sameAs` channel list at the root page (Naver 연관채널 markup: name, url, sameAs), Open Graph images that exist in the repo, feed changes in `scripts/build_literature.py` (`literature/feed.xml`, the capped full-text feed for Naver; `literature/rss.xml` is the complete index the list-page search reads) or `scripts/build_updates_index.py` (`seo-updates/rss.xml`). When a core page changes, bump its JSON-LD `dateModified`; the builder derives sitemap `lastmod` from it.
7. **Regenerate.** Run the literature build again (step 2) when anything under `scripts/build_literature.py`, core-page dates or `seo-updates/` changed; run `python3 scripts/build_updates_index.py` when `seo-updates/` changed. New public files must also be added to `server.py` `PUBLIC_STATIC_FILES` and the `Dockerfile` COPY list.
8. **Verify.** `python3 -m unittest discover -s tests` (no new failures), `python3 scripts/naver_seo_audit.py --full --out /tmp/audit.md` (exit 0), JSON-LD parse of every edited page, `git diff --check`, and a grep that visitor-facing pages gained no forbidden words.
9. **Commit and push to main** (AGENTS.md: `git pull --rebase --autostash` first). GitHub Pages deploys main.
10. **Hand over operator steps.** IndexNow goes through the owner's existing `scripts/submit_indexnow.py` process and receipt ledger; do not submit from an agent session. List the Search Advisor and 인물정보 steps the owner must do (사이트맵·RSS 제출, 수집 요청, 사이트 간단 체크, 인물정보 본인참여 수정신청) with the reason for each.

## Report

Write the result as `docs/naver-seo-<date>.md` in the seo-report house style: verdict bullets first, one to three recommendations with Do this / Why, a "그 밖에 확인한 항목" table, and a closing "이 보고서를 만든 방법" section that separates tool output from what was verified by hand. The report is public on GitHub Pages like the rest of `docs/`: never put keys, receipt data or details about other same-name people in it, and never link it from a visitor-facing page.
