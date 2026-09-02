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

"""README checks."""

from __future__ import annotations

import re

from ansys.pre_commit_hooks.quality_rules.common import file_contains

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


class README:
    """README rule family."""

    family = "readme"


class RM000(README):
    """README file exists."""

    @staticmethod
    def check(root, readme_path: str | None) -> bool | str:
        """Return whether the repository has a supported README file."""
        if readme_path == "README.rst":
            return True
        if readme_path == "README.md":
            return "⚠️ README.md found — PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    """README has a PyAnsys badge."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyAnsys badge."""
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(
                r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys",  # noqa: E501
                re.I,
            ),
        ):
            return True
        return f"⚠️ PyAnsys badge image not found in {readme_path}."


class RM002(README):
    """README has a PyPI badge."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a PyPI badge."""
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(
                r"img\.shields\.io[^)\"']*pypi|pypi\.org/project[^)\"']*badge|badge\.fury\.io/py",
                re.I,
            ),
        ):
            return True
        return f"⚠️ PyPI badge image not found in {readme_path}."


class RM003(README):
    """README has a Codecov badge."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a Codecov badge."""
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"codecov\.io[^)\"']*badge|badge\.svg[^)\"']*codecov", re.I),
        ):
            return True
        return f"⚠️ Codecov badge image not found in {readme_path}."


class RM004(README):
    """README has an MIT license badge."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains an MIT license badge."""
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"shields\.io[^)\"']*mit|img\.shields\.io[^)\"']*license", re.I),
        ):
            return True
        return f"⚠️ MIT license badge image not found in {readme_path}."


class RM005(README):
    """README has a GH-CI badge."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether the README contains a GitHub Actions badge."""
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg", re.I),
        ):
            return True
        return f"⚠️ GH-CI workflow badge.svg URL not found in {readme_path}."


class RM006(README):
    """README has an installation section."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        """Return whether the README mentions installation instructions."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"install", re.I))


class RM007(README):
    """README has a documentation section."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        """Return whether the README contains a documentation section."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"documentation", re.I))


class RM008(README):
    """README has a license section."""

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        """Return whether the README contains a license section."""
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"license", re.I))
