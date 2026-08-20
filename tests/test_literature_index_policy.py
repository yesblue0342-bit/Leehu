from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from literature_index_policy import (
    DEFAULT_POLICY_PATH,
    is_note_indexable,
    load_index_policy,
)


class LiteratureIndexPolicyTest(unittest.TestCase):
    def write_policy(self, directory: Path, payload: object) -> Path:
        path = directory / "policy.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def test_repository_policy_boundaries_and_default(self) -> None:
        policy = load_index_policy(
            DEFAULT_POLICY_PATH,
            [
                {"id": "20260806_leehu_literature_001"},
                {"id": "20260806_leehu_literature_499"},
                {"id": "20260806_leehu_literature_500"},
            ],
        )
        self.assertFalse(
            is_note_indexable("20260806_leehu_literature_001", policy)
        )
        self.assertFalse(
            is_note_indexable("20260806_leehu_literature_499", policy)
        )
        self.assertTrue(
            is_note_indexable("20260806_leehu_literature_500", policy)
        )
        self.assertTrue(
            is_note_indexable("20260807_leehu_literature_001", policy)
        )

    def test_policy_rejects_invalid_version_overlap_range_and_unmatched_rule(self) -> None:
        valid_rule = {
            "id_prefix": "20260806_leehu_literature_",
            "sequence_start": 1,
            "sequence_end": 10,
            "indexable": False,
            "reason": "test",
        }
        cases = (
            (
                {"version": 0, "default_indexable": True, "rules": []},
                "version",
                None,
            ),
            (
                {
                    "version": 1,
                    "default_indexable": True,
                    "rules": [
                        valid_rule,
                        {**valid_rule, "sequence_start": 10, "sequence_end": 12},
                    ],
                },
                "overlap",
                None,
            ),
            (
                {
                    "version": 1,
                    "default_indexable": True,
                    "rules": [
                        {**valid_rule, "sequence_start": 11, "sequence_end": 10}
                    ],
                },
                "range",
                None,
            ),
            (
                {
                    "version": 1,
                    "default_indexable": True,
                    "rules": [valid_rule],
                },
                "matches no source",
                [{"id": "20260807_leehu_literature_001"}],
            ),
        )
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for index, (payload, message, notes) in enumerate(cases, 1):
                path = self.write_policy(directory, payload)
                with self.subTest(case=index), self.assertRaisesRegex(
                    ValueError, message
                ):
                    load_index_policy(path, notes)


if __name__ == "__main__":
    unittest.main()
