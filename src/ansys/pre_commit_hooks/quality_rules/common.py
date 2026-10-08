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


def file_contains(root: Path, path: str, pattern: re.Pattern) -> bool:
    """Return whether a file's contents match the given regular expression."""
    return bool(pattern.search(file_content(root, path)))


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


def normalize_check_result(raw: bool | str, check_obj: Any) -> tuple[str, str]:
    """Normalize a raw README rule result into a status and display message."""
    if raw is True:
        return "pass", ""
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
