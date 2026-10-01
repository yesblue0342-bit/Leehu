import json
import tempfile
import unittest
from pathlib import Path

from scripts import naver_seo_audit as audit_tool

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = audit_tool.ORIGIN

GOOD_HEAD = (
    '<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title>'
    '<meta name="description" content="{description}">'
    '<link rel="canonical" href="{url}">'
    '<meta property="og:type" content="website"><meta property="og:title" content="{title}">'
    '<meta property="og:description" content="{description}"><meta property="og:url" content="{url}">'
    '<meta property="og:image" content="{origin}/og-image.jpg">{extra}</head><body>'
)
LONG_DESCRIPTION = "소설가 이후의 공식 홈페이지입니다. 소설 연과 데자뷔와 소나기, 시집 Fantasy를 소개하고 작가 프로필과 공식 채널을 안내합니다."
BODY = " ".join(f"문장{i} 본문 내용입니다." for i in range(80))


def png_bytes(width: int, height: int) -> bytes:
    header = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR"
    return header + width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00" + b"\x00" * 6000


def jpeg_bytes(width: int, height: int) -> bytes:
    # SOI, then a minimal SOF0 segment: length 17, precision 8, height, width, 3 components
    sof = b"\xff\xc0" + (17).to_bytes(2, "big") + b"\x08" + height.to_bytes(2, "big") + width.to_bytes(2, "big") + b"\x03" + b"\x01\x22\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + sof + b"\xff\xd9"


class NaverSeoAuditTest(unittest.TestCase):
    def build_site(self, root: Path) -> None:
        graph = json.dumps(
            {
                "@context": "https://schema.org",
                "@graph": [
                    {"@type": "Person", "name": "김경", "url": "https://example.org/", "sameAs": ["https://ko.wikipedia.org/wiki/x"]},
                    {
                        "@type": "Person",
                        "@id": f"{ORIGIN}/#person",
                        "name": "이후",
                        "url": f"{ORIGIN}/",
                        "sameAs": ["https://blog.naver.com/example", "https://ko.wikipedia.org/wiki/example"],
                    },
                ],
            },
            ensure_ascii=False,
        )
        (root / "index.html").write_text(
            GOOD_HEAD.format(
                title="소설가 이후 공식 홈페이지", description=LONG_DESCRIPTION, url=f"{ORIGIN}/", origin=ORIGIN,
                extra=f'<script type="application/ld+json">{graph}</script>',
            )
            + f'<h1>소설가 이후</h1><main><p>{BODY}</p></main><a href="/author/">프로필</a><a href="/missing/">없는 페이지</a>'
            + '<a href="/copy/">사본</a><img src="/x.png"></body></html>',
            encoding="utf-8",
        )
        (root / "author").mkdir()
        (root / "author" / "index.html").write_text(
            '<!doctype html><html><head><meta charset="utf-8"><title>작가 작가 작가 프로필</title>'
            f'<link rel="canonical" href="{ORIGIN}/works/"></head>'
            '<body><h1>하나</h1><h1>둘</h1><h2>소제목</h2><h4>건너뜀</h4><p>짧은 본문</p></body></html>',
            encoding="utf-8",
        )
        (root / "copy").mkdir()
        (root / "copy" / "index.html").write_text(
            GOOD_HEAD.format(title="사본 페이지 제목", description=LONG_DESCRIPTION, url=f"{ORIGIN}/copy/", origin=ORIGIN, extra="")
            + f'<h1>사본</h1><main><p>{BODY}</p></main><a href="/">홈</a></body></html>',
            encoding="utf-8",
        )
        (root / "orphan").mkdir()
        (root / "orphan" / "index.html").write_text(
            GOOD_HEAD.format(title="고아 페이지 제목", description="고아 페이지 설명입니다. 다른 페이지와 겹치지 않는 문장으로 길이를 맞추기 위해 조금 더 적어 둡니다.", url=f"{ORIGIN}/orphan/", origin=ORIGIN, extra="")
            + f'<h1>고아</h1><main><p>{BODY} 추가 문장.</p></main><a href="/">홈</a></body></html>',
            encoding="utf-8",
        )
        (root / "works").mkdir()
        (root / "works" / "index.html").write_text(
            GOOD_HEAD.format(title="작품 페이지 제목", description="작품 페이지 설명입니다. 소설과 시집의 서점 정보를 안내하며 다른 페이지와 겹치지 않는 문장으로 적어 둡니다.", url=f"{ORIGIN}/works/", origin=ORIGIN, extra="")
            + f'<h1>작품</h1><main><p>{BODY} 작품 문장.</p></main><a href="/">홈</a></body></html>',
            encoding="utf-8",
        )
        (root / "og-image.jpg").write_bytes(png_bytes(1200, 630))
        (root / "robots.txt").write_text("User-agent: *\nDisallow: /\nUser-agent: Yeti\nDisallow: /\n", encoding="utf-8")
        (root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?><sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<sitemap><loc>{ORIGIN}/sitemap-pages.xml</loc></sitemap></sitemapindex>",
            encoding="utf-8",
        )
        (root / "sitemap-pages.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"<url><loc>{ORIGIN}/</loc><lastmod>2026-10-01</lastmod></url>"
            f"<url><loc>{ORIGIN}/gone/</loc></url>"
            "<url><loc>https://other.example/</loc></url></urlset>",
            encoding="utf-8",
        )
        (root / "literature").mkdir()
        (root / "literature" / "rss.xml").write_text(
            '<?xml version="1.0" encoding="utf-8"?><rss version="2.0"><channel><title>t</title>'
            f"<link>{ORIGIN}/literature/</link><description>d</description>"
            f"<item><title>a</title><link>{ORIGIN}/orphan/</link><description>짧은 요약</description></item>"
            "</channel></rss>",
            encoding="utf-8",
        )

    def test_reports_openseo_and_naver_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_site(root)
            result = audit_tool.audit(root, sample=None)
            found = {(issue["type"], issue["page"]) for issue in result["issues"]}
            for expected in (
                ("broken-internal-link", "index.html"),
                ("images-missing-alt", "index.html"),
                ("duplicate-content", "copy/index.html"),
                ("missing-meta-description", "author/index.html"),
                ("multiple-h1", "author/index.html"),
                ("heading-order-skip", "author/index.html"),
                ("canonicalized-page", "author/index.html"),
                ("thin-content", "author/index.html"),
                ("no-outgoing-links", "author/index.html"),
                ("missing-lang", "author/index.html"),
                ("repeated-keyword", "author/index.html"),
                ("orphan-page", "orphan/index.html"),
                ("robots-blocks-yeti", "robots.txt"),
                ("robots-missing-sitemap", "robots.txt"),
                ("sitemap-missing-file", "sitemap.xml"),
                ("sitemap-host-mismatch", "sitemap.xml"),
                ("feed-excerpt-only", "literature/rss.xml"),
                ("og-image-shared", "index.html"),
                ("missing-verification-file", "/"),
                ("sameas-non-channel", "index.html"),
            ):
                self.assertIn(expected, found)
            self.assertNotIn(("missing-channel-markup", "index.html"), found)
            self.assertEqual(result["facts"]["sitemap"]["urls"], 3)
            channel = result["facts"]["channel_markup"]
            self.assertEqual(channel["person"], "이후")
            self.assertEqual(channel["channel_same_as"], ["https://blog.naver.com/example"])
            report = audit_tool.render_report(result)
            for heading in ("## 점검 결과 요약", "## 발견 항목", "## 그 밖에 확인한 항목", "### 오프라인에서 확인 불가", "## 이 보고서를 만든 방법"):
                self.assertIn(heading, report)
            self.assertNotIn("### 제목이 10자 미만", report)
            self.assertIn("### 제목이 10자 미만", audit_tool.render_report(result, verbose=True))

    def test_exit_codes_and_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.build_site(root)
            out = root / "report.md"
            raw = root / "report.json"
            code = audit_tool.main(["--root", str(root), "--full", "--out", str(out), "--json", str(raw)])
            self.assertEqual(code, 2)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("# 네이버 SEO 로컬 점검"))
            self.assertEqual(json.loads(raw.read_text(encoding="utf-8"))["pages_crawled"], 5)
            (root / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: " + ORIGIN + "/sitemap.xml\n", encoding="utf-8")
            (root / "sitemap-pages.xml").write_text(
                '<?xml version="1.0" encoding="utf-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                f"<url><loc>{ORIGIN}/</loc></url></urlset>",
                encoding="utf-8",
            )
            (root / "index.html").write_text(
                (root / "index.html").read_text(encoding="utf-8").replace('<a href="/missing/">없는 페이지</a>', ""),
                encoding="utf-8",
            )
            self.assertEqual(audit_tool.main(["--root", str(root), "--full", "--out", str(out), "--json", str(raw)]), 0)
            self.assertEqual(audit_tool.main(["--root", str(root), "--full", "--out", str(out), "--fail-on", "warning"]), 1)
            self.assertEqual(
                audit_tool.main(["--root", str(root), "--full", "--out", str(out), "--fail-on", "warning", "--baseline", str(raw)]),
                0,
            )

    def test_main_requires_out_path(self):
        with self.assertRaises(SystemExit):
            audit_tool.main(["--root", str(ROOT)])

    def test_repeated_keywords_ignores_stopwords_and_short_latin_tokens(self):
        self.assertEqual(audit_tool.repeated_keywords("you and you and you"), [])
        self.assertEqual(audit_tool.repeated_keywords("me me me her her her"), [])
        self.assertEqual(audit_tool.repeated_keywords("소설 소설 소설 이야기"), ["소설"])
        self.assertEqual(audit_tool.repeated_keywords("love love love"), ["love"])
        self.assertEqual(audit_tool.repeated_keywords("소설 소설 소설 이야기", limit=4), [])

    def test_image_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            png = Path(directory) / "a.png"
            png.write_bytes(png_bytes(320, 200))
            self.assertEqual(audit_tool.image_dimensions(png), (320, 200))
            jpeg = Path(directory) / "b.jpg"
            jpeg.write_bytes(jpeg_bytes(1200, 630))
            self.assertEqual(audit_tool.image_dimensions(jpeg), (1200, 630))

    def test_repository_has_no_critical_issue(self):
        result = audit_tool.audit(ROOT, sample=20)
        critical = [issue for issue in result["issues"] if issue["severity"] == "critical"]
        self.assertEqual(critical, [])
        self.assertEqual(result["facts"]["channel_markup"]["person"], "이후")
        self.assertIn("https://blog.naver.com/yesblue0342", result["facts"]["channel_markup"]["channel_same_as"])


if __name__ == "__main__":
    unittest.main()
