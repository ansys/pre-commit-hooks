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

"""MCP release readiness checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists, wf_content

__all__ = ["MCP", "MCP001", "MCP002", "MCP003", "MCP004", "MCP005", "MCP006", "MCP007"]


class MCP:
    """MCP release readiness rule family."""

    family = "mcp"


class MCP001(MCP):
    """Core governance files are all present."""

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        """Return whether the required governance files exist for an MCP project."""
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
    """All CI/CD workflow files are present."""

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        """Return whether the canonical workflow files are present for an MCP project."""
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
    """The PR workflow wires in a tests job."""

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        """Return whether the PR workflow includes pytest or a test job."""
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return bool(re.search(r"tests|pytest", content, re.I))


class MCP004(MCP):
    """The PR workflow includes a doc-build job."""

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        """Return whether the PR workflow includes doc-build."""
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return "doc-build" in content


class MCP005(MCP):
    """README and docs metadata are aligned."""

    @staticmethod
    def check(root, is_mcp: bool, readme_path: str | None) -> bool | None | str:
        """Return whether the README metadata in pyproject.toml matches the repository README."""
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
    """No TODO or FIXME markers appear in the docs index."""

    @staticmethod
    def check(root, is_mcp: bool) -> bool | None:
        """Return whether the documentation landing page is free of TODO and FIXME markers."""
        if not is_mcp:
            return None
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return not file_contains(root, "doc/source/index.rst", re.compile(r"TODO|FIXME"))


class MCP007(MCP):
    """Security checks are not bypassed."""

    @staticmethod
    def check(root, is_mcp: bool, workflow_map: dict) -> bool | None:
        """Return whether the workflows do not disable or skip security validation."""
        if not is_mcp:
            return None
        _, pr_content = wf_content(root, "pr", workflow_map)
        _, rel_content = wf_content(root, "release", workflow_map)
        combined = pr_content + rel_content
        if not combined.strip():
            return None
        return not bool(re.search(r"--no-verify|skip.*security|disable.*scan", combined, re.I))
