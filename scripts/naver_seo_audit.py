#!/usr/bin/env python3
"""Credit-free local SEO audit for the static official site.

The per-page and cross-page checks mirror the OpenSEO site-audit issue
catalogue (https://github.com/every-app/open-seo, MIT; see
skills/openseo/README.md). Naver Search Advisor rules that a static site can
satisfy on its own are layered on top: Yeti allowed in robots.txt, ownership
verification file present, sitemap and RSS size limits, full-text RSS,
root-page channel markup (Person with name/url/sameAs), Open Graph image
rules and repeated-keyword titles.

Everything runs against the files in the repository with the standard
library only, so it never spends API credits and never touches the network.
It reports what the files say; it cannot observe crawling, indexing or
rankings, and it never claims to.

Usage:
    python3 scripts/naver_seo_audit.py --full --out /tmp/naver-seo-audit.md
    python3 scripts/naver_seo_audit.py --out report.md --json audit.json --fail-on warning
    python3 scripts/naver_seo_audit.py --out report.md --baseline previous.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import struct
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HOST = "xn--hu5b23z.com"
ORIGIN = f"https://{HOST}"

# OpenSEO thresholds (src/server/lib/audit/issues/page-reporters.ts). They were
# tuned for Latin text; Korean titles of 30-45 characters are normal, so the
# length findings are reported as informational here.
TITLE_MAX_CHARS = 60
TITLE_MIN_CHARS = 10
META_DESCRIPTION_MAX_CHARS = 160
META_DESCRIPTION_MIN_CHARS = 70
THIN_CONTENT_WORDS = 150
DEEP_PAGE_DEPTH = 5

# Naver Search Advisor limits (guide/request-feed, guide/markup-content).
FEED_MAX_BYTES = 10_000_000  # the guide says 10MB; 10 MiB is 10,485,760
FEED_WARN_BYTES = 8_000_000
SITEMAP_MAX_URLS = 50_000
OG_IMAGE_MIN_SIDE = 150
OG_IMAGE_MIN_BYTES = 5_000
OG_IMAGE_MAX_RATIO = 3.0
REPEATED_KEYWORD_LIMIT = 3

# Channels Naver lists for 사이트 연관채널 (guide/structured-data-channel).
NAVER_CHANNEL_DOMAINS = (
    "tv.naver.com",
    "blog.naver.com",
    "smartstore.naver.com",
    "kin.naver.com",
    "chzzk.naver.com",
    "daangn.com",
    "threads.net",
    "threads.com",
    "instagram.com",
    "youtube.com",
    "story.kakao.com",
    "pf.kakao.com",
    "tistory.com",
    "tiktok.com",
    "facebook.com",
    "twitter.com",
    "x.com",
)

CORE_PATHS = (
    "index.html",
    "author/index.html",
    "works/index.html",
    "official-links/index.html",
    "literature/index.html",
    "seo-updates/index.html",
)
SKIP_DIRS = {".git", "assets", "content", "docs", "scripts", "skills", "tests", "deploy", "__pycache__"}
FEED_NAMES = ("rss.xml", "feed.xml")
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}

# Checks from the OpenSEO catalogue that need a live crawl and are therefore
# not decided by this offline tool.
OFFLINE_UNVERIFIABLE = (
    "blocked-page / rate-limited-page (크롤러 차단·429)",
    "server-error / broken-page (실제 HTTP 상태)",
    "redirect-chain / redirect-loop",
    "canonical-conflict (HTTP Link 헤더와의 충돌)",
    "slow-response (응답 시간)",
    "실제 수집·색인·노출·순위",
)

ISSUE_TEXT = {
    "missing-title": ("critical", "제목(title) 태그 없음"),
    "broken-internal-link": ("critical", "존재하지 않는 내부 링크"),
    "sitemap-missing-file": ("critical", "sitemap에 있지만 파일이 없는 URL"),
    "sitemap-host-mismatch": ("critical", "sitemap/RSS에 다른 호스트의 URL"),
    "feed-too-large": ("critical", "피드 용량이 네이버 제출 한도(10MB) 초과"),
    "robots-blocks-yeti": ("critical", "robots.txt가 네이버 검색로봇(Yeti) 수집을 막음"),
    "invalid-xml": ("critical", "XML 파싱 실패"),
    "invalid-jsonld": ("critical", "JSON-LD 파싱 실패"),
    "canonical-foreign": ("critical", "canonical이 다른 호스트를 가리킴"),
    "duplicate-title": ("warning", "같은 제목을 쓰는 페이지"),
    "duplicate-meta-description": ("warning", "같은 설명(description)을 쓰는 페이지"),
    "duplicate-content": ("warning", "본문이 동일한 페이지"),
    "missing-meta-description": ("warning", "설명(description) 태그 없음"),
    "missing-h1": ("warning", "H1 없음"),
    "multiple-h1": ("warning", "H1이 2개 이상"),
    "thin-content": ("warning", "본문 텍스트가 적음"),
    "images-missing-alt": ("warning", "alt 없는 이미지"),
    "orphan-page": ("warning", "다른 페이지에서 링크되지 않는 페이지"),
    "no-outgoing-links": ("warning", "발신 링크 없음"),
    "feed-near-limit": ("warning", "피드 용량이 한도의 80%를 넘음"),
    "feed-excerpt-only": ("warning", "RSS 항목이 본문 전체가 아닌 요약만 담음"),
    "og-image-rule": ("warning", "og:image가 네이버 섬네일 조건에 맞지 않음"),
    "og-image-shared": ("warning", "핵심 페이지들이 같은 og:image를 공유"),
    "repeated-keyword": ("warning", "제목/설명에 같은 단어가 반복됨"),
    "missing-channel-markup": ("warning", "루트 페이지에 연관채널(Person name/url/sameAs) 마크업 없음"),
    "missing-verification-file": ("warning", "네이버 사이트 소유확인 파일 없음"),
    "robots-missing-sitemap": ("warning", "robots.txt에 Sitemap 지시어 없음"),
    "missing-lang": ("warning", "<html lang> 없음"),
    "title-too-long": ("info", "제목이 60자를 넘음"),
    "title-too-short": ("info", "제목이 10자 미만"),
    "meta-description-too-long": ("info", "설명이 160자를 넘음"),
    "meta-description-too-short": ("info", "설명이 70자 미만"),
    "heading-order-skip": ("info", "제목 단계 건너뜀(H2 다음 H4 등)"),
    "noindex-page": ("info", "noindex 페이지"),
    "canonicalized-page": ("info", "canonical이 다른 주소를 가리킴(의도된 경우 정상)"),
    "deep-page": ("info", "홈에서 5클릭 이상 떨어진 페이지"),
    "missing-og": ("info", "Open Graph 기본 태그 일부 없음"),
    "data-uri-favicon": ("info", "파비콘이 data: URI (검색로봇이 파일로 수집하지 못할 수 있음)"),
    "relative-favicon": ("info", "파비콘 href가 절대 경로가 아님(네이버 가이드는 절대 경로 권장)"),
    "external-script": ("info", "외부 CDN 스크립트 사용"),
    "sameas-non-channel": ("info", "sameAs에 네이버 연관채널이 아닌 URL 포함(무해, 참고)"),
}

STOPWORDS = {
    "the", "and", "you", "your", "me", "my", "it", "is", "of", "to", "in", "that", "this", "for", "with",
    "her", "his", "he", "she", "not", "will", "was", "are", "but", "all", "one", "had", "have", "from",
    "they", "their", "them", "there", "these", "those", "what", "when", "where", "which", "while", "were",
    "been", "than", "then", "into", "would", "could", "should", "shall", "about", "upon", "only", "more",
    "most", "some", "such", "very", "every", "after", "before", "over", "under", "like", "just", "also",
    "다시", "함께", "것은", "것이", "그리고", "하는", "있는", "없는", "위한", "대한", "그", "이", "저",
}
HANGUL_OR_CJK = re.compile(r"[ㄱ-ㆎ가-힣一-鿿㐀-䶿]")


@dataclass
class Issue:
    issue_type: str
    page: str
    details: str = ""

    @property
    def severity(self) -> str:
        return ISSUE_TEXT[self.issue_type][0]

    @property
    def title(self) -> str:
        return ISSUE_TEXT[self.issue_type][1]


@dataclass
class Page:
    path: str
    url: str
    title: str = ""
    description: str = ""
    robots: str = ""
    canonical: str = ""
    lang: str = ""
    headings: list = field(default_factory=list)
    text_words: int = 0
    text_chars: int = 0
    article_text: str = ""
    links: list = field(default_factory=list)
    images_total: int = 0
    images_missing_alt: int = 0
    og: dict = field(default_factory=dict)
    twitter: dict = field(default_factory=dict)
    jsonld: list = field(default_factory=list)
    jsonld_errors: list = field(default_factory=list)
    icon: str = ""
    external_scripts: list = field(default_factory=list)
    depth: int | None = None

    @property
    def indexable(self) -> bool:
        return "noindex" not in self.robots.replace(" ", "").lower()

    @property
    def article_chars(self) -> int:
        return len(self.article_text) or self.text_chars


class PageParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "template", "svg"}
    CONTENT = {"article", "main"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.page_title: list[str] = []
        self.metas: dict[str, str] = {}
        self.canonical = ""
        self.icon = ""
        self.lang = ""
        self.headings: list[tuple[int, str]] = []
        self.links: list[str] = []
        self.images_total = 0
        self.images_missing_alt = 0
        self.jsonld_raw: list[str] = []
        self.external_scripts: list[str] = []
        self.text_parts: list[str] = []
        self.article_parts: list[str] = []
        self._stack: list[str] = []
        self._content_depth = 0
        self._in_title = False
        self._heading: tuple[int, list[str]] | None = None
        self._jsonld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang", "") or ""
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key and a.get("content") is not None:
                self.metas.setdefault(key.lower(), a["content"])
        elif tag == "link":
            rel = (a.get("rel") or "").lower().split()
            if "canonical" in rel:
                self.canonical = a.get("href", "")
            if "icon" in rel and not self.icon:
                self.icon = a.get("href", "")
        elif tag == "script":
            if (a.get("type") or "").lower() == "application/ld+json":
                self._jsonld = True
            src = a.get("src")
            if src and src.startswith(("http://", "https://", "//")):
                self.external_scripts.append(src)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._heading = (int(tag[1]), [])
        elif tag == "a":
            href = a.get("href")
            if href is not None:
                self.links.append(href)
        elif tag == "img":
            self.images_total += 1
            if a.get("alt") is None:
                self.images_missing_alt += 1
        if tag in self.CONTENT:
            self._content_depth += 1
        if tag in self.SKIP:
            self._stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._heading:
            level, parts = self._heading
            self.headings.append((level, " ".join("".join(parts).split())))
            self._heading = None
        elif tag == "script":
            self._jsonld = False
        if tag in self.CONTENT and self._content_depth:
            self._content_depth -= 1
        if tag in self.SKIP and self._stack and self._stack[-1] == tag:
            self._stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self.page_title.append(data)
        if self._jsonld:
            self.jsonld_raw.append(data)
            return
        if self._stack:
            return
        if self._heading:
            self._heading[1].append(data)
        self.text_parts.append(data)
        if self._content_depth:
            self.article_parts.append(data)


def path_to_url(relative: str) -> str:
    if relative == "index.html":
        return f"{ORIGIN}/"
    if relative.endswith("/index.html"):
        return f"{ORIGIN}/{relative[: -len('index.html')]}"
    return f"{ORIGIN}/{relative}"


def url_to_file(root: Path, href: str) -> Path | None:
    """Map an internal href to a file in the tree, or None when it is external."""
    parts = urlsplit(href)
    if parts.scheme or parts.netloc:
        if parts.netloc not in (HOST, f"www.{HOST}"):
            return None
        path = parts.path
    else:
        path = parts.path
    if not path or path.startswith("#"):
        return root / "index.html" if path == "" and not parts.fragment else None
    if not path.startswith("/"):
        return None
    clean = path.lstrip("/")
    if clean == "" or clean.endswith("/"):
        return root / clean / "index.html"
    candidate = root / clean
    if candidate.is_dir():
        return candidate / "index.html"
    return candidate


def parse_page(root: Path, relative: str) -> Page:
    source = (root / relative).read_text(encoding="utf-8", errors="replace")
    parser = PageParser()
    parser.feed(source)
    page = Page(path=relative, url=path_to_url(relative))
    page.title = " ".join("".join(parser.page_title).split())
    page.description = (parser.metas.get("description") or "").strip()
    page.robots = parser.metas.get("robots") or ""
    page.canonical = parser.canonical
    page.lang = parser.lang
    page.headings = parser.headings
    text = " ".join("".join(parser.text_parts).split())
    page.text_words = len(text.split())
    page.text_chars = len(text)
    page.article_text = " ".join("".join(parser.article_parts).split())
    page.links = parser.links
    page.images_total = parser.images_total
    page.images_missing_alt = parser.images_missing_alt
    page.og = {k[3:]: v for k, v in parser.metas.items() if k.startswith("og:")}
    page.twitter = {k[8:]: v for k, v in parser.metas.items() if k.startswith("twitter:")}
    page.icon = parser.icon
    page.external_scripts = parser.external_scripts
    for raw in parser.jsonld_raw:
        try:
            page.jsonld.append(json.loads(raw))
        except json.JSONDecodeError as exc:
            page.jsonld_errors.append(str(exc))
    return page


def discover_pages(root: Path, sample: int | None, seed: int = 7) -> list[str]:
    """Every HTML page in the tree; literature notes and archive list pages are sampled unless sample is None."""
    everything: list[str] = []
    for path in sorted(root.rglob("*.html")):
        relative = path.relative_to(root)
        if relative.parts[0] in SKIP_DIRS or any(part.startswith(".") for part in relative.parts):
            continue
        if len(relative.parts) == 1 and re.fullmatch(r"(naver|google)[0-9a-f]+\.html", relative.name):
            continue  # ownership verification files are not pages
        everything.append(str(relative))
    notes = [p for p in everything if p.startswith("literature/") and p.count("/") == 2 and not p.startswith("literature/page/")]
    archives = [p for p in everything if p.startswith("literature/page/")]
    others = [p for p in everything if p not in set(notes) and p not in set(archives)]
    if sample is not None:
        if len(notes) > sample:
            notes = sorted(random.Random(seed).sample(notes, sample))
        archives = [p for p in archives if p in ("literature/page/2/index.html", "literature/page/3/index.html")]
    return others + archives + notes


def keyword_tokens(text: str) -> list[str]:
    """Tokens that can count as keywords: Hangul/CJK words or Latin words of 4+ letters, minus stopwords."""
    tokens = []
    for raw in re.split(r"[\s|·,.:;/()《》〈〉\"'“”‘’\-–—!?]+", text):
        token = raw.lower()
        if not token or token in STOPWORDS:
            continue
        if HANGUL_OR_CJK.search(token) or (token.isascii() and token.isalpha() and len(token) >= 4):
            tokens.append(token)
    return tokens


def repeated_keywords(text: str, limit: int = REPEATED_KEYWORD_LIMIT) -> list[str]:
    """Tokens repeated `limit` times or more; Naver treats 2+ repeats of a keyword as a spam signal."""
    counts = Counter(keyword_tokens(text))
    return [token for token, count in counts.items() if count >= limit]


def page_issues(page: Page) -> list[Issue]:
    issues: list[Issue] = []
    report = lambda kind, details="": issues.append(Issue(kind, page.path, details))  # noqa: E731
    if page.path == "404.html":
        return issues
    if not page.title:
        report("missing-title")
    elif len(page.title) > TITLE_MAX_CHARS:
        report("title-too-long", f"{len(page.title)}자")
    elif len(page.title) < TITLE_MIN_CHARS:
        report("title-too-short", f"{len(page.title)}자")
    if not page.description:
        report("missing-meta-description")
    elif len(page.description) > META_DESCRIPTION_MAX_CHARS:
        report("meta-description-too-long", f"{len(page.description)}자")
    elif len(page.description) < META_DESCRIPTION_MIN_CHARS:
        report("meta-description-too-short", f"{len(page.description)}자")
    h1 = [text for level, text in page.headings if level == 1]
    if not h1:
        report("missing-h1")
    elif len(h1) > 1:
        report("multiple-h1", f"{len(h1)}개: " + " / ".join(h1[:3]))
    levels = [level for level, _ in page.headings]
    if any(b > a + 1 for a, b in zip(levels, levels[1:])):
        report("heading-order-skip")
    if not page.indexable:
        report("noindex-page", page.robots)
    if page.canonical and page.canonical != page.url:
        host = urlsplit(page.canonical).netloc
        if host and host not in (HOST, f"www.{HOST}"):
            report("canonical-foreign", f"canonical={page.canonical}")
        else:
            report("canonicalized-page", f"canonical={page.canonical} 실제={page.url}")
    if page.indexable and page.text_words < THIN_CONTENT_WORDS:
        report("thin-content", f"{page.text_words}어절 / {page.text_chars}자")
    if page.images_missing_alt:
        report("images-missing-alt", f"{page.images_missing_alt}/{page.images_total}")
    if page.indexable and not page.links:
        report("no-outgoing-links")
    if page.depth is not None and page.depth >= DEEP_PAGE_DEPTH:
        report("deep-page", f"깊이 {page.depth}")
    if not page.lang:
        report("missing-lang")
    missing_og = [k for k in ("title", "description", "image", "url", "type") if k not in page.og]
    if page.indexable and missing_og:
        report("missing-og", ", ".join(missing_og))
    title_core = page.title.split(" | ", 1)[0]
    for label, text, limit in (
        ("제목", title_core, REPEATED_KEYWORD_LIMIT),
        ("설명", page.description, REPEATED_KEYWORD_LIMIT + 1),
    ):
        repeated = repeated_keywords(text, limit)
        if repeated:
            report("repeated-keyword", f"{label}: {', '.join(repeated)}")
    if page.icon.startswith("data:"):
        report("data-uri-favicon")
    elif page.icon and not page.icon.startswith(("http://", "https://")):
        report("relative-favicon", page.icon)
    if page.external_scripts:
        report("external-script", ", ".join(page.external_scripts[:3]))
    if page.jsonld_errors:
        report("invalid-jsonld", page.jsonld_errors[0])
    return issues


def image_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return width, height
    if data[:2] == b"\xff\xd8":
        index = 2
        while index + 9 < len(data) and data[index] == 0xFF:
            marker = data[index + 1]
            length = struct.unpack(">H", data[index + 2 : index + 4])[0]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[index + 5 : index + 9])
                return width, height
            index += 2 + length
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        chunk = data[12:16]
        if chunk == b"VP8 ":
            width, height = struct.unpack("<HH", data[26:30])
            return width & 0x3FFF, height & 0x3FFF
        if chunk == b"VP8L":
            bits = struct.unpack("<I", data[21:25])[0]
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":
            width = int.from_bytes(data[24:27], "little") + 1
            height = int.from_bytes(data[27:30], "little") + 1
            return width, height
    return None


def og_image_issues(root: Path, pages: list[Page]) -> list[Issue]:
    issues: list[Issue] = []
    core_usage: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        image = page.og.get("image")
        if not image or not page.indexable:
            continue
        if page.path in CORE_PATHS:
            core_usage[image].append(page.path)
        target = url_to_file(root, image)
        if target is None:
            continue
        if not target.is_file():
            issues.append(Issue("og-image-rule", page.path, f"파일 없음: {image}"))
            continue
        size = target.stat().st_size
        dims = image_dimensions(target)
        problems = []
        if size < OG_IMAGE_MIN_BYTES:
            problems.append(f"{size}바이트 (<5,000)")
        if dims:
            width, height = dims
            if min(width, height) <= OG_IMAGE_MIN_SIDE:
                problems.append(f"{width}x{height} (150 이하)")
            if max(width, height) / max(1, min(width, height)) > OG_IMAGE_MAX_RATIO:
                problems.append(f"비율 {width}:{height} (3:1 초과)")
        if problems:
            issues.append(Issue("og-image-rule", page.path, "; ".join(problems)))
    # Generated notes legitimately share the site image; the hand-maintained
    # core pages are the ones worth giving a page-specific image.
    for image, paths in core_usage.items():
        if len(paths) > 1:
            issues.append(Issue("og-image-shared", "index.html", f"{len(paths)}개 핵심 페이지가 {image} 공유: {', '.join(paths)}"))
    return issues


def resolve_internal(root: Path, page: Page) -> list[tuple[str, str, Path]]:
    """(href, relative path, target) for each internal link of a page, deduplicated by target."""
    resolved = []
    seen: set[str] = set()
    for href in page.links:
        target = url_to_file(root, href)
        if target is None:
            continue
        try:
            relative = str(target.relative_to(root))
        except ValueError:
            continue
        if relative in seen:
            continue
        seen.add(relative)
        resolved.append((href, relative, target))
    return resolved


def cross_page_issues(root: Path, pages: list[Page], sampled: bool = False) -> list[Issue]:
    issues: list[Issue] = []
    by_path = {page.path: page for page in pages}
    titles: dict[str, list[str]] = defaultdict(list)
    descriptions: dict[str, list[str]] = defaultdict(list)
    bodies: dict[str, list[str]] = defaultdict(list)
    inbound: Counter = Counter()
    graph: dict[str, set[str]] = defaultdict(set)
    for page in pages:
        self_canonical = not page.canonical or page.canonical == page.url
        if page.indexable and self_canonical:
            if page.title:
                titles[page.title].append(page.path)
            if page.description:
                descriptions[page.description].append(page.path)
            if page.article_text and page.text_words:
                bodies[hashlib.sha1(page.article_text.encode("utf-8")).hexdigest()].append(page.path)
        for href, relative, target in resolve_internal(root, page):
            if not target.is_file():
                issues.append(Issue("broken-internal-link", page.path, href))
                continue
            if relative != page.path:
                inbound[relative] += 1
            if relative in by_path:
                graph[page.path].add(relative)
    for title, paths in titles.items():
        if len(paths) > 1:
            issues.append(Issue("duplicate-title", paths[0], f"{len(paths)}개: {', '.join(paths[:4])} — “{title[:60]}”"))
    for description, paths in descriptions.items():
        if len(paths) > 1:
            issues.append(Issue("duplicate-meta-description", paths[0], f"{len(paths)}개: {', '.join(paths[:4])}"))
    for digest, paths in bodies.items():
        if len(paths) > 1:
            issues.append(Issue("duplicate-content", paths[0], f"{len(paths)}개: {', '.join(paths[:4])}"))
    for page in pages:
        if page.path in ("index.html", "404.html"):
            continue
        if sampled and page.path.startswith("literature/") and page.path != "literature/index.html":
            # A sampled note is normally linked from list pages and neighbours
            # that are outside the sample, so orphan status is only decided
            # for notes in a --full crawl.
            continue
        if page.indexable and inbound[page.path] == 0:
            issues.append(Issue("orphan-page", page.path, "점검한 어떤 페이지도 이 주소로 링크하지 않음"))
    if "index.html" in by_path:
        depth = {"index.html": 0}
        queue = deque(["index.html"])
        while queue:
            current = queue.popleft()
            for nxt in graph[current]:
                if nxt not in depth:
                    depth[nxt] = depth[current] + 1
                    queue.append(nxt)
        for page in pages:
            page.depth = depth.get(page.path)
    return issues


def robots_issues(root: Path) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    path = root / "robots.txt"
    facts = {"exists": path.is_file()}
    if not path.is_file():
        issues.append(Issue("robots-missing-sitemap", "robots.txt", "파일 없음(모두 허용으로 해석되나 Sitemap 지시어도 없음)"))
        return issues, facts
    text = path.read_text(encoding="utf-8", errors="replace")
    groups: dict[str, list[str]] = defaultdict(list)
    current: list[str] = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if key.lower() == "user-agent":
            current = [value.lower()]
        elif key.lower() in ("allow", "disallow"):
            for agent in current:
                groups[agent].append(f"{key.lower()}:{value}")
    rules = groups.get("yeti") or groups.get("*") or []
    blocked = any(rule == "disallow:/" for rule in rules) and not any(rule == "allow:/" for rule in rules)
    facts["yeti_rules"] = rules
    facts["sitemap_lines"] = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", text)
    if blocked:
        issues.append(Issue("robots-blocks-yeti", "robots.txt", "; ".join(rules)))
    if not facts["sitemap_lines"]:
        issues.append(Issue("robots-missing-sitemap", "robots.txt"))
    return issues, facts


def sitemap_entries(root: Path, relative: str, issues: list[Issue], depth: int = 0) -> list[ET.Element]:
    """<url> elements of a sitemap, following a sitemap index one level down."""
    path = root / relative
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        issues.append(Issue("invalid-xml", relative, str(exc)))
        return []
    ns = {"sm": SITEMAP_NS}
    rootel = tree.getroot()
    if rootel.tag == f"{{{SITEMAP_NS}}}sitemapindex" and depth == 0:
        entries: list[ET.Element] = []
        for child in rootel.findall("sm:sitemap", ns):
            loc = child.findtext("sm:loc", default="", namespaces=ns)
            target = url_to_file(root, loc)
            if target is None or not target.is_file():
                issues.append(Issue("sitemap-missing-file", relative, loc))
                continue
            entries.extend(sitemap_entries(root, str(target.relative_to(root)), issues, depth + 1))
        return entries
    return rootel.findall("sm:url", ns)


def sitemap_issues(root: Path) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    path = root / "sitemap.xml"
    facts: dict = {"exists": path.is_file()}
    if not path.is_file():
        return issues, facts
    facts["bytes"] = path.stat().st_size
    entries = sitemap_entries(root, "sitemap.xml", issues)
    ns = {"sm": SITEMAP_NS}
    locs = [entry.findtext("sm:loc", default="", namespaces=ns) for entry in entries]
    facts["urls"] = len(locs)
    facts["lastmod_missing"] = sum(1 for entry in entries if entry.find("sm:lastmod", ns) is None)
    if len(locs) > SITEMAP_MAX_URLS:
        issues.append(Issue("feed-too-large", "sitemap.xml", f"{len(locs)} URL (>50,000)"))
    if facts["bytes"] >= FEED_MAX_BYTES:
        issues.append(Issue("feed-too-large", "sitemap.xml", f"{facts['bytes']:,} bytes"))
    elif facts["bytes"] >= FEED_WARN_BYTES:
        issues.append(Issue("feed-near-limit", "sitemap.xml", f"{facts['bytes']:,} bytes"))
    missing = 0
    for loc in locs:
        parts = urlsplit(loc)
        if parts.netloc != HOST or parts.scheme != "https":
            issues.append(Issue("sitemap-host-mismatch", "sitemap.xml", loc))
            continue
        target = url_to_file(root, loc)
        if target is None or not target.is_file():
            missing += 1
            if missing <= 5:
                issues.append(Issue("sitemap-missing-file", "sitemap.xml", loc))
    facts["missing_files"] = missing
    core_lastmod = {}
    for entry in entries:
        loc = entry.findtext("sm:loc", default="", namespaces=ns)
        if loc in {f"{ORIGIN}/", f"{ORIGIN}/author/", f"{ORIGIN}/works/", f"{ORIGIN}/official-links/"}:
            core_lastmod[loc] = entry.findtext("sm:lastmod", default="", namespaces=ns)
    facts["core_lastmod"] = core_lastmod
    return issues, facts


def feed_issues(root: Path, relative: str, pages_by_url: dict[str, Page]) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    path = root / relative
    facts: dict = {"exists": path.is_file()}
    if not path.is_file():
        return issues, facts
    facts["bytes"] = path.stat().st_size
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        issues.append(Issue("invalid-xml", relative, str(exc)))
        return issues, facts
    items = tree.getroot().findall("./channel/item")
    facts["items"] = len(items)
    facts["bytes_per_item"] = round(facts["bytes"] / len(items)) if items else 0
    facts["headroom_items"] = (FEED_MAX_BYTES - facts["bytes"]) // facts["bytes_per_item"] if facts["bytes_per_item"] else None
    if facts["bytes"] >= FEED_MAX_BYTES:
        issues.append(Issue("feed-too-large", relative, f"{facts['bytes']:,} bytes, {len(items)} items"))
    elif facts["bytes"] >= FEED_WARN_BYTES:
        issues.append(Issue("feed-near-limit", relative, f"{facts['bytes']:,} bytes, {len(items)} items (남은 여유 약 {facts['headroom_items']}건)"))
    excerpt_like = 0
    compared = 0
    for item in items:
        link = item.findtext("link") or ""
        if urlsplit(link).netloc != HOST:
            issues.append(Issue("sitemap-host-mismatch", relative, link))
            continue
        body = item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or item.findtext("description") or ""
        page = pages_by_url.get(link)
        if page is None:
            target = url_to_file(root, link)
            if target is not None and target.is_file():
                page = parse_page(root, str(target.relative_to(root)))
                pages_by_url[link] = page
        if page is None or page.article_chars == 0:
            continue
        compared += 1
        if len(body) < 0.5 * page.article_chars:
            excerpt_like += 1
        if compared >= 40:
            break
    facts["compared"] = compared
    facts["excerpt_like"] = excerpt_like
    if compared and excerpt_like / compared > 0.5:
        issues.append(
            Issue("feed-excerpt-only", relative, f"비교한 {compared}건 중 {excerpt_like}건의 description이 본문(article)의 절반 미만")
        )
    return issues, facts


def jsonld_nodes(page: Page) -> list[dict]:
    nodes: list[dict] = []
    for block in page.jsonld:
        if isinstance(block, dict) and isinstance(block.get("@graph"), list):
            nodes.extend(node for node in block["@graph"] if isinstance(node, dict))
        elif isinstance(block, dict):
            nodes.append(block)
        elif isinstance(block, list):
            nodes.extend(node for node in block if isinstance(node, dict))
    return nodes


def channel_markup_issues(root_page: Page | None) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    facts: dict = {"person": None, "same_as": [], "channel_same_as": [], "other_same_as": [], "selected_by": None}
    if root_page is None:
        return issues, facts
    candidates = []
    for node in jsonld_nodes(root_page):
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if not ("Person" in types or "Organization" in types):
            continue
        same_as = node.get("sameAs") or []
        if isinstance(same_as, str):
            same_as = [same_as]
        if node.get("name") and node.get("url") and same_as:
            candidates.append((node, same_as))
    chosen = None
    for node, same_as in candidates:
        if node.get("url") == f"{ORIGIN}/" or node.get("@id") == f"{ORIGIN}/#person":
            chosen = (node, same_as)
            facts["selected_by"] = "url or @id of the site"
            break
    if chosen is None and candidates:
        chosen = candidates[0]
        facts["selected_by"] = "first node with name/url/sameAs (no node has the site url)"
    if chosen is None:
        issues.append(Issue("missing-channel-markup", "index.html"))
        return issues, facts
    node, same_as = chosen
    facts["person"] = node.get("name")
    facts["same_as"] = same_as
    for url in same_as:
        host = urlsplit(url).netloc.lower().removeprefix("www.").removeprefix("m.")
        if any(host == domain or host.endswith("." + domain) for domain in NAVER_CHANNEL_DOMAINS):
            facts["channel_same_as"].append(url)
        else:
            facts["other_same_as"].append(url)
    if facts["other_same_as"]:
        issues.append(Issue("sameas-non-channel", "index.html", ", ".join(facts["other_same_as"][:5])))
    return issues, facts


def verification_facts(root: Path) -> tuple[list[Issue], dict]:
    issues: list[Issue] = []
    naver = sorted(p.name for p in root.glob("naver*.html"))
    google = sorted(p.name for p in root.glob("google*.html"))
    indexnow = sorted(p.name for p in root.glob("*.txt") if re.fullmatch(r"[0-9a-f]{32}\.txt", p.name))
    facts = {"naver": naver, "google": google, "indexnow_key": indexnow}
    if not naver:
        issues.append(Issue("missing-verification-file", "/", "naver*.html 없음(meta 태그 방식이면 index.html에 naver-site-verification 필요)"))
    return issues, facts


def audit(root: Path, sample: int | None = 200) -> dict:
    relatives = discover_pages(root, sample)
    pages = [parse_page(root, relative) for relative in relatives]
    issues: list[Issue] = []
    issues.extend(cross_page_issues(root, pages, sampled=sample is not None))  # sets depth first
    for page in pages:
        issues.extend(page_issues(page))
    issues.extend(og_image_issues(root, pages))
    robots, robots_facts = robots_issues(root)
    sitemap, sitemap_facts = sitemap_issues(root)
    pages_by_url = {page.url: page for page in pages}
    feeds: dict[str, dict] = {}
    for feed in sorted(str(p.relative_to(root)) for p in root.rglob("*.xml") if p.name in FEED_NAMES and ".git" not in p.parts):
        found, facts = feed_issues(root, feed, pages_by_url)
        issues.extend(found)
        feeds[feed] = facts
    root_page = pages_by_url.get(f"{ORIGIN}/")
    channel, channel_facts = channel_markup_issues(root_page)
    verification, verification_facts_ = verification_facts(root)
    issues.extend(robots + sitemap + channel + verification)
    issues.sort(key=lambda item: (SEVERITY_ORDER[item.severity], item.issue_type, item.page))
    return {
        "date": date.today().isoformat(),
        "root": str(root),
        "pages_crawled": len(pages),
        "sample": sample,
        "issues": [
            {"type": i.issue_type, "severity": i.severity, "title": i.title, "page": i.page, "details": i.details}
            for i in issues
        ],
        "facts": {
            "robots": robots_facts,
            "sitemap": sitemap_facts,
            "feeds": feeds,
            "channel_markup": channel_facts,
            "verification": verification_facts_,
            "core_titles": {p.path: p.title for p in pages if p.path in CORE_PATHS},
        },
    }


def issue_key(issue: dict) -> tuple[str, str]:
    return (issue["type"], issue["page"])


def render_report(result: dict, verbose: bool = False) -> str:
    issues = result["issues"]
    by_type: dict[str, list[dict]] = defaultdict(list)
    for issue in issues:
        by_type[issue["type"]].append(issue)
    counts = Counter(issue["severity"] for issue in issues)
    facts = result["facts"]
    lines = [
        f"# 네이버 SEO 로컬 점검 — {result['date']}",
        "",
        "검사 대상: 저장소 파일 기준 (수집·색인·순위는 관찰하지 않음).",
        f"점검한 페이지 {result['pages_crawled']}개"
        + (f" (문학노트는 {result['sample']}개 표본)" if result["sample"] else " (전체)")
        + f", 발견 항목 심각 {counts['critical']} / 경고 {counts['warning']} / 참고 {counts['info']}.",
        "",
        "## 점검 결과 요약",
        "",
    ]
    actionable = [t for t in by_type if ISSUE_TEXT[t][0] in ("critical", "warning")]
    actionable.sort(key=lambda t: (SEVERITY_ORDER[ISSUE_TEXT[t][0]], -len(by_type[t])))
    if not actionable:
        lines.append("- 심각·경고 항목 없음. 참고 항목은 JSON 결과(또는 --verbose)에서 확인합니다.")
    for kind in actionable[:5]:
        group = by_type[kind]
        lines.append(f"- **{ISSUE_TEXT[kind][1]}** ({len(group)}건): 예 `{group[0]['page']}` {group[0]['details']}".rstrip())
    lines += ["", "다음 조치는 이 요약을 읽은 사람이 기회 목록을 만든 뒤 정합니다(도구가 고르지 않습니다).", "", "## 발견 항목", ""]
    shown = [t for t in sorted(by_type, key=lambda t: (SEVERITY_ORDER[ISSUE_TEXT[t][0]], t)) if verbose or ISSUE_TEXT[t][0] != "info"]
    if not shown:
        lines.append("- 없음")
    for kind in shown:
        group = by_type[kind]
        lines.append(f"### {ISSUE_TEXT[kind][1]} — {ISSUE_TEXT[kind][0]} · {len(group)}건")
        lines.append("")
        for issue in group[:10]:
            detail = f" — {issue['details']}" if issue["details"] else ""
            lines.append(f"- `{issue['page']}`{detail}")
        if len(group) > 10:
            lines.append(f"- … 외 {len(group) - 10}건")
        lines.append("")
    info_types = [t for t in by_type if ISSUE_TEXT[t][0] == "info"]
    if info_types and not verbose:
        lines.append("참고(info) 항목: " + ", ".join(f"{ISSUE_TEXT[t][1]} {len(by_type[t])}건" for t in sorted(info_types)) + " — JSON 결과 또는 `--verbose`에서 상세 확인.")
        lines.append("")
    lines += ["## 그 밖에 확인한 항목", "", "| 항목 | 결과 |", "| --- | --- |"]
    robots = facts["robots"]
    lines.append(f"| robots.txt | 존재 {robots.get('exists')} · Yeti 규칙 {robots.get('yeti_rules')} · Sitemap {robots.get('sitemap_lines')} |")
    sitemap = facts["sitemap"]
    lines.append(
        f"| sitemap.xml | URL {sitemap.get('urls')}개 · {sitemap.get('bytes', 0):,} bytes · 파일 없는 URL {sitemap.get('missing_files', 0)}개 · 핵심 페이지 lastmod {sitemap.get('core_lastmod')} |"
    )
    for feed, info in facts["feeds"].items():
        lines.append(
            f"| {feed} | 항목 {info.get('items')}개 · {info.get('bytes', 0):,} bytes (한도 10,000,000; 10MiB 기준 10,485,760) · 항목당 평균 {info.get('bytes_per_item', 0):,} bytes · 남은 여유 약 {info.get('headroom_items')}건 · 본문 비교 {info.get('compared')}건 중 요약형 {info.get('excerpt_like')}건 |"
        )
    channel = facts["channel_markup"]
    lines.append(
        f"| 루트 연관채널 마크업 | Person `{channel.get('person')}` ({channel.get('selected_by')}) · 인식 채널 {len(channel.get('channel_same_as', []))}개 · 기타 {len(channel.get('other_same_as', []))}개 |"
    )
    verification = facts["verification"]
    lines.append(
        f"| 소유확인·IndexNow | naver {verification.get('naver')} · google {verification.get('google')} · IndexNow 키 {verification.get('indexnow_key')} |"
    )
    for path, title in facts["core_titles"].items():
        lines.append(f"| 제목 `{path}` | {title} ({len(title)}자) |")
    lines += ["", "### 오프라인에서 확인 불가", ""]
    lines += [f"- {item}" for item in OFFLINE_UNVERIFIABLE]
    lines += [
        "",
        "## 이 보고서를 만든 방법",
        "",
        "OpenSEO SEO Audit skill (https://openseo.so/docs/skills/seo-audit) 방법론과 사이트 감사 이슈 목록(스냅샷 커밋 95c4d10c, `skills/openseo/`)을"
        " 저장소 파일에 적용했고, 네이버 서치어드바이저 웹마스터 가이드(robots.txt, RSS·사이트맵 제출, 콘텐츠 마크업, 사이트 연관채널, 파비콘) 항목을 더했습니다.",
        "",
        "- 도구가 보고한 것: 위 발견 항목과 표의 수치 전부 (파일 기준, 표준 라이브러리만 사용, 네트워크 없음).",
        "- 사람이 확인한 것: (에이전트가 채움 — 날짜를 적은 실제 네이버 검색 결과, 서치어드바이저 상태 등)",
        "",
        "제목·설명 길이 기준은 OpenSEO의 라틴 문자 기준(10–60자, 70–160자)이라 한글 페이지에서는 참고용입니다."
        " 실제 수집 여부와 노출은 네이버 서치어드바이저의 요청·리포트 메뉴에서만 확인할 수 있습니다.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local Naver/OpenSEO style audit of the static site")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, required=True, help="write the markdown report here (choose a path outside the published tree unless it is meant to be public)")
    parser.add_argument("--json", type=Path, help="write the raw result here")
    parser.add_argument("--sample", type=int, default=200, help="number of literature notes to sample (default 200)")
    parser.add_argument("--full", action="store_true", help="crawl every literature note (about 20 seconds)")
    parser.add_argument("--verbose", action="store_true", help="list info-level findings in the report too")
    parser.add_argument("--fail-on", choices=("critical", "warning"), default="critical", help="lowest severity that makes the exit code non-zero")
    parser.add_argument("--baseline", type=Path, help="previous --json result; only issues absent from it count towards the exit code")
    args = parser.parse_args(argv)
    result = audit(args.root.resolve(), None if args.full else args.sample)
    report = render_report(result, verbose=args.verbose)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    counted = result["issues"]
    if args.baseline:
        previous = {issue_key(issue) for issue in json.loads(args.baseline.read_text(encoding="utf-8"))["issues"]}
        counted = [issue for issue in counted if issue_key(issue) not in previous]
    severities = Counter(issue["severity"] for issue in counted)
    if severities["critical"]:
        return 2
    if args.fail_on == "warning" and severities["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
