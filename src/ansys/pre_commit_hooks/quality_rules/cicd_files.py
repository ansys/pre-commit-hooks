# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""CI/CD workflow file naming checks."""

from __future__ import annotations

from .common import CANONICAL_WF, file_exists, wf_label

__all__ = ["CICDFiles", "CI001", "CI002", "CI003"]


class CICDFiles:
    family = "cicd_files"


class CI001(CICDFiles):
    "ci_cd_main.yml exists"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["main"]):
            return True
        lbl = wf_label("main", workflow_map)
        return f"⚠️ Canonical ci_cd_main.yml not found — detected: {lbl}"


class CI002(CICDFiles):
    "ci_cd_pr.yml exists"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["pr"]):
            return True
        lbl = wf_label("pr", workflow_map)
        return f"⚠️ Canonical ci_cd_pr.yml not found — detected: {lbl}"


class CI003(CICDFiles):
    "ci_cd_release.yml exists"

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["release"]):
            return True
        lbl = wf_label("release", workflow_map)
        return f"⚠️ Canonical ci_cd_release.yml not found — detected: {lbl}"
