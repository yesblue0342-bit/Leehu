import unittest

from scripts import submit_indexnow


class IndexNowTest(unittest.TestCase):
    def test_payload_matches_public_key_file_and_official_host(self) -> None:
        payload = submit_indexnow.build_payload(submit_indexnow.DEFAULT_URLS)
        key = submit_indexnow.KEY_FILE.read_text(encoding="utf-8").strip()
        self.assertEqual(payload["host"], submit_indexnow.HOST)
        self.assertEqual(payload["key"], key)
        self.assertEqual(
            payload["keyLocation"],
            f"{submit_indexnow.ORIGIN}/{key}.txt",
        )
        self.assertEqual(payload["urlList"], list(submit_indexnow.DEFAULT_URLS))

    def test_urls_are_deduplicated_and_external_hosts_are_rejected(self) -> None:
        url = f"{submit_indexnow.ORIGIN}/author/"
        self.assertEqual(submit_indexnow.normalize_urls([url, url]), [url])
        with self.assertRaises(ValueError):
            submit_indexnow.normalize_urls(["https://example.com/author/"])

    def test_urls_reject_fragments_userinfo_and_non_https(self) -> None:
        for url in (
            f"http://{submit_indexnow.HOST}/author/",
            f"https://user@{submit_indexnow.HOST}/author/",
            f"https://{submit_indexnow.HOST}/author/#profile",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                submit_indexnow.normalize_urls([url])


if __name__ == "__main__":
    unittest.main()
