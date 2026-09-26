#!/usr/bin/env python3
"""Rebuild the public updates index from existing pages, never a publication ledger."""

from __future__ import annotations

import json
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://xn--hu5b23z.com"


class UpdateParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = []
        self.in_heading = False
        self.canonical = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "h1":
            self.in_heading = True
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_heading = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading.append(data)


def collect_updates(root=ROOT):
    entries = []
    for page in sorted((root / "seo-updates").glob("*/index.html"), reverse=True):
        slug = page.parent.name
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+", slug):
            raise ValueError(f"Unexpected update path: {slug}")
        parser = UpdateParser()
        parser.feed(page.read_text(encoding="utf-8"))
        url = f"{ORIGIN}/seo-updates/{slug}/"
        title = " ".join("".join(parser.heading).split())
        if not title or parser.canonical != url:
            raise ValueError(f"Missing heading or mismatched canonical: {page}")
        entries.append({"url": url, "title": title, "date": slug[:10]})
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
<meta name="description" content="소설가 이후가 일상에서 떠올린 짧은 글과 작품 관련 소식을 모았습니다.">
<link rel="canonical" href="{ORIGIN}/seo-updates/">
<script type="application/ld+json">{structured}</script>
<style>body{{font-family:-apple-system,'Noto Sans KR',sans-serif;max-width:820px;margin:auto;padding:40px 20px;line-height:1.8}}a{{color:inherit}}li{{margin:12px 0}}time{{color:#666;font-size:.875rem;white-space:nowrap}}</style>
</head><body><nav><a href="/">홈</a> · <a href="/author/">작가 프로필</a> · <a href="/works/">작품 안내</a> · <a href="/literature/">문학노트</a></nav>
<main><h1>소설가 이후 공식 소식</h1><p>일상에서 떠올린 짧은 글과 작품 관련 소식을 모았습니다.</p><ul>
{items}
</ul></main></body></html>
'''


def build(root=ROOT):
    entries = collect_updates(root)
    target = root / "seo-updates" / "index.html"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(render_index(entries), encoding="utf-8")
    temporary.replace(target)
    return len(entries)


if __name__ == "__main__":
    print(f"Built updates index from {build()} existing pages")
