# Author identity and bibliographic consistency — 2026-09-08

## Corrected findings
- Fantasy used different identifiers and publication dates on the author/works and public-links pages. Reused `/works/#fantasy` everywhere and qualified 2024-10-18 as the Kyobo paperback catalog date. YES24 currently lists 2024-10-04 for the same ISBN; this source discrepancy is recorded here rather than treating both sources as date confirmation.
- The music section created a separate MusicGroup under a nonexistent `/music/` page. It now describes the visible Cash Only recording and links `byArtist` to the existing Person identity.
- Replaced unsupported blanket long-novel classification with the broader, source-supported novel classification on the four core pages.
- Added publisher-confirmed paperback dates and ISBNs for four books. Paperback editions use workExample/exampleOfWork; existing ebook links are preserved without assigning paperback identifiers to ebooks.
- Updated the public-links sitemap modification date. Existing literary notes, index policy, navigation and deployment workflows are preserved.

## Publication evidence
- 데자뷔: 좋은땅, 2016-10-10, ISBN 9791159824234 — https://www.g-world.co.kr/book/1468
- 환상: 좋은땅, 2012-10-08, ISBN 9788964493274 — https://www.g-world.co.kr/book/1469
- 별이 빛나는 밤에: 좋은땅, 2014-03-15, ISBN 9788964498323 — https://www.g-world.co.kr/book/819
- 처음처럼: 좋은땅, 2015-02-17, ISBN 9791157665990 — https://www.g-world.co.kr/book/1049
- Fantasy: Kyobo catalog 2024-10-18, ISBN 9791169572347 — https://product.kyobobook.co.kr/detail/S000214458787
- Fantasy alternate catalog date: YES24 2024-10-04 — https://www.yes24.com/product/goods/134295859

## Validation scope
Four new identity tests cover shared Fantasy data, paperback/ebook separation and ISBN checksums, music/person linkage, and visible question-answer consistency. Existing homepage metadata, public profile and visitor-facing privacy regressions are also checked.

Naver person ordering is determined by its own search/click signals: https://help.naver.com/service/30003/contents/1174?lang=ko
AI search uses normal search quality and discoverability principles: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
No search rank, index inclusion or AI citation is guaranteed by these changes.
