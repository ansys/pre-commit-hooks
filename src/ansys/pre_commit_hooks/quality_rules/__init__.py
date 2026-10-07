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

"""Initial README-only quality-check registry."""

from ansys.pre_commit_hooks.quality_rules.readme import (
    README,
    RM000,
    RM001,
    RM002,
    RM003,
    RM004,
    RM005,
    RM006,
    RM007,
    RM008,
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
    "repo_review_checks",
    "repo_review_families",
]

QUALITY_RULES = (RM000, RM001, RM002, RM003, RM004, RM005, RM006, RM007, RM008)


def repo_review_checks() -> dict[str, object]:
    """Return the supported README checks keyed by rule ID."""
    return {rule.__name__: rule() for rule in QUALITY_RULES}


def repo_review_families() -> dict[str, dict[str, str | int]]:
    """Return metadata for the README rule family."""
    return {"readme": {"name": "README", "order": 10}}
