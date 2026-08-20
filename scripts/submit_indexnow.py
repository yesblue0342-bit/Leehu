#!/usr/bin/env python3
"""Notify Naver IndexNow about updated pages on the official site."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
HOST = "xn--hu5b23z.com"
ORIGIN = f"https://{HOST}"
ENDPOINT = "https://searchadvisor.naver.com/indexnow"
KEY_FILE = ROOT / "2a3ff96b2a71425482930b5267565b8a.txt"
DEFAULT_URLS = (f"{ORIGIN}/", f"{ORIGIN}/author/")
KEY_RE = re.compile(r"^[A-Fa-f0-9-]{8,128}$")


def read_key() -> str:
    """Read and validate the public IndexNow ownership key."""
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not KEY_RE.fullmatch(key):
        raise ValueError("IndexNow key file contains an invalid key")
    return key


def normalize_urls(values: list[str] | tuple[str, ...]) -> list[str]:
    """Return unique HTTPS URLs that belong to the configured official host."""
    urls: list[str] = []
    for value in values:
        parsed = urlsplit(value)
        if parsed.scheme != "https" or parsed.hostname != HOST:
            raise ValueError(f"IndexNow URL must use https://{HOST}: {value}")
        if parsed.username or parsed.password or parsed.port or parsed.fragment:
            raise ValueError(f"IndexNow URL contains unsupported components: {value}")
        if value not in urls:
            urls.append(value)
    if not urls:
        raise ValueError("At least one URL is required")
    if len(urls) > 10_000:
        raise ValueError("IndexNow accepts at most 10,000 URLs per request")
    return urls


def build_payload(values: list[str] | tuple[str, ...]) -> dict[str, object]:
    """Build the JSON body required by Naver's IndexNow endpoint."""
    key = read_key()
    return {
        "host": HOST,
        "key": key,
        "keyLocation": f"{ORIGIN}/{key}.txt",
        "urlList": normalize_urls(values),
    }


def submit(values: list[str] | tuple[str, ...], timeout: float = 20.0) -> int:
    """Submit updated URLs and return the successful HTTP status code."""
    body = json.dumps(build_payload(values), ensure_ascii=False).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
    except HTTPError as error:
        raise RuntimeError(f"Naver IndexNow rejected the request: HTTP {error.code}") from error
    except URLError as error:
        raise RuntimeError(f"Naver IndexNow request failed: {error.reason}") from error
    if status not in (200, 202):
        raise RuntimeError(f"Unexpected Naver IndexNow response: HTTP {status}")
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*", default=list(DEFAULT_URLS))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print(json.dumps(build_payload(args.urls), ensure_ascii=False, indent=2))
        return
    status = submit(args.urls)
    print(f"Naver IndexNow accepted {len(normalize_urls(args.urls))} URL(s): HTTP {status}")


if __name__ == "__main__":
    main()
