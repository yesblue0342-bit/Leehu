"""HTTP regressions for OCI public files, HEAD parity and canonical aliases.

Run with: python -m unittest discover -s tests -p test_public_http_routes.py
"""

import http.client
import importlib.util
import os
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
SPEC = importlib.util.spec_from_file_location("leehu_http_test_server", REPO_ROOT / "server.py")
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


class PublicHTTPRoutesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        fixtures = {
            "index.html": b"<h1>Author homepage</h1>",
            "author/index.html": b"<h1>Author profile</h1>",
            "works/index.html": b"<h1>Works</h1>",
            "official-links/index.html": b"<h1>Official links</h1>",
            "literature/index.html": b"<h1>Literature notes</h1>",
            "literature/sample/index.html": b"<h1>A literature note</h1>",
            "robots.txt": b"User-agent: *\nAllow: /\n",
            "sitemap.xml": b"<?xml version='1.0'?><urlset/>",
            "assets/official-share.js": b"/* Official profile sharing */",
            "assets/internal.json": b'{"private":true}',
            "assets/unlisted.js": b"/* Unlisted implementation */",
            "seo-updates/index.html": b"<h1>Author updates</h1>",
            "seo-updates/latest.html": b"<h1>Latest update</h1>",
            "seo-updates/illustration.jpg": b"JPEG fixture",
            "seo-updates/illustration.png": b"PNG fixture",
            "seo-updates/internal.json": b'{"private":true}',
            "seo-updates/internal.py": b"private = True",
            "seo-updates/internal.js": b"/* Not a public update */",
            "docs/private.html": b"Internal documentation",
            "content/private.json": b'{"private":true}',
            "server.py": b"private = True",
        }
        for name, data in fixtures.items():
            target = cls.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        cls.fixtures = fixtures
        cls.patches = [
            patch.object(server, "ROOT", cls.root),
            patch.object(server, "POSTS_DIR", cls.root / "board-data"),
            patch.dict(os.environ, {"LITERATURE_PUBLICATION_MODE": "static"}),
        ]
        for item in cls.patches:
            item.start()

        class Handler(server.LeehuHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(cls.root), **kwargs)

            def log_message(self, *args):
                pass

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        for item in reversed(cls.patches):
            item.stop()
        cls.directory.cleanup()

    def request(self, method, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        try:
            connection.request(method, path)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_existing_public_pages_and_newly_packaged_files_serve_get_and_head(self):
        paths = {
            "/": "index.html",
            "/author/": "author/index.html",
            "/works/": "works/index.html",
            "/official-links/": "official-links/index.html",
            "/literature/": "literature/index.html",
            "/robots.txt": "robots.txt",
            "/sitemap.xml": "sitemap.xml",
            "/assets/official-share.js?v=1": "assets/official-share.js",
            "/seo-updates/": "seo-updates/index.html",
            "/seo-updates/latest.html": "seo-updates/latest.html",
            "/seo-updates/illustration.jpg": "seo-updates/illustration.jpg",
            "/seo-updates/illustration.png": "seo-updates/illustration.png",
        }
        for path, fixture in paths.items():
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                head_status, head_headers, head_body = self.request("HEAD", path)
                self.assertEqual(status, 200)
                self.assertEqual(body, self.fixtures[fixture])
                self.assertEqual(head_status, status)
                self.assertEqual(head_headers["Content-Type"], headers["Content-Type"])
                self.assertEqual(head_headers["Content-Length"], str(len(body)))
                self.assertEqual(head_body, b"")

    def test_private_missing_and_unlisted_files_stay_404_for_get_and_head(self):
        for path in (
            "/docs/private.html", "/content/private.json", "/server.py",
            "/assets/internal.json", "/assets/unlisted.js",
            "/seo-updates/internal.json", "/seo-updates/internal.py",
            "/seo-updates/internal.js", "/seo-updates/missing.html",
            "/assets/../content/private.json", "/seo-updates/%2e%2e/content/private.json",
            "/literature/missing/index.html", "/docs/index.html",
        ):
            for method in ("GET", "HEAD"):
                with self.subTest(method=method, path=path):
                    status, _, body = self.request(method, path)
                    self.assertEqual(status, 404)
                    if method == "HEAD":
                        self.assertEqual(body, b"")

    def test_existing_public_index_aliases_redirect_and_preserve_queries(self):
        aliases = {
            "/index.html": "/",
            "/author/index.html": "/author/",
            "/works/index.html": "/works/",
            "/official-links/index.html": "/official-links/",
            "/literature/index.html": "/literature/",
            "/literature/sample/index.html": "/literature/sample/",
            "/seo-updates/index.html": "/seo-updates/",
            "/author": "/author/",
            "/seo-updates": "/seo-updates/",
        }
        for source, destination in aliases.items():
            for method in ("GET", "HEAD"):
                with self.subTest(method=method, path=source):
                    status, headers, body = self.request(method, source + "?ref=profile")
                    self.assertEqual(status, 301)
                    self.assertEqual(headers["Location"], destination + "?ref=profile")
                    self.assertEqual(body, b"")

    def test_head_api_uses_get_handler_and_sends_no_body(self):
        status, headers, body = self.request("GET", "/api/board/posts")
        head_status, head_headers, head_body = self.request("HEAD", "/api/board/posts")
        self.assertEqual(status, 200)
        self.assertEqual(head_status, status)
        self.assertEqual(head_headers["Content-Type"], headers["Content-Type"])
        self.assertEqual(head_headers["Content-Length"], str(len(body)))
        self.assertEqual(head_body, b"")

    def test_dynamic_sitemap_head_preserves_get_status_and_metadata(self):
        with patch.dict(os.environ, {"LITERATURE_PUBLICATION_MODE": "dynamic"}), patch.object(
            server, "render_sitemap", return_value="<urlset><url/></urlset>"
        ):
            status, headers, body = self.request("GET", "/sitemap.xml")
            head_status, head_headers, head_body = self.request("HEAD", "/sitemap.xml")
        self.assertEqual(status, 200)
        self.assertEqual(head_status, status)
        self.assertEqual(body, b"<urlset><url/></urlset>")
        self.assertEqual(head_headers["Content-Length"], str(len(body)))
        self.assertEqual(head_headers["Content-Type"], headers["Content-Type"])
        self.assertEqual(head_body, b"")


if __name__ == "__main__":
    unittest.main()
