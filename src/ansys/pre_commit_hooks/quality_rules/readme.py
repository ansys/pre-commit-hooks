# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""README checks."""

from __future__ import annotations

import re

from .common import file_contains

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
    family = "readme"


class RM000(README):
    "README file exists"

    @staticmethod
    def check(root, readme_path: str | None) -> bool | str:
        if readme_path == "README.rst":
            return True
        if readme_path == "README.md":
            return "⚠️ README.md found — PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    "README has PyAnsys badge"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(
                r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys",
                re.I,
            ),
        ):
            return True
        return f"⚠️ PyAnsys badge image not found in {readme_path}."


class RM002(README):
    "README has PyPI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
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
    "README has Codecov badge"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
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
    "README has MIT license badge"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
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
    "README has GH-CI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
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
    "README has Installation section"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"install", re.I))


class RM007(README):
    "README has Documentation section"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"documentation", re.I))


class RM008(README):
    "README has License section"

    requires = {"RM000"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"license", re.I))
