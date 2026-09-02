# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""MCP release readiness checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists, wf_content

__all__ = ["MCP", "MCP001", "MCP002", "MCP003", "MCP004", "MCP005", "MCP006", "MCP007"]


class MCP:
    family = "mcp"


class MCP001(MCP):
    "Core governance files all present"

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        required = [
            "LICENSE",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            ".github/CODEOWNERS",
        ]
        missing = [p for p in required if not file_exists(root, p)]
        return True if not missing else f"Missing: {', '.join(missing)}"


class MCP002(MCP):
    "CI/CD workflows all present"

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        workflows = [
            ".github/workflows/ci_cd_main.yml",
            ".github/workflows/ci_cd_pr.yml",
            ".github/workflows/ci_cd_release.yml",
        ]
        missing = [p for p in workflows if not file_exists(root, p)]
        return True if not missing else f"Missing: {', '.join(missing)}"


class MCP003(MCP):
    "tests job wired in PR workflow"

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return bool(re.search(r"tests|pytest", content, re.I))


class MCP004(MCP):
    "doc-build job present in PR workflow"

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return "doc-build" in content


class MCP005(MCP):
    "README and docs metadata aligned"

    @staticmethod
    def check(root, is_mcp: bool, readme_path: str | None) -> bool | None | str:
        if not is_mcp:
            return None
        if not file_exists(root, "pyproject.toml"):
            return None
        if not readme_path:
            return False
        filename = readme_path.split("/")[-1]
        if not file_contains(root, "pyproject.toml", filename):
            return f"pyproject.toml does not reference {filename} as readme."
        if readme_path == "README.md":
            return "⚠️ README.md found — PyAnsys preferred format is README.rst."
        return True


class MCP006(MCP):
    "No TODO/FIXME in doc/source/index.rst"

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return not file_contains(root, "doc/source/index.rst", re.compile(r"TODO|FIXME"))


class MCP007(MCP):
    "Security checks not bypassed"

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, pr_content = wf_content(root, "pr", workflow_map)
        _, rel_content = wf_content(root, "release", workflow_map)
        combined = pr_content + rel_content
        if not combined.strip():
            return None
        return not bool(re.search(r"--no-verify|skip.*security|disable.*scan", combined, re.I))
