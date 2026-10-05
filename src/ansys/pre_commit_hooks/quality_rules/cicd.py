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

from functools import cache
import re

from ansys.pre_commit_hooks.quality_rules.common import all_workflows_content


@cache
def _workflow_text(root) -> str | None:
    """Return merged workflow text, or ``None`` when workflows are unavailable."""
    content = all_workflows_content(root)
    return content or None


def _contains_any(content: str, pattern: re.Pattern) -> bool:
    """Return whether the workflow content matches the provided regex pattern."""
    return bool(pattern.search(content))


_ACTION_PATTERNS = {
    "labeler": re.compile(
        r"^\s*(?:-\s*)?uses:\s*[^\s#]*label[^\s#]*", re.IGNORECASE | re.MULTILINE
    ),
    "vulnerabilities": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/check-vulnerabilities(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "code_style": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/code-style(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "changelog": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/[^\s#]*changelog[^\s#]*",
        re.IGNORECASE | re.MULTILINE,
    ),
    "doc_style": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/check-doc-style(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "doc_build": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/doc-build(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "wheelhouse": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/build-wheelhouse(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "tests": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/tests(?:-pytest)?(?:@|\s)|\b(?:pytest|tox)\b",
        re.IGNORECASE | re.MULTILINE,
    ),
    "release": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/release-github(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "actions_security": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/check-actions-security(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "build_library": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/build-library(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "doc_deploy_dev": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/doc-deploy-dev(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "doc_deploy_stable": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/doc-deploy-stable(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
    "doc_deploy_changelog": re.compile(
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/doc-deploy-changelog(?:@|\s|$)",
        re.IGNORECASE | re.MULTILINE,
    ),
}

_ACTION_USE_PATTERN = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.IGNORECASE | re.MULTILINE)
_SHA_PATTERN = re.compile(r"@[0-9a-f]{40}$", re.IGNORECASE)
_ROOT_PERMISSIONS_PATTERN = re.compile(r"^permissions:\s*\{\}", re.MULTILINE)


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
    "WorkflowActionRule",
]


class CICD:
    """CI/CD rule family."""

    family = "cicd"


def _check_action_presence(root, pattern: str) -> bool | None:
    """Return whether a single action/pattern is present in workflows."""
    content = _workflow_text(root)
    if not content:
        return None
    return _contains_any(content, _ACTION_PATTERNS[pattern])


def _action_references(content: str) -> list[str]:
    """Return action references from workflow uses statements."""
    return _ACTION_USE_PATTERN.findall(content)


class WorkflowActionRule(CICD):
    """Base class for rules that require a specific workflow action."""

    pattern = ""

    @classmethod
    def check(cls, root) -> bool | None:
        """Return whether the configured action is present in workflows."""
        return _check_action_presence(root, cls.pattern)


class CI001(CICD):
    """At least one workflow file exists under .github/workflows."""

    @staticmethod
    def check(root) -> bool:
        """Return whether any workflow file exists in the repository."""
        return _workflow_text(root) is not None


class CI002(CICD):
    """Workflows use concurrency blocks."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | None | str:
        """Return whether workflow files define concurrency blocks."""
        content = _workflow_text(root)
        if not content:
            return None

        return (
            True if "concurrency:" in content else "WARN: concurrency: block missing in workflows."
        )


class CI003(CICD):
    """Workflows set root permissions: {}."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | None | str:
        """Return whether workflow files have explicit root permissions."""
        content = _workflow_text(root)
        if not content:
            return None

        return (
            True
            if _ROOT_PERMISSIONS_PATTERN.search(content)
            else "WARN: Missing root permissions: {} in workflows."
        )


class CI004(CICD):
    """Checkout uses persist-credentials: false."""

    @staticmethod
    def check(root, workflow_map: dict | None = None) -> bool | None | str:
        """Return whether workflows disable persisting credentials during checkout."""
        content = _workflow_text(root)
        if not content:
            return None

        return (
            True
            if "persist-credentials: false" in content
            else "WARN: persist-credentials: false missing in workflows."
        )


class CI005(WorkflowActionRule):
    """A labeler job is present across workflows."""

    pattern = "labeler"


class CI006(WorkflowActionRule):
    """The vulnerability check action is used."""

    pattern = "vulnerabilities"


class CI007(WorkflowActionRule):
    """The code-style action is used."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the workflows include the code-style action."""
        content = _workflow_text(root)
        if not content:
            return None

        if _contains_any(content, _ACTION_PATTERNS["code_style"]):
            return True

        return "WARN: ansys/actions/code-style not found in any workflow file."


class CI008(WorkflowActionRule):
    """The changelog fragment step is present across workflows."""

    pattern = "changelog"


class CI009(WorkflowActionRule):
    """The doc-style action is used."""

    pattern = "doc_style"


class CI010(WorkflowActionRule):
    """The doc-build action is used."""

    pattern = "doc_build"


class CI011(WorkflowActionRule):
    """The build-wheelhouse action is used."""

    pattern = "wheelhouse"


class CI012(WorkflowActionRule):
    """The pytest test action is used."""

    pattern = "tests"


class CI013(WorkflowActionRule):
    """The update-changelog step is present across workflows."""

    pattern = "release"


class CI014(WorkflowActionRule):
    """The actions-security action is used."""

    pattern = "actions_security"


class CI015(WorkflowActionRule):
    """The build-library action is used."""

    pattern = "build_library"


class CI016(WorkflowActionRule):
    """The doc-deploy-dev action is used."""

    pattern = "doc_deploy_dev"


class CI017(WorkflowActionRule):
    """The doc-deploy-stable action is used."""

    pattern = "doc_deploy_stable"


class CI018(WorkflowActionRule):
    """The doc-deploy-changelog action is used."""

    pattern = "doc_deploy_changelog"


class CI019(CICD):
    """Actions use immutable commit SHAs instead of mutable tags."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether all workflow actions are SHA-pinned."""
        content = _workflow_text(root)
        if not content:
            return None

        unpinned = [
            reference
            for reference in _action_references(content)
            if not _SHA_PATTERN.search(reference)
        ]
        if not unpinned:
            return True
        return f"WARN: Actions are not SHA-pinned: {', '.join(unpinned)}."
