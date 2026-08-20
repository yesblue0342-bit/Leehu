import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

import server


TOKEN = "test-token"


def sample_payload(**overrides):
    data = {
        "title": "Shakespeare on Love",
        "quote": "Love looks not with the eyes, but with the mind.",
        "source_author": "William Shakespeare",
        "source_work": "A Midsummer Night's Dream",
        "source_location": "Act 1, Scene 1",
        "source_language": "en",
        "translation_note": "영문 원전 기반 자체 번역",
        "rights_note": "원전 및 번역 사용 조건 확인",
        "commentary": (
            "사랑은 상대를 있는 그대로 보는 일이라기보다, 때로는 보고 싶은 모습으로 바라보는 "
            "일인지도 모릅니다. 소설 『연』을 쓰던 때에도 사랑이 사람의 기억을 어떻게 바꾸는지 "
            "오래 생각했습니다. 오늘은 이 문장을 함께 나누고 싶습니다."
        ),
        "closing": "소설가 이후 드림",
        "author": "소설가 이후",
        "published_at": "2026-07-27T09:00:00+09:00",
        "tags": ["사랑", "셰익스피어", "고전문학", "소설가 이후"],
        "related_work": {
            "name": "연",
            "url": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756",
        },
        "status": "published",
    }
    data.update(overrides)
    return data


class LiteratureServerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.old_posts_dir = server.POSTS_DIR
        self.old_literature_posts_dir = server.LITERATURE_POSTS_DIR
        server.POSTS_DIR = root / "board-posts"
        server.LITERATURE_POSTS_DIR = root / "literature-posts"
        server.ensure_dirs()
        self.old_token = server.os.environ.get("LITERATURE_API_TOKEN")
        self.old_publication_mode = server.os.environ.get("LITERATURE_PUBLICATION_MODE")
        server.os.environ["LITERATURE_API_TOKEN"] = TOKEN
        server.os.environ["LITERATURE_PUBLICATION_MODE"] = "dynamic"
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.LeehuHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()
        if self.old_token is None:
            server.os.environ.pop("LITERATURE_API_TOKEN", None)
        else:
            server.os.environ["LITERATURE_API_TOKEN"] = self.old_token
        if self.old_publication_mode is None:
            server.os.environ.pop("LITERATURE_PUBLICATION_MODE", None)
        else:
            server.os.environ["LITERATURE_PUBLICATION_MODE"] = self.old_publication_mode
        server.POSTS_DIR = self.old_posts_dir
        server.LITERATURE_POSTS_DIR = self.old_literature_posts_dir
        self.tmp.cleanup()

    def request(self, method, path, body=None, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {}
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        data = response.read()
        content_type = response.getheader("Content-Type") or ""
        conn.close()
        return response.status, content_type, data

    def json_request(self, method, path, body=None, token=None):
        status, content_type, data = self.request(method, path, body, token)
        parsed = json.loads(data.decode("utf-8")) if data else {}
        return status, content_type, parsed

    def create_post(self, **overrides):
        status, _, data = self.json_request("POST", "/api/literature/posts", sample_payload(**overrides), TOKEN)
        self.assertEqual(status, 201, data)
        return data["post"]

    def test_home_and_board_api_work(self):
        status, content_type, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn("이후의 문학노트".encode("utf-8"), body)

        status, _, board = self.json_request("POST", "/api/board/posts", {"title": "응원", "body": "좋은 글입니다"})
        self.assertEqual(status, 201)
        status, _, board_list = self.json_request("GET", "/api/board/posts?q=%EC%9D%91%EC%9B%90")
        self.assertEqual(status, 200)
        self.assertEqual(len(board_list["posts"]), 1)

    def test_literature_crud_rendering_sitemap_and_rss(self):
        post = self.create_post()
        slug = post["slug"]
        self.assertEqual(post["id"], "20260727_leehu_literature_01")
        self.assertTrue(slug.startswith("20260727-leehu-literature-01-"))
        self.assertIn("canonical_url", post)

        status, content_type, html = self.request("GET", "/literature/")
        text = html.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(post["title"], text)
        self.assertIn(slug, text)

        status, content_type, homepage = self.request("GET", "/")
        homepage_text = homepage.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(post["title"], homepage_text)
        self.assertIn(slug, homepage_text)
        self.assertEqual(
            homepage_text.count("<!-- LITERATURE_LATEST_ITEMS:START -->"), 1
        )

        status, content_type, html = self.request("GET", f"/literature/{slug}")
        text = html.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("text/html", content_type)
        self.assertIn(post["title"], text)
        self.assertIn(post["quote"], text)
        self.assertIn(post["source_author"], text)
        self.assertIn(post["source_work"], text)
        self.assertIn("이후의 생각", text)
        self.assertIn(post["commentary"], text)
        self.assertIn(f'<link rel="canonical" href="{post["canonical_url"]}">', text)
        self.assertIn('<meta name="robots" content="index, follow">', text)
        self.assertIn('application/ld+json', text)
        self.assertIn('og:type" content="article"', text)

        status, _, missing = self.request("GET", "/literature/no-such-slug")
        self.assertEqual(status, 404)

        status, content_type, item = self.json_request("GET", f"/api/literature/posts/{slug}")
        self.assertEqual(status, 200)
        self.assertIn("application/json", content_type)
        self.assertEqual(item["post"]["slug"], slug)

        status, _, sitemap = self.request("GET", "/sitemap.xml")
        sitemap_text = sitemap.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn(post["canonical_url"], sitemap_text)

        status, _, rss = self.request("GET", "/literature/rss.xml")
        rss_text = rss.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn(post["title"], rss_text)

        status, _, updated = self.json_request(
            "PUT",
            f"/api/literature/posts/{slug}",
            {"commentary": post["commentary"] + " 한 번 더 다듬은 문장입니다.", "status": "published"},
            TOKEN,
        )
        self.assertEqual(status, 200, updated)
        self.assertEqual(updated["post"]["created_at"], post["created_at"])
        self.assertIn("updated_at", updated["post"])

        status, _, deleted = self.json_request("DELETE", f"/api/literature/posts/{slug}", token=TOKEN)
        self.assertEqual(status, 200, deleted)
        self.assertEqual(deleted["post"]["status"], "archived")

        status, _, archived_html = self.request("GET", f"/literature/{slug}")
        self.assertEqual(status, 404)
        status, _, sitemap_after = self.request("GET", "/sitemap.xml")
        self.assertNotIn(post["canonical_url"], sitemap_after.decode("utf-8"))
        status, _, homepage_after = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertNotIn(slug, homepage_after.decode("utf-8"))

    def test_auth_validation_duplicates_and_sequences(self):
        status, _, unauth = self.json_request("POST", "/api/literature/posts", sample_payload())
        self.assertEqual(status, 401)
        self.assertEqual(unauth["error"], "unauthorized")

        status, _, bad_token = self.json_request("POST", "/api/literature/posts", sample_payload(), "wrong")
        self.assertEqual(status, 403)

        missing = sample_payload()
        missing.pop("source_work")
        status, _, error = self.json_request("POST", "/api/literature/posts", missing, TOKEN)
        self.assertEqual(status, 400)
        self.assertIn("source_work_required", error["details"])

        short = sample_payload(commentary="짧음")
        status, _, error = self.json_request("POST", "/api/literature/posts", short, TOKEN)
        self.assertEqual(status, 400)
        self.assertIn("commentary_too_short", error["details"])

        first = self.create_post()
        status, _, duplicate = self.json_request("POST", "/api/literature/posts", sample_payload(id=first["id"]), TOKEN)
        self.assertEqual(status, 409)
        self.assertEqual(duplicate["error"], "duplicate_id_or_slug")

        second = self.create_post(
            title="Goethe on Love",
            source_author="Johann Wolfgang von Goethe",
            source_work="Faust",
            quote="A short line about love.",
        )
        self.assertEqual(second["id"], "20260727_leehu_literature_02")

        next_day = self.create_post(
            title="Yi Sang on Loneliness",
            source_author="Yi Sang",
            source_work="Wings",
            quote="A short line about loneliness.",
            published_at="2026-07-28T09:00:00+09:00",
        )
        self.assertEqual(next_day["id"], "20260728_leehu_literature_01")

        draft = self.create_post(
            title="Draft Note",
            source_author="Draft Author",
            source_work="Draft Work",
            quote="Draft quote.",
            status="draft",
        )
        status, _, public_list = self.json_request("GET", "/api/literature/posts")
        self.assertNotIn(draft["slug"], json.dumps(public_list, ensure_ascii=False))

        status, _, malicious = self.json_request(
            "POST",
            "/api/literature/posts",
            sample_payload(slug="../bad", title="<script>alert(1)</script>"),
            TOKEN,
        )
        self.assertEqual(status, 400)

    def test_xss_escape_and_persistence_after_restart(self):
        post = self.create_post(
            title="<script>alert(1)</script>",
            quote="<b>quote</b>",
            source_author="Author <A>",
            source_work="Work <W>",
            commentary="이 문장은 인용보다 훨씬 긴 해설입니다. <script>alert(1)</script> 같은 입력이 실행되지 않고 화면에는 문자로만 남아야 합니다.",
        )
        status, _, html = self.request("GET", f"/literature/{post['slug']}")
        text = html.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
        self.assertNotIn("<script>alert(1)</script>", text)

        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.LeehuHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

        status, _, item = self.json_request("GET", f"/api/literature/posts/{post['slug']}")
        self.assertEqual(status, 200)
        self.assertEqual(item["post"]["slug"], post["slug"])

    def test_dynamic_excluded_post_is_noindex_and_not_discoverable(self):
        post = self.create_post(
            id="20260806_leehu_literature_042",
            slug="20260806-leehu-literature-042-policy-excluded",
            published_at="2026-08-06T09:00:00+09:00",
        )

        status, _, detail = self.request("GET", f"/literature/{post['slug']}/")
        detail_text = detail.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn('<meta name="robots" content="noindex, follow">', detail_text)
        self.assertNotIn(">이전 글</a>", detail_text)
        self.assertNotIn(">다음 글</a>", detail_text)

        for path in ("/", "/literature/", "/literature/rss.xml", "/sitemap.xml"):
            status, _, body = self.request("GET", path)
            self.assertEqual(status, 200)
            self.assertNotIn(post["slug"], body.decode("utf-8"))

    def test_invalid_publication_mode_is_rejected(self):
        server.os.environ["LITERATURE_PUBLICATION_MODE"] = "statci"
        with self.assertRaisesRegex(RuntimeError, "static.*dynamic"):
            server.literature_publication_mode()
        server.os.environ["LITERATURE_PUBLICATION_MODE"] = "dynamic"

    def test_dynamic_rss_includes_more_than_twenty_indexable_posts(self):
        posts = []
        for sequence in range(1, 22):
            posts.append(
                self.create_post(
                    title=f"RSS note {sequence}",
                    source_author=f"Author {sequence}",
                    source_work=f"Work {sequence}",
                    quote=f"A short quote number {sequence}.",
                )
            )
        status, content_type, body = self.request("GET", "/literature/rss.xml")
        text = body.decode("utf-8")
        self.assertEqual(status, 200)
        self.assertIn("application/rss+xml", content_type)
        self.assertEqual(text.count("<item>"), 21)
        self.assertIn(posts[0]["slug"], text)


class StaticLiteratureProductionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.notes = {}
        for path in (server.ROOT / "content" / "literature").glob("*.json"):
            note = json.loads(path.read_text(encoding="utf-8"))
            if note.get("id") in {
                "20260806_leehu_literature_001",
                "20260806_leehu_literature_499",
                "20260806_leehu_literature_500",
            }:
                cls.notes[note["id"]] = note
        if len(cls.notes) != 3:
            raise AssertionError("expected static production fixtures 001, 499, and 500")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.old_posts_dir = server.POSTS_DIR
        self.old_literature_posts_dir = server.LITERATURE_POSTS_DIR
        self.old_token = server.os.environ.get("LITERATURE_API_TOKEN")
        self.old_publication_mode = server.os.environ.get("LITERATURE_PUBLICATION_MODE")
        server.POSTS_DIR = root / "board-posts"
        server.LITERATURE_POSTS_DIR = root / "literature-posts"
        server.os.environ["LITERATURE_API_TOKEN"] = TOKEN
        server.os.environ["LITERATURE_PUBLICATION_MODE"] = "static"
        server.ensure_dirs()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.LeehuHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.thread.join(timeout=5)
        self.httpd.server_close()
        server.POSTS_DIR = self.old_posts_dir
        server.LITERATURE_POSTS_DIR = self.old_literature_posts_dir
        if self.old_token is None:
            server.os.environ.pop("LITERATURE_API_TOKEN", None)
        else:
            server.os.environ["LITERATURE_API_TOKEN"] = self.old_token
        if self.old_publication_mode is None:
            server.os.environ.pop("LITERATURE_PUBLICATION_MODE", None)
        else:
            server.os.environ["LITERATURE_PUBLICATION_MODE"] = self.old_publication_mode
        self.tmp.cleanup()

    def request(self, method, path, body=None, token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        headers = {}
        payload = None
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        conn.request(method, path, body=payload, headers=headers)
        response = conn.getresponse()
        result = (
            response.status,
            response.getheader("Content-Type") or "",
            response.read(),
            dict(response.getheaders()),
        )
        conn.close()
        return result

    def test_static_outputs_and_redirect_contract(self):
        excluded_slugs = [
            self.notes["20260806_leehu_literature_001"]["slug"],
            self.notes["20260806_leehu_literature_499"]["slug"],
        ]
        included_slug = self.notes["20260806_leehu_literature_500"]["slug"]

        for slug in excluded_slugs:
            status, content_type, body, _ = self.request("GET", f"/literature/{slug}/")
            self.assertEqual(status, 200)
            self.assertIn("text/html", content_type)
            self.assertIn('<meta name="robots" content="noindex, follow">', body.decode("utf-8"))
        status, _, body, _ = self.request("GET", f"/literature/{included_slug}/")
        self.assertEqual(status, 200)
        self.assertIn('<meta name="robots" content="index, follow">', body.decode("utf-8"))

        status, _, page_two, _ = self.request("GET", "/literature/page/2/")
        self.assertEqual(status, 200)
        self.assertIn('<meta name="robots" content="noindex, follow">', page_two.decode("utf-8"))

        for path in ("/literature/", "/literature/rss.xml", "/sitemap.xml"):
            status, content_type, body, _ = self.request("GET", path)
            text = body.decode("utf-8")
            self.assertEqual(status, 200)
            if path.endswith("rss.xml"):
                self.assertIn("application/rss+xml", content_type)
            elif path.endswith("sitemap.xml"):
                self.assertIn("application/xml", content_type)
            if path != "/literature/":
                self.assertIn(included_slug, text)
            for slug in excluded_slugs:
                self.assertNotIn(slug, text)
        _, _, sitemap, _ = self.request("GET", "/sitemap.xml")
        sitemap_text = sitemap.decode("utf-8")
        self.assertIn(f"{server.CANONICAL_ORIGIN}/author/", sitemap_text)
        self.assertNotIn("/literature/page/", sitemap_text)

        for source, target in (
            ("/literature", "/literature/"),
            ("/author", "/author/"),
            ("/sitemap", "/sitemap.xml"),
            ("/literature/page/2", "/literature/page/2/"),
            (f"/literature/{included_slug}", f"/literature/{included_slug}/"),
        ):
            status, _, _, headers = self.request("GET", source)
            self.assertEqual(status, 301)
            self.assertEqual(headers.get("Location"), target)

        status, _, author, _ = self.request("GET", "/author/")
        self.assertEqual(status, 200)
        self.assertIn(
            f'<link rel="canonical" href="{server.CANONICAL_ORIGIN}/author/">',
            author.decode("utf-8"),
        )
        status, _, _, _ = self.request("GET", "/literature/%2e%2e/server.py")
        self.assertEqual(status, 404)
        for private_path in (
            "/server.py",
            "/literature_index_policy.py",
            "/content/literature-index-policy.json",
            "/Dockerfile",
            "/README.md",
        ):
            status, _, _, _ = self.request("GET", private_path)
            self.assertEqual(status, 404, private_path)

    def test_api_write_does_not_change_static_publication(self):
        payload = sample_payload(
            title="Static mode stored only",
            slug="20260727-leehu-literature-01-static-stored-only",
        )
        status, _, body, _ = self.request("POST", "/api/literature/posts", payload, TOKEN)
        self.assertEqual(status, 201, body.decode("utf-8"))
        post = json.loads(body.decode("utf-8"))["post"]
        self.assertTrue((server.LITERATURE_POSTS_DIR / f"{post['slug']}.json").is_file())

        status, _, api_body, _ = self.request("GET", f"/api/literature/posts/{post['slug']}")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(api_body.decode("utf-8"))["post"]["slug"], post["slug"])
        for path in (
            "/literature/",
            f"/literature/{post['slug']}/",
            "/literature/rss.xml",
            "/sitemap.xml",
        ):
            status, _, public_body, _ = self.request("GET", path)
            if path.startswith(f"/literature/{post['slug']}"):
                self.assertEqual(status, 404)
            else:
                self.assertEqual(status, 200)
                self.assertNotIn(post["slug"], public_body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
