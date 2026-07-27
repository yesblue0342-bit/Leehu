import json
import mimetypes
import os
import posixpath
import sqlite3
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("BOARD_DB_PATH", "/data/leehu_board.sqlite3"))
MAX_BODY_BYTES = 64 * 1024


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
          id TEXT PRIMARY KEY,
          title TEXT NOT NULL,
          body TEXT NOT NULL,
          author TEXT NOT NULL,
          source TEXT NOT NULL,
          created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def post_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "author": row["author"],
        "source": row["source"],
        "created_at": row["created_at"],
    }


def clipped(value, limit):
    return str(value or "").strip()[:limit]


class LeehuHandler(SimpleHTTPRequestHandler):
    server_version = "LeehuBoard/1.0"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/board/posts":
            self.handle_list_posts(parsed.query)
            return
        if parsed.path.startswith("/api/"):
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/board/posts":
            self.handle_create_post()
            return
        self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        prefix = "/api/board/posts/"
        if parsed.path.startswith(prefix):
            self.handle_delete_post(unquote(parsed.path[len(prefix):]))
            return
        self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def handle_list_posts(self, query_string):
        query = clipped(parse_qs(query_string).get("q", [""])[0], 120)
        with db() as connection:
            if query:
                like = f"%{query}%"
                rows = connection.execute(
                    """
                    SELECT id, title, body, author, source, created_at
                    FROM posts
                    WHERE title LIKE ? OR body LIKE ? OR author LIKE ?
                    ORDER BY datetime(created_at) DESC
                    LIMIT 200
                    """,
                    (like, like, like),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT id, title, body, author, source, created_at
                    FROM posts
                    ORDER BY datetime(created_at) DESC
                    LIMIT 200
                    """
                ).fetchall()
        self.json_response({"posts": [post_to_dict(row) for row in rows]})

    def handle_create_post(self):
        payload = self.read_json_body()
        if payload is None:
            return

        title = clipped(payload.get("title"), 120)
        body = clipped(payload.get("body") or payload.get("content"), 5000)
        author = clipped(payload.get("author") or "방문자", 40)
        source = clipped(payload.get("source") or "api", 40)

        if not title or not body:
            self.json_response({"error": "title_and_body_required"}, HTTPStatus.BAD_REQUEST)
            return

        post_id = uuid.uuid4().hex
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        with db() as connection:
            connection.execute(
                """
                INSERT INTO posts (id, title, body, author, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (post_id, title, body, author, source, created_at),
            )
            row = connection.execute(
                "SELECT id, title, body, author, source, created_at FROM posts WHERE id = ?",
                (post_id,),
            ).fetchone()

        self.json_response({"post": post_to_dict(row)}, HTTPStatus.CREATED)

    def handle_delete_post(self, post_id):
        post_id = clipped(post_id, 64)
        if not post_id:
            self.json_response({"error": "post_id_required"}, HTTPStatus.BAD_REQUEST)
            return

        with db() as connection:
            cursor = connection.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        if cursor.rowcount == 0:
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        self.json_response({"ok": True})

    def read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self.json_response({"error": "invalid_body_size"}, HTTPStatus.BAD_REQUEST)
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.json_response({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return None

    def json_response(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_static(self, request_path):
        path = posixpath.normpath(unquote(request_path.split("?", 1)[0]))
        if path in ("", "/", "."):
            path = "/index.html"
        target = (ROOT / path.lstrip("/")).resolve()
        if not str(target).startswith(str(ROOT)) or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        content = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    db().close()
    port = int(os.environ.get("PORT", "80"))
    server = ThreadingHTTPServer(("0.0.0.0", port), LeehuHandler)
    print(f"Leehu board server listening on :{port}", flush=True)
    server.serve_forever()
