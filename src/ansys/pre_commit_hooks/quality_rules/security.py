# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Security checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists, wf_content

__all__ = ["Security", "SEC001", "SEC002", "SEC003", "SEC004", "SEC005"]


class Security:
    family = "security"


class SEC001(Security):
    ".github/zizmor.yml exists"

    @staticmethod
    def check(root) -> bool | str:
        if file_exists(root, ".github/zizmor.yml"):
            return True
        return "⚠️ .github/zizmor.yml not found — optional but recommended."


class SEC002(Security):
    "zizmor.yml has secrets-outside-env rule"

    requires = {"SEC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".github/zizmor.yml"):
            return None
        return file_contains(root, ".github/zizmor.yml", "secrets-outside-env")


class SEC003(Security):
    "gitleaks hook configured"

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "gitleaks")


class SEC004(Security):
    "Workflows pin action SHAs"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        if re.search(r"uses:\s*\S+@[0-9a-f]{40}", content, re.I):
            return True
        return "⚠️ No SHA-pinned actions detected in PR workflow. Use full commit SHAs."


class SEC005(Security):
    "SECURITY.md discourages public issue reporting"

    requires = {"PM008"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, "SECURITY.md"):
            return None
        if file_contains(root, "SECURITY.md", re.compile(r"do not|don't|please don", re.I)):
            return True
        return "⚠️ SECURITY.md may not clearly discourage public issue reporting."
