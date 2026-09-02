# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Project metadata checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists, file_content

__all__ = [
    "ProjectMetadata",
    "PM001",
    "PM002",
    "PM003",
    "PM004",
    "PM005",
    "PM006",
    "PM007",
    "PM008",
    "PM009",
    "PM010",
    "PM011",
]


class ProjectMetadata:
    family = "project_metadata"


class PM001(ProjectMetadata):
    "AUTHORS exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "AUTHORS")


class PM002(ProjectMetadata):
    "CHANGELOG.md exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "CHANGELOG.md")


class PM003(ProjectMetadata):
    "CODE_OF_CONDUCT.md exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "CODE_OF_CONDUCT.md")


class PM004(ProjectMetadata):
    "CONTRIBUTING.md exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "CONTRIBUTING.md")


class PM005(ProjectMetadata):
    "CONTRIBUTORS.md exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "CONTRIBUTORS.md")


class PM006(ProjectMetadata):
    "LICENSE exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "LICENSE")


class PM007(ProjectMetadata):
    "README exists (.rst preferred)"

    @staticmethod
    def check(root, readme_path: str | None) -> bool | str:
        if readme_path is None:
            return False
        if readme_path == "README.md":
            return "⚠️ README.md found — README.rst is the preferred format."
        return True


class PM008(ProjectMetadata):
    "SECURITY.md exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "SECURITY.md")


class PM009(ProjectMetadata):
    ".github/CODEOWNERS exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, ".github/CODEOWNERS")


class PM010(ProjectMetadata):
    "pyproject.toml references README file"

    requires = {"PM007"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", content):
            m = re.search(
                r"\[tool\.poetry\][\s\S]*?readme\s*=\s*[\"']([^\"']+)[\"']",
                content,
                re.M,
            )
            if m:
                return True
            return False
        rm = readme_path or "README.rst"
        if rm in content:
            return True
        if "README" in content:
            return "⚠️ readme key found but exact README filename not confirmed."
        return False


class PM011(ProjectMetadata):
    "pyproject.toml references LICENSE file"

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "pyproject.toml"):
            return None
        c = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", c):
            return bool(re.search(r"\[tool\.poetry\][\s\S]*?license\s*=", c, re.M))
        return bool(
            re.search(r"license-files\s*=", c)
            or re.search(r"license\s*=\s*\{[^}]*file", c)
            or re.search(r'license\s*=\s*["\']LICENSE["\']', c)
        )
