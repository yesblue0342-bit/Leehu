"""Shared, versioned search-index policy for literature-note publication."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


ROOT = Path(__file__).resolve().parent
DEFAULT_POLICY_PATH = ROOT / "content" / "literature-index-policy.json"
LITERATURE_ID_RE = re.compile(
    r"^(?P<prefix>\d{8}_leehu_literature_)(?P<sequence>\d{2,})$"
)


@dataclass(frozen=True)
class IndexRule:
    """One inclusive sequence range within a literature ID prefix."""

    id_prefix: str
    sequence_start: int
    sequence_end: int
    indexable: bool
    reason: str

    def matches(self, note_id: str) -> bool:
        match = LITERATURE_ID_RE.fullmatch(note_id)
        if not match or match.group("prefix") != self.id_prefix:
            return False
        sequence = int(match.group("sequence"))
        return self.sequence_start <= sequence <= self.sequence_end


@dataclass(frozen=True)
class IndexPolicy:
    """Validated policy used by both the static builder and runtime server."""

    version: int
    default_indexable: bool
    rules: tuple[IndexRule, ...]


def _note_id(note: Mapping[str, object] | str) -> str:
    return str(note.get("id", "")) if isinstance(note, Mapping) else str(note)


def load_index_policy(
    path: Path | str = DEFAULT_POLICY_PATH,
    notes: Iterable[Mapping[str, object]] | None = None,
) -> IndexPolicy:
    """Load and validate a policy, optionally requiring every rule to match sources."""

    policy_path = Path(path)
    try:
        raw = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid literature index policy: {policy_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("literature index policy root must be an object")

    version = raw.get("version")
    default_indexable = raw.get("default_indexable")
    raw_rules = raw.get("rules")
    if not isinstance(version, int) or version < 1:
        raise ValueError("literature index policy version must be a positive integer")
    if not isinstance(default_indexable, bool):
        raise ValueError("literature index policy default_indexable must be boolean")
    if not isinstance(raw_rules, list):
        raise ValueError("literature index policy rules must be an array")

    rules: list[IndexRule] = []
    for position, raw_rule in enumerate(raw_rules, 1):
        if not isinstance(raw_rule, dict):
            raise ValueError(f"literature index policy rule {position} must be an object")
        id_prefix = raw_rule.get("id_prefix")
        sequence_start = raw_rule.get("sequence_start")
        sequence_end = raw_rule.get("sequence_end")
        indexable = raw_rule.get("indexable")
        reason = raw_rule.get("reason")
        if not isinstance(id_prefix, str) or not re.fullmatch(
            r"\d{8}_leehu_literature_", id_prefix
        ):
            raise ValueError(f"literature index policy rule {position} has invalid id_prefix")
        if (
            not isinstance(sequence_start, int)
            or isinstance(sequence_start, bool)
            or sequence_start < 0
            or not isinstance(sequence_end, int)
            or isinstance(sequence_end, bool)
            or sequence_end < sequence_start
        ):
            raise ValueError(f"literature index policy rule {position} has invalid sequence range")
        if not isinstance(indexable, bool):
            raise ValueError(f"literature index policy rule {position} indexable must be boolean")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"literature index policy rule {position} requires a reason")
        rules.append(
            IndexRule(
                id_prefix=id_prefix,
                sequence_start=sequence_start,
                sequence_end=sequence_end,
                indexable=indexable,
                reason=reason.strip(),
            )
        )

    for left, rule in enumerate(rules):
        for other in rules[left + 1 :]:
            overlaps = (
                rule.id_prefix == other.id_prefix
                and rule.sequence_start <= other.sequence_end
                and other.sequence_start <= rule.sequence_end
            )
            if overlaps:
                raise ValueError("literature index policy rules must not overlap")

    policy = IndexPolicy(
        version=version,
        default_indexable=default_indexable,
        rules=tuple(rules),
    )
    if notes is not None:
        note_ids = [_note_id(note) for note in notes]
        invalid_ids = [note_id for note_id in note_ids if not LITERATURE_ID_RE.fullmatch(note_id)]
        if invalid_ids:
            raise ValueError(f"literature index policy received invalid note id: {invalid_ids[0]}")
        unmatched = [
            rule
            for rule in policy.rules
            if not any(rule.matches(note_id) for note_id in note_ids)
        ]
        if unmatched:
            first = unmatched[0]
            raise ValueError(
                "literature index policy rule matches no source IDs: "
                f"{first.id_prefix}{first.sequence_start}..{first.sequence_end}"
            )
    return policy


def is_note_indexable(
    note: Mapping[str, object] | str,
    policy: IndexPolicy,
) -> bool:
    """Return the first matching rule decision, or the policy default."""

    note_id = _note_id(note)
    for rule in policy.rules:
        if rule.matches(note_id):
            return rule.indexable
    return policy.default_indexable


def partition_indexable_notes(
    notes: Iterable[Mapping[str, object]],
    policy: IndexPolicy,
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    """Split notes without changing their existing order."""

    indexable: list[Mapping[str, object]] = []
    excluded: list[Mapping[str, object]] = []
    for note in notes:
        (indexable if is_note_indexable(note, policy) else excluded).append(note)
    return indexable, excluded
