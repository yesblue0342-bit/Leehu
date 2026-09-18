#!/usr/bin/env python3
"""Independently review the fifty Lee Hu literature notes dated 2026-09-18."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import runpy
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "content" / "leehu-works-20260918-50.json"
GENERATOR = ROOT / "scripts" / "append_leehu_works_20260918_50.py"
AUTHOR_FILES = tuple(
    ROOT / "scripts" / f"leehu_notes_20260918_{suffix}.py"
    for suffix in ("a", "b", "c")
)
CONTENT_DIR = ROOT / "content" / "literature"
EXPECTED_BEFORE = 6131
EXPECTED = 50
START_SEQUENCE = 3761
BATCH_DATE = "20260918"
PUBLISHED_AT = "2026-09-18T18:50:00+09:00"
SECTION_KEYS = (
    "work_introduction",
    "why_read_now",
    "personal_reflection",
    "meaning_today",
)
FLOWS = ("question", "contrast", "observation", "thought_experiment", "practice")
EXPECTED_WORKS = {
    "연(戀)": 9,
    "데자뷔": 9,
    "소나기": 8,
    "환상": 8,
    "별이 빛나는 밤에": 8,
    "Fantasy": 8,
}
APPROVED_SOURCES = {
    "연(戀)": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377756",
    "데자뷔": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377772",
    "소나기": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000002957780",
    "환상": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377769",
    "별이 빛나는 밤에": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000005377770",
    "Fantasy": "https://ebook-product.kyobobook.co.kr/dig/epd/ebook/E000009124008",
}
REQUIRED_KEYS = {
    "id",
    "slug",
    "title",
    "quote",
    "source_author",
    "source_work",
    "source_location",
    "source_language",
    "source_url",
    "translation_note",
    "rights_note",
    "commentary",
    "closing",
    "author",
    "tags",
    "related_work",
    "published_at",
    "content_kind",
    "seo_sections",
}
UNIQUE_FIELDS = (
    "id",
    "slug",
    "title",
    "quote",
    "commentary",
    "closing",
    "source_location",
    "translation_note",
    "rights_note",
)
PUBLIC_FIELDS = (
    "title",
    "quote",
    "commentary",
    "closing",
    "source_location",
    "translation_note",
    "rights_note",
)
FORBIDDEN = (
    "AI",
    "인공지능",
    "자동 생성",
    "자동화",
    "에이전트",
    "GitHub",
    "SEO",
    "검색 최적화",
    "검수 도구",
    "원문 확인 필요",
    "blockquote",
)
UNSUPPORTED_PATTERNS = (
    re.compile(r"주인공(?:은|이|에게|의)"),
    re.compile(r"등장인물(?:은|이|의)"),
    re.compile(r"(?:작가|저자)(?:는|가|의)?\s*.{0,12}(?:의도|말하려|전하려)"),
    re.compile(r"(?:결말|마지막 장면|마지막 대목)(?:에서|은|이|의)"),
    re.compile(r"(?:줄거리|사건 전개|서사의 결말)(?:는|가|를|에서)"),
)
KNOWN_BAD = (
    "권리이",
    "자유을",
    "과정를",
    "소나기을",
    "환상와",
    "환상를",
    "데자뷔을",
    "밤에를",
    "메모은",
    "윤리을",
    "거리이라는",
    "소유을",
    "적기이라는",
    "묻기이라는",
    "확인하기이라는",
)
INCOMPLETE_ENDING = re.compile(r"(?:기|하기|것|수|때문|대해|통해|위해)[”’']?\s*[.!?]$")
TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
AUTOBIOGRAPHICAL_PAST = re.compile(
    r"(?:나는|나\s+역시|나도|내가|내게도|내\s+경우(?:에는|엔)?)\s*.{0,100}?"
    r"(?:적(?:이|도)\s+있(?:었)?다|곤\s+했다|편이었다|해\s+보았다|겪었다|보냈다|살았다)"
    r"(?!면|고\s*(?:가정|상상|치자|보자))"
)


def canonical_json(value: object) -> str:
    """Return a stable JSON representation used for deep equality checks."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def title_key(value: object) -> str:
    """Normalize titles only; other intended fields retain their authored text."""
    return re.sub(r"[\W_]+", "", str(value).casefold())


def prose_sentences(text: object, *, minimum: int = 25) -> list[str]:
    """Extract exact, sufficiently substantive sentences from public prose."""
    return [
        re.sub(r"\s+", " ", part).strip().casefold()
        for part in re.split(r"(?<=[.!?。])\s+", str(text).strip())
        if len(re.sub(r"\s+", " ", part).strip()) >= minimum
    ]


def normalize_skeleton(
    sentence: str,
    known_lenses: Iterable[str] = (),
) -> str:
    """Remove approved variables to expose repeated sentence templates."""
    value = sentence.casefold()
    value = re.sub(r"(?:《[^》]+》|『[^』]+』)", "<work>", value)
    for work in sorted(APPROVED_SOURCES, key=len, reverse=True):
        value = value.replace(work.casefold(), "<work>")
    for lens in sorted({str(item).casefold() for item in known_lenses if str(item)}, key=len, reverse=True):
        value = value.replace(lens, "<lens>")
    value = re.sub(r"\b\d+(?:[.,]\d+)?\b", "<number>", value)
    value = re.sub(r"[‘’“”\"']([^‘’“”\"']{1,40})[‘’“”\"']", "<variable>", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def meaningless_padding_reason(text: object) -> str | None:
    """Reject repeated filler that reaches a length threshold without substance."""
    raw = re.sub(r"\s+", " ", str(text)).strip()
    tokens = TOKEN_RE.findall(raw.casefold())
    if not raw:
        return "empty"
    if re.fullmatch(r"(.{1,24})(?:\s*\1){4,}", raw):
        return "repeated fragment"
    if len(tokens) >= 20:
        most_common = Counter(tokens).most_common(1)[0][1]
        if most_common / len(tokens) >= 0.35:
            return "repeated token"
        trigrams = Counter(tuple(tokens[index:index + 3]) for index in range(len(tokens) - 2))
        if trigrams and trigrams.most_common(1)[0][1] >= 4:
            return "repeated phrase"
    meaningful = {token for token in tokens if len(token) >= 2}
    if len(raw) >= 180 and len(meaningful) < 10:
        return "low lexical variety"
    return None


def _is_negated_claim(text: str, match: re.Match[str]) -> bool:
    """Recognize nearby boundary language that explicitly refuses a factual claim."""
    window = text[max(0, match.start() - 20):min(len(text), match.end() + 45)]
    return bool(
        re.search(
            r"(?:말|추정|추론|가정|암시|설명|단정|확인)(?:하|되|할|한|하지)?.{0,12}"
            r"(?:않|아니|없|금지|배제)",
            window,
        )
        or re.search(r"(?:않|아니|없).{0,12}(?:말|추정|추론|가정|암시|설명|단정|확인)", window)
    )


def autobiographical_claims(text: object) -> list[str]:
    """Return concrete first-person past-experience claims, excluding hypotheticals."""
    return [
        sentence
        for sentence in prose_sentences(text, minimum=1)
        if AUTOBIOGRAPHICAL_PAST.search(sentence)
    ]


def text_rule_errors(note: Mapping[str, object]) -> list[str]:
    """Return content, rights, grammar, and unsupported-claim errors for one note."""
    note_id = str(note.get("id", "<unknown>"))
    values = [str(note.get(field, "")) for field in PUBLIC_FIELDS]
    sections = note.get("seo_sections")
    if isinstance(sections, Mapping):
        values.extend(str(sections.get(key, "")) for key in SECTION_KEYS)
    public = " ".join(values)
    errors: list[str] = []
    folded = public.casefold()
    for term in FORBIDDEN:
        if term.casefold() in folded:
            errors.append(f"forbidden term {term}: {note_id}")
    for term in KNOWN_BAD:
        if term in public:
            errors.append(f"known bad Korean {term}: {note_id}")
    for pattern in UNSUPPORTED_PATTERNS:
        matches = list(pattern.finditer(public))
        if any(not _is_negated_claim(public, match) for match in matches):
            errors.append(f"unsupported claim {pattern.pattern}: {note_id}")
    if autobiographical_claims(public):
        errors.append(f"unsupported autobiographical claim: {note_id}")
    if "직접 인용 없음" not in str(note.get("rights_note", "")):
        errors.append(f"rights note missing direct-quote boundary: {note_id}")
    for sentence in prose_sentences(public, minimum=1):
        if INCOMPLETE_ENDING.search(sentence):
            errors.append(f"incomplete sentence ending: {note_id}")
            break
    for field in ("quote", "commentary"):
        reason = meaningless_padding_reason(note.get(field, ""))
        if reason:
            errors.append(f"meaningless padding in {field} ({reason}): {note_id}")
    if isinstance(sections, Mapping):
        for key in SECTION_KEYS:
            reason = meaningless_padding_reason(sections.get(key, ""))
            if reason:
                errors.append(f"meaningless padding in {key} ({reason}): {note_id}")
    return errors


def duplicate_values(notes: Sequence[Mapping[str, object]], field: str) -> list[str]:
    """Find duplicates, applying punctuation normalization to titles only."""
    values = [title_key(note.get(field, "")) if field == "title" else str(note.get(field, "")) for note in notes]
    return [value for value, count in Counter(values).items() if count > 1]


def concentration_report(notes: Sequence[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    """Calculate the site's author-exempt work and tag concentration gates."""
    tag_values: list[str] = []
    for note in notes:
        tags = note.get("tags")
        if isinstance(tags, (list, tuple)):
            tag_values.extend(tag for tag in tags if isinstance(tag, str))
    groups: tuple[tuple[str, list[str], float], ...] = (
        (
            "author",
            [str(note.get("source_author", "")) for note in notes if str(note.get("source_author", "")) != "이후"],
            0.30,
        ),
        ("work", [str(note.get("source_work", "")) for note in notes], 0.12),
        ("tag", tag_values, 0.18),
    )
    result: dict[str, dict[str, object]] = {}
    for label, values, limit in groups:
        counts = Counter(values)
        top, count = counts.most_common(1)[0] if counts else ("", 0)
        total = len(values)
        result[label] = {
            "top": top,
            "count": count,
            "total": total,
            "ratio": count / total if total else 0.0,
            "limit": limit,
            "ok": not total or count / total <= limit,
        }
    return result


def expected_site_metrics(additional_sitemap_pages: int) -> dict[str, int]:
    """Return post-append counts without reading or mutating generated output."""
    return {
        "sources": 6181,
        "indexable": 5682,
        "noindex": 499,
        "list_pages": 228,
        "sitemap_urls": 5682 + 5 + additional_sitemap_pages,
    }


def validate_batch(
    notes: object,
    authored: object,
    *,
    existing_notes: Sequence[Mapping[str, object]] = (),
    generated_notes: object | None = None,
    source_notes: object | None = None,
    additional_sitemap_pages: int = 0,
) -> dict[str, object]:
    """Validate supplied data without filesystem access, suitable for unit tests."""
    errors: list[str] = []
    batch = notes if isinstance(notes, list) else []
    entries = authored if isinstance(authored, list) else []
    if not isinstance(notes, list) or len(batch) != EXPECTED:
        errors.append(f"manifest count must be {EXPECTED}")
    if not isinstance(authored, list) or len(entries) != EXPECTED:
        errors.append(f"authored entry count must be {EXPECTED}")

    generator_match = generated_notes is not None and canonical_json(generated_notes) == canonical_json(batch)
    if generated_notes is not None and not generator_match:
        errors.append("generator output differs from manifest")
    source_match = None if source_notes is None else canonical_json(source_notes) == canonical_json(batch)
    if source_match is False:
        errors.append("applied source files differ from manifest")

    positions = [entry.get("position") for entry in entries if isinstance(entry, Mapping)]
    if positions != list(range(1, EXPECTED + 1)):
        errors.append("entry positions must be 1..50")
    flows = [str(entry.get("flow", "")) for entry in entries if isinstance(entry, Mapping)]
    if flows != [FLOWS[index % len(FLOWS)] for index in range(EXPECTED)]:
        errors.append("entry flows must cycle through the five approved flows ten times")
    if any(flows[index] == flows[index + 1] == flows[index + 2] for index in range(max(0, len(flows) - 2))):
        errors.append("the same flow appears three consecutive times")
    lenses = {str(entry.get("lens", "")) for entry in entries if isinstance(entry, Mapping)}
    if len(lenses) < 20:
        errors.append("entries must use at least 20 lenses")

    works = Counter(str(note.get("source_work", "")) for note in batch if isinstance(note, Mapping))
    if works != Counter(EXPECTED_WORKS):
        errors.append(f"invalid work distribution: {dict(works)}")

    for index, note in enumerate(batch, 1):
        if not isinstance(note, Mapping):
            errors.append(f"item {index} must be an object")
            continue
        if set(note) != REQUIRED_KEYS:
            errors.append(f"item {index} schema keys differ: {sorted(set(note) ^ REQUIRED_KEYS)}")
        expected_id = f"{BATCH_DATE}_leehu_literature_{START_SEQUENCE + index - 1:04d}"
        if note.get("id") != expected_id:
            errors.append(f"unexpected id at {index}: {note.get('id')}")
        if not SLUG_RE.fullmatch(str(note.get("slug", ""))):
            errors.append(f"invalid slug: {note.get('id', index)}")
        if note.get("published_at") != PUBLISHED_AT:
            errors.append(f"wrong published_at: {note.get('id', index)}")
        if note.get("source_author") != "이후" or note.get("author") != "소설가 이후":
            errors.append(f"wrong author: {note.get('id', index)}")
        if note.get("source_language") != "ko" or note.get("content_kind") != "original_reflection":
            errors.append(f"wrong language/content kind: {note.get('id', index)}")
        work = str(note.get("source_work", ""))
        source_url = APPROVED_SOURCES.get(work)
        if note.get("source_url") != source_url:
            errors.append(f"unapproved source edition: {note.get('id', index)}")
        if note.get("related_work") != {"name": work, "url": source_url}:
            errors.append(f"related_work differs from approved edition: {note.get('id', index)}")
        tags = note.get("tags")
        if not isinstance(tags, list) or len(tags) != 4 or tags[:2] != ["소설가 이후", work]:
            errors.append(f"invalid tags: {note.get('id', index)}")
        sections = note.get("seo_sections")
        if not isinstance(sections, Mapping) or tuple(sections) != SECTION_KEYS:
            errors.append(f"invalid section keys/order: {note.get('id', index)}")
        else:
            short_sections = [
                f"{key}={len(sections[key]) if isinstance(sections[key], str) else 0}"
                for key in SECTION_KEYS
                if not isinstance(sections[key], str) or len(sections[key]) < 180
            ]
            if short_sections:
                errors.append(
                    f"short semantic section ({', '.join(short_sections)}): "
                    f"{note.get('id', index)}"
                )
        quote = str(note.get("quote", ""))
        commentary = str(note.get("commentary", ""))
        if not 50 <= len(quote) <= 260:
            errors.append(f"quote length out of range: {note.get('id', index)}")
        if len(prose_sentences(quote, minimum=1)) > 2:
            errors.append(f"quote exceeds two sentences: {note.get('id', index)}")
        if len(commentary) < max(300, int(len(quote) * 1.25)):
            errors.append(f"commentary too short: {note.get('id', index)}")
        if not 4 <= len(re.findall(r"다\.", commentary)) <= 8:
            errors.append(f"commentary must have 4-8 declarative sentences: {note.get('id', index)}")
        errors.extend(text_rule_errors(note))

    for field in UNIQUE_FIELDS:
        duplicates = duplicate_values([note for note in batch if isinstance(note, Mapping)], field)
        if duplicates:
            errors.append(f"duplicate {field}: {len(duplicates)}")
        previous = {
            title_key(note.get(field, "")) if field == "title" else str(note.get(field, ""))
            for note in existing_notes
        }
        incoming = {
            title_key(note.get(field, "")) if field == "title" else str(note.get(field, ""))
            for note in batch
            if isinstance(note, Mapping)
        }
        if previous.intersection(incoming):
            errors.append(f"existing corpus collision in {field}")
    canonicals = [f"https://xn--hu5b23z.com/literature/{note.get('slug', '')}/" for note in batch if isinstance(note, Mapping)]
    if len(canonicals) != len(set(canonicals)):
        errors.append("duplicate canonical")
    for key in SECTION_KEYS:
        section_values = [
            str(note.get("seo_sections", {}).get(key, ""))
            for note in batch
            if isinstance(note, Mapping) and isinstance(note.get("seo_sections"), Mapping)
        ]
        if len(section_values) != len(set(section_values)):
            errors.append(f"duplicate section {key}")

    body_sentences: list[str] = []
    for note in batch:
        if not isinstance(note, Mapping):
            continue
        text = " ".join(str(note.get(field, "")) for field in ("quote", "commentary", "closing"))
        sections = note.get("seo_sections")
        if isinstance(sections, Mapping):
            text += " " + " ".join(str(sections.get(key, "")) for key in SECTION_KEYS)
        body_sentences.extend(prose_sentences(text))
    exact_duplicates = [value for value, count in Counter(body_sentences).items() if count > 1]
    skeletons = [normalize_skeleton(sentence, lenses) for sentence in body_sentences]
    skeleton_duplicates = [value for value, count in Counter(skeletons).items() if count > 1]
    if exact_duplicates:
        errors.append(f"duplicate exact sentence: {exact_duplicates[0]}")
    if skeleton_duplicates:
        errors.append(f"duplicate normalized skeleton: {skeleton_duplicates[0]}")

    concentration = concentration_report([*existing_notes, *[n for n in batch if isinstance(n, Mapping)]])
    for label, result in concentration.items():
        if not result["ok"]:
            errors.append(
                f"{label} over-concentration: {result['top']} "
                f"({result['count']}/{result['total']})"
            )

    return {
        "ok": not errors,
        "count": len(batch),
        "works": dict(works),
        "generator_match": generator_match,
        "source_match": source_match,
        "exact_sentence_duplicates": len(exact_duplicates),
        "normalized_skeleton_duplicates": len(skeleton_duplicates),
        "errors": errors,
        "concentration": concentration,
        "expected_site_metrics": expected_site_metrics(additional_sitemap_pages),
    }


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_existing() -> list[dict[str, object]]:
    notes: list[dict[str, object]] = []
    for number in range(1, EXPECTED_BEFORE + 1):
        value = _load_json(CONTENT_DIR / f"{number:03d}.json")
        if not isinstance(value, dict):
            raise ValueError(f"existing source {number:03d}.json must contain an object")
        notes.append(value)
    return notes


def _load_applied_sources() -> list[object] | None:
    paths = [CONTENT_DIR / f"{number:03d}.json" for number in range(6132, 6182)]
    present = [path.is_file() for path in paths]
    if not any(present):
        return None
    if not all(present):
        raise ValueError("2026-09-18 source batch is only partially applied")
    return [_load_json(path) for path in paths]


def _additional_sitemap_pages() -> int:
    update_root = ROOT / "seo-updates"
    if not (update_root / "index.html").is_file():
        return 0
    updates = sum(
        1
        for child in update_root.iterdir()
        if child.is_dir()
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9-]+", child.name)
        and (child / "index.html").is_file()
    )
    return 1 + updates


def review(path: Path) -> dict[str, object]:
    """Load generator, manifest and the fixed pre-batch corpus, then review once."""
    module = runpy.run_path(str(GENERATOR), run_name="leehu_works_20260918_review")
    generated = module["generate"]()
    authored = module["entries"]()
    notes = _load_json(path)
    result = validate_batch(
        notes,
        authored,
        existing_notes=_load_existing(),
        generated_notes=generated,
        source_notes=_load_applied_sources(),
        additional_sitemap_pages=_additional_sitemap_pages(),
    )
    result["manifest_sha256"] = _sha256_bytes(canonical_json(notes).encode("utf-8"))
    artifacts = (GENERATOR, *AUTHOR_FILES, Path(__file__).resolve())
    result["input_sha256"] = {
        str(artifact.relative_to(ROOT)).replace("\\", "/"): _file_sha256(artifact)
        for artifact in artifacts
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        result = review(args.manifest)
    except (ImportError, KeyError, OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "ok": False,
            "count": 0,
            "works": {},
            "generator_match": False,
            "exact_sentence_duplicates": 0,
            "normalized_skeleton_duplicates": 0,
            "errors": [str(exc)],
            "concentration": {},
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
