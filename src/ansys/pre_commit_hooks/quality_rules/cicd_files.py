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

"""CI/CD workflow file naming checks."""

from __future__ import annotations

from .common import CANONICAL_WF, file_exists, wf_label

__all__ = ["CICDFiles", "CI001", "CI002", "CI003"]


class CICDFiles:
    """CI/CD workflow file naming rule family."""

    family = "cicd_files"


class CI001(CICDFiles):
    """The ci_cd_main.yml workflow file exists."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        """Return whether the canonical main workflow file is present."""
        if file_exists(root, CANONICAL_WF["main"]):
            return True
        lbl = wf_label("main", workflow_map)
        return f"⚠️ Canonical ci_cd_main.yml not found — detected: {lbl}"


class CI002(CICDFiles):
    """The ci_cd_pr.yml workflow file exists."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        """Return whether the canonical PR workflow file is present."""
        if file_exists(root, CANONICAL_WF["pr"]):
            return True
        lbl = wf_label("pr", workflow_map)
        return f"⚠️ Canonical ci_cd_pr.yml not found — detected: {lbl}"


class CI003(CICDFiles):
    """The ci_cd_release.yml workflow file exists."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | str:
        """Return whether the canonical release workflow file is present."""
        if file_exists(root, CANONICAL_WF["release"]):
            return True
        lbl = wf_label("release", workflow_map)
        return f"⚠️ Canonical ci_cd_release.yml not found — detected: {lbl}"
