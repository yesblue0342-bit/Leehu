#!/usr/bin/env python3
"""Independently review the 1,000 Lee Hu literature notes dated 2026-09-23."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import re
import runpy
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

try:
    from .review_leehu_works_20260918_50 import (
        APPROVED_SOURCES,
        FLOWS,
        PUBLIC_FIELDS,
        REQUIRED_KEYS,
        SECTION_KEYS,
        UNIQUE_FIELDS,
        canonical_json,
        concentration_report,
        duplicate_values,
        normalize_skeleton,
        prose_sentences,
        text_rule_errors as legacy_text_rule_errors,
        title_key,
    )
except ImportError:
    from review_leehu_works_20260918_50 import (
        APPROVED_SOURCES,
        FLOWS,
        PUBLIC_FIELDS,
        REQUIRED_KEYS,
        SECTION_KEYS,
        UNIQUE_FIELDS,
        canonical_json,
        concentration_report,
        duplicate_values,
        normalize_skeleton,
        prose_sentences,
        text_rule_errors as legacy_text_rule_errors,
        title_key,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "content" / "leehu-works-20260923-1000.json"
GENERATOR = ROOT / "scripts" / "append_leehu_works_20260923_1000.py"
AUTHOR_FILES = tuple(
    ROOT / "scripts" / f"leehu_notes_20260923_{suffix}.py"
    for suffix in ("a", "b", "c", "d", "e")
)
CONTENT_DIR = ROOT / "content" / "literature"
OPTIONAL_KEYS = {"work_anchor"}
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
MAX_EXAMPLES_PER_RULE = 3
MAX_DIAGNOSTICS = 80
LOCAL_KNOWN_BAD = (
    "주의과",
    "경계과",
    "절제을",
    "경계이",
    "읽기은",
    "읽기으로",
    "태도은",
    "데자뷔》은",
    "Fantasy》은",
    "Fantasy》이라는",
    "대비은",
    "대비을",
)
EDITORIAL_SCAFFOLDS = (
    "핵심 명제에서는",
    "논증의 ",
    "작품 소개에서는",
    "현재성은",
    "가정적 성찰은",
    "사회적 의미는",
    *(f"{flow} 흐름" for flow in FLOWS),
)


@dataclass(frozen=True)
class BatchSpec:
    """Fixed publication boundaries, injectable for focused unit tests."""

    expected_before: int = 6191
    expected: int = 1000
    start_sequence: int = 3821
    batch_date: str = "20260923"
    expected_works: tuple[tuple[str, int], ...] = (
        ("연(戀)", 150),
        ("데자뷔", 130),
        ("소나기", 130),
        ("환상", 130),
        ("별이 빛나는 밤에", 130),
        ("Fantasy", 330),
    )


DEFAULT_SPEC = BatchSpec()
EXPECTED_BEFORE = DEFAULT_SPEC.expected_before
EXPECTED = DEFAULT_SPEC.expected
START_SEQUENCE = DEFAULT_SPEC.start_sequence
BATCH_DATE = DEFAULT_SPEC.batch_date
EXPECTED_WORKS = dict(DEFAULT_SPEC.expected_works)


def expected_work_sequence(spec: BatchSpec = DEFAULT_SPEC) -> tuple[str, ...]:
    """Return the reviewed weighted cycle when every allocation is ten-divisible."""
    allocations = dict(spec.expected_works)
    if any(count % 10 for count in allocations.values()):
        return ()
    return tuple(
        work
        for turn in range(max(allocations.values()) // 10)
        for work, count in spec.expected_works
        if turn < count // 10
    )


def text_rule_errors(note: Mapping[str, object]) -> list[str]:
    """Apply the established prose rules plus evidenced batch-specific grammar checks."""
    errors = legacy_text_rule_errors(note)
    public = _note_text(note)
    note_id = str(note.get("id", "<unknown>"))
    for term in LOCAL_KNOWN_BAD:
        if term in public:
            errors.append(f"known bad Korean {term}: {note_id}")
    for term in EDITORIAL_SCAFFOLDS:
        if term in public:
            errors.append(f"editorial scaffold {term.strip()}: {note_id}")
    return errors


def _rule_key(error: str) -> str:
    """Group diagnostics without retaining authored prose in the grouping key."""
    if error.startswith("unsupported claim "):
        return "unsupported claim"
    return error.split(":", 1)[0]


def _bounded_diagnostics(errors: Sequence[str]) -> tuple[list[str], dict[str, int]]:
    """Return representative failures while keeping CLI JSON safely bounded."""
    counts = Counter(_rule_key(error) for error in errors)
    examples: Counter[str] = Counter()
    bounded: list[str] = []
    for error in errors:
        key = _rule_key(error)
        if examples[key] >= MAX_EXAMPLES_PER_RULE or len(bounded) >= MAX_DIAGNOSTICS:
            continue
        examples[key] += 1
        bounded.append(error)
    suppressed = len(errors) - len(bounded)
    if suppressed:
        bounded.append(f"additional diagnostics suppressed: {suppressed}")
    return bounded, dict(counts)


def _note_text(note: Mapping[str, object]) -> str:
    """Collect public prose fields used by exact and skeleton duplicate gates."""
    values = [str(note.get(field, "")) for field in PUBLIC_FIELDS]
    sections = note.get("seo_sections")
    if isinstance(sections, Mapping):
        values.extend(str(sections.get(key, "")) for key in SECTION_KEYS)
    return " ".join(values)


def _note_sentences(note: Mapping[str, object]) -> list[str]:
    """Extract sentences per prose field so field boundaries cannot hide reuse."""
    values = [str(note.get(field, "")) for field in ("quote", "commentary", "closing")]
    sections = note.get("seo_sections")
    if isinstance(sections, Mapping):
        values.extend(str(sections.get(key, "")) for key in SECTION_KEYS)
    return [sentence for value in values for sentence in prose_sentences(value)]


def _sentence_collision_errors(
    incoming: Sequence[Mapping[str, object]],
    existing: Sequence[Mapping[str, object]],
    lenses: Iterable[str],
) -> tuple[list[str], int, int]:
    """Find sentence collisions involving new notes, ignoring old-to-old duplicates."""
    lens_values = sorted(
        {str(lens).strip() for lens in lenses if str(lens).strip()},
        key=len,
        reverse=True,
    )
    lens_pattern = re.compile(
        "|".join(re.escape(lens) for lens in lens_values), re.IGNORECASE
    ) if lens_values else None

    def skeleton(sentence: str) -> str:
        without_lenses = lens_pattern.sub("<lens>", sentence) if lens_pattern else sentence
        return normalize_skeleton(without_lenses)

    exact_seen: dict[str, str] = {}
    skeleton_seen: dict[str, str] = {}
    for note in existing:
        note_id = str(note.get("id") or note.get("position") or "existing")
        for sentence in _note_sentences(note):
            exact_seen.setdefault(sentence, note_id)
            skeleton_seen.setdefault(skeleton(sentence), note_id)

    errors: list[str] = []
    exact_pairs: set[tuple[str, str]] = set()
    skeleton_pairs: set[tuple[str, str]] = set()
    for note in incoming:
        note_id = str(note.get("id") or note.get("position") or "<unknown>")
        for sentence in _note_sentences(note):
            prior = exact_seen.get(sentence)
            if prior is not None:
                pair = (prior, note_id)
                if pair not in exact_pairs:
                    exact_pairs.add(pair)
                    errors.append(f"duplicate exact sentence: {prior} / {note_id}")
            exact_seen.setdefault(sentence, note_id)

            normalized = skeleton(sentence)
            prior = skeleton_seen.get(normalized)
            if prior is not None:
                pair = (prior, note_id)
                if pair not in skeleton_pairs:
                    skeleton_pairs.add(pair)
                    errors.append(f"duplicate normalized skeleton: {prior} / {note_id}")
            skeleton_seen.setdefault(normalized, note_id)
    return errors, len(exact_pairs), len(skeleton_pairs)


def _valid_publication_date(value: object, batch_date: str) -> bool:
    try:
        published = datetime.fromisoformat(str(value))
    except ValueError:
        return False
    return published.strftime("%Y%m%d") == batch_date and published.tzinfo is not None


def author_module_errors(
    modules: Sequence[object], spec: BatchSpec = DEFAULT_SPEC
) -> list[str]:
    """Verify five author modules own equal, contiguous position ranges."""
    errors: list[str] = []
    if len(modules) != 5:
        return [f"author module count must be 5: found {len(modules)}"]
    if spec.expected % len(modules):
        return ["expected batch size must divide evenly across author modules"]
    module_size = spec.expected // len(modules)
    for module_index, value in enumerate(modules):
        entries = value if isinstance(value, list) else []
        if not isinstance(value, list) or len(entries) != module_size:
            errors.append(
                f"author module {module_index + 1} count must be {module_size}: "
                f"found {len(entries)}"
            )
            continue
        first = module_index * module_size + 1
        positions = [entry.get("position") for entry in entries if isinstance(entry, Mapping)]
        if positions != list(range(first, first + module_size)):
            errors.append(
                f"author module {module_index + 1} positions must be "
                f"{first}..{first + module_size - 1}"
            )
    return errors


def validate_batch(
    notes: object,
    authored: object,
    *,
    existing_notes: Sequence[Mapping[str, object]] = (),
    generated_notes: object | None = None,
    source_notes: object | None = None,
    authored_modules: Sequence[object] | None = None,
    spec: BatchSpec = DEFAULT_SPEC,
) -> dict[str, object]:
    """Validate supplied data without filesystem access."""
    errors: list[str] = []
    batch = notes if isinstance(notes, list) else []
    entries = authored if isinstance(authored, list) else []
    incoming = [note for note in batch if isinstance(note, Mapping)]

    if not isinstance(notes, list) or len(batch) != spec.expected:
        errors.append(f"manifest count must be {spec.expected}: found {len(batch)}")
    if not isinstance(authored, list) or len(entries) != spec.expected:
        errors.append(f"authored entry count must be {spec.expected}: found {len(entries)}")
    if authored_modules is not None:
        errors.extend(author_module_errors(authored_modules, spec))

    generator_match = generated_notes is not None and canonical_json(generated_notes) == canonical_json(batch)
    if generated_notes is not None and not generator_match:
        errors.append("generator output differs from manifest")
    source_match = None if source_notes is None else canonical_json(source_notes) == canonical_json(batch)
    if source_match is False:
        errors.append("applied source files differ from manifest")

    positions = [entry.get("position") for entry in entries if isinstance(entry, Mapping)]
    if positions != list(range(1, spec.expected + 1)):
        errors.append(f"entry positions must be 1..{spec.expected}")
    flows = [str(entry.get("flow", "")) for entry in entries if isinstance(entry, Mapping)]
    unknown_flows = sorted(set(flows) - set(FLOWS))
    if unknown_flows:
        errors.append(f"unapproved flows: {unknown_flows}")
    if set(flows) != set(FLOWS):
        errors.append("entries must use all five approved flows")
    if any(flows[index] == flows[index + 1] == flows[index + 2] for index in range(max(0, len(flows) - 2))):
        errors.append("the same flow appears three consecutive times")
    lenses = {str(entry.get("lens", "")).strip() for entry in entries if isinstance(entry, Mapping)}
    lenses.discard("")
    if len(lenses) < 20:
        errors.append("entries must use at least 20 lenses")
    work_cycle = expected_work_sequence(spec)
    if work_cycle and spec.expected % len(work_cycle) == 0:
        authored_works = [
            str(entry.get("work", "")) for entry in entries if isinstance(entry, Mapping)
        ]
        if authored_works != list(work_cycle) * (spec.expected // len(work_cycle)):
            errors.append("authored work order differs from the reviewed weighted cycle")

    works = Counter(str(note.get("source_work", "")) for note in incoming)
    if works != Counter(dict(spec.expected_works)):
        errors.append(f"invalid work distribution: {dict(works)}")

    required = set(REQUIRED_KEYS)
    allowed = required | OPTIONAL_KEYS
    for index, note in enumerate(batch, 1):
        if not isinstance(note, Mapping):
            errors.append(f"item {index} must be an object")
            continue
        missing = sorted(required - set(note))
        unexpected = sorted(set(note) - allowed)
        if missing or unexpected:
            errors.append(f"item {index} schema keys differ: missing={missing}, unexpected={unexpected}")
        expected_id = f"{spec.batch_date}_leehu_literature_{spec.start_sequence + index - 1:04d}"
        if note.get("id") != expected_id:
            errors.append(f"unexpected id at {index}: {note.get('id')}")
        if not SLUG_RE.fullmatch(str(note.get("slug", ""))):
            errors.append(f"invalid slug: {note.get('id', index)}")
        if not _valid_publication_date(note.get("published_at"), spec.batch_date):
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
        expected_anchor = {
            "연(戀)": "yeon",
            "데자뷔": "deja-vu",
            "소나기": "sonagi",
            "환상": "illusion",
            "별이 빛나는 밤에": "starry-night",
            "Fantasy": "fantasy",
        }.get(work)
        if "work_anchor" in note and note.get("work_anchor") != expected_anchor:
            errors.append(f"work_anchor differs from official work: {note.get('id', index)}")
        tags = note.get("tags")
        if not isinstance(tags, list) or len(tags) != 4 or tags[:2] != ["소설가 이후", work]:
            errors.append(f"invalid tags: {note.get('id', index)}")
        sections = note.get("seo_sections")
        if not isinstance(sections, Mapping) or tuple(sections) != SECTION_KEYS:
            errors.append(f"invalid section keys/order: {note.get('id', index)}")
        else:
            short = [
                f"{key}={len(sections[key]) if isinstance(sections[key], str) else 0}"
                for key in SECTION_KEYS
                if not isinstance(sections[key], str) or len(sections[key].strip()) < 180
            ]
            if short:
                errors.append(f"short semantic section ({', '.join(short)}): {note.get('id', index)}")
        quote = str(note.get("quote", ""))
        commentary = str(note.get("commentary", ""))
        if not 50 <= len(quote.strip()) <= 260:
            errors.append(f"quote length out of range: {note.get('id', index)}")
        if len(prose_sentences(quote, minimum=1)) > 2:
            errors.append(f"quote exceeds two sentences: {note.get('id', index)}")
        if len(commentary.strip()) < max(300, int(len(quote.strip()) * 1.25)):
            errors.append(f"commentary too short: {note.get('id', index)}")
        if not 4 <= len(re.findall(r"다\.", commentary)) <= 8:
            errors.append(f"commentary must have 4-8 declarative sentences: {note.get('id', index)}")
        errors.extend(text_rule_errors(note))

    for field in UNIQUE_FIELDS:
        duplicates = duplicate_values(incoming, field)
        if duplicates:
            errors.append(f"duplicate {field}: {len(duplicates)}")
        previous = {
            title_key(note.get(field, "")) if field == "title" else str(note.get(field, ""))
            for note in existing_notes
        }
        current = {
            title_key(note.get(field, "")) if field == "title" else str(note.get(field, ""))
            for note in incoming
        }
        if previous.intersection(current):
            errors.append(f"existing corpus collision in {field}")

    canonicals = [f"https://xn--hu5b23z.com/literature/{note.get('slug', '')}/" for note in incoming]
    if len(canonicals) != len(set(canonicals)):
        errors.append("duplicate canonical")
    for key in SECTION_KEYS:
        values = [
            str(note.get("seo_sections", {}).get(key, ""))
            for note in incoming
            if isinstance(note.get("seo_sections"), Mapping)
        ]
        if len(values) != len(set(values)):
            errors.append(f"duplicate section {key}")

    sentence_errors, exact_count, skeleton_count = _sentence_collision_errors(
        incoming, existing_notes, lenses
    )
    errors.extend(sentence_errors)

    concentration = concentration_report([*existing_notes, *incoming])
    for label, result in concentration.items():
        if not result["ok"]:
            errors.append(
                f"{label} over-concentration: {result['top']} "
                f"({result['count']}/{result['total']})"
            )

    bounded, diagnostic_counts = _bounded_diagnostics(errors)
    return {
        "ok": not errors,
        "count": len(batch),
        "works": dict(works),
        "generator_match": generator_match,
        "source_match": source_match,
        "exact_sentence_duplicates": exact_count,
        "normalized_skeleton_duplicates": skeleton_count,
        "error_count": len(errors),
        "errors": bounded,
        "diagnostic_counts": diagnostic_counts,
        "concentration": concentration,
    }


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_existing(spec: BatchSpec = DEFAULT_SPEC) -> list[dict[str, object]]:
    notes: list[dict[str, object]] = []
    for number in range(1, spec.expected_before + 1):
        value = _load_json(CONTENT_DIR / f"{number:03d}.json")
        if not isinstance(value, dict):
            raise ValueError(f"existing source {number:03d}.json must contain an object")
        notes.append(value)
    return notes


def _load_applied_sources(spec: BatchSpec = DEFAULT_SPEC) -> list[object] | None:
    first = spec.expected_before + 1
    paths = [CONTENT_DIR / f"{number:03d}.json" for number in range(first, first + spec.expected)]
    present = [path.is_file() for path in paths]
    if not any(present):
        return None
    if not all(present):
        raise ValueError("2026-09-23 source batch is only partially applied")
    return [_load_json(path) for path in paths]


def _load_author_modules() -> list[list[dict[str, object]]]:
    modules: list[list[dict[str, object]]] = []
    for suffix, path in zip("abcde", AUTHOR_FILES, strict=True):
        if __package__:
            module = importlib.import_module(f".leehu_notes_20260923_{suffix}", __package__)
            value = module.entries() if hasattr(module, "entries") else module.ENTRIES
        else:
            namespace = runpy.run_path(str(path), run_name=f"leehu_notes_20260923_{suffix}_review")
            value = namespace["entries"]() if "entries" in namespace else namespace["ENTRIES"]
        modules.append(value)
    return modules


def review(path: Path, *, spec: BatchSpec = DEFAULT_SPEC) -> dict[str, object]:
    """Load generator, manifest and fixed pre-batch corpus, then review once."""
    if __package__:
        generator = importlib.import_module(".append_leehu_works_20260923_1000", __package__)
        generate = generator.generate
        entries = generator.entries
    else:
        module = runpy.run_path(str(GENERATOR), run_name="leehu_works_20260923_review")
        generate = module["generate"]
        entries = module["entries"]
    notes = _load_json(path)
    result = validate_batch(
        notes,
        entries(),
        existing_notes=_load_existing(spec),
        generated_notes=generate(),
        source_notes=_load_applied_sources(spec),
        authored_modules=_load_author_modules(),
        spec=spec,
    )
    result["manifest_sha256"] = hashlib.sha256(
        canonical_json(notes).encode("utf-8")
    ).hexdigest()
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
    except (ImportError, KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "ok": False,
            "count": 0,
            "works": {},
            "generator_match": False,
            "source_match": None,
            "exact_sentence_duplicates": 0,
            "normalized_skeleton_duplicates": 0,
            "error_count": 1,
            "errors": [str(exc)],
            "diagnostic_counts": {type(exc).__name__: 1},
            "concentration": {},
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
