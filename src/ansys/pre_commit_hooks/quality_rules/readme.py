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

"""README quality checks."""

from __future__ import annotations

from pathlib import Path
import re

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


def _project_license(root: Path) -> str | None:
    """Read a project license identifier or common license text from pyproject metadata."""
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
            return "WARN: README.md found; README.rst is preferred."
        return False


class RM001(README):
    """README has a PyAnsys badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyAnsys badge."""
        if not readme_path:
            return None
        pattern = re.compile(
            r"badge\.svg[^)\"']*pyansys|"
            r"pyansys[^)\"']*badge\.svg|"
            r"img\.shields\.io[^)\"']*pyansys",
            re.IGNORECASE,
        )
        return (
            True
            if file_contains(root, readme_path, pattern)
            else (f"WARN: PyAnsys badge image not found in {readme_path}.")
        )


class RM002(README):
    """README has a PyPI badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyPI badge."""
        if not readme_path:
            return None
        pattern = re.compile(
            r"img\.shields\.io[^)\"']*pypi|"
            r"pypi\.org/project[^)\"']*badge|"
            r"badge\.fury\.io/py",
            re.IGNORECASE,
        )
        return (
            True
            if file_contains(root, readme_path, pattern)
            else (f"WARN: PyPI badge image not found in {readme_path}.")
        )


class RM003(README):
    """README has a Codecov badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a Codecov badge."""
        if not readme_path:
            return None
        pattern = re.compile(
            r"codecov\.io[^)\"']*badge|badge\.svg[^)\"']*codecov",
            re.IGNORECASE,
        )
        return (
            True
            if file_contains(root, readme_path, pattern)
            else (f"WARN: Codecov badge image not found in {readme_path}.")
        )


class RM004(README):
    """README has a license badge matching project metadata."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README license badge matches project metadata."""
        if not readme_path:
            return None
        identifier = _project_license(root)
        if not identifier:
            return None

        badge_terms = {
            "Apache-2.0": r"apache(?:[-_% ]?2(?:[._-]?0)?)?",
            "MIT": r"mit",
            "BSD-2-Clause": r"bsd[-_ ]?2[-_ ]?clause",
            "BSD-3-Clause": r"bsd[-_ ]?3[-_ ]?clause",
        }
        license_pattern = badge_terms.get(identifier, re.escape(identifier))
        pattern = re.compile(
            rf"(?:img\.)?shields\.io[^)\"']*{license_pattern}|"
            rf"{license_pattern}[^)\"']*license",
            re.IGNORECASE,
        )
        if file_contains(root, readme_path, pattern):
            return True
        return (
            f"WARN: {identifier} license badge image not found or does not "
            f"match project metadata in {readme_path}."
        )


class RM005(README):
    """README has a GitHub Actions badge."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a GitHub Actions badge."""
        if not readme_path:
            return None
        pattern = re.compile(
            r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg",
            re.IGNORECASE,
        )
        return (
            True
            if file_contains(root, readme_path, pattern)
            else (f"WARN: GitHub Actions badge URL not found in {readme_path}.")
        )


class RM006(README):
    """README has an installation section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README mentions installation instructions."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"install", re.IGNORECASE))


class RM007(README):
    """README has a documentation section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README contains a documentation section."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"documentation", re.IGNORECASE))


class RM008(README):
    """README has a license section."""

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | None:
        """Return whether the README contains a license section."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"license", re.IGNORECASE))
