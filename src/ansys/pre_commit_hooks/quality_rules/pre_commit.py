# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Pre-commit configuration checks."""

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


class PreCommit:
    family = "pre_commit"


class PC001(PreCommit):
    ".pre-commit-config.yaml exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, ".pre-commit-config.yaml")


class PC002(PreCommit):
    "ruff-pre-commit configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "ruff-pre-commit")


class PC003(PreCommit):
    "zizmor configured with --pedantic"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        has_zizmor = file_contains(root, ".pre-commit-config.yaml", "zizmor")
        has_pedantic = file_contains(root, ".pre-commit-config.yaml", "--pedantic")
        if not has_zizmor:
            return False
        if not has_pedantic:
            return "⚠️ zizmor found but --pedantic flag not set."
        return True


class PC004(PreCommit):
    "blacken-docs configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "blacken-docs")


class PC005(PreCommit):
    "codespell configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "codespell")


class PC006(PreCommit):
    "ansys/pre-commit-hooks configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "ansys/pre-commit-hooks")


class PC007(PreCommit):
    "google/yamlfmt configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "yamlfmt")


class PC008(PreCommit):
    "pyright configured"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "pyright")


class PC009(PreCommit):
    "autofix_prs: true enabled"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        if file_contains(root, ".pre-commit-config.yaml", "autofix_prs: true"):
            return True
        return "⚠️ autofix_prs: true not set in ci: block."


class PC010(PreCommit):
    "autoupdate_schedule: weekly"

    requires = {"PC001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        if file_contains(
            root, ".pre-commit-config.yaml", re.compile(r"autoupdate_schedule:\s*weekly")
        ):
            return True
        return "⚠️ autoupdate_schedule: weekly not found."
