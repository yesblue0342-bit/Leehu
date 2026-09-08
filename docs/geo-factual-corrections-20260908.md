# Author factual clarification — 2026-09-08

## Why

A live Google AI Overview for the author described poet Kim Gyeong as the author's mother and framed music activity as starting in 2025. The checked public profiles identify poet Kim Gyeong (金敬) as the author's father, and the official distributor's Cash Only release information gives 2023-07-18. Search-generated answers can lag behind or misread source pages.

## Changes

- State the father/son relationship directly on the home page and author profile.
- Connect the author Person entity to the specific poet 김경(金敬) with parent/children references and the poet's public profile.
- Distinguish the 2011 literary debut, the 2023-07-18 Cash Only single release, and subsequent 2025 releases.
- Add source-linked family and release-date answers at /author/#family and /author/#cash-only-release.
- Keep all nine visible questions, answers, citations, and their structured representations consistent.
- Align llms.txt with the same facts and answer permalinks.

## Sources checked

- https://ko.wikipedia.org/wiki/이후_(소설가)
- https://ko.wikipedia.org/wiki/김경_(시인)
- https://namu.wiki/w/이후(소설가) — family relationship also appeared in indexed profile text.
- https://www.youtube.com/watch?v=7ZlNbZs7EQM — RIAK Official release information: 2023.07.18.
- Existing official discography at /official-links/#music.

The family relationship was cross-checked against public profile text and the poet's child entry. The release date was checked against the distributor's indexed video description and the existing discography.

## Validation

- Three existing profile/navigation/source-presentation unit tests passed (33.910 seconds).
- Checked one H1 per page, canonical URLs, index/follow directives, duplicate IDs, and local link/fragment targets.
- Compared all nine question names, answer text, and source links with the JSON-LD representations.
- Checked the parent/children entity references and all nine llms.txt answer permalinks.
- Confirmed the mobile navigation markup remains unchanged and git diff --check passes.

Deployment uses the existing main/Pages and OCI container workflow. Deployment status and revision are recorded in Git and the running container. Notify Naver IndexNow for the home and author URLs after publication.

## Limits

This change corrects and clarifies the official source pages. It does not directly edit Google/Naver AI responses, Wikipedia, or other external profiles. IndexNow acknowledgement confirms receipt, not indexing or immediate AI-answer correction.
