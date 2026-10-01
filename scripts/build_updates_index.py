#!/usr/bin/env python3
"""Rebuild the public updates index and RSS feed from existing pages, never a publication ledger."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://xn--hu5b23z.com"
# Naver Search Advisor wants an RSS feed of the latest items with their full
# body and under 10MB; the sitemap lists every update URL.
RSS_ITEM_LIMIT = 50
KST = timezone(timedelta(hours=9))


class UpdateParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.heading = []
        self.in_heading = False
        self.canonical = None
        self.robots = ""
        self.description = ""
        self.paragraphs = []
        self.published = None
        self._in_article = False
        self._in_paragraph = False
        self._paragraph = []
        self._in_ld = False
        self._ld = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.in_heading = True
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        if tag == "meta" and values.get("name") == "robots":
            self.robots = values.get("content") or ""
        if tag == "meta" and values.get("name") == "description":
            self.description = values.get("content") or ""
        if tag == "script" and values.get("type") == "application/ld+json":
            self._in_ld = True
        if tag == "article":
            self._in_article = True
        if self._in_article and tag == "p" and "meta" not in (values.get("class") or "").split():
            self._in_paragraph = True
            self._paragraph = []

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False
        if tag == "script" and self._in_ld:
            self._in_ld = False
            try:
                data = json.loads("".join(self._ld))
            except json.JSONDecodeError:
                data = {}
            if isinstance(data, dict) and data.get("datePublished"):
                self.published = str(data["datePublished"])
            self._ld = []
        if tag == "article":
            self._in_article = False
        if tag == "p" and self._in_paragraph:
            self._in_paragraph = False
            text = "\n".join(" ".join(line.split()) for line in "".join(self._paragraph).splitlines())
            text = re.sub(r"\n{2,}", "\n\n", text).strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)
        if self._in_ld:
            self._ld.append(data)
        if self._in_paragraph:
            self._paragraph.append(data)


def collect_updates(root=ROOT):
    """Return published updates newest first; duplicates that canonicalize to another update are skipped."""
    entries = []
    for page in sorted((root / "seo-updates").glob("*/index.html"), reverse=True):
        slug = page.parent.name
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+", slug):
            raise ValueError(f"Unexpected update path: {slug}")
        parser = UpdateParser()
        parser.feed(page.read_text(encoding="utf-8"))
        url = f"{ORIGIN}/seo-updates/{slug}/"
        title = " ".join("".join(parser.heading).split())
        canonical = parser.canonical or ""
        if canonical != url and canonical.startswith(f"{ORIGIN}/seo-updates/") and "noindex" in parser.robots:
            continue  # a republished duplicate pointing at its original: not listed, not fed
        if not title or canonical != url:
            raise ValueError(f"Missing heading or mismatched canonical: {page}")
        entries.append(
            {
                "url": url,
                "title": title,
                "date": slug[:10],
                "description": " ".join(parser.description.split()),
                "body": "\n\n".join(parser.paragraphs),
                "published": parser.published,
            }
        )
    if not entries:
        raise ValueError("No published updates; refusing to replace the index")
    return entries


def render_index(entries):
    items = "\n".join(
        f'<li><a href="{escape(item["url"], quote=True)}">{escape(item["title"])}</a> '
        f'<time datetime="{item["date"]}">{item["date"]}</time></li>'
        for item in entries
    )
    schema = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "소설가 이후 공식 소식", "url": f"{ORIGIN}/seo-updates/",
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i, "name": item["title"], "url": item["url"]}
            for i, item in enumerate(entries, 1)
        ]},
    }
    structured = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>소설가 이후 공식 소식</title>
<meta name="description" content="소설가 이후(李後, Lee Hu)가 일상에서 떠올린 짧은 글과 작품 관련 소식을 날짜순으로 모았습니다.">
<link rel="canonical" href="{ORIGIN}/seo-updates/">
<meta property="og:type" content="website">
<meta property="og:title" content="소설가 이후 공식 소식">
<meta property="og:description" content="소설가 이후(李後, Lee Hu)가 일상에서 떠올린 짧은 글과 작품 관련 소식을 날짜순으로 모았습니다.">
<meta property="og:url" content="{ORIGIN}/seo-updates/">
<meta property="og:image" content="{ORIGIN}/og-image.jpg">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="소설가 이후 공식 소식 RSS" href="{ORIGIN}/seo-updates/rss.xml">
<script type="application/ld+json">{structured}</script>
<style>body{{font-family:-apple-system,'Noto Sans KR',sans-serif;max-width:820px;margin:auto;padding:40px 20px;line-height:1.8}}a{{color:inherit}}li{{margin:12px 0}}time{{color:#666;font-size:.875rem;white-space:nowrap}}</style>
</head><body><nav><a href="/">홈</a> · <a href="/author/">작가 프로필</a> · <a href="/works/">작품 안내</a> · <a href="/literature/">문학노트</a></nav>
<main><h1>소설가 이후 공식 소식</h1><p>일상에서 떠올린 짧은 글과 작품 관련 소식을 모았습니다.</p><ul>
{items}
</ul></main></body></html>
'''


def publication_datetime(item):
    raw = item.get("published") or f"{item['date']}T00:00:00"
    moment = datetime.fromisoformat(raw)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=KST)
    return moment


def render_rss(entries):
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for name, value in (
        ("title", "소설가 이후 공식 소식"),
        ("link", f"{ORIGIN}/seo-updates/"),
        ("description", "소설가 이후가 일상에서 떠올린 짧은 글과 작품 관련 소식"),
        ("language", "ko"),
    ):
        ET.SubElement(channel, name).text = value
    ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
        href=f"{ORIGIN}/seo-updates/rss.xml",
        rel="self",
        type="application/rss+xml",
    )
    for item in entries[:RSS_ITEM_LIMIT]:
        node = ET.SubElement(channel, "item")
        ET.SubElement(node, "title").text = item["title"]
        ET.SubElement(node, "link").text = item["url"]
        ET.SubElement(node, "guid", isPermaLink="true").text = item["url"]
        ET.SubElement(node, "pubDate").text = format_datetime(publication_datetime(item))
        ET.SubElement(node, "description").text = item["body"] or item["description"]
        ET.SubElement(node, "author").text = "소설가 이후"
    return ET.tostring(rss, encoding="unicode", xml_declaration=True)


def write_atomic(target: Path, text: str) -> None:
    temporary = target.with_suffix(".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(target)


def build(root=ROOT):
    entries = collect_updates(root)
    write_atomic(root / "seo-updates" / "index.html", render_index(entries))
    write_atomic(root / "seo-updates" / "rss.xml", render_rss(entries))
    return len(entries)


if __name__ == "__main__":
    print(f"Built updates index and RSS from {build()} existing pages")
