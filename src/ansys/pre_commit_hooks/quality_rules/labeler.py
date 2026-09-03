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
"""Labeler checks.

This rule set validates the repository label configuration used for issue and
pull request triage.

The checks cover:

* labeler configuration presence
* labels.yml presence
* bug label definition
* enhancement label definition
* documentation label definition
"""

from __future__ import annotations

from .common import file_contains, file_exists

__all__ = [
    "Labeler",
    "LB001",
    "LB002",
    "LB003",
    "LB004",
    "LB005",
]


class Labeler:
    """Labeler rule family."""

    family = "labeler"


class LB001(Labeler):
    """The .github/labeler.yml file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the labeler configuration exists."""
        return file_exists(root, ".github/labeler.yml")


class LB002(Labeler):
    """The .github/labels.yml file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the labels configuration exists."""
        return file_exists(root, ".github/labels.yml")


class LB003(Labeler):
    """Labels.yml has a bug label."""

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the bug label is present."""
        if not file_exists(root, ".github/labels.yml"):
            return None

        return file_contains(root, ".github/labels.yml", "bug")


class LB004(Labeler):
    """Labels.yml has an enhancement label."""

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the enhancement label is present."""
        if not file_exists(root, ".github/labels.yml"):
            return None

        return file_contains(root, ".github/labels.yml", "enhancement")


class LB005(Labeler):
    """Labels.yml has a documentation label."""

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the documentation label is present."""
        if not file_exists(root, ".github/labels.yml"):
            return None

        return file_contains(root, ".github/labels.yml", "documentation")
