import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

import server


class LiteratureApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        root = Path(cls.temp.name)
        server.BOARD_POSTS_DIR = root / "board-posts"
        server.LITERATURE_POSTS_DIR = root / "literature-posts"
        server.LITERATURE_API_TOKEN = "test-token"
        server.LITERATURE_ALLOWED_ORIGINS = {"http://localhost"}
        server.ensure_dirs()
        cls.httpd = server.ThreadingHTTPServer(("127.0.0.1", 0), server.LeehuHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.thread.join(timeout=3)
        cls.temp.cleanup()

    def request(self, method, path, payload=None, token=True):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer test-token"
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        conn = HTTPConnection("127.0.0.1", self.port, timeout=3)
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        content = response.read()
        conn.close()
        return response.status, content

    def payload(self):
        return {
            "slug": "austen-pride-and-prejudice",
            "title": "풍자가 먼저 여는 사랑의 문장",
            "quote": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
            "source": "Jane Austen, Pride and Prejudice, Chapter 1 (1813, public domain original)",
            "author": "Jane Austen",
            "work": "Pride and Prejudice",
            "location": "Chapter 1",
            "original_language": "English",
            "translation_method": "공공영역 영어 원전 기반 자체 번역",
            "commentary": "이 첫 문장은 결혼을 둘러싼 사회의 상식을 단정하는 것처럼 보이지만, 사실은 그 상식이 얼마나 자연스럽게 개인을 규정하는지 보여 주는 풍자다. 재산과 혼인의 언어가 먼저 등장하는 순간, 인물의 마음은 이미 타인의 기대 속에서 읽힌다. 오늘의 독서는 누군가를 설명하는 말이 정말 그 사람의 삶을 넉넉히 담아내는지 되묻게 한다. 이후의 소설에서도 인물은 타인이 붙인 이름과 자신의 감정 사이에서 조금씩 다른 목소리를 찾는다. 관습이 제공하는 편리한 문장을 잠시 멈춰 세우고, 한 사람이 자기 삶의 문장을 스스로 고를 수 있는 여백을 살펴볼 필요가 있다.",
            "status": "published",
            "idempotency_key": "test-2026-07-27",
        }

    def test_literature_lifecycle_and_feeds(self):
        status, _ = self.request("POST", "/api/literature/posts", self.payload(), token=False)
        self.assertEqual(status, 401)
        status, content = self.request("POST", "/api/literature/posts", self.payload())
        self.assertEqual(status, 201)
        self.assertEqual(json.loads(content)["post"]["slug"], "austen-pride-and-prejudice")
        status, _ = self.request("POST", "/api/literature/posts", self.payload())
        self.assertEqual(status, 409)
        status, content = self.request("GET", "/api/literature/posts/austen-pride-and-prejudice", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["post"]["work"], "Pride and Prejudice")
        for route in ("/literature/", "/literature/austen-pride-and-prejudice", "/sitemap.xml", "/literature/rss.xml"):
            status, content = self.request("GET", route, token=False)
            self.assertEqual(status, 200)
            self.assertIn(b"austen-pride-and-prejudice", content)
        status, _ = self.request("PUT", "/api/literature/posts/austen-pride-and-prejudice", {"status": "archived"})
        self.assertEqual(status, 200)
        status, _ = self.request("GET", "/api/literature/posts/austen-pride-and-prejudice", token=False)
        self.assertEqual(status, 404)

    def test_board_regression(self):
        status, _ = self.request("POST", "/api/board/posts", {"id": "board-test", "title": "Board", "body": "Regression", "author": "test"}, token=False)
        self.assertEqual(status, 201)
        status, content = self.request("GET", "/api/board/posts?q=Board", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(content)["posts"][0]["id"], "board-test")
        status, _ = self.request("DELETE", "/api/board/posts/board-test", token=False)
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
