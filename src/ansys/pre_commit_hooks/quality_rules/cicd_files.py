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
"""CI/CD workflow action checks.

This rule set validates the required reusable GitHub Actions used by the
repository automation policy, instead of checking canonical workflow filenames.

The checks cover the expected automation actions for branch, pull-request, and
release workflows.
"""

from __future__ import annotations

import re

from .common import all_workflows_content

__all__ = ["CICDFiles", "CI001", "CI002", "CI003"]


class CICDFiles:
    """CI/CD workflow action rule family."""

    family = "cicd_files"

    @staticmethod
    def _check_actions(root, patterns: list[str], description: str) -> bool | str:
        """Validate that all required actions are present in repo workflows."""
        content = all_workflows_content(root)

        if not content:
            return False

        missing = [
            pattern for pattern in patterns if not re.search(pattern, content, re.IGNORECASE)
        ]

        if not missing:
            return True

        return f"⚠️ Required {description} not found in workflow content: {', '.join(missing)}"


class CI001(CICDFiles):
    """The repository includes the required PR and CI automation actions."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | str:
        """Return whether the repo includes core CI actions used for PR automation."""
        return CICDFiles._check_actions(
            root,
            [
                r"ansys/actions/check-pr-title|check-pr-title",
                r"ansys/actions/code-style|code-style",
                r"ansys/actions/tests-pytest|ansys/actions/tests|\btests\b|pytest",
                r"ansys/actions/check-vulnerabilities",
                r"ansys/actions/[^\s]*label|\blabeler\b",
            ],
            "PR/CI actions",
        )


class CI002(CICDFiles):
    """The repository includes the required documentation/build actions."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | str:
        """Return whether the repo includes documentation and build automation."""
        return CICDFiles._check_actions(
            root,
            [
                r"ansys/actions/check-doc-style|doc-style",
                r"ansys/actions/doc-build|\bdoc-build\b",
                r"ansys/actions/build-wheelhouse|build-wheelhouse",
            ],
            "documentation/build actions",
        )


class CI003(CICDFiles):
    """The repository includes the required release automation actions."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | str:
        """Return whether the repo includes release automation actions."""
        return CICDFiles._check_actions(
            root,
            [
                r"ansys/actions/[^\s]*changelog|changelog-fragment",
                r"ansys/actions/release-github|update-changelog",
            ],
            "release actions",
        )
