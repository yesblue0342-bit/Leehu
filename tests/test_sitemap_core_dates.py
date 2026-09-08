import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from scripts import build_literature as builder


class CorePageDatesTest(unittest.TestCase):
    def test_sitemap_keeps_profile_dates_when_a_new_note_is_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pages = {
                "index.html": "2026-09-08",
                "author/index.html": "2026-09-08",
                "works/index.html": "2026-09-07",
                "official-links/index.html": None,
            }
            for name, date in pages.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                node = {"@type": "WebPage", "dateModified": date}
                quote = "'" if name.startswith("author") else '"'
                path.write_text(
                    f"<script type={quote}application/ld+json{quote}>"
                    + json.dumps({"@graph": [node]}) + "</script>",
                    encoding="utf-8",
                )
            with patch.object(builder, "ROOT", root):
                builder.write_sitemap([{"slug": "new-note", "published_at": "2026-09-10T08:00:00+09:00"}])
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            entries = {
                node.findtext("sm:loc", namespaces=ns):
                node.findtext("sm:lastmod", namespaces=ns)
                for node in ET.parse(root / "sitemap.xml").getroot()
            }
            self.assertEqual(entries[builder.ORIGIN + "/"], "2026-09-10")
            self.assertEqual(entries[builder.ORIGIN + "/author/"], "2026-09-08")
            self.assertEqual(entries[builder.ORIGIN + "/works/"], "2026-09-07")
            self.assertEqual(entries[builder.ORIGIN + "/official-links/"], builder.CORE_PAGE_LASTMOD)
