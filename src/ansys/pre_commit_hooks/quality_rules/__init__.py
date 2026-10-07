# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

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
