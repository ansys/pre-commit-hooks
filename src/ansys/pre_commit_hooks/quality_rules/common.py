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
from typing import ClassVar, Final, Literal, Protocol, TypeAlias

__all__ = [
    "_first_doc_line",
    "ERROR",
    "file_content",
    "file_exists",
    "normalize_check_result",
    "PASSED",
    "readme_path",
    "RuleCheckResult",
    "RuleStatus",
    "WARNING",
]

RuleCheckResult: TypeAlias = bool | str
RuleStatus: TypeAlias = Literal["PASSED", "WARNING", "ERROR"]
PASSED: Final[RuleStatus] = "PASSED"
WARNING: Final[RuleStatus] = "WARNING"
ERROR: Final[RuleStatus] = "ERROR"


class _QualityRule(Protocol):
    """Interface implemented by every quality-report rule."""

    family: ClassVar[str]

    def check(self, repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate the rule for a repository.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, or ``None`` when no supported README exists.

        Returns
        -------
        bool or str
            Raw rule result consumed by ``normalize_check_result``.
        """
        ...


def _repository_file(repository_root: Path, relative_path: str) -> Path | None:
    """Resolve a file path that remains within a repository.

    Parameters
    ----------
    repository_root : pathlib.Path
        Root directory that contains the file.
    relative_path : str
        File path relative to ``repository_root``.

    Returns
    -------
    pathlib.Path or None
        Resolved file path, or ``None`` if the path escapes the repository or
        cannot be resolved.
    """
    try:
        resolved_repository_root = repository_root.resolve()
        resolved_file = resolved_repository_root.joinpath(relative_path).resolve()
        resolved_file.relative_to(resolved_repository_root)
    except (OSError, RuntimeError, ValueError):
        return None
    return resolved_file


def file_exists(repository_root: Path, relative_path: str) -> bool:
    """Return whether a repository file exists.

    Parameters
    ----------
    repository_root : pathlib.Path
        Root directory that contains the file.
    relative_path : str
        File path relative to ``repository_root``.

    Returns
    -------
    bool
        ``True`` when the path resolves to a regular file within the
        repository, otherwise ``False``.
    """
    resolved_file = _repository_file(repository_root, relative_path)
    if resolved_file is None:
        return False
    try:
        return resolved_file.is_file()
    except OSError:
        return False


def file_content(repository_root: Path, relative_path: str) -> str | None:
    """Read a UTF-8 repository file without allowing path traversal.

    Parameters
    ----------
    repository_root : pathlib.Path
        Root directory that contains the file.
    relative_path : str
        File path relative to ``repository_root``.

    Returns
    -------
    str or None
        File content, or ``None`` when the path is unsafe or the file cannot
        be read as UTF-8.
    """
    resolved_file = _repository_file(repository_root, relative_path)
    if resolved_file is None:
        return None
    try:
        return resolved_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError):
        return None


def readme_path(repository_root: Path) -> str | None:
    """Return the preferred README path for a repository.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    str or None
        ``"README.rst"`` when present, otherwise ``"README.md"`` when
        present. ``None`` is returned when neither file exists.
    """
    if file_exists(repository_root, "README.rst"):
        return "README.rst"
    if file_exists(repository_root, "README.md"):
        return "README.md"
    return None


def _first_doc_line(rule: _QualityRule) -> str:
    """Return the first non-empty line of a rule check docstring.

    Parameters
    ----------
    rule : _QualityRule
        Rule whose ``check`` method provides the docstring.

    Returns
    -------
    str
        First non-empty docstring line, or an empty string when the method has
        no docstring content.
    """
    docstring_lines = [
        line.strip() for line in (rule.check.__doc__ or "").splitlines() if line.strip()
    ]
    return docstring_lines[0] if docstring_lines else ""


def normalize_check_result(raw_result: object, rule: _QualityRule) -> tuple[RuleStatus, str]:
    """Normalize a rule return value into a public status and detail.

    Parameters
    ----------
    raw_result : object
        Value returned by a rule check.
    rule : _QualityRule
        Rule that produced ``raw_result``.

    Returns
    -------
    tuple[RuleStatus, str]
        Public status and its display detail. Invalid return values are
        converted to ``ERROR``.
    """
    if raw_result is True:
        return PASSED, ""
    if isinstance(raw_result, str):
        if raw_result.startswith("ERROR: "):
            return ERROR, raw_result.removeprefix("ERROR: ")
        if raw_result.startswith("WARNING: "):
            return WARNING, raw_result.removeprefix("WARNING: ")
        return ERROR, f"Invalid check result: {raw_result!r}"
    if raw_result is False:
        rule_description = (type(rule).__doc__ or "").strip().splitlines()
        return ERROR, rule_description[0].strip() if rule_description else ""
    return ERROR, f"Invalid check result type: {type(raw_result).__name__}"
