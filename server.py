import hmac
import html
import json
import mimetypes
import os
import posixpath
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import lru_cache
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
from zoneinfo import ZoneInfo

from literature_index_policy import is_note_indexable, load_index_policy


ROOT = Path(__file__).resolve().parent
LITERATURE_INDEX_POLICY_PATH = ROOT / "content" / "literature-index-policy.json"
PUBLIC_STATIC_FILES = {
    "/index.html",
    "/robots.txt",
    "/sitemap.xml",
    "/404.html",
    "/og-image.jpg",
    "/google17ccaa674b8b790b.html",
    "/naver7a6895689b825b13f6abd14a77c7c18a.html",
}
PUBLIC_STATIC_ROOTS = ("/author", "/literature")
CANONICAL_ORIGIN = "https://xn--hu5b23z.com"
OG_IMAGE = f"{CANONICAL_ORIGIN}/og-image.jpg"
MAX_BODY_BYTES = 128 * 1024
KST = ZoneInfo("Asia/Seoul")

LOCAL_DRIVE_POSTS_DIR = Path("G:/내 드라이브/1개인/7 이후닷컴 홈페이지/6 게시판")
POSTS_DIR = Path(os.environ.get(
    "BOARD_POSTS_DIR",
    str(LOCAL_DRIVE_POSTS_DIR if LOCAL_DRIVE_POSTS_DIR.exists() else Path("/data/board-posts")),
))
LITERATURE_POSTS_DIR = Path(os.environ.get("LITERATURE_POSTS_DIR", "/data/literature-posts"))

LITERATURE_ID_RE = re.compile(r"^\d{8}_leehu_literature_\d{2,}$")
LITERATURE_SLUG_RE = re.compile(r"^\d{8}-leehu-literature-\d{2,}-[a-z0-9][a-z0-9-]*$")
TOPIC_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
STATUS_VALUES = {"draft", "published", "archived", "deleted"}
LITERATURE_WRITE_LOCK = threading.Lock()


def ensure_dirs():
    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    LITERATURE_POSTS_DIR.mkdir(parents=True, exist_ok=True)


def literature_publication_mode():
    mode = os.environ.get("LITERATURE_PUBLICATION_MODE", "static").strip().lower()
    if mode not in {"static", "dynamic"}:
        raise RuntimeError(
            "LITERATURE_PUBLICATION_MODE must be exactly 'static' or 'dynamic'"
        )
    return mode


@lru_cache(maxsize=1)
def literature_index_policy():
    return load_index_policy(LITERATURE_INDEX_POLICY_PATH)


def literature_post_is_indexable(post):
    return is_note_indexable(post, literature_index_policy())


def clipped(value, limit):
    return str(value or "").strip()[:limit]


def escape(value):
    return html.escape(str(value or ""), quote=True)


def text_excerpt(value, limit=150):
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def parse_int(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return min(max(number, minimum), maximum)


def json_script(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def safe_json_name(value):
    safe = "".join(ch for ch in str(value or "") if ch.isalnum() or ch in ("-", "_"))[:120]
    return safe or uuid.uuid4().hex


def board_post_path(post_id):
    return POSTS_DIR / f"{safe_json_name(post_id)}.json"


def literature_post_path(slug):
    if not LITERATURE_SLUG_RE.match(str(slug or "")):
        return None
    return LITERATURE_POSTS_DIR / f"{slug}.json"


def read_json_file(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def write_json_file(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    tmp.replace(path)


def read_board_post(path):
    data = read_json_file(path)
    if not data or data.get("deleted"):
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


def list_board_posts(query=""):
    ensure_dirs()
    needle = query.casefold()
    posts = []
    for path in POSTS_DIR.glob("*.json"):
        post = read_board_post(path)
        if not post:
            continue
        haystack = " ".join([post["title"], post["body"], post["author"]]).casefold()
        if needle and needle not in haystack:
            continue
        posts.append(post)
    posts.sort(key=lambda item: item.get("updated_at") or item.get("created_at") or "", reverse=True)
    return posts[:200]


def parse_datetime(value):
    if not value:
        return datetime.now(KST)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def iso_kst(dt=None):
    return (dt or datetime.now(KST)).astimezone(KST).isoformat(timespec="seconds")


def yyyymmdd_from_published(value):
    parsed = parse_datetime(value)
    if not parsed:
        return None
    return parsed.strftime("%Y%m%d")


def slugify_topic(*parts):
    source = " ".join(str(part or "") for part in parts)
    source = source.lower()
    source = re.sub(r"[^a-z0-9]+", "-", source)
    source = re.sub(r"-{2,}", "-", source).strip("-")
    if not source:
        source = "literature-note"
    if not TOPIC_SLUG_RE.match(source):
        source = "literature-note"
    return source[:70].strip("-") or "literature-note"


def all_literature_posts(include_private=True):
    ensure_dirs()
    posts = []
    for path in LITERATURE_POSTS_DIR.glob("*.json"):
        data = read_json_file(path)
        if not isinstance(data, dict):
            continue
        post = normalize_literature_post(data)
        if not post:
            continue
        if include_private or post.get("status") == "published":
            posts.append(post)
    posts.sort(key=lambda item: item.get("published_at") or item.get("updated_at") or "", reverse=True)
    return posts


def published_literature_posts(query="", limit=50, offset=0):
    needle = query.casefold()
    posts = []
    for post in all_literature_posts(include_private=False):
        if not literature_post_is_indexable(post):
            continue
        haystack = " ".join([
            post.get("title", ""),
            post.get("quote", ""),
            post.get("source_author", ""),
            post.get("source_work", ""),
            post.get("commentary", ""),
            " ".join(post.get("tags", [])),
        ]).casefold()
        if needle and needle not in haystack:
            continue
        posts.append(post)
    return posts[offset: offset + limit], len(posts)


def normalize_literature_post(data):
    slug = str(data.get("slug") or "").strip()
    post_id = str(data.get("id") or "").strip()
    if not LITERATURE_SLUG_RE.match(slug) or not LITERATURE_ID_RE.match(post_id):
        return None
    status = str(data.get("status") or "draft").strip()
    if status not in STATUS_VALUES:
        return None
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    related = data.get("related_work") if isinstance(data.get("related_work"), dict) else {}
    post = {
        "id": post_id,
        "slug": slug,
        "title": clipped(data.get("title"), 160),
        "quote": clipped(data.get("quote"), 500),
        "source_author": clipped(data.get("source_author"), 120),
        "source_work": clipped(data.get("source_work"), 160),
        "source_location": clipped(data.get("source_location"), 120),
        "source_language": clipped(data.get("source_language") or "ko", 20),
        "source_url": clipped(data.get("source_url"), 500),
        "translation_note": clipped(data.get("translation_note"), 300),
        "rights_note": clipped(data.get("rights_note"), 300),
        "commentary": clipped(data.get("commentary"), 8000),
        "closing": clipped(data.get("closing") or "소설가 이후 드림", 120),
        "author": clipped(data.get("author") or "소설가 이후", 80),
        "published_at": clipped(data.get("published_at"), 40),
        "created_at": clipped(data.get("created_at"), 40),
        "updated_at": clipped(data.get("updated_at"), 40),
        "tags": [clipped(tag, 40) for tag in tags if clipped(tag, 40)][:20],
        "related_work": {
            "name": clipped(related.get("name"), 120),
            "url": clipped(related.get("url"), 500),
        },
        "status": status,
    }
    post["canonical_url"] = literature_url(slug)
    return post


def next_literature_sequence(date_prefix):
    max_seq = 0
    for post in all_literature_posts(include_private=True):
        match = re.match(rf"^{re.escape(date_prefix)}_leehu_literature_(\d{{2,}})$", post["id"])
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return max_seq + 1


def literature_url(slug):
    return f"{CANONICAL_ORIGIN}/literature/{slug}/"


def build_literature_identity(payload, existing=None):
    published_at = payload.get("published_at") or (existing or {}).get("published_at") or iso_kst()
    date_prefix = yyyymmdd_from_published(published_at)
    if not date_prefix:
        return None, None, "invalid_published_at"

    provided_id = clipped(payload.get("id") or (existing or {}).get("id"), 80)
    if provided_id:
        if not LITERATURE_ID_RE.match(provided_id):
            return None, None, "invalid_id"
        id_parts = provided_id.split("_")
        date_prefix = id_parts[0]
        seq = int(id_parts[-1])
    else:
        seq = next_literature_sequence(date_prefix)
        provided_id = f"{date_prefix}_leehu_literature_{seq:02d}"

    provided_slug = clipped(payload.get("slug") or (existing or {}).get("slug"), 160)
    if provided_slug:
        if not LITERATURE_SLUG_RE.match(provided_slug):
            return None, None, "invalid_slug"
    else:
        topic = clipped(payload.get("topic_slug"), 80)
        if topic and not TOPIC_SLUG_RE.match(topic):
            return None, None, "invalid_topic_slug"
        topic = topic or slugify_topic(payload.get("title"), payload.get("source_author"), payload.get("source_work"))
        provided_slug = f"{date_prefix}-leehu-literature-{seq:02d}-{topic}"

    return provided_id, provided_slug, None


def validate_literature_payload(payload, existing=None):
    errors = []
    merged = dict(existing or {})
    merged.update({key: value for key, value in payload.items() if value is not None})

    required = ["title", "quote", "source_author", "source_work", "commentary", "author", "published_at", "status"]
    for field in required:
        if not clipped(merged.get(field), 10000):
            errors.append(f"{field}_required")

    title = clipped(merged.get("title"), 10000)
    quote = clipped(merged.get("quote"), 10000)
    commentary = clipped(merged.get("commentary"), 10000)
    status = clipped(merged.get("status"), 40)

    if len(title) > 160:
        errors.append("title_too_long")
    if len(quote) > 500:
        errors.append("quote_too_long")
    if quote.count(".") + quote.count("!") + quote.count("?") + quote.count("。") > 3:
        errors.append("quote_too_long")
    if len(commentary) <= max(len(quote), 80):
        errors.append("commentary_too_short")
    if status and status not in STATUS_VALUES:
        errors.append("invalid_status")
    if parse_datetime(merged.get("published_at")) is None:
        errors.append("invalid_published_at")

    return errors


def prepare_literature_post(payload, existing=None):
    payload = dict(payload or {})
    post_id, slug, identity_error = build_literature_identity(payload, existing)
    if identity_error:
        return None, [identity_error]

    now = iso_kst()
    created_at = (existing or {}).get("created_at") or payload.get("created_at") or now
    post = {
        "id": post_id,
        "slug": slug,
        "title": clipped(payload.get("title") or (existing or {}).get("title"), 160),
        "quote": clipped(payload.get("quote") or (existing or {}).get("quote"), 500),
        "source_author": clipped(payload.get("source_author") or (existing or {}).get("source_author"), 120),
        "source_work": clipped(payload.get("source_work") or (existing or {}).get("source_work"), 160),
        "source_location": clipped(payload.get("source_location") or (existing or {}).get("source_location"), 120),
        "source_language": clipped(payload.get("source_language") or (existing or {}).get("source_language") or "ko", 20),
        "source_url": clipped(payload.get("source_url") or (existing or {}).get("source_url"), 500),
        "translation_note": clipped(payload.get("translation_note") or (existing or {}).get("translation_note"), 300),
        "rights_note": clipped(payload.get("rights_note") or (existing or {}).get("rights_note"), 300),
        "commentary": clipped(payload.get("commentary") or (existing or {}).get("commentary"), 8000),
        "closing": clipped(payload.get("closing") or (existing or {}).get("closing") or "소설가 이후 드림", 120),
        "author": clipped(payload.get("author") or (existing or {}).get("author") or "소설가 이후", 80),
        "published_at": clipped(payload.get("published_at") or (existing or {}).get("published_at"), 40),
        "created_at": clipped(created_at, 40),
        "updated_at": now,
        "tags": payload.get("tags") if isinstance(payload.get("tags"), list) else (existing or {}).get("tags", []),
        "related_work": payload.get("related_work") if isinstance(payload.get("related_work"), dict) else (existing or {}).get("related_work", {}),
        "status": clipped(payload.get("status") or (existing or {}).get("status") or "draft", 40),
    }
    normalized = normalize_literature_post(post)
    if not normalized:
        return None, ["invalid_post"]
    errors = validate_literature_payload(normalized)
    return normalized, errors


def token_is_valid(header):
    expected = os.environ.get("LITERATURE_API_TOKEN", "")
    if not expected:
        return False
    prefix = "Bearer "
    if not header or not header.startswith(prefix):
        return False
    actual = header[len(prefix):].strip()
    return hmac.compare_digest(actual.encode("utf-8"), expected.encode("utf-8"))


def allowed_literature_origin(origin):
    if not origin:
        return None
    allowed = [item.strip() for item in os.environ.get("LITERATURE_ALLOWED_ORIGINS", "").split(",") if item.strip()]
    if origin in allowed:
        return origin
    return None


def render_common_nav():
    return """
<nav class="site-nav">
  <a class="nav-logo" href="/">이후</a>
  <ul class="nav-links">
    <li><a href="/author/">공식 프로필</a></li>
    <li><a href="/#about">소개</a></li>
    <li><a href="/#works">작품</a></li>
    <li><a href="/#identity">활동</a></li>
    <li><a href="/#martial">무도</a></li>
    <li><a href="/#books">전문저서</a></li>
    <li><a href="/#music">음악</a></li>
    <li><a href="/#contact">연락</a></li>
    <li><a href="/literature/">문학노트</a></li>
    <li><a href="/#board">게시판</a></li>
  </ul>
</nav>
"""


def render_page(head, body):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{head}
<link rel="preconnect" href="https://fonts.googleapis.com/">
<link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin="">
<link href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&family=Noto+Serif+KR:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#fff;--panel:#f7f7f8;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--gold:#b89a5c;--blue:#2f66b1;--red:#8b1a1a}}
html{{scroll-behavior:smooth}}
body{{font-family:"Gowun Batang","Noto Serif KR",serif;background:var(--bg);color:var(--ink);overflow-x:hidden}}
a{{color:inherit}}
.site-nav{{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;height:74px;padding:0 56px;background:rgba(255,255,255,.92);border-bottom:1px solid var(--line);backdrop-filter:blur(16px)}}
.nav-logo{{font-weight:900;font-size:1.25rem;text-decoration:none}}
.nav-links{{display:flex;align-items:center;gap:22px;list-style:none}}
.nav-links a{{text-decoration:none;color:#4b5563;font-size:.86rem}}
.nav-links a:hover{{color:var(--ink)}}
.sec{{padding:84px 64px;max-width:1060px;margin:0 auto}}
.sec-title{{font-size:1rem;font-style:italic;color:var(--red);letter-spacing:.22em;margin-bottom:24px}}
.literature-hero h1{{font-size:clamp(2.35rem,5vw,4.4rem);line-height:1.18;letter-spacing:-.02em;margin-bottom:18px}}
.literature-hero p{{color:#4b5563;line-height:2;max-width:760px}}
.note-list{{display:grid;gap:14px;margin-top:28px}}
.note-card{{border:1px solid var(--line);border-radius:16px;padding:20px;background:#fff;text-decoration:none;display:block}}
.note-card:hover{{border-color:var(--gold)}}
.note-card h2,.note-card h3{{font-size:1.2rem;line-height:1.45;margin-bottom:8px}}
.note-meta{{color:#8a6f34;font-size:.86rem;line-height:1.7}}
.note-summary{{color:#4b5563;line-height:1.85;margin-top:8px}}
.tags{{display:flex;flex-wrap:wrap;gap:7px;margin-top:16px}}
.tag{{border:1px solid var(--line);border-radius:999px;padding:6px 10px;color:#374151;font-size:.78rem;background:#fafafa}}
.article{{max-width:860px}}
.article h1{{font-size:clamp(2.2rem,5vw,4.1rem);line-height:1.2;margin-bottom:16px}}
.article-meta{{color:#6b7280;line-height:1.8;margin-bottom:34px}}
blockquote{{border-left:3px solid var(--gold);padding:14px 0 14px 24px;margin:30px 0;font-size:1.55rem;line-height:1.75;font-style:italic;color:#111827}}
.source-box{{background:#fafafa;border:1px solid var(--line);border-radius:14px;padding:18px;line-height:1.85;color:#374151;margin-bottom:30px}}
.commentary h2{{font-size:1.2rem;color:#8b1a1a;letter-spacing:.08em;margin-bottom:12px}}
.commentary p{{white-space:pre-wrap;color:#374151;line-height:2.05;font-size:1.05rem}}
.article-nav{{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:36px;border-top:1px solid var(--line);padding-top:20px}}
.article-nav a,.plain-link{{border:1px solid var(--line);border-radius:999px;padding:9px 13px;text-decoration:none;background:#fff;color:#374151}}
.article-nav a:hover,.plain-link:hover{{background:#111827;color:#fff}}
.footer{{padding:48px 24px;text-align:center;border-top:1px solid var(--line);background:#fafafa;color:#4b5563;margin-top:40px}}
@media(max-width:1000px){{.site-nav{{padding:0 22px}}.nav-links{{display:none}}.sec{{padding:52px 22px}}blockquote{{font-size:1.25rem;padding-left:18px}}}}
</style>
</head>
<body>
{render_common_nav()}
{body}
</body>
</html>"""


def literature_json_ld(post):
    description = text_excerpt(post["commentary"], 155)
    citation = f'{post["source_author"]}, {post["source_work"]}'
    if post.get("source_location"):
        citation += f', {post["source_location"]}'
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "headline": post["title"],
                "description": description,
                "datePublished": post["published_at"],
                "dateModified": post["updated_at"],
                "mainEntityOfPage": post["canonical_url"],
                "author": {
                    "@type": "Person",
                    "@id": f"{CANONICAL_ORIGIN}/#person",
                    "name": "이후",
                    "alternateName": ["소설가 이후", "Lee Hu", "李後"],
                    "url": f"{CANONICAL_ORIGIN}/author/",
                },
                "publisher": {
                    "@type": "Organization",
                    "@id": f"{CANONICAL_ORIGIN}/#organization",
                    "name": "주식회사 소설가이후",
                    "url": f"{CANONICAL_ORIGIN}/",
                },
                "keywords": post.get("tags", []),
                "citation": citation,
                "about": [post["source_author"], post["source_work"], "고전문학", "한국문학", "소설가 이후"],
                "inLanguage": "ko-KR",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{CANONICAL_ORIGIN}/"},
                    {"@type": "ListItem", "position": 2, "name": "문학노트", "item": f"{CANONICAL_ORIGIN}/literature/"},
                    {"@type": "ListItem", "position": 3, "name": post["title"], "item": post["canonical_url"]},
                ],
            },
        ],
    }


def render_literature_list(query="", limit=20, offset=0):
    posts, total = published_literature_posts(query, limit, offset)
    canonical = f"{CANONICAL_ORIGIN}/literature/"
    description = "고전 문학의 한 문장과 그 문장을 바라보는 소설가 이후의 생각을 모은 문학노트입니다."
    list_items = []
    for index, post in enumerate(posts, start=offset + 1):
        list_items.append({"@type": "ListItem", "position": index, "url": post["canonical_url"], "name": post["title"]})
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "CollectionPage", "name": "이후의 문학노트", "description": description, "url": canonical, "inLanguage": "ko-KR"},
            {"@type": "ItemList", "itemListElement": list_items},
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{CANONICAL_ORIGIN}/"},
                    {"@type": "ListItem", "position": 2, "name": "문학노트", "item": canonical},
                ],
            },
        ],
    }
    robots = "index, follow" if not query and offset == 0 else "noindex, follow"
    head = f"""
<title>이후의 문학노트 | 소설가 이후</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="이후의 문학노트">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:site_name" content="소설가 이후">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="이후의 문학노트">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<script type="application/ld+json">{json_script(ld)}</script>
"""
    cards = "\n".join(render_note_card(post, heading="h2") for post in posts)
    if not cards:
        cards = '<div class="note-card"><p class="note-summary">아직 공개된 문학노트가 없습니다.</p></div>'
    search_value = escape(query)
    next_offset = offset + limit
    more = ""
    if total > next_offset:
        more = f'<p style="margin-top:24px"><a class="plain-link" href="/literature/?q={escape(query)}&offset={next_offset}&limit={limit}">더 보기</a></p>'
    body = f"""
<main class="sec literature-hero">
  <p class="sec-title">Literature Notes</p>
  <h1>이후의 문학노트</h1>
  <p>고전 문학의 한 문장과 그 문장을 바라보는 소설가 이후의 생각.</p>
  <form method="get" action="/literature/" style="margin-top:28px">
    <input name="q" value="{search_value}" placeholder="문학노트 검색" style="width:100%;border:1px solid var(--line);border-radius:13px;padding:13px 14px;font:inherit">
  </form>
  <div class="note-list">{cards}</div>
  {more}
</main>
<footer class="footer"><a class="plain-link" href="/">홈페이지로 돌아가기</a></footer>
"""
    return render_page(head, body)


def render_note_card(post, heading="h3"):
    tags = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in post.get("tags", [])[:5])
    return f"""
<a class="note-card" href="/literature/{escape(post['slug'])}/">
  <{heading}>{escape(post['title'])}</{heading}>
  <div class="note-meta">{escape(format_display_date(post['published_at']))} · {escape(post['source_author'])} · {escape(post['source_work'])}</div>
  <p class="note-summary">{escape(text_excerpt(post['commentary'], 120))}</p>
  <div class="tags">{tags}</div>
</a>
"""


def format_display_date(value):
    parsed = parse_datetime(value)
    if not parsed:
        return value or ""
    return parsed.strftime("%Y.%m.%d")


def render_literature_detail(post):
    indexable = literature_post_is_indexable(post)
    posts = [item for item in all_literature_posts(include_private=False) if literature_post_is_indexable(item)]
    ordered = sorted(posts, key=lambda item: item.get("published_at", ""))
    index = next((idx for idx, item in enumerate(ordered) if item["slug"] == post["slug"]), -1)
    prev_post = ordered[index - 1] if indexable and index > 0 else None
    next_post = ordered[index + 1] if indexable and 0 <= index < len(ordered) - 1 else None
    description = text_excerpt(post["commentary"], 155)
    tags_meta = "\n".join(f'<meta property="article:tag" content="{escape(tag)}">' for tag in post.get("tags", []))
    tags = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in post.get("tags", []))
    source_parts = [
        f"<strong>출처 작가</strong>: {escape(post['source_author'])}",
        f"<strong>작품</strong>: {escape(post['source_work'])}",
    ]
    if post.get("source_location"):
        source_parts.append(f"<strong>작품 내 위치</strong>: {escape(post['source_location'])}")
    if post.get("translation_note"):
        source_parts.append(f"<strong>번역 안내</strong>: {escape(post['translation_note'])}")
    if post.get("rights_note"):
        source_parts.append(f"<strong>권리 안내</strong>: {escape(post['rights_note'])}")
    if post.get("source_url"):
        source_parts.append(f'<a href="{escape(post["source_url"])}" target="_blank" rel="noopener">출처 보기</a>')
    related = ""
    if post.get("related_work", {}).get("name"):
        related_url = post.get("related_work", {}).get("url")
        if related_url:
            related = f'<p style="margin-top:22px"><a class="plain-link" href="{escape(related_url)}" target="_blank" rel="noopener">관련 작품: {escape(post["related_work"]["name"])}</a></p>'
        else:
            related = f'<p style="margin-top:22px">관련 작품: {escape(post["related_work"]["name"])}</p>'
    prev_next = []
    if prev_post:
        prev_next.append(f'<a href="/literature/{escape(prev_post["slug"])}/">이전 글</a>')
    if next_post:
        prev_next.append(f'<a href="/literature/{escape(next_post["slug"])}/">다음 글</a>')
    head = f"""
<title>{escape(post['title'])} | 소설가 이후 문학노트</title>
<meta name="description" content="{escape(description)}">
<meta name="robots" content="{'index, follow' if indexable else 'noindex, follow'}">
<link rel="canonical" href="{escape(post['canonical_url'])}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(post['title'])}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{escape(post['canonical_url'])}">
<meta property="og:site_name" content="소설가 이후">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(post['title'])}">
<meta name="twitter:description" content="{escape(description)}">
<meta name="twitter:image" content="{OG_IMAGE}">
<meta property="article:published_time" content="{escape(post['published_at'])}">
<meta property="article:modified_time" content="{escape(post['updated_at'])}">
<meta property="article:author" content="{escape(post['author'])}">
{tags_meta}
<script type="application/ld+json">{json_script(literature_json_ld(post))}</script>
"""
    body = f"""
<main class="sec article">
  <p class="sec-title">문학노트</p>
  <h1>{escape(post['title'])}</h1>
  <div class="article-meta">{escape(format_display_date(post['published_at']))} · 작성자 {escape(post['author'])}</div>
  <blockquote>{escape(post['quote'])}</blockquote>
  <div class="source-box">{'<br>'.join(source_parts)}</div>
  <section class="commentary">
    <h2>이후의 생각</h2>
    <p>{escape(post['commentary'])}</p>
  </section>
  {related}
  <p style="margin-top:26px;color:#8a6f34">{escape(post['closing'])}</p>
  <div class="tags">{tags}</div>
  <nav class="article-nav">
    {''.join(prev_next)}
    <a href="/literature/">문학노트 목록으로 돌아가기</a>
    <a href="/">홈페이지로 돌아가기</a>
  </nav>
</main>
<footer class="footer">이후 李後</footer>
"""
    return render_page(head, body)


def latest_literature_cards(count=4):
    posts, _ = published_literature_posts(limit=count, offset=0)
    if not posts:
        return '<p class="tagline">아직 공개된 문학노트가 없습니다.</p>'
    return "".join(render_home_note_card(post) for post in posts)


def render_home_note_card(post):
    return f"""
<a class="note-card" href="/literature/{escape(post['slug'])}/">
  <small>{escape(post['source_author'])} · {escape(post['source_work'])}</small>
  <h2>{escape(post['title'])}</h2>
  <blockquote>{escape(post['quote'])}</blockquote>
  <p>{' · '.join(escape(tag) for tag in post['tags'])}</p>
</a>
"""


def latest_literature_links(count=3):
    posts, _ = published_literature_posts(limit=count, offset=0)
    if not posts:
        return '<div class="empty-posts">아직 공개된 문학노트가 없습니다.</div>'
    return "".join(
        f'<a href="/literature/{escape(post["slug"])}/"><strong>{escape(post["title"])}</strong>'
        f'<span>{escape(post["source_author"])} · {escape(post["source_work"])}</span></a>'
        for post in posts
    )


def replace_homepage_marker(content, marker, replacement):
    block = re.compile(
        rf"<!-- {re.escape(marker)}:START -->.*?<!-- {re.escape(marker)}:END -->",
        re.S,
    )
    rendered = (
        f"<!-- {marker}:START -->\n{replacement}\n<!-- {marker}:END -->"
    )
    if block.search(content):
        return block.sub(lambda _match: rendered, content)
    plain = f"<!-- {marker} -->"
    if plain not in content:
        raise ValueError(f"homepage marker missing: {marker}")
    return content.replace(plain, rendered)


def render_homepage():
    content = (ROOT / "index.html").read_text(encoding="utf-8")
    content = replace_homepage_marker(
        content, "LITERATURE_LATEST_ITEMS", latest_literature_cards(6)
    )
    content = replace_homepage_marker(
        content, "BOARD_LITERATURE_ITEMS", latest_literature_links(3)
    )
    return content


def render_sitemap():
    posts, _ = published_literature_posts(limit=10000, offset=0)
    urls = [
        (f"{CANONICAL_ORIGIN}/", "weekly", "1.0", None),
        (f"{CANONICAL_ORIGIN}/author/", "monthly", "0.8", None),
        (f"{CANONICAL_ORIGIN}/literature/", "daily", "0.9", None),
    ]
    for post in posts:
        urls.append((post["canonical_url"], "monthly", "0.8", post.get("updated_at") or post.get("published_at")))
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, priority, lastmod in urls:
        body.append("  <url>")
        body.append(f"    <loc>{escape(loc)}</loc>")
        if lastmod:
            body.append(f"    <lastmod>{escape(lastmod[:10])}</lastmod>")
        body.append(f"    <changefreq>{freq}</changefreq>")
        body.append(f"    <priority>{priority}</priority>")
        body.append("  </url>")
    body.append("</urlset>")
    return "\n".join(body) + "\n"


def render_rss():
    posts, _ = published_literature_posts(limit=1000000, offset=0)
    items = []
    for post in posts:
        parsed = parse_datetime(post.get("published_at"))
        pub_date = format_datetime(parsed.astimezone(timezone.utc)) if parsed else ""
        items.append(f"""
    <item>
      <title>{escape(post['title'])}</title>
      <link>{escape(post['canonical_url'])}</link>
      <guid>{escape(post['canonical_url'])}</guid>
      <description>{escape(text_excerpt(post['commentary'], 180))}</description>
      <pubDate>{escape(pub_date)}</pubDate>
    </item>""")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>이후의 문학노트</title>
    <link>{CANONICAL_ORIGIN}/literature/</link>
    <description>고전 문학의 한 문장과 소설가 이후의 생각</description>
    <language>ko-KR</language>
{''.join(items)}
  </channel>
</rss>
"""


class LeehuHandler(SimpleHTTPRequestHandler):
    server_version = "LeehuLiterature/2.0"

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self):
        parsed = urlparse(self.path)
        if self.is_protected_literature_path(parsed.path):
            origin = allowed_literature_origin(self.headers.get("Origin"))
            self.send_response(HTTPStatus.NO_CONTENT)
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
            self.end_headers()
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/literature":
            self.redirect_permanently("/literature/")
            return
        if parsed.path == "/author":
            self.redirect_permanently("/author/")
            return
        if parsed.path == "/sitemap":
            self.redirect_permanently("/sitemap.xml")
            return
        if parsed.path in ("/", "/index.html"):
            if literature_publication_mode() == "static":
                self.serve_static("/index.html")
            else:
                self.html_response(render_homepage())
            return
        if parsed.path == "/author/":
            self.serve_static(parsed.path)
            return
        if literature_publication_mode() == "static" and (
            parsed.path == "/sitemap.xml"
            or parsed.path == "/literature/rss.xml"
            or parsed.path == "/literature/"
            or parsed.path.startswith("/literature/")
        ):
            self.serve_static(parsed.path)
            return
        if parsed.path == "/sitemap.xml":
            self.text_response(render_sitemap(), "application/xml; charset=utf-8")
            return
        if parsed.path == "/literature/rss.xml":
            self.text_response(render_rss(), "application/rss+xml; charset=utf-8")
            return
        if parsed.path == "/literature/":
            query = parse_qs(parsed.query)
            q = clipped(query.get("q", [""])[0], 120)
            limit = parse_int(query.get("limit", ["20"])[0], 20, 1, 100)
            offset = parse_int(query.get("offset", ["0"])[0], 0, 0, 1000000)
            self.html_response(render_literature_list(q, limit, offset))
            return
        if parsed.path.startswith("/literature/"):
            slug = unquote(parsed.path[len("/literature/"):]).strip("/")
            post = self.get_published_literature(slug)
            if not post:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.html_response(render_literature_detail(post))
            return
        if parsed.path == "/api/board/posts":
            self.handle_list_board_posts(parsed.query)
            return
        if parsed.path == "/api/literature/posts":
            self.handle_list_literature_json(parsed.query)
            return
        if parsed.path.startswith("/api/literature/posts/"):
            slug = unquote(parsed.path[len("/api/literature/posts/"):])
            post = self.get_published_literature(slug)
            if not post:
                self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
                return
            self.json_response({"post": post})
            return
        if parsed.path.startswith("/api/"):
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        self.serve_static(parsed.path)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/board/posts":
            self.handle_create_board_post()
            return
        if parsed.path == "/api/literature/posts":
            if not self.require_literature_auth():
                return
            self.handle_create_literature_post()
            return
        self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/literature/posts/"):
            if not self.require_literature_auth():
                return
            slug = unquote(parsed.path[len("/api/literature/posts/"):])
            self.handle_update_literature_post(slug)
            return
        self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        board_prefix = "/api/board/posts/"
        lit_prefix = "/api/literature/posts/"
        if parsed.path.startswith(board_prefix):
            self.handle_delete_board_post(unquote(parsed.path[len(board_prefix):]))
            return
        if parsed.path.startswith(lit_prefix):
            if not self.require_literature_auth():
                return
            self.handle_delete_literature_post(unquote(parsed.path[len(lit_prefix):]))
            return
        self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def is_protected_literature_path(self, path):
        return path == "/api/literature/posts" or path.startswith("/api/literature/posts/")

    def require_literature_auth(self):
        if token_is_valid(self.headers.get("Authorization")):
            return True
        status = HTTPStatus.FORBIDDEN if self.headers.get("Authorization") else HTTPStatus.UNAUTHORIZED
        self.json_response({"error": "unauthorized"}, status)
        return False

    def get_published_literature(self, slug):
        if not LITERATURE_SLUG_RE.match(str(slug or "")):
            return None
        path = literature_post_path(slug)
        if not path or not path.exists():
            return None
        post = normalize_literature_post(read_json_file(path) or {})
        if not post or post.get("status") != "published":
            return None
        return post

    def handle_list_board_posts(self, query_string):
        query = clipped(parse_qs(query_string).get("q", [""])[0], 120)
        self.json_response({"posts": list_board_posts(query)})

    def handle_create_board_post(self):
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
        post = {"id": post_id, "title": title, "body": body, "author": author, "source": source, "created_at": created_at, "updated_at": created_at}
        write_json_file(board_post_path(post_id), post)
        self.json_response({"post": post}, HTTPStatus.CREATED)

    def handle_delete_board_post(self, post_id):
        target = board_post_path(post_id)
        if not target.exists():
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        target.unlink()
        self.json_response({"ok": True})

    def handle_list_literature_json(self, query_string):
        query = parse_qs(query_string)
        q = clipped(query.get("q", [""])[0], 120)
        limit = parse_int(query.get("limit", ["20"])[0], 20, 1, 100)
        if "page" in query:
            page = parse_int(query.get("page", ["0"])[0], 0, 0, 1000000)
            offset = page * limit
        else:
            offset = parse_int(query.get("offset", ["0"])[0], 0, 0, 1000000)
        posts, total = published_literature_posts(q, limit, offset)
        self.json_response({"posts": posts, "total": total, "limit": limit, "offset": offset})

    def handle_create_literature_post(self):
        payload = self.read_json_body()
        if payload is None:
            return
        with LITERATURE_WRITE_LOCK:
            post, errors = prepare_literature_post(payload)
            if errors:
                self.json_response({"error": "validation_failed", "details": errors}, HTTPStatus.BAD_REQUEST)
                return
            path = literature_post_path(post["slug"])
            if path.exists() or any(item["id"] == post["id"] for item in all_literature_posts(include_private=True)):
                self.json_response({"error": "duplicate_id_or_slug"}, HTTPStatus.CONFLICT)
                return
            write_json_file(path, post)
        self.json_response({"post": post, "id": post["id"], "slug": post["slug"], "canonical_url": post["canonical_url"]}, HTTPStatus.CREATED)

    def handle_update_literature_post(self, slug):
        path = literature_post_path(slug)
        if not path or not path.exists():
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        existing = normalize_literature_post(read_json_file(path) or {})
        if not existing:
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        payload = self.read_json_body()
        if payload is None:
            return
        payload.pop("slug", None)
        payload.pop("id", None)
        with LITERATURE_WRITE_LOCK:
            post, errors = prepare_literature_post(payload, existing=existing)
            if errors:
                self.json_response({"error": "validation_failed", "details": errors}, HTTPStatus.BAD_REQUEST)
                return
            post["id"] = existing["id"]
            post["slug"] = existing["slug"]
            post["created_at"] = existing["created_at"]
            post["canonical_url"] = literature_url(post["slug"])
            write_json_file(path, post)
        self.json_response({"post": post, "id": post["id"], "slug": post["slug"], "canonical_url": post["canonical_url"]})

    def handle_delete_literature_post(self, slug):
        path = literature_post_path(slug)
        if not path or not path.exists():
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        post = normalize_literature_post(read_json_file(path) or {})
        if not post:
            self.json_response({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return
        with LITERATURE_WRITE_LOCK:
            post["status"] = "archived"
            post["updated_at"] = iso_kst()
            write_json_file(path, post)
        self.json_response({"ok": True, "post": post})

    def read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self.json_response({"error": "invalid_body_size"}, HTTPStatus.BAD_REQUEST)
            return None
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.json_response({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return None
        if not isinstance(payload, dict):
            self.json_response({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return None
        return payload

    def json_response(self, payload, status=HTTPStatus.OK):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        origin = allowed_literature_origin(self.headers.get("Origin"))
        if origin and self.is_protected_literature_path(urlparse(self.path).path):
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def html_response(self, content, status=HTTPStatus.OK):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def text_response(self, content, content_type, status=HTTPStatus.OK):
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def redirect_permanently(self, location):
        self.send_response(HTTPStatus.MOVED_PERMANENTLY)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def serve_static(self, request_path):
        decoded_path = unquote(request_path.split("?", 1)[0])
        if ".." in decoded_path.replace("\\", "/").split("/"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        path = posixpath.normpath(decoded_path)
        if path in ("", "/", "."):
            path = "/index.html"
        if path not in PUBLIC_STATIC_FILES and not any(
            path == root or path.startswith(root + "/")
            for root in PUBLIC_STATIC_ROOTS
        ):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        target = (ROOT / path.lstrip("/")).resolve()
        try:
            target.relative_to(ROOT.resolve())
        except ValueError:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if target.is_dir():
            if not decoded_path.endswith("/"):
                self.redirect_permanently(urlparse(self.path).path + "/")
                return
            target = target / "index.html"
        if not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if path == "/literature/rss.xml":
            content_type = "application/rss+xml; charset=utf-8"
        elif target.suffix.lower() == ".xml":
            content_type = "application/xml; charset=utf-8"
        else:
            content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if content_type.startswith("text/"):
                content_type += "; charset=utf-8"
        content = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


if __name__ == "__main__":
    ensure_dirs()
    publication_mode = literature_publication_mode()
    port = int(os.environ.get("PORT", "80"))
    server = ThreadingHTTPServer(("0.0.0.0", port), LeehuHandler)
    print(
        f"Leehu server listening on :{port} ({publication_mode} publication)",
        flush=True,
    )
    server.serve_forever()
