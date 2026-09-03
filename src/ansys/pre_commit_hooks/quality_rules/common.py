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

"""Shared helpers used by the repository quality checks."""

from __future__ import annotations

import re
from typing import Any

try:
    from importlib.resources.abc import Traversable
except ImportError:  # pragma: no cover
    from importlib.abc import Traversable

__all__ = [
    "file_exists",
    "file_content",
    "file_contains",
    "CANONICAL_WF",
    "all_workflows_content",
    "wf_content",
    "wf_label",
    "workflow_map",
    "readme_path",
    "is_mcp",
    "normalize_check_result",
    "_first_doc_line",
]


CANONICAL_WF: dict[str, str] = {
    "main": ".github/workflows/ci_cd_main.yml",
    "pr": ".github/workflows/ci_cd_pr.yml",
    "release": ".github/workflows/ci_cd_release.yml",
}


def file_exists(root: Traversable, path: str) -> bool:
    """Return whether a file exists under the repository root."""
    try:
        return root.joinpath(path).is_file()
    except (AttributeError, TypeError, ValueError):
        return False


def file_content(root: Traversable, path: str) -> str:
    """Return the text content of a file under the repository root."""
    try:
        file_path = root.joinpath(path)

        if file_path.is_file():
            return file_path.read_text(encoding="utf-8")

    except (AttributeError, OSError, TypeError, UnicodeError, ValueError):
        return ""

    return ""


def file_contains(
    root: Traversable,
    path: str,
    pattern: str | re.Pattern,
) -> bool:
    """Return whether a file contains the given string or regex pattern."""
    content = file_content(root, path)

    if not content:
        return False

    if isinstance(pattern, str):
        return pattern in content

    return bool(pattern.search(content))


def all_workflows_content(root: Traversable) -> str:
    """Return the combined content of all workflow files in the repository."""
    return _merge_all_workflows(root)


def wf_content(
    root: Traversable,
    role: str,
    workflow_map: dict,
) -> tuple[bool, str]:
    """Return the content for the workflow matching the given role."""
    canonical = CANONICAL_WF[role]

    if file_exists(root, canonical):
        return True, file_content(root, canonical)

    entry = workflow_map.get(role)

    if entry and not entry.get("is_fallback"):
        path = entry.get("path", "")
        return False, file_content(root, path) if path else ""

    return False, _merge_all_workflows(root)


def _merge_all_workflows(root: Traversable) -> str:
    """Merge the contents of all workflow files into a single string."""
    try:
        entries = [
            entry
            for entry in root.joinpath(".github/workflows").iterdir()
            if entry.name.endswith((".yml", ".yaml"))
        ]
    except (AttributeError, FileNotFoundError, OSError, TypeError):
        return ""

    parts: list[str] = []

    for entry in entries:
        try:
            content = entry.read_text(encoding="utf-8")

            if content:
                parts.append(content)

        except (AttributeError, OSError, TypeError, UnicodeError, ValueError):
            continue

    return "\n\n".join(parts)


def wf_label(role: str, workflow_map: dict) -> str:
    """Return a human-readable label for a workflow role."""
    entry = workflow_map.get(role)

    if not entry:
        return CANONICAL_WF.get(role, role)

    if entry.get("is_fallback"):
        sources = entry.get("sources", [])
        return f"{len(sources)} workflow file(s) ({', '.join(sources)})"

    return entry.get("name", role)


def workflow_map(root: Traversable) -> dict[str, dict]:
    """Classify workflow files into canonical roles for repository checks."""
    workflow_dir = root.joinpath(".github/workflows")

    try:
        entries = [
            entry for entry in workflow_dir.iterdir() if entry.name.endswith((".yml", ".yaml"))
        ]
    except (AttributeError, FileNotFoundError, OSError, TypeError):
        entries = []

    result: dict[str, dict] = {}

    for entry in entries:
        role = _classify_workflow(entry.name)

        if role != "unknown" and role not in result:
            result[role] = {
                "name": entry.name,
                "path": f".github/workflows/{entry.name}",
                "is_fallback": False,
                "sources": [entry.name],
            }

    for role in ("main", "pr", "release"):
        if role not in result and entries:
            result[role] = {
                "name": f"{len(entries)} workflow(s)",
                "path": None,
                "is_fallback": True,
                "sources": [entry.name for entry in entries],
            }

    return result


def _classify_workflow(name: str) -> str:
    """Classify a workflow filename into a canonical workflow role."""
    workflow_name = name.lower()

    if re.search(r"release|publish|deploy", workflow_name):
        return "release"

    if re.search(r"(^|[_-])pr(?:[_-]|[.]|$)|pull.?request|pull_request", workflow_name):
        return "pr"

    if re.search(
        r"main|push|branch|nightly|schedule|ci_cd_main|ci.main",
        workflow_name,
    ):
        return "main"

    if re.search(r"\bci\b|build|test", workflow_name):
        return "pr"

    return "unknown"


def readme_path(root: Traversable) -> str | None:
    """Return the preferred README filename if present."""
    if file_exists(root, "README.rst"):
        return "README.rst"

    if file_exists(root, "README.md"):
        return "README.md"

    return None


def is_mcp(root: Traversable) -> bool:
    """Return whether the repository appears to be an MCP project."""
    try:
        pyproject_text = root.joinpath("pyproject.toml").read_text()

        return bool(
            re.search(
                r"\b(fastmcp|mcp)\b",
                pyproject_text,
                re.IGNORECASE,
            )
        )

    except (AttributeError, OSError, TypeError, UnicodeError, ValueError):
        pass

    try:
        return file_exists(root, "src/server.py") or file_exists(root, "server.py")
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def _first_doc_line(obj: Any) -> str:
    """Return the first line of the check method's docstring, if present."""
    lines = [line.strip() for line in (obj.check.__doc__ or "").splitlines() if line.strip()]

    return lines[0] if lines else ""


def normalize_check_result(
    raw: bool | str | None,
    check_obj: Any | None = None,
) -> tuple[str, str]:
    """Normalize a raw rule result to the canonical status/detail contract.

    The canonical contract is intentionally simple and shared across the whole
    quality-rule package: ``pass``, ``warn``, ``fail``, and ``na`` are the only
    valid statuses.
    """
    if raw is True:
        return "pass", ""

    if raw is None:
        return "na", ""

    if isinstance(raw, str):
        if raw.startswith("⚠️ "):
            return "warn", raw.removeprefix("⚠️ ")

        if raw:
            return "warn", raw

        return "fail", ""

    if raw is False:
        if check_obj is None:
            return "fail", ""

        doc = (check_obj.check.__doc__ or "").strip()
        lines = [line.strip() for line in doc.splitlines() if line.strip()]

        detail = lines[-1] if len(lines) > 1 else (lines[0] if lines else "")

        return "fail", detail

    return "fail", str(raw)
