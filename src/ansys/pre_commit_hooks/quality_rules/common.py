# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Shared helpers for the initial README quality checks."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

__all__ = [
    "_first_doc_line",
    "file_contains",
    "file_content",
    "file_exists",
    "normalize_check_result",
    "readme_path",
]


def file_exists(root: Path, path: str) -> bool:
    """Return whether a file exists under the repository root."""
    return root.joinpath(path).is_file()


def file_content(root: Path, path: str) -> str:
    """Return file text, or an empty string when it cannot be read."""
    try:
        return root.joinpath(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return ""


def file_contains(root: Path, path: str, pattern: str | re.Pattern) -> bool:
    """Return whether a file contains a literal string or regular expression."""
    content = file_content(root, path)
    if isinstance(pattern, str):
        return pattern in content
    return bool(pattern.search(content))


def readme_path(root: Path) -> str | None:
    """Return README.rst when available, otherwise README.md."""
    if file_exists(root, "README.rst"):
        return "README.rst"
    if file_exists(root, "README.md"):
        return "README.md"
    return None


def _first_doc_line(obj: Any) -> str:
    """Return the first non-empty line of an object's check docstring."""
    lines = [line.strip() for line in (obj.check.__doc__ or "").splitlines() if line.strip()]
    return lines[0] if lines else ""


def normalize_check_result(raw: bool | str | None, check_obj: Any) -> tuple[str, str]:
    """Normalize a raw README rule result into a status and display message."""
    if raw is True:
        return "pass", ""
    if raw is None:
        return "na", ""
    if isinstance(raw, str):
        if raw.startswith("FAIL: "):
            return "fail", raw.removeprefix("FAIL: ")
        if raw.startswith("WARN: "):
            return "warn", raw.removeprefix("WARN: ")
        if raw:
            return "warn", raw
        return "fail", ""
    if raw is False:
        description = (type(check_obj).__doc__ or "").strip().splitlines()
        return "fail", description[0].strip() if description else ""
    return "fail", str(raw)


def project_license(root: Path) -> str | None:
    """Read a simple SPDX-like license identifier from pyproject metadata."""
    if not file_exists(root, "pyproject.toml"):
        return None

    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 uses toml.
        import toml as tomllib

    try:
        metadata = tomllib.loads(file_content(root, "pyproject.toml"))
    except (TypeError, ValueError):
        return None
    project = metadata.get("project")
    if not isinstance(project, dict):
        return None

    license_value = project.get("license")
    if isinstance(license_value, str):
        license_text = license_value.strip()
    elif isinstance(license_value, dict) and isinstance(license_value.get("text"), str):
        license_text = license_value["text"].strip()
    elif isinstance(license_value, dict) and isinstance(license_value.get("file"), str):
        license_text = file_content(root, license_value["file"])
    else:
        return None

    if re.search(r"\bMIT(?: License)?\b", license_text, re.IGNORECASE):
        return "MIT"
    if re.search(r"Apache License(?:,| )? Version 2\.0|Apache-2\.0", license_text, re.IGNORECASE):
        return "Apache-2.0"
    if re.search(r"BSD[-_ ]?2[-_ ]?Clause", license_text, re.IGNORECASE):
        return "BSD-2-Clause"
    if re.search(r"BSD[-_ ]?3[-_ ]?Clause", license_text, re.IGNORECASE):
        return "BSD-3-Clause"
    return license_text
