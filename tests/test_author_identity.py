"""Prevent conflicting book editions and split author identities in public pages."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://xn--hu5b23z.com"


def graphs(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    blocks = re.findall(r'<script[^>]*type=[\'\"]application/ld\+json[\'\"][^>]*>(.*?)</script>', text, re.S)
    return [node for block in blocks for node in json.loads(block).get("@graph", [])]


def all_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from all_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from all_nodes(child)


class AuthorIdentityTest(unittest.TestCase):
    def test_fantasy_has_one_identity_and_publication_date_across_pages(self):
        found = []
        for page in ("index.html", "author/index.html", "works/index.html", "official-links/index.html"):
            for node in all_nodes(graphs(page)):
                if node.get("@type") == "Book" and node.get("isbn") == "9791169572347":
                    self.assertEqual(node["@id"], ORIGIN + "/works/#fantasy", page)
                    self.assertEqual(node["datePublished"], "2024-10-18", page)
                    self.assertEqual(node["author"]["@id"], ORIGIN + "/#person", page)
                    found.append(page)
        self.assertEqual(len(found), 3)

    def test_paperback_facts_do_not_replace_ebook_identity(self):
        text = (ROOT / "works/index.html").read_text(encoding="utf-8")
        listing = next(node for node in graphs("works/index.html") if node.get("@type") == "ItemList")
        editions = []
        for entry in listing["itemListElement"]:
            book = entry["item"]
            edition = book.get("workExample")
            if not edition:
                continue
            self.assertIn("ebook-product.kyobobook.co.kr", book["url"])
            self.assertNotIn("isbn", book)
            self.assertEqual(edition["exampleOfWork"]["@id"], book["@id"])
            self.assertEqual(edition["author"]["@id"], ORIGIN + "/#person")
            isbn = edition["isbn"]
            self.assertEqual(len(isbn), 13)
            self.assertEqual(sum(int(n) * (1 if i % 2 == 0 else 3) for i, n in enumerate(isbn)) % 10, 0)
            self.assertIn(f'id="{edition["@id"].split("#")[-1]}"', text)
            visible = re.sub(r"<script\b[^>]*>.*?</script>", "", text, flags=re.S)
            for fact in (isbn, edition["datePublished"], edition["url"]):
                self.assertIn(fact, visible)
            editions.append(edition)
        self.assertEqual(len(editions), 4)

    def test_music_recording_belongs_to_the_same_person(self):
        nodes = graphs("official-links/index.html")
        self.assertFalse(any(node.get("@type") == "MusicGroup" for node in nodes))
        recording = next(node for node in nodes if node.get("@type") == "MusicRecording")
        self.assertEqual(recording["byArtist"]["@id"], ORIGIN + "/#person")
        self.assertEqual(recording["datePublished"], "2023-07-18")
        text = (ROOT / "official-links/index.html").read_text(encoding="utf-8")
        self.assertIn('id="cash-only"', text)
        self.assertIn(recording["url"], text.split("</head>")[-1])

    def test_answers_match_visible_copy(self):
        text = (ROOT / "author/index.html").read_text(encoding="utf-8")
        for node in all_nodes(graphs("author/index.html")):
            if node.get("@type") == "Question":
                self.assertIn(node["acceptedAnswer"]["text"], text.split("</head>")[-1])


if __name__ == "__main__":
    unittest.main()
