# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Generate a PyAnsys repository quality report for the current project.

This implementation keeps the quality logic bundled in the hook repo itself so it
works in a standalone pre-commit environment without the separate
``pyansys-repo-review`` package being installed.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from io import BytesIO, StringIO
import json
import os
from pathlib import Path
from typing import Any

from ansys.pre_commit_hooks import tech_review

try:
    from importlib.resources.abc import Traversable
except ImportError:  # pragma: no cover
    from importlib.abc import Traversable

from ansys.pre_commit_hooks.quality_rules import (
    _first_doc_line,
    _interpret,
    is_mcp,
    readme_path,
    repo_review_checks,
    repo_review_families,
    workflow_map,
)

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


class MemoryTraversable(Traversable):
    """In-memory Traversable backed by a flat dict mapping path -> content."""

    def __init__(self, files: dict[str, str | None], path: str = "") -> None:
        """Initialize a virtual Traversable with a dict of file contents."""
        self._files = files
        self._path = path.strip("/")

    @property
    def name(self) -> str:
        """Return the final path component for this virtual file or directory."""
        return self._path.split("/")[-1] if self._path else ""

    def is_file(self) -> bool:
        """Return whether this virtual path resolves to a file."""
        return self._path in self._files and self._files[self._path] is not None

    def is_dir(self) -> bool:
        """Return whether this virtual path resolves to a directory."""
        if not self._path:
            return True
        prefix = self._path + "/"
        return any(key.startswith(prefix) for key in self._files)

    def iterdir(self) -> Iterator[MemoryTraversable]:
        """Yield child paths for this virtual directory."""
        prefix = (self._path + "/") if self._path else ""
        seen: set[str] = set()
        for key in self._files:
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix) :]
            child_name = rest.split("/")[0]
            if child_name and child_name not in seen:
                seen.add(child_name)
                yield MemoryTraversable(self._files, f"{prefix}{child_name}")

    def joinpath(self, *parts: str) -> MemoryTraversable:
        """Join path components under this virtual root."""
        combined = "/".join(filter(None, [self._path, *parts]))
        return MemoryTraversable(self._files, combined)

    __truediv__ = joinpath

    def open(self, mode: str = "r", encoding: str = "utf-8", **_) -> StringIO | BytesIO:
        """Open the virtual file as a text or binary stream."""
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        if "b" in mode:
            return BytesIO(content.encode(encoding))
        return StringIO(content)

    def read_bytes(self) -> bytes:
        """Read the virtual file as raw bytes."""
        return self.open("rb").read()

    def read_text(self, encoding: str = "utf-8") -> str:
        """Read the virtual file as UTF-8 text."""
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        return content

    def __repr__(self) -> str:
        """Return a string representation of the virtual path."""
        return f"MemoryTraversable({self._path!r})"

    def __str__(self) -> str:
        """Return a string representation of the virtual path."""
        return self._path


def _run_checks(files: dict[str, str | None], is_mcp_flag: bool) -> dict[str, Any]:
    """Run the package-based repo review checks against an in-memory file set."""
    root = MemoryTraversable(files)
    fixture_values = {
        "root": root,
        "package": root,
        "workflow_map": workflow_map(root),
        "readme_path": readme_path(root),
        "is_mcp": is_mcp_flag or is_mcp(root),
    }

    checks = repo_review_checks()
    families = repo_review_families()
    results = []

    for code, check_obj in checks.items():
        try:
            import inspect

            signature = inspect.signature(check_obj.check)
            kwargs = {
                key: fixture_values[key] for key in signature.parameters if key in fixture_values
            }
            raw = check_obj.check(**kwargs)
        except (AttributeError, TypeError, ValueError) as exc:  # pragma: no cover
            raw = f"⚠️ Check error: {exc}"

        status, detail = _interpret(raw, check_obj)
        results.append(
            {
                "id": code,
                "family": check_obj.family,
                "family_name": families.get(check_obj.family, {}).get("name", check_obj.family),
                "label": type(check_obj).__doc__ or code,
                "description": _first_doc_line(check_obj),
                "status": status,
                "detail": detail,
            }
        )

    tally = {"pass": 0, "fail": 0, "warn": 0, "na": 0}
    for result in results:
        tally[result["status"]] += 1

    scored = tally["pass"] + tally["fail"]
    score = round(tally["pass"] / scored * 100) if scored else 0
    return {
        "results": results,
        "tally": tally,
        "score": score,
        "workflow_map": fixture_values["workflow_map"],
        "project_metadata": {
            "build_system": {"name": "Unknown", "key": "unknown"},
            "license": None,
            "python_requires": None,
        },
    }


def _load_files(repo_root: Path) -> dict[str, str | None]:
    """Load the repository files needed by the quality report from disk."""
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


def _style_status(status: str, text: str) -> str:
    """Style a status label for console output."""
    colors = {
        "pass": "\033[32m",
        "warn": "\033[33m",
        "fail": "\033[31m",
        "na": "\033[36m",
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    return f"{color}{text}{reset}" if color else text


def _print_report(review: dict[str, Any], *, show_passes: bool = False) -> None:
    """Print the repo quality summary to stdout."""
    results = review["results"]
    tally = review["tally"]
    score = review["score"]

    print("PyAnsys quality report")
    print("=" * 24)
    print(f"Score: {score}%")
    summary = (
        f"Summary: pass={_style_status('pass', str(tally['pass']))} "
        f"fail={_style_status('fail', str(tally['fail']))} "
        f"warn={_style_status('warn', str(tally['warn']))} "
        f"na={_style_status('na', str(tally['na']))}"
    )
    print(summary)

    for item in results:
        if item["status"] == "pass" and not show_passes:
            continue
        detail = item["detail"] or ""
        label = _style_status(item["status"], item["status"].upper())
        print(f"- [{label}] {item['id']} - {item['label']}")
        if detail:
            print(f"  {detail}")


def main(argv: list[str] | None = None) -> int:
    """Run the PyAnsys repository quality report."""
    parser = argparse.ArgumentParser(description="Run the PyAnsys repository quality report.")
    parser.add_argument("--repo-root", default=".", help="Repository root to review.")
    parser.add_argument(
        "--json", action="store_true", help="Emit a JSON report instead of a text summary."
    )
    parser.add_argument(
        "--all", action="store_true", help="Show all checks, including passing ones."
    )
    parser.add_argument(
        "--fix-missing",
        action="store_true",
        help="Generate missing repository scaffolding before running the quality report.",
    )
    args, unknown = parser.parse_known_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    if args.fix_missing:
        legacy_argv: list[str] = []
        raw_argv = list(argv) if argv is not None else list(__import__("sys").argv[1:])

        idx = 0
        while idx < len(raw_argv):
            token = raw_argv[idx]
            if token in {"--repo-root", "--json", "--all", "--fix-missing"}:
                idx += 1
                if token == "--repo-root" and idx < len(raw_argv):
                    idx += 1
                continue
            legacy_argv.append(token)
            idx += 1

        if unknown:
            legacy_argv.extend(unknown)

        current_dir = Path.cwd()
        os.chdir(repo_root)
        try:
            return tech_review.main(legacy_argv)
        finally:
            os.chdir(current_dir)

    files = _load_files(repo_root)
    review = _run_checks(files, is_mcp_flag=is_mcp(MemoryTraversable(files)))

    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] else 0

    _print_report(review, show_passes=args.all)
    return 1 if review["tally"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())


def main(argv: list[str] | None = None) -> int:
    """Run the PyAnsys repository quality report."""
    parser = argparse.ArgumentParser(description="Run the PyAnsys repository quality report.")
    parser.add_argument("--repo-root", default=".", help="Repository root to review.")
    parser.add_argument(
        "--json", action="store_true", help="Emit a JSON report instead of a text summary."
    )
    parser.add_argument(
        "--all", action="store_true", help="Show all checks, including passing ones."
    )
    parser.add_argument(
        "--fix-missing",
        action="store_true",
        help="Generate missing repository scaffolding before running the quality report.",
    )
    args, unknown = parser.parse_known_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    if args.fix_missing:
        legacy_argv: list[str] = []
        raw_argv = list(argv) if argv is not None else list(__import__("sys").argv[1:])

        idx = 0
        while idx < len(raw_argv):
            token = raw_argv[idx]
            if token in {"--repo-root", "--json", "--all", "--fix-missing"}:
                idx += 1
                if token == "--repo-root" and idx < len(raw_argv):
                    idx += 1
                continue
            legacy_argv.append(token)
            idx += 1

        if unknown:
            legacy_argv.extend(unknown)

        current_dir = Path.cwd()
        os.chdir(repo_root)
        try:
            return tech_review.main(legacy_argv)
        finally:
            os.chdir(current_dir)

    files = _load_files(repo_root)
    review = _run_checks(files, is_mcp_flag=is_mcp(MemoryTraversable(files)))

    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] else 0

    _print_report(review, show_passes=args.all)
    return 1 if review["tally"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
