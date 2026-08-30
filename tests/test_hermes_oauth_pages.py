from pathlib import Path

import server


ROOT = Path(__file__).resolve().parents[1]


def test_hermes_oauth_pages_are_public_and_linked():
    assert {"/hermes.html", "/hermes-privacy.html"} <= server.PUBLIC_STATIC_FILES
    homepage = (ROOT / "hermes.html").read_text(encoding="utf-8")
    privacy = (ROOT / "hermes-privacy.html").read_text(encoding="utf-8")
    assert 'href="/hermes-privacy.html"' in homepage
    assert 'href="/hermes.html"' in privacy
    assert "Google API Services User Data Policy" in privacy
    assert "yesblue0342@gmail.com" in homepage
