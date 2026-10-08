# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Run the initial README checks for a repository."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

from ansys.pre_commit_hooks.quality_rules import repo_review_checks
from ansys.pre_commit_hooks.quality_rules.common import (
    _first_doc_line,
    normalize_check_result,
    readme_path,
)


def _normalize_codes(values: list[str]) -> set[str]:
    """Split repeated and comma-separated rule IDs into a normalized set."""
    return {value.strip().upper() for item in values for value in item.split(",") if value.strip()}


def _execute_check(check_obj: Any, code: str, root: Path, detected_readme: str | None) -> dict:
    """Run one check and normalize its report result."""
    signature = inspect.signature(check_obj.check)
    available = {"root": root, "readme_path": detected_readme}
    kwargs = {name: available[name] for name in signature.parameters if name in available}
    try:
        raw = check_obj.check(**kwargs)
    except (OSError, TypeError, ValueError) as exc:
        raw = f"WARN: Check error: {exc}"

    status, detail = normalize_check_result(raw, check_obj)
    return {
        "id": code,
        "family": check_obj.family,
        "label": (type(check_obj).__doc__ or code).strip().splitlines()[0],
        "description": _first_doc_line(check_obj),
        "status": status,
        "detail": detail,
    }


def _run_checks(
    root: Path,
    *,
    selected_codes: set[str] | None = None,
    ignored_codes: set[str] | None = None,
) -> dict[str, Any]:
    """Evaluate registered README checks for a repository directory."""
    checks = repo_review_checks()
    selected = {code.upper() for code in selected_codes or set()}
    ignored = {code.upper() for code in ignored_codes or set()}
    if selected:
        checks = {code: item for code, item in checks.items() if code.upper() in selected}
    readme = readme_path(root)
    results = [
        _execute_check(check, code, root, readme)
        for code, check in checks.items()
        if code.upper() not in ignored
    ]

    passed = sum(result["status"] == "pass" for result in results)
    failed = sum(result["status"] == "fail" for result in results)
    warned = sum(result["status"] == "warn" for result in results)
    scored = passed + failed
    return {
        "results": results,
        "tally": {
            "pass": passed,
            "fail": failed,
            "warn": warned,
        },
        "score": round(passed / scored * 100) if scored else 0,
    }


def _metadata_report(selected_codes: set[str] | None = None) -> list[dict[str, str]]:
    """Return metadata for available README checks."""
    checks = repo_review_checks()
    selected = {code.upper() for code in selected_codes or set()}
    return [
        {
            "id": code,
            "family": check.family,
            "name": _first_doc_line(check),
            "description": (type(check).__doc__ or "").strip().splitlines()[0],
        }
        for code, check in sorted(checks.items())
        if not selected or code.upper() in selected
    ]


def _print_report(review: dict[str, Any], *, show_all: bool = False) -> None:
    """Print the report, using problem messages as warning/failure headlines."""
    print("PyAnsys quality report")
    print("========================")
    print(f"Score: {review['score']}%")
    tally = review["tally"]
    print(f"Summary: pass={tally['pass']} fail={tally['fail']} warn={tally['warn']}")
    for item in review["results"]:
        if item["status"] == "pass" and not show_all:
            continue
        detail = item["detail"] or ""
        headline = detail if item["status"] in {"warn", "fail"} and detail else item["label"]
        print(f"- [{item['status'].upper()}] {item['id']} - {headline}")
        if detail and item["status"] not in {"warn", "fail"} and detail != headline:
            print(f"  {detail}")


def _find_project_root(start: Path) -> Path:
    """Return the project root for a starting directory.

    Parameters
    ----------
    start : pathlib.Path
        Directory where the search begins, usually the current directory.

    Returns
    -------
    pathlib.Path
        The nearest directory that contains ``pyproject.toml``, searching ``start``
        and then its parents. ``start`` if none contains one.
    """
    for directory in (start, *start.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    return start


def _validate_rule_ids(parser: argparse.ArgumentParser, option: str, codes: set[str]) -> None:
    """Exit with an error if any rule ID passed to an option does not exist."""
    available = sorted(repo_review_checks())
    unknown = sorted(codes.difference(available))
    if unknown:
        parser.error(
            f"unknown rule ID(s) for {option}: {', '.join(unknown)}. "
            f"Available rules: {', '.join(available)}"
        )


def main(argv: list[str] | None = None) -> int:
    """Run README quality checks for a repository."""
    parser = argparse.ArgumentParser(description="Run PyAnsys README quality checks.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report.")
    parser.add_argument("--metadata", action="store_true", help="List available rule metadata.")
    parser.add_argument("--check", action="append", default=[], help="Select rule IDs.")
    parser.add_argument("--family", action="append", default=[], help="Select rule family.")
    parser.add_argument("--ignore", action="append", default=[], help="Ignore rule IDs.")
    parser.add_argument("--show-all", action="store_true", help="Include passing checks.")
    parser.add_argument(
        "--fails-only",
        action="store_true",
        help="Show warnings and failures only (the default).",
    )
    args = parser.parse_args(argv)
    if args.show_all and args.fails_only:
        parser.error("Use only one of --show-all or --fails-only")

    selected_codes = _normalize_codes(args.check)
    ignored_codes = _normalize_codes(args.ignore)
    _validate_rule_ids(parser, "--check", selected_codes)
    _validate_rule_ids(parser, "--ignore", ignored_codes)
    selected_families = {
        family.strip().lower() for value in args.family for family in value.split(",")
    }
    if selected_families and selected_families - {"readme"}:
        parser.error("This release supports only the readme rule family")

    if args.metadata:
        print(json.dumps(_metadata_report(selected_codes), indent=2))
        return 0

    root = _find_project_root(Path.cwd())
    review = _run_checks(
        root,
        selected_codes=selected_codes,
        ignored_codes=ignored_codes,
    )
    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] else 0

    _print_report(review, show_all=args.show_all)
    return 1 if review["tally"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
