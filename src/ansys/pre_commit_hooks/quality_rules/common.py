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
from typing import Any, Final, Literal, TypeAlias

__all__ = [
    "_first_doc_line",
    "ERROR",
    "file_content",
    "file_exists",
    "normalize_check_result",
    "PASSED",
    "readme_path",
    "RuleStatus",
    "WARNING",
]

RuleStatus: TypeAlias = Literal["PASSED", "WARNING", "ERROR"]
PASSED: Final[RuleStatus] = "PASSED"
WARNING: Final[RuleStatus] = "WARNING"
ERROR: Final[RuleStatus] = "ERROR"


def _repository_file(root: Path, path: str) -> Path | None:
    """Return a resolved repository file path without allowing path traversal."""
    try:
        resolved_root = root.resolve()
        resolved_path = resolved_root.joinpath(path).resolve()
        resolved_path.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved_path


def file_exists(root: Path, path: str) -> bool:
    """Return whether a file exists under the repository root."""
    resolved_path = _repository_file(root, path)
    if resolved_path is None:
        return False
    try:
        return resolved_path.is_file()
    except OSError:
        return False


def file_content(root: Path, path: str) -> str | None:
    """Return repository file text, or ``None`` when it cannot be read safely."""
    resolved_path = _repository_file(root, path)
    if resolved_path is None:
        return None
    try:
        return resolved_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None


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


def normalize_check_result(raw: bool | str, check_obj: Any) -> tuple[RuleStatus, str]:
    """Normalize a raw README rule result into a status and display message."""
    if raw is True:
        return PASSED, ""
    if isinstance(raw, str):
        if raw.startswith("ERROR: "):
            return ERROR, raw.removeprefix("ERROR: ")
        if raw.startswith("WARNING: "):
            return WARNING, raw.removeprefix("WARNING: ")
        return ERROR, f"Invalid check result: {raw!r}"
    if raw is False:
        description = (type(check_obj).__doc__ or "").strip().splitlines()
        return ERROR, description[0].strip() if description else ""
    return ERROR, f"Invalid check result type: {type(raw).__name__}"
