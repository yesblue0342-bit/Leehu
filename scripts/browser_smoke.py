#!/usr/bin/env python3
"""Check the local production handler with desktop and mobile Chromium pages.

Requires Playwright and Chromium. No downloads, publishing, or external requests.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Browser check requires the playwright Python package.", file=sys.stderr)
        return 1
    executable = os.environ.get("CHROMIUM_EXECUTABLE") or shutil.which("chromium") or shutil.which("chromium-browser")
    with tempfile.TemporaryDirectory(prefix="leehu-browser-") as directory:
        os.environ["BOARD_POSTS_DIR"] = str(Path(directory) / "board")
        os.environ["LITERATURE_POSTS_DIR"] = str(Path(directory) / "literature")
        os.environ["LITERATURE_PUBLICATION_MODE"] = "static"
        import server

        class Handler(server.LeehuHandler):
            def log_message(self, *args):
                pass

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT)))
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        origin = f"http://127.0.0.1:{httpd.server_port}"
        try:
            with sync_playwright() as runtime:
                browser = runtime.chromium.launch(headless=True, executable_path=executable)
                try:
                    for label, viewport in (("desktop", {"width": 1440, "height": 1000}), ("mobile", {"width": 390, "height": 844})):
                        context = browser.new_context(viewport=viewport)
                        # Only this temporary local server may receive requests.
                        context.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin + "/") else route.abort())
                        page = context.new_page()
                        for path in ("/", "/author/", "/works/", "/official-links/", "/literature/"):
                            response = page.goto(origin + path, wait_until="domcontentloaded")
                            if response is None or response.status != 200:
                                raise RuntimeError(f"{label} {path}: HTTP response is not 200")
                            if not page.title().strip() or not page.locator("body").inner_text().strip():
                                raise RuntimeError(f"{label} {path}: page title or content is empty")
                            canonical = page.locator('link[rel="canonical"]').get_attribute("href")
                            if canonical != server.CANONICAL_ORIGIN + path:
                                raise RuntimeError(f"{label} {path}: unexpected canonical {canonical!r}")
                            links = page.locator("a[href]").evaluate_all("els => els.map(a => a.getAttribute('href'))")
                            link = next((href for href in links if href and href.startswith("/") and not href.startswith("//") and href != path and not urlsplit(href).fragment), None)
                            if link is None:
                                raise RuntimeError(f"{label} {path}: no internal navigation link")
                            navigation = page.goto(origin + link, wait_until="domcontentloaded")
                            if navigation is None or navigation.status != 200:
                                raise RuntimeError(f"{label} {path}: internal navigation failed: {link}")
                            print(f"PASS {label} {path}: HTTP, content, canonical, internal navigation", flush=True)
                        context.close()
                finally:
                    browser.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
