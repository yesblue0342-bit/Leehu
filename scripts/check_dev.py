#!/usr/bin/env python3
"""Run existing development checks and optional local browser smoke checks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUICK_TESTS = (
    "test_public_http_routes.py",
    "test_author_identity.py",
    "test_literature_index_policy.py",
    "test_indexnow.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("quick", "full"), default="quick")
    parser.add_argument("--browser", action="store_true", help="also run local browser smoke checks")
    parser.add_argument("--report", type=Path, help="write command results as JSON outside the checkout")
    args = parser.parse_args()
    if args.report and args.report.resolve().is_relative_to(ROOT):
        parser.error("choose a report path outside the checkout, such as /tmp/leehu-check.json")

    commands = [["git", "diff", "--check"]]
    patterns = ("test_*.py",) if args.suite == "full" else QUICK_TESTS
    commands.extend(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern]
        for pattern in patterns
    )
    if args.browser:
        commands.append([sys.executable, "scripts/browser_smoke.py"])

    results = []
    with tempfile.TemporaryDirectory(prefix="leehu-check-") as directory:
        environment = dict(os.environ)
        environment.update({
            "BOARD_POSTS_DIR": str(Path(directory) / "board"),
            "LITERATURE_POSTS_DIR": str(Path(directory) / "literature"),
            "INDEXNOW_NOTIFY": "0",
        })
        for command in commands:
            print("Running:", " ".join(command), flush=True)
            try:
                result = subprocess.run(command, cwd=ROOT, env=environment, check=False)
                code = result.returncode
            except OSError as exc:
                print(f"Cannot run check: {exc}", file=sys.stderr)
                code = 1
            results.append({"command": command, "exit_code": code})
    passed = all(item["exit_code"] == 0 for item in results)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "suite": args.suite,
            "passed": passed,
            "checks": results,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Development checks:", "PASS" if passed else "FAIL", flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
