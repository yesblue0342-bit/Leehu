import json
import mimetypes
import os
import posixpath
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parent
MAX_BODY_BYTES = 64 * 1024
LOCAL_DRIVE_POSTS_DIR = Path("G:/내 드라이브/1개인/7 이후닷컴 홈페이지/6 게시판")
POSTS_DIR = Path(os.environ.get(
    "BOARD_POSTS_DIR",
    str(LOCAL_DRIVE_POSTS_DIR if LOCAL_DRIVE_POSTS_DIR.exists() else Path("/data/board-posts")),
))


def ensure_posts_dir():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)


def post_path(post_id):
    safe_id = "".join(ch for ch in post_id if ch.isalnum() or ch in ("-", "_"))[:80]
    return POSTS_DIR / f"{safe_id}.json"


def read_post(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if data.get("deleted"):
        return None
    return {
        "id": clipped(data.get("id") or path.stem, 80),
        "title": clipped(data.get("title") or "제목 없음", 120),
        "body": clipped(data.get("body") or "", 5000),
        "author": clipped(data.get("author") or "방문자", 40),
        "source": clipped(data.get("source") or "api", 40),
        "created_at": clipped(data.get("created_at") or data.get("createdAt") or "", 40),
        "updated_at": clipped(data.get("updated_at") or data.get("updatedAt") or data.get("created_at") or "", 40),
    }


def list_posts(query=""):
    ensure_posts_dir()
    query = query.casefold()
    posts = []
    for path in POSTS_DIR.glob("*.json"):
        post = read_post(path)
        if not post:
            continue
        haystack = " ".join([post["title"], post["body"], post["author"]]).casefold()
        if query and query not in haystack:
            continue
        posts.append(post)
    posts.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return posts[:200]


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
        self.json_response({"posts": list_posts(query)})

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

        post_id = clipped(payload.get("id"), 80) or uuid.uuid4().hex
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        post = {
            "id": post_id,
            "title": title,
            "body": body,
            "author": author,
            "source": source,
            "created_at": created_at,
            "updated_at": created_at,
        }
        ensure_posts_dir()
        with post_path(post_id).open("w", encoding="utf-8") as handle:
            json.dump(post, handle, ensure_ascii=False, indent=2)

        self.json_response({"post": post}, HTTPStatus.CREATED)

    def handle_delete_post(self, post_id):
        post_id = clipped(post_id, 64)
        if not post_id:
            self.json_response({"error": "post_id_required"}, HTTPStatus.BAD_REQUEST)
            return

        target = post_path(post_id)
        if not target.exists():
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        target.unlink()
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
    ensure_posts_dir()
    port = int(os.environ.get("PORT", "80"))
    server = ThreadingHTTPServer(("0.0.0.0", port), LeehuHandler)
    print(f"Leehu board server listening on :{port}, posts={POSTS_DIR}", flush=True)
    server.serve_forever()
