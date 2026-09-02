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
    """CI/CD rule family."""

    family = "cicd"


class CI004(CICD):
    """Workflows use concurrency blocks."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR and main workflows define concurrency blocks."""
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
    """Workflows set root permissions: {}."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR and release workflows have explicit root permissions."""
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
    """Checkout uses persist-credentials: false."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether workflows disable persisting credentials during checkout."""
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
    """A labeler job is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include a labeler action."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/[^\s]*label|\blabeler\b", content, re.IGNORECASE))


class CI008(CICD):
    """The vulnerability check action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the vulnerability check action."""
        content = all_workflows_content(root)
        if not content:
            return None
        return "ansys/actions/check-vulnerabilities" in content


class CI009(CICD):
    """The code-style action is used."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the workflows include the code-style action."""
        content = all_workflows_content(root)
        if not content:
            return None
        if "ansys/actions/code-style" in content:
            return True
        return "⚠️ ansys/actions/code-style not found in any workflow file."


class CI010(CICD):
    """The check-pr-title step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows enforce the PR title check."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/check-pr-title|check-pr-title", content, re.IGNORECASE)
        )


class CI011(CICD):
    """The changelog fragment step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include changelog-fragment validation."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/[^\s]*changelog|changelog-fragment", content, re.IGNORECASE)
        )


class CI012(CICD):
    """The doc-style action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the doc-style action."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/check-doc-style|doc-style", content, re.IGNORECASE))


class CI013(CICD):
    """The doc-build action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the doc-build action."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/doc-build|\bdoc-build\b", content, re.IGNORECASE))


class CI014(CICD):
    """The build-wheelhouse action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the build-wheelhouse action."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/build-wheelhouse|build-wheelhouse", content, re.IGNORECASE)
        )


class CI015(CICD):
    """The pytest test action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include pytest-based tests."""
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
    """The update-changelog step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include changelog updates during release."""
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(
            re.search(r"ansys/actions/release-github|update-changelog", content, re.IGNORECASE)
        )
