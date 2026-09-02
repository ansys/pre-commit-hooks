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

"""Security checks."""

from __future__ import annotations

import re

from ansys.pre_commit_hooks.quality_rules.common import file_contains, file_exists, wf_content

__all__ = ["Security", "SEC001", "SEC002", "SEC003", "SEC004", "SEC005"]


class Security:
    """Security rule family."""

    family = "security"


class SEC001(Security):
    """The .github/zizmor.yml file exists."""

    @staticmethod
    def check(root) -> bool | str:
        """Return whether the Zizmor config is present."""
        if file_exists(root, ".github/zizmor.yml"):
            return True
        return "⚠️ .github/zizmor.yml not found — optional but recommended."


class SEC002(Security):
    """The zizmor config includes the secrets-outside-env rule."""

    requires = {"SEC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Zizmor config enables the secrets-outside-env rule."""
        if not file_exists(root, ".github/zizmor.yml"):
            return None
        return file_contains(root, ".github/zizmor.yml", "secrets-outside-env")


class SEC003(Security):
    """The gitleaks hook is configured."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the pre-commit config includes gitleaks."""
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "gitleaks")


class SEC004(Security):
    """Workflows pin action SHAs."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR workflow pins GitHub Actions to full SHAs."""
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        if re.search(r"uses:\s*\S+@[0-9a-f]{40}", content, re.I):
            return True
        return "⚠️ No SHA-pinned actions detected in PR workflow. Use full commit SHAs."


class SEC005(Security):
    """SECURITY.md discourages public issue reporting."""

    requires = {"PM008"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the security policy discourages public issue reporting."""
        if not file_exists(root, "SECURITY.md"):
            return None
        if file_contains(root, "SECURITY.md", re.compile(r"do not|don't|please don", re.I)):
            return True
        return "⚠️ SECURITY.md may not clearly discourage public issue reporting."
