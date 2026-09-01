# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Generate a PyAnsys repository quality report for the current project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pyansys_review._traversable import MemoryTraversable
from pyansys_review.checks import repo_review_checks
from pyansys_review.fixtures import is_mcp, readme_path, workflow_map
from pyansys_review.server import _run_checks

_PATHS_TO_FETCH = [
    "AUTHORS",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "LICENSE",
    "README.rst",
    "README.md",
    "SECURITY.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/labeler.yml",
    ".github/labels.yml",
    ".github/zizmor.yml",
    ".github/workflows/ci_cd_main.yml",
    ".github/workflows/ci_cd_pr.yml",
    ".github/workflows/ci_cd_release.yml",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "doc/.vale.ini",
    "doc/source/index.rst",
    "doc/source/conf.py",
    "doc/styles/config/vocabularies/ANSYS/accept.txt",
    "doc/styles/config/vocabularies/ANSYS/reject.txt",
]


def _load_files(repo_root: Path) -> dict[str, str | None]:
    """Collect the repository files most relevant to the quality review."""
    files: dict[str, str | None] = {}
    for relative_path in _PATHS_TO_FETCH:
        candidate = repo_root / relative_path
        if candidate.is_file():
            files[relative_path] = candidate.read_text(encoding="utf-8", errors="replace")
        else:
            files[relative_path] = None

    workflows = repo_root / ".github" / "workflows"
    if workflows.is_dir():
        for workflow in workflows.glob("*.y*ml"):
            files[workflow.relative_to(repo_root).as_posix()] = workflow.read_text(
                encoding="utf-8", errors="replace"
            )

    return files


def _print_report(review: dict[str, Any]) -> None:
    """Print a short repo-quality summary to stdout."""
    results = review["results"]
    tally = review["tally"]
    score = review["score"]

    print("PyAnsys quality report")
    print("=" * 24)
    print(f"Score: {score}%")
    print(
        "Summary: "
        f"pass={tally['pass']} fail={tally['fail']} warn={tally['warn']} na={tally['na']}"
    )

    for item in results:
        if item["status"] == "pass":
            continue
        label = item["label"]
        detail = item["detail"] or ""
        print(f"- [{item['status'].upper()}] {item['id']} - {label}")
        if detail:
            print(f"  {detail}")


def main(argv: list[str] | None = None) -> int:
    """Run all configured PyAnsys quality checks against a repository."""
    parser = argparse.ArgumentParser(description="Run the PyAnsys repository quality report.")
    parser.add_argument("--repo-root", default=".", help="Repository root to review.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of a text summary.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    files = _load_files(repo_root)
    root = MemoryTraversable(files)
    review = _run_checks(files, is_mcp_flag=is_mcp(root))

    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] else 0

    _print_report(review)
    return 1 if review["tally"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
