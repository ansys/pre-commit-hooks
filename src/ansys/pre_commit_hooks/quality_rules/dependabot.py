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

"""Dependabot checks."""

from __future__ import annotations

import re

from .common import file_contains, file_content, file_exists

__all__ = [
    "Dependabot",
    "DB001",
    "DB002",
    "DB003",
    "DB004",
    "DB005",
    "DB006",
    "DB007",
    "DB008",
]


_PATH_DEPENDABOT = ".github/dependabot.yml"


class Dependabot:
    """Dependabot rule family."""

    family = "dependabot"


class DB001(Dependabot):
    """The .github/dependabot.yml file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the Dependabot config file exists."""
        return file_exists(root, _PATH_DEPENDABOT)


class DB002(Dependabot):
    """Dependabot.yml sets version 2."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Dependabot config uses the expected schema version."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(root, _PATH_DEPENDABOT, re.compile(r"^version:\s*2\s*$", re.M))


class DB003(Dependabot):
    """Pip or uv ecosystem is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether a supported dependency ecosystem is configured."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        has_pip = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?")
        )
        has_uv = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?")
        )
        if has_pip:
            return True
        if has_uv:
            return "⚠️ uv ecosystem configured (pip preferred for PyAnsys standard)."
        return False


class DB004(Dependabot):
    """The GitHub Actions ecosystem is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the GitHub Actions ecosystem is configured."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?github-actions[\"']?")
        )


class DB005(Dependabot):
    """A weekly update interval is set."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the weekly update interval is configured for enough ecosystems."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        content = file_content(root, _PATH_DEPENDABOT)
        count = len(re.findall(r"interval:\s*[\"']?weekly[\"']?", content))
        if count >= 2:
            return True
        return f"⚠️ Only {count} ecosystem(s) use weekly interval (expected ≥2)."


class DB006(Dependabot):
    """Cooldown default-days: 7 is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the Dependabot cooldown policy is set to seven days."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r"default-days:\s*7")):
            return True
        return "⚠️ Cooldown default-days: 7 not found in dependabot.yml."


class DB007(Dependabot):
    """Pip uses the lockfile-only versioning strategy."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether pip uses the lockfile-only versioning strategy."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        has_uv = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?")
        )
        has_pip = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?")
        )
        if has_uv and not has_pip:
            return None
        if file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"versioning-strategy:\s*[\"']?lockfile-only[\"']?")
        ):
            return True
        return "⚠️ versioning-strategy: lockfile-only not found for pip ecosystem."


class DB008(Dependabot):
    """Pip groups all dependencies together."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the pip group wildcard pattern is defined."""
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r'patterns:\s*\n\s+- ["\']?\*["\']?')):
            return True
        return '⚠️ pip groups wildcard pattern "- "*"" not found in dependabot.yml.'
