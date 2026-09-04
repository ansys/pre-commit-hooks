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

"""Security checks.

This rule set validates repository security configurations and
secure-development best practices.

The checks cover:

* Zizmor configuration
    - .github/zizmor.yml exists
    - secrets-outside-env rule enabled

* Secret scanning
    - gitleaks pre-commit hook configured

* GitHub Actions security
    - Actions are pinned to full commit SHAs

* Security policy
    - SECURITY.md discourages public disclosure of vulnerabilities
"""

from __future__ import annotations

import re

from ansys.pre_commit_hooks.quality_rules.common import (
    checked_contains,
    file_contains,
    file_exists,
    wf_content,
)

__all__ = [
    "Security",
    "SEC001",
    "SEC002",
    "SEC003",
    "SEC004",
    "SEC005",
]

_ZIZMOR_CONFIG = ".github/zizmor.yml"
_PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
_SECURITY_POLICY = "SECURITY.md"


class Security:
    """Security rule family."""

    family = "security"


class SEC001(Security):
    """The .github/zizmor.yml file exists."""

    @staticmethod
    def check(root) -> bool | str:
        """Return whether the Zizmor configuration is present."""
        if file_exists(root, _ZIZMOR_CONFIG):
            return True

        return "⚠️ .github/zizmor.yml not found " "— optional but recommended."


class SEC002(Security):
    """The zizmor config includes the secrets-outside-env rule."""

    requires = {"SEC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Zizmor configuration enables the secrets-outside-env rule."""
        return checked_contains(
            root,
            _ZIZMOR_CONFIG,
            "secrets-outside-env",
        )


class SEC003(Security):
    """The gitleaks hook is configured."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the pre-commit configuration includes gitleaks."""
        return checked_contains(
            root,
            _PRE_COMMIT_CONFIG,
            "gitleaks",
        )


class SEC004(Security):
    """Workflows pin action SHAs."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR workflow pins GitHub Actions to full commit SHAs."""
        _, content = wf_content(
            root,
            "pr",
            workflow_map,
        )

        if not content:
            return None

        uses_lines = re.findall(r"^\s*-?\s*uses:\s*([^\n#]+)", content, re.MULTILINE)
        if not uses_lines:
            return None

        pinned = 0
        for uses in uses_lines:
            value = uses.strip()
            if re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@(?:[0-9a-fA-F]{40}|[A-Fa-f0-9]{40})", value
            ):
                pinned += 1

        if pinned == len(uses_lines):
            return True

        return (
            "⚠️ Some GitHub Actions in the PR workflow are not pinned to full commit SHAs. "
            "Use full commit SHAs for all actions."
        )


class SEC005(Security):
    """SECURITY.md discourages public issue reporting."""

    requires = {"PM008"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the security policy discourages public issue reporting."""
        if not file_exists(root, _SECURITY_POLICY):
            return None

        if file_contains(
            root,
            _SECURITY_POLICY,
            re.compile(
                r"do not|don't|please don",
                re.IGNORECASE,
            ),
        ):
            return True

        return "⚠️ SECURITY.md may not clearly discourage " "public issue reporting."
