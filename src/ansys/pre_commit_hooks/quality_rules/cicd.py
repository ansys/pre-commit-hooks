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

"""CI/CD content checks.

This rule set validates the expected GitHub Actions workflow policy for
repository automation.

The checks cover:

* concurrency blocks in the PR and main workflows
* root permissions configuration
* workflow triggers and required jobs
* SHA-pinned action references
* required security and release controls
"""

from __future__ import annotations

import re

from .common import all_workflows_content, wf_content, wf_label


def _workflow_text(root) -> str | None:
    """Return merged workflow text, or ``None`` when workflows are unavailable."""
    content = all_workflows_content(root)
    return content or None


def _contains_any(content: str, pattern: str) -> bool:
    """Return whether the workflow content matches the provided regex pattern."""
    return bool(re.search(pattern, content, re.IGNORECASE))


def _workflows_for_roles(root, workflow_map: dict, roles: list[str]):
    """Collect available workflow content for the requested workflow roles."""
    return [
        (role, wf_label(role, workflow_map), content)
        for role in roles
        if (content := wf_content(root, role, workflow_map)[1])
    ]


__all__ = [
    "CI001",
    "CI002",
    "CI003",
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
    "CI017",
    "CI018",
    "CI019",
    "CICD",
]


class CICD:
    """CI/CD rule family."""

    family = "cicd"


def _check_action_presence(root, pattern: str) -> bool | None:
    """Return whether a single action/pattern is present in workflows."""
    content = _workflow_text(root)
    if not content:
        return None
    return _contains_any(content, pattern)


class CI001(CICD):
    """At least one workflow file exists under .github/workflows."""

    @staticmethod
    def check(root) -> bool:
        """Return whether any workflow file exists in the repository."""
        return _workflow_text(root) is not None


class CI002(CICD):
    """Workflows use concurrency blocks."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR and main workflows define concurrency blocks."""
        present = _workflows_for_roles(
            root,
            workflow_map,
            ["pr", "main"],
        )

        if not present:
            return None

        missing = [label for _, label, content in present if "concurrency:" not in content]

        return True if not missing else f"WARN: concurrency: block missing in: {', '.join(missing)}"


class CI003(CICD):
    """Workflows set root permissions: {}."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether the PR and release workflows have explicit root permissions."""
        present = _workflows_for_roles(
            root,
            workflow_map,
            ["pr", "release"],
        )

        if not present:
            return None

        missing = [
            label
            for _, label, content in present
            if not re.search(r"^permissions:\s*\{\}", content, re.MULTILINE)
        ]

        return True if not missing else f"Missing root permissions: {{}} in: {', '.join(missing)}"


class CI004(CICD):
    """Checkout uses persist-credentials: false."""

    @staticmethod
    def check(root, workflow_map: dict) -> bool | None | str:
        """Return whether workflows disable persisting credentials during checkout."""
        present = _workflows_for_roles(
            root,
            workflow_map,
            ["pr", "release"],
        )

        if not present:
            return None

        missing = [
            label for _, label, content in present if "persist-credentials: false" not in content
        ]

        return (
            True
            if not missing
            else f"WARN: persist-credentials: false missing in: {', '.join(missing)}"
        )


class CI005(CICD):
    """A labeler job is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include a labeler action."""
        return _check_action_presence(root, r"ansys/actions/[^\s]*label|\blabeler\b")


class CI006(CICD):
    """The vulnerability check action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the vulnerability check action."""
        return _check_action_presence(root, r"ansys/actions/check-vulnerabilities")


class CI007(CICD):
    """The code-style action is used."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the workflows include the code-style action."""
        content = _workflow_text(root)
        if not content:
            return None

        if _contains_any(content, r"ansys/actions/code-style"):
            return True

        return "WARN: ansys/actions/code-style not found in any workflow file."


class CI008(CICD):
    """The check-pr-title step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows enforce the PR title check."""
        return _check_action_presence(root, r"ansys/actions/check-pr-title|check-pr-title")


class CI009(CICD):
    """The changelog fragment step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include changelog-fragment validation."""
        return _check_action_presence(root, r"ansys/actions/[^\s]*changelog|changelog-fragment")


class CI010(CICD):
    """The doc-style action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the doc-style action."""
        return _check_action_presence(root, r"ansys/actions/check-doc-style|doc-style")


class CI011(CICD):
    """The doc-build action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the doc-build action."""
        return _check_action_presence(root, r"ansys/actions/doc-build|\bdoc-build\b")


class CI012(CICD):
    """The build-wheelhouse action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include the build-wheelhouse action."""
        return _check_action_presence(root, r"ansys/actions/build-wheelhouse|build-wheelhouse")


class CI013(CICD):
    """The pytest test action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the workflows include pytest-based tests."""
        return _check_action_presence(
            root,
            r"ansys/actions/tests-pytest|ansys/actions/tests|\btests\b|pytest",
        )


class CI014(CICD):
    """The update-changelog step is present across workflows."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include changelog updates during release."""
        return _check_action_presence(root, r"ansys/actions/release-github|update-changelog")


class CI015(CICD):
    """The actions-security action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include the GitHub Actions security check."""
        return _check_action_presence(
            root,
            r"ansys/actions/check-actions-security|check-actions-security",
        )


class CI016(CICD):
    """The build-library action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows include the build-library action."""
        return _check_action_presence(root, r"ansys/actions/build-library|\bbuild-library\b")


class CI017(CICD):
    """The doc-deploy-dev action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows deploy dev docs with the Ansys action."""
        return _check_action_presence(root, r"ansys/actions/doc-deploy-dev|doc-deploy-dev")


class CI018(CICD):
    """The doc-deploy-stable action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows deploy stable docs with the Ansys action."""
        return _check_action_presence(root, r"ansys/actions/doc-deploy-stable|doc-deploy-stable")


class CI019(CICD):
    """The doc-deploy-changelog action is used."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether workflows deploy changelog docs with the Ansys action."""
        return _check_action_presence(
            root, r"ansys/actions/doc-deploy-changelog|doc-deploy-changelog"
        )
