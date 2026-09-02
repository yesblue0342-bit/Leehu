#!/usr/bin/env python3
"""Validate source notes and build the complete static literature-note site."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import stat
import sys
import time
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from literature_index_policy import (  # noqa: E402
    load_index_policy,
    partition_indexable_notes,
)


CONTENT_DIR = ROOT / "content" / "literature"
INDEX_POLICY_PATH = ROOT / "content" / "literature-index-policy.json"
LITERATURE_DIR = ROOT / "literature"
ORIGIN = "https://xn--hu5b23z.com"
CORE_PAGE_LASTMOD = "2026-09-03"
PAGE_SIZE = 25
EXPECTED_COUNT = 4631
REQUIRED_FIELDS = (
    "id", "slug", "title", "quote", "source_author", "source_work",
    "source_location", "source_language", "source_url", "translation_note",
    "rights_note", "commentary", "closing", "author", "tags",
    "related_work", "published_at",
)
SENTENCE_RE = re.compile(r"(?<=[.!?。])\s+")
PROTECTED_ABBREVIATION_RE = re.compile(
    r"\b(?:Mr|Mrs|Ms|Dr|Prof|St|Jr|Sr|[A-Z])\."
)
WORK_TITLE_RE = re.compile(r"《[^》]*》")
TITLE_PUNCTUATION_TO_PLACEHOLDER = str.maketrans(
    {".": "\u2024", "!": "\ufe15", "?": "\ufe16", "。": "\uff61"}
)
TITLE_PLACEHOLDER_TO_PUNCTUATION = str.maketrans(
    {"\u2024": ".", "\ufe15": "!", "\ufe16": "?", "\uff61": "。"}
)

STYLE = """
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#fff;--panel:#f7f7f8;--ink:#111827;--muted:#6b7280;--line:#e5e7eb;--gold:#b89a5c;--red:#8b1a1a}
body{font-family:"Gowun Batang","Noto Serif KR",serif;background:var(--bg);color:var(--ink);line-height:1.8}
a{color:inherit}.site-nav{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;height:74px;padding:0 clamp(20px,5vw,56px);background:rgba(255,255,255,.94);border-bottom:1px solid var(--line)}
.site-nav a{text-decoration:none}.nav-logo{font-weight:900;font-size:1.25rem}.nav-links{display:flex;gap:18px;list-style:none;color:#4b5563;font-size:.9rem}
.wrap{width:min(1120px,calc(100% - 40px));margin:0 auto}.hero{padding:76px 0 48px;border-bottom:1px solid var(--line)}
.eyebrow{font-size:.86rem;letter-spacing:.24em;color:var(--red);font-style:italic}.hero h1{font-size:clamp(2.5rem,7vw,5rem);line-height:1.15;margin:12px 0}.lede{color:var(--muted);max-width:720px}
.search-panel{margin-top:28px;max-width:720px}.search-box{display:flex;gap:10px;align-items:center}.search-box input{width:100%;border:1px solid var(--line);border-radius:999px;padding:13px 16px;font:inherit;background:#fff;color:var(--ink)}.search-box button{border:1px solid var(--ink);border-radius:999px;padding:12px 18px;background:var(--ink);color:#fff;font:inherit;white-space:nowrap;cursor:pointer}.search-meta{margin-top:10px;color:var(--muted);font-size:.88rem}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding:42px 0}
.note-card{display:flex;flex-direction:column;min-height:330px;border:1px solid var(--line);border-radius:18px;padding:22px;text-decoration:none;background:#fff}
.note-card:hover{border-color:var(--gold);transform:translateY(-2px)}.note-card small{color:var(--gold);letter-spacing:.08em}.note-card h2{font-size:1.08rem;line-height:1.5;margin:10px 0}
.note-card blockquote{color:#374151;font-size:.9rem;line-height:1.85;flex:1}.note-card p{color:var(--muted);font-size:.8rem;margin-top:14px}
.pagination{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;padding:0 0 54px}.pagination a,.pagination span{border:1px solid var(--line);border-radius:999px;padding:7px 12px;text-decoration:none}
.pagination .current{background:var(--ink);color:#fff}.footer{padding:46px 20px;text-align:center;border-top:1px solid var(--line);background:#fafafa;color:var(--muted)}
.article{width:min(820px,calc(100% - 40px));margin:0 auto;padding:64px 0}.breadcrumbs{font-size:.82rem;color:var(--muted);margin-bottom:32px}.article h1{font-size:clamp(2rem,5vw,3.7rem);line-height:1.25;margin:12px 0 18px}
.meta{color:var(--muted);font-size:.88rem}.article blockquote{margin:42px 0 20px;padding:30px;border-left:3px solid var(--gold);background:var(--panel);font-size:clamp(1.25rem,3vw,1.8rem);line-height:1.7;font-style:italic}
.source{font-size:.9rem;color:var(--muted);margin-bottom:42px}.source a{text-underline-offset:3px}.commentary h2{font-size:1.2rem;margin-bottom:14px}.commentary p{font-size:1.04rem;line-height:2.05;white-space:normal}.commentary + .commentary{margin-top:clamp(48px,7vw,68px)}
.collection-introduction{margin:34px 0 18px;font-size:1.08rem;line-height:2}.collection-deck{margin:0 0 24px;color:#374151;font-size:1.05rem;line-height:1.95}.rights-note{margin:0 0 36px;padding:18px 20px;background:var(--panel);border-radius:12px;color:var(--muted);font-size:.9rem;line-height:1.8}.collection-work{margin:46px 0;padding-top:34px;border-top:1px solid var(--line)}.collection-work h2{font-size:1.45rem;line-height:1.5}.collection-meta{margin:6px 0 22px;color:var(--muted)}.collection-work dl{display:grid;gap:18px}.collection-work dt{font-weight:700;color:var(--red)}.collection-work dd{margin-top:4px;line-height:1.9}.collection-closing{margin:46px 0;padding:28px;background:var(--panel);border-radius:16px;line-height:2}
.tags{display:flex;gap:8px;flex-wrap:wrap;margin:30px 0}.tag{border:1px solid var(--line);border-radius:999px;padding:6px 11px;font-size:.78rem}
.related{border-top:1px solid var(--line);padding-top:24px}.post-nav{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:42px}.post-nav a{border:1px solid var(--line);border-radius:14px;padding:14px;text-decoration:none}.post-nav .next{text-align:right}
.site-links{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:26px}.site-links a{text-decoration:none;border:1px solid var(--line);border-radius:999px;padding:7px 11px;background:#fff}
@media(max-width:850px){.grid{grid-template-columns:1fr}.nav-links{gap:10px;font-size:.78rem}.post-nav{grid-template-columns:1fr}}
"""

SEARCH_COMPONENT = """<form class="search-panel" id="literatureSearch" role="search">
  <div class="search-box"><input id="literatureSearchInput" type="search" placeholder="제목, 작가, 작품, 키워드로 문학노트 검색" autocomplete="off" aria-label="문학노트 검색"><button type="submit">검색</button></div>
  <p class="search-meta" id="literatureSearchMeta">키워드를 입력하면 전체 문학노트에서 찾아 보여줍니다.</p>
</form>
<script>
(function(){
  function initialize(){
    const form=document.getElementById("literatureSearch"), input=document.getElementById("literatureSearchInput"), meta=document.getElementById("literatureSearchMeta"), grid=document.querySelector(".grid"), pagination=document.querySelector(".pagination");
    if(!form||!input||!meta||!grid) return;
    const original=grid.innerHTML, originalPagination=pagination ? pagination.style.display : "";
    let feed;
    function posts(){ if(!feed) feed=fetch("/literature/rss.xml",{cache:"no-store"}).then(function(r){if(!r.ok)throw Error("rss");return r.text();}).then(function(xml){const doc=new DOMParser().parseFromString(xml,"application/xml");return Array.from(doc.querySelectorAll("item")).map(function(item){const text=function(name){const n=item.querySelector(name);return n?n.textContent.trim():"";};return {title:text("title"),link:text("link"),description:text("description"),author:text("author"),work:text("source"),tags:Array.from(item.querySelectorAll("category")).map(function(n){return n.textContent.trim();})};});}); return feed; }
    function add(post){const a=document.createElement("a"), small=document.createElement("small"), h2=document.createElement("h2"), quote=document.createElement("blockquote"), p=document.createElement("p");a.className="note-card";a.href=post.link;small.textContent=[post.author,post.work].filter(Boolean).join(" · ");h2.textContent=post.title;quote.textContent=post.description.slice(0,180)+(post.description.length>180?"…":"");p.textContent="자세히 읽기";a.append(small,h2,quote,p);grid.appendChild(a);}
    function search(){const query=input.value.trim().toLocaleLowerCase();if(!query){grid.innerHTML=original;meta.textContent="키워드를 입력하면 전체 문학노트에서 찾아 보여줍니다.";if(pagination)pagination.style.display=originalPagination;return;}meta.textContent="검색 중입니다.";posts().then(function(items){const terms=query.split(/\\s+/).filter(Boolean), results=items.filter(function(post){return terms.every(function(term){return [post.title,post.author,post.work,post.description,post.tags.join(" ")].join(" ").toLocaleLowerCase().includes(term);});}).slice(0,60);grid.replaceChildren();results.forEach(add);if(!results.length){const empty=document.createElement("p");empty.className="lede";empty.textContent="검색 결과가 없습니다. 다른 키워드로 다시 찾아보세요.";grid.appendChild(empty);}meta.textContent="검색 결과 "+results.length+"건";if(pagination)pagination.style.display="none";}).catch(function(){meta.textContent="검색 데이터를 불러오지 못했습니다.";});}
    form.addEventListener("submit",function(e){e.preventDefault();search();}); input.addEventListener("input",function(){clearTimeout(input._timer);input._timer=setTimeout(search,180);});
  }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",initialize,{once:true}); else initialize();
}());
</script>"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def seo_title(value: object, suffix: str = " | 이후의 문학노트", limit: int = 60) -> str:
    title = re.sub(r"\s+", " ", str(value)).strip()
    available = limit - len(suffix)
    if len(title) > available:
        title = title[: available - 1].rstrip() + "…"
    return title + suffix


def write_text_atomic(path: Path, text: str) -> None:
    if path.is_file():
        try:
            if path.read_text(encoding="utf-8") == text:
                return
        except OSError:
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    replace_with_retry(tmp, path)


def write_xml_atomic(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    ET.ElementTree(root).write(tmp, encoding="utf-8", xml_declaration=True)
    replace_with_retry(tmp, path)


def replace_with_retry(source: Path, target: Path) -> None:
    for attempt in range(12):
        try:
            source.replace(target)
            return
        except PermissionError:
            if attempt == 11:
                raise
            time.sleep(0.25)


def remove_tree_with_retry(path: Path) -> None:
    """Remove generated directories despite brief Windows/OneDrive locks."""

    def clear_readonly(function, target, error) -> None:
        if not isinstance(error, PermissionError):
            raise error
        os.chmod(target, stat.S_IWRITE)
        function(target)

    for attempt in range(20):
        try:
            shutil.rmtree(path, onexc=clear_readonly)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(0.5)


def normalize(value: object) -> str:
    return re.sub(r"[\W_]+", "", str(value).casefold())


def canonical(note: dict[str, object]) -> str:
    return f"{ORIGIN}/literature/{note['slug']}/"


COLLECTION_WORK_FIELDS = (
    "title", "author", "country_genre", "core_theme", "summary",
    "love_form", "literary_question", "one_line", "source_url",
)
COLLECTION_SOURCE_HOSTS = {
    "ebook-product.kyobobook.co.kr",
    "m.yes24.com",
    "openlibrary.org",
    "product.kyobobook.co.kr",
    "search.kyobobook.co.kr",
    "store.kyobobook.co.kr",
    "www.aladin.co.kr",
    "www.goodreads.com",
    "www.gutenberg.org",
    "www.penguin.co.uk",
}
ORIGINAL_REFLECTION_HOSTS = {
    "ebook-product.kyobobook.co.kr",
    "library.ltikorea.or.kr",
    "ko.wikisource.org",
    "www.gutenberg.org",
    "www.lepetitprince.com",
    "www.penguin.co.uk",
}
SEO_SECTION_KEYS = {
    "work_introduction",
    "why_read_now",
    "personal_reflection",
    "meaning_today",
}


def is_allowed_https_url(value: object, allowed_hosts: set[str]) -> bool:
    parsed = urlparse(str(value))
    return (
        parsed.scheme == "https"
        and parsed.hostname in allowed_hosts
        and parsed.username is None
        and parsed.password is None
    )


def validate_collection_note(
    note: dict[str, object], path_name: str, errors: list[str]
) -> None:
    """Validate the ten-work payload used by collection reflection pages."""
    for field in ("collection_introduction", "collection_closing"):
        if not isinstance(note.get(field), str) or not str(note[field]).strip():
            errors.append(f"{path_name}: missing {field}")
    sections = note.get("collection_sections")
    if not isinstance(sections, list) or len(sections) != 10:
        errors.append(f"{path_name}: collection_sections must contain 10 works")
        return
    for position, work in enumerate(sections, 1):
        if not isinstance(work, dict):
            errors.append(f"{path_name}: collection work {position} must be an object")
            continue
        for field in COLLECTION_WORK_FIELDS:
            if not isinstance(work.get(field), str) or not str(work[field]).strip():
                errors.append(
                    f"{path_name}: collection work {position} missing {field}"
                )
        if not is_allowed_https_url(work.get("source_url", ""), COLLECTION_SOURCE_HOSTS):
            errors.append(
                f"{path_name}: collection work {position} source URL must use an approved host"
            )


def sentence_edges(commentary: str) -> tuple[str, str]:
    sentences = [
        item.strip()
        for item in re.split(r"(?<=다\.)\s+", commentary.strip())
        if item.strip()
    ]
    return (normalize(sentences[0]), normalize(sentences[-1])) if sentences else ("", "")


def prose_sentences(text: str) -> list[str]:
    protected_titles = WORK_TITLE_RE.sub(
        lambda match: match.group(0).translate(TITLE_PUNCTUATION_TO_PLACEHOLDER),
        text,
    )
    protected = PROTECTED_ABBREVIATION_RE.sub(
        lambda match: match.group(0)[:-1] + "\u2024",
        protected_titles,
    )
    return [
        part.translate(TITLE_PLACEHOLDER_TO_PUNCTUATION).strip()
        for part in SENTENCE_RE.split(protected)
        if part.strip()
    ]


def prose_sentence_count(text: str) -> int:
    return len(prose_sentences(text))


def similar(a: str, b: str, threshold: float) -> bool:
    if abs(len(a) - len(b)) > max(len(a), len(b)) * 0.3:
        return False
    return SequenceMatcher(None, normalize(a), normalize(b), autojunk=False).ratio() >= threshold


def first_near_duplicate(
    notes: list[dict[str, object]], field: str, threshold: float
) -> tuple[str, str] | None:
    """Find a near duplicate with a cheap shingle gate before SequenceMatcher."""
    shingle_size = 8
    prepared: list[tuple[str, set[str]]] = []
    for note in notes:
        value = normalize(note[field])
        shingles = {value[index:index + shingle_size] for index in range(max(1, len(value) - shingle_size + 1))}
        prepared.append((value, shingles))
    for left in range(len(notes)):
        left_value, left_shingles = prepared[left]
        for right in range(left + 1, len(notes)):
            right_value, right_shingles = prepared[right]
            if abs(len(left_value) - len(right_value)) > max(
                len(left_value), len(right_value)
            ) * 0.3:
                continue
            union = len(left_shingles | right_shingles)
            jaccard = len(left_shingles & right_shingles) / union if union else 1.0
            if jaccard < max(0.32, threshold - 0.35):
                continue
            if SequenceMatcher(
                None, left_value, right_value, autojunk=False
            ).ratio() >= threshold:
                return str(notes[left]["id"]), str(notes[right]["id"])
    return None


def sort_for_publication(notes: list[dict[str, object]]) -> list[dict[str, object]]:
    """Return newest publication batches first, then highest batch sequence first."""
    return sorted(
        notes,
        key=lambda note: (
            datetime.fromisoformat(str(note["published_at"])),
            str(note["id"]),
        ),
        reverse=True,
    )


def load_and_validate(expected_count: int = EXPECTED_COUNT) -> list[dict[str, object]]:
    paths = sorted(CONTENT_DIR.glob("*.json"), key=lambda item: int(item.stem))
    errors: list[str] = []
    if len(paths) != expected_count:
        errors.append(f"expected {expected_count} source files, found {len(paths)}")
    notes: list[dict[str, object]] = []
    for position, path in enumerate(paths, 1):
        expected_name = f"{position:03d}.json"
        if path.name != expected_name:
            errors.append(f"{path.name}: expected filename {expected_name}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: invalid JSON: {exc}")
            continue
        missing = [field for field in REQUIRED_FIELDS if field not in data]
        if missing:
            errors.append(f"{path.name}: missing {', '.join(missing)}")
            continue
        id_match = re.fullmatch(
            r"(?P<date>\d{8})_leehu_literature_(?P<sequence>\d{3,})",
            str(data["id"]),
        )
        if not id_match:
            errors.append(f"{path.name}: invalid literature id")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(data["slug"])):
            errors.append(f"{path.name}: invalid slug")
        if not isinstance(data["tags"], list) or not 2 <= len(data["tags"]) <= 6:
            errors.append(f"{path.name}: tags must contain 2-6 items")
        elif len({normalize(tag) for tag in data["tags"]}) != len(data["tags"]):
            errors.append(f"{path.name}: duplicate tags")
        if not isinstance(data["related_work"], dict) or not {"name", "url"} <= set(data["related_work"]):
            errors.append(f"{path.name}: invalid related_work")
        content_kind = str(data.get("content_kind", "source_quote"))
        parsed_url = urlparse(str(data["source_url"]))
        allowed_hosts = {"www.gutenberg.org", "ko.wikisource.org"}
        if content_kind == "collection_reflection":
            validate_collection_note(data, path.name, errors)
            if "직접 인용 없음" not in str(data["rights_note"]):
                errors.append(
                    f"{path.name}: collection_reflection must disclose no direct quote"
                )
            if not is_allowed_https_url(data["source_url"], COLLECTION_SOURCE_HOSTS):
                errors.append(f"{path.name}: invalid collection source URL")
        elif content_kind == "original_reflection":
            if "직접 인용 없음" not in str(data["rights_note"]):
                errors.append(f"{path.name}: original_reflection must disclose no direct quote")
            if not is_allowed_https_url(
                data["source_url"], ORIGINAL_REFLECTION_HOSTS
            ):
                errors.append(f"{path.name}: invalid source URL for content kind")
        elif content_kind == "source_quote":
            if parsed_url.scheme != "https" or parsed_url.netloc not in allowed_hosts:
                errors.append(f"{path.name}: invalid source URL for content kind")
        else:
            errors.append(f"{path.name}: invalid content_kind")
        if isinstance(data.get("related_work"), dict) and not is_allowed_https_url(
            data["related_work"].get("url", ""), COLLECTION_SOURCE_HOSTS
        ):
            errors.append(f"{path.name}: invalid related_work URL")
        try:
            published_at = datetime.fromisoformat(str(data["published_at"]))
        except ValueError:
            errors.append(f"{path.name}: invalid published_at")
        else:
            if id_match and id_match.group("date") != published_at.strftime("%Y%m%d"):
                errors.append(f"{path.name}: id date must match published_at")
        quote = str(data["quote"]).strip()
        commentary = str(data["commentary"]).strip()
        seo_sections = data.get("seo_sections")
        if seo_sections is not None:
            if not isinstance(seo_sections, dict) or set(seo_sections) != SEO_SECTION_KEYS:
                errors.append(f"{path.name}: invalid seo_sections keys")
            elif any(
                not isinstance(value, str) or len(value.strip()) < 80
                for value in seo_sections.values()
            ):
                errors.append(f"{path.name}: seo_sections values too short")
        minimum_quote_length = 12 if str(data["source_language"]) == "ko" and content_kind == "source_quote" else 50
        if not minimum_quote_length <= len(quote) <= 260:
            errors.append(f"{path.name}: quote length out of range")
        if prose_sentence_count(quote) > 2:
            errors.append(f"{path.name}: quote exceeds two sentences")
        # Curated commentary is Korean declarative prose; counting Korean
        # sentence endings avoids treating initials/titles inside citations as
        # additional sentences.
        sentence_count = len(re.findall(r"다\.", commentary))
        if not 4 <= sentence_count <= 8:
            errors.append(f"{path.name}: commentary must have 4-8 sentences")
        if len(commentary) < max(220, int(len(quote) * 1.25)):
            errors.append(f"{path.name}: commentary too short relative to quote")
        notes.append(data)

    unique_fields = {
        "id": [str(n["id"]) for n in notes],
        "slug": [str(n["slug"]) for n in notes],
        "title": [str(n["title"]) for n in notes],
        "quote": [str(n["quote"]) for n in notes],
        "canonical": [canonical(n) for n in notes],
    }
    for field, values in unique_fields.items():
        normalized = [normalize(value) for value in values]
        duplicates = [value for value, count in Counter(normalized).items() if count > 1]
        if duplicates:
            errors.append(f"duplicate {field}: {len(duplicates)}")

    openings, closings = zip(*(sentence_edges(str(note["commentary"])) for note in notes)) if notes else ((), ())
    if len(set(openings)) != len(openings):
        errors.append("duplicate commentary opening sentence")
    if len(set(closings)) != len(closings):
        errors.append("duplicate commentary closing sentence")

    similarity_specs = (("title", 0.94), ("quote", 0.97), ("commentary", 0.92))
    for field, threshold in similarity_specs:
        candidates = [
            note for note in notes if str(note.get("content_kind", "source_quote")) == "source_quote"
        ]
        duplicate = first_near_duplicate(candidates, field, threshold)
        if duplicate:
            errors.append(f"near-duplicate {field}: {duplicate[0]} / {duplicate[1]}")

    # This is novelist Lee Hu's official archive. Notes about Lee Hu's own
    # works are intentionally exempt from author concentration limits; the
    # original diversity guard remains unchanged for every other author.
    concentration_values = {
        "author": [str(n["source_author"]) for n in notes if str(n["source_author"]) != "이후"],
        "work": [str(n["source_work"]) for n in notes],
        "tag": [str(tag) for n in notes for tag in n["tags"]],
    }
    for label, values, limit in (
        ("author", concentration_values["author"], 0.30),
        ("work", concentration_values["work"], 0.12),
        ("tag", concentration_values["tag"], 0.18),
    ):
        counts = Counter(values)
        denominator = len(values)
        top, count = counts.most_common(1)[0] if counts else ("", 0)
        if denominator and count / denominator > limit:
            errors.append(f"{label} over-concentration: {top} ({count}/{denominator})")

    if errors:
        raise ValueError("literature validation failed:\n- " + "\n- ".join(errors))
    return sort_for_publication(notes)


def base_head(
    title: str,
    description: str,
    canonical_url: str,
    extra: str = "",
    robots: str = "index, follow",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="{esc(robots)}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical_url)}">
<meta property="og:site_name" content="소설가 이후">
<meta property="og:image" content="{ORIGIN}/og-image.jpg">
<meta property="og:image:secure_url" content="{ORIGIN}/og-image.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">
{extra}
<link rel="preconnect" href="https://fonts.googleapis.com/">
<link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Gowun+Batang:wght@400;700&amp;family=Noto+Serif+KR:wght@400;600;700;900&amp;display=swap" rel="stylesheet">
<style>{STYLE}</style>
</head>"""


def nav() -> str:
    return """<nav class="site-nav">
  <a class="nav-logo" href="/">이후</a>
  <ul class="nav-links">
    <li><a href="/">홈</a></li>
    <li><a href="/author/">공식 프로필</a></li>
    <li><a href="/literature/">문학노트</a></li>
    <li><a href="/#board">게시판</a></li>
    <li><a href="/#contact">연락</a></li>
  </ul>
</nav>"""


def card(note: dict[str, object]) -> str:
    return f"""<a class="note-card" href="/literature/{esc(note['slug'])}/">
  <small>{esc(note['source_author'])} · {esc(note['source_work'])}</small>
  <h2>{esc(note['title'])}</h2>
  <blockquote>{esc(note['quote'])}</blockquote>
  <p>{' · '.join(esc(tag) for tag in note['tags'])}</p>
</a>"""


def list_page(notes: list[dict[str, object]], page: int, total_pages: int) -> str:
    start = (page - 1) * PAGE_SIZE
    current = notes[start:start + PAGE_SIZE]
    url = f"{ORIGIN}/literature/" if page == 1 else f"{ORIGIN}/literature/page/{page}/"
    title = "이후의 문학노트" if page == 1 else f"이후의 문학노트 {page}쪽"
    links = []
    for number in range(1, total_pages + 1):
        href = "/literature/" if number == 1 else f"/literature/page/{number}/"
        links.append(
            f'<span class="current" aria-current="page">{number}</span>'
            if number == page else f'<a href="{href}">{number}</a>'
        )
    extra = f"""<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="퍼블릭 도메인 고전 원문과 소설가 이후의 독서 기록">
<meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="퍼블릭 도메인 고전 원문과 소설가 이후의 독서 기록">
<meta name="twitter:image" content="{ORIGIN}/og-image.jpg">
<meta name="twitter:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">
<link rel="alternate" type="application/rss+xml" title="이후의 문학노트 RSS" href="/literature/rss.xml">"""
    robots = "index, follow" if page == 1 else "noindex, follow"
    return f"""{base_head(title + " | 소설가 이후", "퍼블릭 도메인 고전 원문의 한 문장과 소설가 이후의 독서 기록.", url, extra, robots)}
<body>{nav()}
<header class="hero"><div class="wrap">
  <p class="eyebrow">Literature Notes</p>
  <h1>이후의 문학노트</h1>
  <p class="lede">직접 확인한 퍼블릭 도메인 원전의 짧은 인용과, 원문을 인용하지 않은 독창적 감상을 오늘의 삶으로 이어 읽은 소설가 이후의 기록입니다.</p>
{SEARCH_COMPONENT}
</div></header>
<main class="wrap"><section class="grid">{''.join(card(note) for note in current)}</section>
<nav class="pagination" aria-label="문학노트 페이지">{''.join(links)}</nav></main>
<footer class="footer">© 소설가 이후<div class="site-links"><a href="/">홈</a><a href="/#board">게시판</a><a href="/literature/rss.xml">RSS</a></div></footer>
</body></html>
"""


def detail_page(
    note: dict[str, object],
    previous: dict[str, object] | None,
    following: dict[str, object] | None,
    indexable: bool = True,
) -> str:
    url = canonical(note)
    description = re.sub(r"\s+", " ", str(note["commentary"]))[:155]
    search_title = seo_title(note["title"])
    published = str(note["published_at"])
    source_link_label = "작품 정보 확인" if str(note.get("content_kind", "source_quote")) == "original_reflection" else "원문 확인"
    article_ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": note["title"],
        "description": description,
        "url": url,
        "mainEntityOfPage": url,
        "datePublished": published,
        "dateModified": published,
        "author": {
            "@type": "Person",
            "@id": f"{ORIGIN}/#person",
            "name": "이후",
            "alternateName": ["소설가 이후", "李後", "Lee Hu"],
            "url": f"{ORIGIN}/author/",
        },
        "publisher": {
            "@type": "Organization",
            "@id": f"{ORIGIN}/#organization",
            "name": "주식회사 소설가이후",
            "url": f"{ORIGIN}/",
        },
        "image": {
            "@type": "ImageObject",
            "url": f"{ORIGIN}/og-image.jpg",
            "width": 1200,
            "height": 630,
        },
        "keywords": note["tags"],
        "inLanguage": "ko",
        "citation": {
            "@type": "CreativeWork",
            "name": note["source_work"],
            "author": note["source_author"],
            "url": note["source_url"],
        },
    }
    breadcrumb_ld = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "홈", "item": f"{ORIGIN}/"},
            {"@type": "ListItem", "position": 2, "name": "문학노트", "item": f"{ORIGIN}/literature/"},
            {"@type": "ListItem", "position": 3, "name": note["title"], "item": url},
        ],
    }
    json_ld = json.dumps([article_ld, breadcrumb_ld], ensure_ascii=False).replace("</", "<\\/")
    extra = f"""<meta property="og:type" content="article">
<meta property="og:title" content="{esc(search_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="article:published_time" content="{esc(published)}">
<meta property="article:author" content="{esc(note['author'])}">
{''.join(f'<meta property="article:tag" content="{esc(tag)}">' for tag in note['tags'])}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(search_title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{ORIGIN}/og-image.jpg">
<meta name="twitter:image:alt" content="소설가 이후 공식 홈페이지 대표 이미지">
<script type="application/ld+json">{json_ld}</script>"""
    prev_link = (
        f'<a href="/literature/{esc(previous["slug"])}/">← {esc(previous["title"])}</a>'
        if previous else "<span></span>"
    )
    next_link = (
        f'<a class="next" href="/literature/{esc(following["slug"])}/">{esc(following["title"])} →</a>'
        if following else "<span></span>"
    )
    content_kind = str(note.get("content_kind", "source_quote"))
    collection_sections = note.get("collection_sections")
    seo_sections = note.get("seo_sections")
    if content_kind == "collection_reflection" and isinstance(collection_sections, list):
        collection_blocks = []
        for position, work in enumerate(collection_sections, 1):
            collection_blocks.append(f"""
    <section class="collection-work">
      <h2>{position}. {esc(work['title'])}</h2>
      <p class="collection-meta">{esc(work['author'])} · {esc(work['country_genre'])}</p>
      <dl>
        <div><dt>작품의 핵심 주제</dt><dd>{esc(work['core_theme'])}</dd></div>
        <div><dt>주요 내용</dt><dd>{esc(work['summary'])}</dd></div>
        <div><dt>작품에서 표현되는 사랑의 형태</dt><dd>{esc(work['love_form'])}</dd></div>
        <div><dt>문학적으로 생각해볼 점</dt><dd>{esc(work['literary_question'])}</dd></div>
        <div><dt>문학노트 한 줄 감상</dt><dd>{esc(work['one_line'])}</dd></div>
      </dl>
      <p class="source"><a href="{esc(work['source_url'])}" rel="external noopener">작품 정보 확인</a></p>
    </section>""")
        article_body = f"""
    <p class="collection-introduction">{esc(note['collection_introduction'])}</p>
    <p class="collection-deck">{esc(note['quote'])}</p>
    <p class="rights-note"><strong>저작권 안내</strong><br>{esc(note['rights_note'])}</p>
{''.join(collection_blocks)}
    <p class="collection-closing">{esc(note['collection_closing'])}</p>"""
    elif (
        content_kind == "original_reflection"
        and isinstance(seo_sections, dict)
        and SEO_SECTION_KEYS <= set(seo_sections)
    ):
        article_body = f"""
    <section class="commentary"><h2>작품 소개</h2><p>{esc(seo_sections['work_introduction'])}</p></section>
    <p class="reflection-deck">{esc(note['quote'])}</p>
    <p class="source"><a href="{esc(note['source_url'])}" rel="external noopener">작품 정보 확인</a><br>
    {esc(note['translation_note'])} {esc(note['rights_note'])}</p>
    <section class="commentary"><h2>읽기의 초점</h2><p>{esc(note['commentary'])}</p></section>
    <section class="commentary"><h2>왜 지금도 읽히는가</h2><p>{esc(seo_sections['why_read_now'])}</p></section>
    <section class="commentary"><h2>나의 감상</h2><p>{esc(seo_sections['personal_reflection'])}</p></section>
    <section class="commentary"><h2>오늘 우리에게 주는 의미</h2><p>{esc(seo_sections['meaning_today'])}</p></section>"""
    elif isinstance(seo_sections, dict) and SEO_SECTION_KEYS <= set(seo_sections):
        article_body = f"""
    <section class="commentary"><h2>작품 소개</h2><p>{esc(seo_sections['work_introduction'])}</p></section>
    <blockquote>{esc(note['quote'])}</blockquote>
    <p class="source">— {esc(note['source_author'])}, <cite>{esc(note['source_work'])}</cite>, {esc(note['source_location'])}<br>
    <a href="{esc(note['source_url'])}" rel="external noopener">{source_link_label}</a><br>
    {esc(note['translation_note'])} {esc(note['rights_note'])}</p>
    <section class="commentary"><h2>왜 지금도 읽히는가</h2><p>{esc(seo_sections['why_read_now'])}</p></section>
    <section class="commentary"><h2>나의 감상</h2><p>{esc(seo_sections['personal_reflection'])}</p></section>
    <section class="commentary"><h2>오늘 우리에게 주는 의미</h2><p>{esc(seo_sections['meaning_today'])}</p></section>"""
    else:
        article_body = f"""
    <blockquote>{esc(note['quote'])}</blockquote>
    <p class="source">— {esc(note['source_author'])}, <cite>{esc(note['source_work'])}</cite>, {esc(note['source_location'])}<br>
    <a href="{esc(note['source_url'])}" rel="external noopener">{source_link_label}</a><br>
    {esc(note['translation_note'])} {esc(note['rights_note'])}</p>
    <section class="commentary"><h2>이후의 생각</h2><p>{esc(note['commentary'])}</p></section>"""
    robots = "index, follow" if indexable else "noindex, follow"
    return f"""{base_head(search_title, description, url, extra, robots)}
<body>{nav()}
<main class="article">
  <nav class="breadcrumbs" aria-label="이동 경로"><a href="/">홈</a> / <a href="/literature/">문학노트</a> / {esc(note['title'])}</nav>
  <article>
    <header><p class="eyebrow">Literature Note · {esc(note['id'])}</p><h1>{esc(note['title'])}</h1>
    <p class="meta">글 {esc(note['author'])} · <time datetime="{esc(published)}">{datetime.fromisoformat(published).year}년 {datetime.fromisoformat(published).month}월 {datetime.fromisoformat(published).day}일</time></p></header>
{article_body}
    <div class="tags">{''.join(f'<span class="tag">#{esc(tag)}</span>' for tag in note['tags'])}</div>
    <p class="related">글쓴이: <a href="/author/">소설가 이후 공식 프로필</a></p>
    <p class="related">함께 읽기: <a href="{esc(note['related_work']['url'])}" rel="external noopener">{esc(note['related_work']['name'])}</a></p>
    <p class="meta" style="margin-top:28px">{esc(note['closing'])}</p>
  </article>
  <nav class="post-nav" aria-label="이전 및 다음 문학노트">{prev_link}{next_link}</nav>
  <div class="site-links"><a href="/literature/">전체 목록</a><a href="/">홈</a><a href="/#board">게시판</a></div>
</main>
<footer class="footer">© 소설가 이후</footer>
</body></html>
"""


def update_homepage(notes: list[dict[str, object]]) -> None:
    path = ROOT / "index.html"
    source = path.read_text(encoding="utf-8")
    homepage_cards = "".join(card(note) for note in notes[:6])
    board_cards = "".join(
        f'<a href="/literature/{esc(note["slug"])}/"><strong>{esc(note["title"])}</strong>'
        f'<span>{esc(note["source_author"])} · {esc(note["source_work"])}</span></a>'
        for note in notes[:3]
    )
    source = replace_marker(source, "LITERATURE_LATEST_ITEMS", homepage_cards)
    source = replace_marker(source, "BOARD_LITERATURE_ITEMS", board_cards)
    write_text_atomic(path, source)


def replace_marker(source: str, marker: str, replacement: str) -> str:
    block = re.compile(
        rf"<!-- {re.escape(marker)}:START -->.*?<!-- {re.escape(marker)}:END -->",
        re.S,
    )
    rendered = f"<!-- {marker}:START -->\n{replacement}\n<!-- {marker}:END -->"
    if block.search(source):
        return block.sub(lambda _match: rendered, source)
    plain = f"<!-- {marker} -->"
    if plain not in source:
        raise ValueError(f"homepage marker missing: {marker}")
    return source.replace(plain, rendered)


def write_rss(notes: list[dict[str, object]]) -> None:
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    for name, value in (
        ("title", "이후의 문학노트"),
        ("link", f"{ORIGIN}/literature/"),
        ("description", "퍼블릭 도메인 고전 원문과 소설가 이후의 독서 기록"),
        ("language", "ko"),
    ):
        ET.SubElement(channel, name).text = value
    ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
        href=f"{ORIGIN}/literature/rss.xml",
        rel="self",
        type="application/rss+xml",
    )
    for note in notes:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = str(note["title"])
        ET.SubElement(item, "link").text = canonical(note)
        ET.SubElement(item, "guid", isPermaLink="true").text = canonical(note)
        published = datetime.fromisoformat(str(note["published_at"]))
        ET.SubElement(item, "pubDate").text = format_datetime(published)
        ET.SubElement(item, "description").text = str(note["commentary"])
        ET.SubElement(item, "author").text = str(note["source_author"])
        ET.SubElement(item, "source").text = str(note["source_work"])
        for tag in note["tags"]:
            ET.SubElement(item, "category").text = str(tag)
    write_xml_atomic(LITERATURE_DIR / "rss.xml", rss)


def additional_sitemap_urls() -> list[tuple[str, str]]:
    """Return independently published static pages that literature builds must preserve."""
    update_root = ROOT / "seo-updates"
    if not (update_root / "index.html").is_file():
        return []
    updates: list[tuple[str, str]] = []
    for child in sorted(update_root.iterdir(), key=lambda path: path.name):
        match = re.fullmatch(r"(?P<date>\d{4}-\d{2}-\d{2})-[a-z0-9-]+", child.name)
        if not match or not child.is_dir() or not (child / "index.html").is_file():
            continue
        try:
            datetime.fromisoformat(match.group("date"))
        except ValueError:
            continue
        updates.append(
            (f"{ORIGIN}/seo-updates/{child.name}/", match.group("date"))
        )
    index_date = max((date for _, date in updates), default=CORE_PAGE_LASTMOD)
    return [(f"{ORIGIN}/seo-updates/", index_date), *updates]


def write_sitemap(notes: list[dict[str, object]]) -> None:
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}urlset")
    latest_date = max(str(note["published_at"])[:10] for note in notes)
    core_page_date = max(latest_date, CORE_PAGE_LASTMOD)
    urls = [
        (f"{ORIGIN}/", core_page_date),
        (f"{ORIGIN}/author/", core_page_date),
        (f"{ORIGIN}/literature/", latest_date),
    ]
    urls.extend(
        (canonical(note), str(note["published_at"])[:10]) for note in notes
    )
    urls.extend(additional_sitemap_urls())
    for url, last_modified in urls:
        node = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(node, f"{{{namespace}}}loc").text = url
        ET.SubElement(node, f"{{{namespace}}}lastmod").text = last_modified
    write_xml_atomic(ROOT / "sitemap.xml", root)


def generated_html_paths(notes: list[dict[str, object]], total_pages: int) -> list[Path]:
    paths = [LITERATURE_DIR / "index.html"]
    paths.extend(LITERATURE_DIR / "page" / str(page) / "index.html" for page in range(2, total_pages + 1))
    paths.extend(LITERATURE_DIR / str(note["slug"]) / "index.html" for note in notes)
    return paths


def internal_target(href: str) -> Path | None:
    if not href.startswith("/") or href.startswith("//"):
        return None
    path_value = href.split("#", 1)[0].split("?", 1)[0]
    if not path_value:
        return ROOT / "index.html"
    target = ROOT / path_value.lstrip("/")
    if path_value.endswith("/"):
        target /= "index.html"
    return target


def verify_generated(
    all_notes: list[dict[str, object]],
    indexable_notes: list[dict[str, object]],
    total_pages: int,
) -> None:
    errors: list[str] = []
    paths = generated_html_paths(all_notes, total_pages)
    notes_by_slug = {str(note["slug"]): note for note in all_notes}
    indexable_slugs = {str(note["slug"]) for note in indexable_notes}
    if any(not path.is_file() for path in paths):
        errors.append("missing generated HTML")
    href_re = re.compile(r'href="([^"]+)"')
    json_re = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for href in href_re.findall(text):
            target = internal_target(html.unescape(href))
            if target is not None and not target.exists():
                errors.append(f"broken internal link in {path.relative_to(ROOT)}: {href}")
        if path.parent.name in notes_by_slug:
            note = notes_by_slug.get(path.parent.name)
            if note:
                expected_robots = (
                    "index, follow"
                    if str(note["slug"]) in indexable_slugs
                    else "noindex, follow"
                )
                if f'<meta name="robots" content="{expected_robots}">' not in text:
                    errors.append(
                        f"robots policy missing: {path.relative_to(ROOT)}"
                    )
                fields = ["title", "quote", "source_author", "source_work", "source_location", "closing"]
                content_kind = note.get("content_kind", "source_quote")
                collection_sections = note.get("collection_sections")
                seo_sections = note.get("seo_sections")
                if content_kind == "collection_reflection" and isinstance(collection_sections, list):
                    expected_values = [
                        note["title"], note["quote"], note["closing"],
                        note["collection_introduction"], note["collection_closing"],
                        note["rights_note"],
                    ]
                    for work in collection_sections:
                        expected_values.extend(
                            work[field] for field in COLLECTION_WORK_FIELDS[:-1]
                        )
                elif (
                    content_kind == "original_reflection"
                    and isinstance(seo_sections, dict)
                ):
                    expected_values = [
                        note["title"],
                        note["quote"],
                        note["closing"],
                        note["source_url"],
                        note["translation_note"],
                        note["rights_note"],
                    ] + list(seo_sections.values())
                elif isinstance(seo_sections, dict):
                    expected_values = [note[field] for field in fields] + list(seo_sections.values())
                else:
                    expected_values = [note[field] for field in fields + ["commentary"]]
                for value in expected_values:
                    if esc(value) not in text:
                        errors.append(
                            f"escaped note content missing: {path.relative_to(ROOT)}"
                        )
            blocks = json_re.findall(text)
            if len(blocks) != 1:
                errors.append(f"JSON-LD count invalid: {path.relative_to(ROOT)}")
            else:
                try:
                    json.loads(blocks[0].replace("<\\/", "</"))
                except json.JSONDecodeError as exc:
                    errors.append(f"invalid JSON-LD: {path.relative_to(ROOT)}: {exc}")
    sitemap = ET.parse(ROOT / "sitemap.xml")
    sitemap_count = len(sitemap.getroot())
    expected_sitemap = 3 + len(indexable_notes) + len(additional_sitemap_urls())
    if sitemap_count != expected_sitemap:
        errors.append(f"sitemap count {sitemap_count}, expected {expected_sitemap}")
    rss = ET.parse(LITERATURE_DIR / "rss.xml")
    rss_count = len(rss.findall("./channel/item"))
    if rss_count != len(indexable_notes):
        errors.append(f"RSS count {rss_count}, expected {len(indexable_notes)}")
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    block = re.search(
        r"<!-- LITERATURE_LATEST_ITEMS:START -->(.*?)<!-- LITERATURE_LATEST_ITEMS:END -->",
        homepage,
        re.S,
    )
    if not block or block.group(1).count('class="note-card"') != 6:
        errors.append("homepage must contain exactly six generated representative note cards")
    excluded_slugs = {
        str(note["slug"]) for note in all_notes if str(note["slug"]) not in indexable_slugs
    }
    discovery_texts = [homepage, (ROOT / "sitemap.xml").read_text(encoding="utf-8"), (LITERATURE_DIR / "rss.xml").read_text(encoding="utf-8")]
    discovery_texts.append(
        (LITERATURE_DIR / "index.html").read_text(encoding="utf-8")
    )
    discovery_texts.extend(
        (LITERATURE_DIR / "page" / str(page) / "index.html").read_text(encoding="utf-8")
        for page in range(2, total_pages + 1)
    )
    for note in indexable_notes:
        discovery_texts.append(
            (LITERATURE_DIR / str(note["slug"]) / "index.html").read_text(encoding="utf-8")
        )
    discovered_hrefs: set[str] = set()
    for text in discovery_texts:
        discovered_hrefs.update(html.unescape(value) for value in href_re.findall(text))
        discovered_hrefs.update(
            re.findall(r"https://xn--hu5b23z\.com/literature/([a-z0-9-]+)/", text)
        )
    leaked = [
        slug
        for slug in excluded_slugs
        if f"/literature/{slug}/" in discovered_hrefs or slug in discovered_hrefs
    ]
    if leaked:
        errors.append(f"noindex note leaked into discovery surfaces: {leaked[0]}")
    for page in range(2, total_pages + 1):
        page_text = (LITERATURE_DIR / "page" / str(page) / "index.html").read_text(encoding="utf-8")
        if '<meta name="robots" content="noindex, follow">' not in page_text:
            errors.append(f"archive page {page} must be noindex, follow")
    if errors:
        raise ValueError("generated-site verification failed:\n- " + "\n- ".join(errors))


def build(expected_count: int = EXPECTED_COUNT) -> None:
    all_notes = load_and_validate(expected_count)
    policy = load_index_policy(INDEX_POLICY_PATH, all_notes)
    raw_indexable, _ = partition_indexable_notes(all_notes, policy)
    indexable_notes = [dict(note) for note in raw_indexable]
    total_pages = (len(indexable_notes) + PAGE_SIZE - 1) // PAGE_SIZE
    expected_slugs = {str(note["slug"]) for note in all_notes}
    if LITERATURE_DIR.exists():
        for child in LITERATURE_DIR.iterdir():
            if (
                child.is_dir()
                and child.name != "page"
                and child.name not in expected_slugs
                and (child / "index.html").exists()
            ):
                remove_tree_with_retry(child)
        page_root = LITERATURE_DIR / "page"
        if page_root.exists():
            for child in page_root.iterdir():
                if (
                    child.is_dir()
                    and child.name.isdigit()
                    and int(child.name) > total_pages
                ):
                    remove_tree_with_retry(child)
    LITERATURE_DIR.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        LITERATURE_DIR / "index.html",
        list_page(indexable_notes, 1, total_pages),
    )
    for page in range(2, total_pages + 1):
        target = LITERATURE_DIR / "page" / str(page)
        target.mkdir(parents=True, exist_ok=True)
        write_text_atomic(
            target / "index.html",
            list_page(indexable_notes, page, total_pages),
        )
    indexable_positions = {
        str(note["id"]): position for position, note in enumerate(indexable_notes)
    }
    for note in all_notes:
        target = LITERATURE_DIR / str(note["slug"])
        target.mkdir(parents=True, exist_ok=True)
        position = indexable_positions.get(str(note["id"]))
        previous = (
            indexable_notes[position - 1]
            if position is not None and position > 0
            else None
        )
        following = (
            indexable_notes[position + 1]
            if position is not None and position + 1 < len(indexable_notes)
            else None
        )
        write_text_atomic(
            target / "index.html",
            detail_page(note, previous, following, position is not None),
        )
    write_rss(indexable_notes)
    write_sitemap(indexable_notes)
    update_homepage(indexable_notes)
    verify_generated(all_notes, indexable_notes, total_pages)
    print(
        f"built {len(all_notes)} detail pages, {total_pages} list pages, "
        f"{len(indexable_notes)} RSS items, and "
        f"{3 + len(indexable_notes) + len(additional_sitemap_urls())} sitemap URLs; "
        f"noindexed {len(all_notes) - len(indexable_notes)} detail pages"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the static literature site")
    parser.add_argument("--expected-count", type=int, default=EXPECTED_COUNT)
    build(parser.parse_args().expected_count)
