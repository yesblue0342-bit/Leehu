#!/usr/bin/env python3
"""Safely append curated literature manifests and verify static outputs."""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from . import build_literature
except ImportError:
    import build_literature

from literature_index_policy import is_note_indexable, load_index_policy


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content" / "literature"
LITERATURE_DIR = ROOT / "literature"
ID_RE = re.compile(r"(?P<date>\d{8})_leehu_literature_(?P<sequence>\d{3,})")
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class AppendPlan:
    """Files planned or written by one manifest append."""

    paths: tuple[Path, ...]
    applied: bool


@dataclass(frozen=True)
class SiteMetrics:
    """Counts used by the static publishing gate."""

    sources: int
    indexable: int
    details: int
    rss_items: int
    sitemap_urls: int
    list_pages: int


def numbered_paths(content_dir: Path) -> list[Path]:
    """Return source paths after enforcing a contiguous 001..NNN sequence."""
    paths = sorted(content_dir.glob("*.json"), key=lambda path: int(path.stem))
    expected = [f"{number:03d}.json" for number in range(1, len(paths) + 1)]
    if [path.name for path in paths] != expected:
        raise ValueError("existing literature files must be contiguous from 001.json")
    return paths


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc


def validate_manifest_note(note: object, position: int) -> dict[str, object]:
    """Validate fields needed before a manifest can enter the source corpus."""
    if not isinstance(note, dict):
        raise ValueError(f"manifest item {position} must be an object")
    missing = [field for field in build_literature.REQUIRED_FIELDS if field not in note]
    if missing:
        raise ValueError(f"manifest item {position} missing: {', '.join(missing)}")
    note_id = str(note["id"])
    match = ID_RE.fullmatch(note_id)
    if not match:
        raise ValueError(f"manifest item {position} has invalid id")
    if not SLUG_RE.fullmatch(str(note["slug"])):
        raise ValueError(f"manifest item {position} has invalid slug")
    try:
        published = datetime.fromisoformat(str(note["published_at"]))
    except ValueError as exc:
        raise ValueError(f"manifest item {position} has invalid published_at") from exc
    if match.group("date") != published.strftime("%Y%m%d"):
        raise ValueError(f"manifest item {position} id date differs from published_at")
    if not isinstance(note["tags"], list) or not 2 <= len(note["tags"]) <= 6:
        raise ValueError(f"manifest item {position} must have 2-6 tags")
    return note


def append_manifest(
    content_dir: Path,
    manifest: list[object],
    *,
    apply: bool,
) -> AppendPlan:
    """Validate and append a manifest without overwriting existing source files."""
    content_dir.mkdir(parents=True, exist_ok=True)
    existing_paths = numbered_paths(content_dir)
    existing_notes = [load_json(path) for path in existing_paths]
    if any(not isinstance(note, dict) for note in existing_notes):
        raise ValueError("existing literature source must contain JSON objects")

    incoming = [validate_manifest_note(note, index) for index, note in enumerate(manifest, 1)]
    if not incoming:
        raise ValueError("manifest must contain at least one note")

    existing_ids = {str(note["id"]) for note in existing_notes if isinstance(note, dict)}
    existing_slugs = {str(note["slug"]) for note in existing_notes if isinstance(note, dict)}
    incoming_ids = [str(note["id"]) for note in incoming]
    incoming_slugs = [str(note["slug"]) for note in incoming]
    if existing_ids.intersection(incoming_ids) or len(incoming_ids) != len(set(incoming_ids)):
        raise ValueError("duplicate id in manifest or existing corpus")
    if existing_slugs.intersection(incoming_slugs) or len(incoming_slugs) != len(set(incoming_slugs)):
        raise ValueError("duplicate slug in manifest or existing corpus")

    paths = tuple(
        content_dir / f"{len(existing_paths) + offset:03d}.json"
        for offset in range(1, len(incoming) + 1)
    )
    if any(path.exists() for path in paths):
        raise ValueError("append target already exists")
    if not apply:
        return AppendPlan(paths=paths, applied=False)

    temporary_paths: list[Path] = []
    applied_paths: list[Path] = []
    try:
        for path, note in zip(paths, incoming):
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(note, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_paths.append(temporary)
        for temporary, path in zip(temporary_paths, paths):
            temporary.replace(path)
            applied_paths.append(path)
    except OSError:
        for path in reversed(applied_paths):
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary_paths:
            path.unlink(missing_ok=True)
    return AppendPlan(paths=paths, applied=True)


def site_metrics() -> SiteMetrics:
    source_paths = numbered_paths(CONTENT_DIR)
    notes = [load_json(path) for path in source_paths]
    if any(not isinstance(note, dict) for note in notes):
        raise ValueError("literature source must contain JSON objects")
    policy = load_index_policy(build_literature.INDEX_POLICY_PATH, notes)
    indexable = sum(is_note_indexable(note, policy) for note in notes)
    details = sum(
        1
        for child in LITERATURE_DIR.iterdir()
        if child.is_dir() and child.name != "page" and (child / "index.html").is_file()
    )
    list_pages = 1 + sum(
        1 for path in (LITERATURE_DIR / "page").glob("*/index.html") if path.is_file()
    )
    rss_items = len(ET.parse(LITERATURE_DIR / "rss.xml").findall("./channel/item"))
    sitemap_urls = len(ET.parse(ROOT / "sitemap.xml").getroot())
    return SiteMetrics(
        len(source_paths), indexable, details, rss_items, sitemap_urls, list_pages
    )


def verify_site(expected_count: int | None = None) -> SiteMetrics:
    metrics = site_metrics()
    expected = expected_count if expected_count is not None else metrics.sources
    expected_pages = math.ceil(metrics.indexable / build_literature.PAGE_SIZE)
    expected_sitemap = metrics.indexable + 3
    errors = []
    if metrics.sources != expected:
        errors.append(f"sources={metrics.sources}, expected={expected}")
    if metrics.details != expected:
        errors.append(f"details={metrics.details}, expected={expected}")
    if metrics.rss_items != metrics.indexable:
        errors.append(
            f"rss_items={metrics.rss_items}, expected={metrics.indexable}"
        )
    if metrics.list_pages != expected_pages:
        errors.append(f"list_pages={metrics.list_pages}, expected={expected_pages}")
    if metrics.sitemap_urls != expected_sitemap:
        errors.append(f"sitemap_urls={metrics.sitemap_urls}, expected={expected_sitemap}")
    if errors:
        raise ValueError("static publishing verification failed: " + "; ".join(errors))
    return metrics


def print_metrics(metrics: SiteMetrics) -> None:
    print(
        f"sources={metrics.sources} details={metrics.details} "
        f"indexable={metrics.indexable} "
        f"rss_items={metrics.rss_items} sitemap_urls={metrics.sitemap_urls} "
        f"list_pages={metrics.list_pages}"
    )


def builder_command(expected_count: int) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "scripts" / "build_literature.py"),
        "--expected-count",
        str(expected_count),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    append_parser = subparsers.add_parser("append", help="validate or append a curated JSON manifest")
    append_parser.add_argument("manifest", type=Path)
    append_parser.add_argument("--apply", action="store_true", help="write files; omitted means dry-run")

    verify_parser = subparsers.add_parser("verify", help="verify source and generated output counts")
    verify_parser.add_argument("--expected-count", type=int)

    build_parser = subparsers.add_parser("build", help="run the static builder and verify outputs")
    build_parser.add_argument("--expected-count", type=int)
    build_parser.add_argument("--test", action="store_true", help="run the full unittest suite after build")

    args = parser.parse_args()
    try:
        if args.command == "append":
            raw = load_json(args.manifest)
            if not isinstance(raw, list):
                raise ValueError("manifest root must be a JSON array")
            plan = append_manifest(CONTENT_DIR, raw, apply=args.apply)
            mode = "applied" if plan.applied else "dry-run"
            print(f"{mode}: {len(plan.paths)} notes -> {plan.paths[0].name}..{plan.paths[-1].name}")
        elif args.command == "verify":
            print_metrics(verify_site(args.expected_count))
        else:
            expected_count = args.expected_count or len(numbered_paths(CONTENT_DIR))
            subprocess.run(builder_command(expected_count), check=True)
            print_metrics(verify_site(expected_count))
            if args.test:
                subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                    cwd=ROOT,
                    check=True,
                )
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
