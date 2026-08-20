from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import literature_batch


class LiteratureBatchTest(unittest.TestCase):
    def test_builder_command_passes_expected_count(self) -> None:
        command = literature_batch.builder_command(2000)
        self.assertEqual(command[-2:], ["--expected-count", "2000"])

    def sample_note(self, identifier: str, slug: str) -> dict[str, object]:
        return {
            "id": identifier,
            "slug": slug,
            "title": f"문학노트 {slug}",
            "quote": "This is a sufficiently long public-domain quotation for validation.",
            "source_author": "Test Author",
            "source_work": "Test Work",
            "source_location": "Test location",
            "source_language": "en",
            "source_url": "https://www.gutenberg.org/ebooks/1",
            "translation_note": "영어 원문 직접 인용.",
            "rights_note": "Project Gutenberg 공개 원문.",
            "commentary": "첫 번째 생각이다. 두 번째 생각이다. 세 번째 생각이다. 네 번째 생각이다.",
            "closing": "소설가 이후 드림",
            "author": "소설가 이후",
            "tags": ["문학", "감상"],
            "related_work": {"name": "연", "url": "https://example.com/"},
            "published_at": "2026-08-07T09:00:00+09:00",
            "content_kind": "source_quote",
        }

    def write_note(self, directory: Path, number: int, note: dict[str, object]) -> None:
        (directory / f"{number:03d}.json").write_text(
            json.dumps(note, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_append_manifest_is_dry_run_by_default_and_atomic_on_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            content_dir = Path(temporary)
            self.write_note(content_dir, 1, self.sample_note("20260807_leehu_literature_001", "existing"))
            incoming = [self.sample_note("20260807_leehu_literature_002", "new-note")]

            plan = literature_batch.append_manifest(content_dir, incoming, apply=False)
            self.assertEqual(plan.paths, (content_dir / "002.json",))
            self.assertFalse((content_dir / "002.json").exists())

            applied = literature_batch.append_manifest(content_dir, incoming, apply=True)
            self.assertEqual(applied.paths, plan.paths)
            saved = json.loads((content_dir / "002.json").read_text(encoding="utf-8"))
            self.assertEqual(saved, incoming[0])
            self.assertFalse(list(content_dir.glob("*.tmp")))

    def test_append_manifest_rejects_duplicate_id_and_slug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            content_dir = Path(temporary)
            existing = self.sample_note("20260807_leehu_literature_001", "existing")
            self.write_note(content_dir, 1, existing)

            with self.assertRaisesRegex(ValueError, "duplicate id"):
                literature_batch.append_manifest(
                    content_dir,
                    [self.sample_note("20260807_leehu_literature_001", "new-note")],
                    apply=False,
                )
            with self.assertRaisesRegex(ValueError, "duplicate slug"):
                literature_batch.append_manifest(
                    content_dir,
                    [self.sample_note("20260807_leehu_literature_002", "existing")],
                    apply=False,
                )

    def test_append_manifest_requires_contiguous_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            content_dir = Path(temporary)
            self.write_note(content_dir, 2, self.sample_note("20260807_leehu_literature_001", "existing"))
            with self.assertRaisesRegex(ValueError, "contiguous"):
                literature_batch.append_manifest(
                    content_dir,
                    [self.sample_note("20260807_leehu_literature_002", "new-note")],
                    apply=False,
                )


if __name__ == "__main__":
    unittest.main()
