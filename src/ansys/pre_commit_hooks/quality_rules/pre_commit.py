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

"""Pre-commit configuration checks.

This rule set validates the presence of a standard PyAnsys pre-commit
configuration and verifies that the following tools and hooks are configured:

* ruff-pre-commit
* zizmor (--pedantic)
* blacken-docs
* codespell
* ansys/pre-commit-hooks
* yamlfmt
* pyright

The checks also verify repository maintenance settings such as:

* autofix_prs: true
* autoupdate_schedule: weekly
"""

from __future__ import annotations

import re

from .common import file_contains, file_exists

__all__ = [
    "PreCommit",
    "PC001",
    "PC002",
    "PC003",
    "PC004",
    "PC005",
    "PC006",
    "PC007",
    "PC008",
    "PC009",
    "PC010",
]

_PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"


class PreCommit:
    """Pre-commit rule family."""

    family = "pre_commit"


class PC001(PreCommit):
    """The .pre-commit-config.yaml file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the pre-commit configuration exists."""
        return file_exists(root, _PRE_COMMIT_CONFIG)


class PC002(PreCommit):
    """Ruff-pre-commit is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether ruff-pre-commit is configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(root, _PRE_COMMIT_CONFIG, "ruff-pre-commit")


class PC003(PreCommit):
    """Zizmor is configured with the --pedantic flag."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether zizmor is configured with the pedantic option."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        has_zizmor = file_contains(
            root,
            _PRE_COMMIT_CONFIG,
            "zizmor",
        )

        has_pedantic = file_contains(
            root,
            _PRE_COMMIT_CONFIG,
            "--pedantic",
        )

        if not has_zizmor:
            return False

        if not has_pedantic:
            return "⚠️ zizmor found but --pedantic flag not set."

        return True


class PC004(PreCommit):
    """Blacken-docs is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether blacken-docs is configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(root, _PRE_COMMIT_CONFIG, "blacken-docs")


class PC005(PreCommit):
    """Codespell is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether codespell is configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(root, _PRE_COMMIT_CONFIG, "codespell")


class PC006(PreCommit):
    """Ansys/pre-commit-hooks is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the shared Ansys pre-commit hooks are configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(
            root,
            _PRE_COMMIT_CONFIG,
            "ansys/pre-commit-hooks",
        )


class PC007(PreCommit):
    """Google/yamlfmt is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether yamlfmt is configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(root, _PRE_COMMIT_CONFIG, "yamlfmt")


class PC008(PreCommit):
    """Pyright is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether pyright is configured."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        return file_contains(root, _PRE_COMMIT_CONFIG, "pyright")


class PC009(PreCommit):
    """Autofix_prs: true is enabled."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether automatic pull-request fixes are enabled."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        if file_contains(
            root,
            _PRE_COMMIT_CONFIG,
            "autofix_prs: true",
        ):
            return True

        return "⚠️ autofix_prs: true not set in ci: block."


class PC010(PreCommit):
    """Autoupdate_schedule: weekly is configured."""

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the pre-commit autoupdate schedule is weekly."""
        if not file_exists(root, _PRE_COMMIT_CONFIG):
            return None

        if file_contains(
            root,
            _PRE_COMMIT_CONFIG,
            re.compile(
                r"autoupdate_schedule:\s*weekly",
            ),
        ):
            return True

        return "⚠️ autoupdate_schedule: weekly not found."
