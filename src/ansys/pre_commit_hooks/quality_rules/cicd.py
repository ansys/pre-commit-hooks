# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""CI/CD content checks."""

from __future__ import annotations

import re

from .common import all_workflows_content, wf_content

__all__ = [
    "CICD",
    "CI004",
    "CI005",
    "CI006",
    "CI007",
    "CI008",
    "CI009",
    "CI010",
    "CI011",
    "CI012",
    "CI013",
    "CI014",
    "CI015",
    "CI016",
]


class CICD:
    family = "cicd"


class CI004(CICD):
    "Workflows use concurrency blocks"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("main", "ci_cd_main.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [
            lbl
            for role, lbl in present
            if "concurrency:" not in wf_content(root, role, workflow_map)[1]
        ]
        if not missing:
            return True
        return f"⚠️ concurrency: block missing in: {', '.join(missing)}"


class CI005(CICD):
    "Workflows set root `permissions: {}`"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("release", "ci_cd_release.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [
            lbl
            for role, lbl in present
            if not re.search(r"^permissions:\s*\{\}", wf_content(root, role, workflow_map)[1], re.M)
        ]
        return True if not missing else f"Missing root permissions: {{}} in: {', '.join(missing)}"


class CI006(CICD):
    "checkout uses persist-credentials: false"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("release", "ci_cd_release.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [
            lbl
            for role, lbl in present
            if "persist-credentials: false" not in wf_content(root, role, workflow_map)[1]
        ]
        if not missing:
            return True
        return f"⚠️ persist-credentials: false missing in: {', '.join(missing)}"


class CI007(CICD):
    "Labeler job present across workflows"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/[^\s]*label|\blabeler\b", content, re.IGNORECASE))


class CI008(CICD):
    "ansys/actions/check-vulnerabilities used"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return "ansys/actions/check-vulnerabilities" in content


class CI009(CICD):
    "ansys/actions/code-style used"

    @staticmethod
    def check(root) -> bool | None | str:
        content = all_workflows_content(root)
        if not content:
            return None
        if "ansys/actions/code-style" in content:
            return True
        return "⚠️ ansys/actions/code-style not found in any workflow file."


class CI010(CICD):
    "check-pr-title step present across workflows"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/check-pr-title|check-pr-title", content, re.IGNORECASE)
        )


class CI011(CICD):
    "changelog-fragment step present across workflows"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/[^\s]*changelog|changelog-fragment", content, re.IGNORECASE)
        )


class CI012(CICD):
    "ansys/actions/check-doc-style used"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/check-doc-style|doc-style", content, re.IGNORECASE))


class CI013(CICD):
    "ansys/actions/doc-build used"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/doc-build|\bdoc-build\b", content, re.IGNORECASE))


class CI014(CICD):
    "ansys/actions/build-wheelhouse used"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/build-wheelhouse|build-wheelhouse", content, re.IGNORECASE)
        )


class CI015(CICD):
    "ansys/actions/tests-pytest (or pytest) used"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(
                r"ansys/actions/tests-pytest|ansys/actions/tests|\btests\b|pytest",
                content,
                re.IGNORECASE,
            )
        )


class CI016(CICD):
    "update-changelog step present across workflows"

    @staticmethod
    def check(root) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/release-github|update-changelog", content, re.IGNORECASE)
        )
