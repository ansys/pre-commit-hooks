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

"""README quality checks.

This rule set validates that the repository README follows PyAnsys
documentation standards and includes commonly expected project badges.

The checks cover:

* README availability
    - README.rst (preferred)
    - README.md (supported but not preferred)

* Badges
    - PyAnsys badge
    - PyPI badge
    - Codecov badge
    - Project license badge
    - GitHub Actions CI badge

* Content sections
    - Installation
    - Documentation
    - License
"""

from __future__ import annotations

from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

from ansys.pre_commit_hooks.quality_rules.common import (
    file_contains,
    file_content,
    file_exists,
)

__all__ = [
    "README",
    "RM000",
    "RM001",
    "RM002",
    "RM003",
    "RM004",
    "RM005",
    "RM006",
    "RM007",
    "RM008",
]

# Badge presence patterns, compiled once and reused across checks.
_PYANSYS_BADGE = re.compile(
    r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys",
    re.IGNORECASE,
)
_PYPI_BADGE = re.compile(
    r"img\.shields\.io[^)\"']*pypi|pypi\.org/project[^)\"']*badge|badge\.fury\.io/py",
    re.IGNORECASE,
)
_CODECOV_BADGE = re.compile(r"codecov\.io[^)\"']*badge|badge\.svg[^)\"']*codecov", re.IGNORECASE)
_GH_CI_BADGE = re.compile(
    r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg", re.IGNORECASE
)

# Content section patterns.
_INSTALL_SECTION = re.compile(r"install", re.IGNORECASE)
_DOCUMENTATION_SECTION = re.compile(r"documentation", re.IGNORECASE)
_LICENSE_SECTION = re.compile(r"license", re.IGNORECASE)

# Maps a project license to the token expected in its README badge.
_BADGE_IDENTIFIERS = {
    "Apache-2.0": r"apache(?:[-_% ]?2(?:[._-]?0)?)?",
    "MIT": r"mit",
    "BSD-2-Clause": r"bsd[-_ ]?2[-_ ]?clause",
    "BSD-3-Clause": r"bsd[-_ ]?3[-_ ]?clause",
}

# Recognizes a normalized license identifier from declared license text.
_LICENSE_IDENTIFIERS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bMIT(?: License)?\b", re.IGNORECASE), "MIT"),
    (re.compile(r"Apache License(?:,| )? Version 2\.0|Apache-2\.0", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"BSD[-_ ]?2[-_ ]?Clause", re.IGNORECASE), "BSD-2-Clause"),
    (re.compile(r"BSD[-_ ]?3[-_ ]?Clause", re.IGNORECASE), "BSD-3-Clause"),
)


def _declared_license_text(project: object, root: Path) -> str | None:
    """Return the license text declared in the ``[project]`` table, if any."""
    if not isinstance(project, dict):
        return None

    value = project.get("license")
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"].strip()
        if isinstance(value.get("file"), str):
            return file_content(root, value["file"])
    return None


def _project_license(root: Path) -> str | None:
    """Return the project license identifier declared in ``pyproject.toml``."""
    if not file_exists(root, "pyproject.toml"):
        return None

    try:
        metadata = tomllib.loads(file_content(root, "pyproject.toml"))
    except (TypeError, ValueError):
        return None

    license_text = _declared_license_text(metadata.get("project"), root)
    if license_text is None:
        return None

    for pattern, identifier in _LICENSE_IDENTIFIERS:
        if pattern.search(license_text):
            return identifier
    return license_text


def _badge_result(
    root: Path, readme_path: str | None, pattern: re.Pattern, label: str
) -> bool | None | str:
    """Return the result for a README badge-presence check."""
    if not readme_path:
        return None
    if file_contains(root, readme_path, pattern):
        return True
    return f"WARN: {label} not found in {readme_path}."


def _section_result(root: Path, readme_path: str | None, pattern: re.Pattern) -> bool | None:
    """Return whether a README content section is present."""
    if not readme_path:
        return None
    return file_contains(root, readme_path, pattern)


class README:
    """README rule family."""

    family = "readme"


class RM000(README):
    """README file exists."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the repository has a supported README file."""
        if readme_path == "README.rst":
            return True
        if readme_path == "README.md":
            return "WARN: README.md found — PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    """README has a PyAnsys badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyAnsys badge."""
        return _badge_result(root, readme_path, _PYANSYS_BADGE, "PyAnsys badge image")


class RM002(README):
    """README has a PyPI badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyPI badge."""
        return _badge_result(root, readme_path, _PYPI_BADGE, "PyPI badge image")


class RM003(README):
    """README has a Codecov badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a Codecov badge."""
        return _badge_result(root, readme_path, _CODECOV_BADGE, "Codecov badge image")


class RM004(README):
    """README has a license badge matching project metadata."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README license badge matches project metadata."""
        if not readme_path:
            return None

        identifier = _project_license(root)
        if identifier is None:
            return None

        term = _BADGE_IDENTIFIERS.get(identifier, re.escape(identifier))
        pattern = re.compile(
            rf"(?:img\.)?shields\.io[^)\"']*{term}|{term}[^)\"']*license",
            re.IGNORECASE,
        )
        if file_contains(root, readme_path, pattern):
            return True
        return (
            f"WARN: {identifier} license badge image not found or does not "
            f"match project metadata in {readme_path}."
        )


class RM005(README):
    """README has a GH-CI badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a GitHub Actions badge."""
        return _badge_result(root, readme_path, _GH_CI_BADGE, "GH-CI workflow badge.svg URL")


class RM006(README):
    """README has an installation section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README mentions installation instructions."""
        return _section_result(root, readme_path, _INSTALL_SECTION)


class RM007(README):
    """README has a documentation section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README contains a documentation section."""
        return _section_result(root, readme_path, _DOCUMENTATION_SECTION)


class RM008(README):
    """README has a license section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README contains a license section."""
        return _section_result(root, readme_path, _LICENSE_SECTION)
