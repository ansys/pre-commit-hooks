# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

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
    family = "dependabot"


class DB001(Dependabot):
    ".github/dependabot.yml exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, _PATH_DEPENDABOT)


class DB002(Dependabot):
    "dependabot.yml sets version: 2"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(root, _PATH_DEPENDABOT, re.compile(r"^version:\s*2\s*$", re.M))


class DB003(Dependabot):
    "pip or uv ecosystem configured"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
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
    "github-actions ecosystem configured"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?github-actions[\"']?")
        )


class DB005(Dependabot):
    "Weekly update interval set"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        content = file_content(root, _PATH_DEPENDABOT)
        count = len(re.findall(r"interval:\s*[\"']?weekly[\"']?", content))
        if count >= 2:
            return True
        return f"⚠️ Only {count} ecosystem(s) use weekly interval (expected ≥2)."


class DB006(Dependabot):
    "Cooldown default-days: 7 configured"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r"default-days:\s*7")):
            return True
        return "⚠️ Cooldown default-days: 7 not found in dependabot.yml."


class DB007(Dependabot):
    "pip uses versioning-strategy: lockfile-only"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
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
    "pip groups all dependencies together"

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r'patterns:\s*\n\s+- ["\']?\*["\']?')):
            return True
        return '⚠️ pip groups wildcard pattern "- "*"" not found in dependabot.yml.'
