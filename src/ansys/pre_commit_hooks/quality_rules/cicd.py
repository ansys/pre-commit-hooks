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

This rule set validates the GitHub Actions workflow policy for repository
automation. Every ``.yml`` and ``.yaml`` file directly under
``.github/workflows`` is searched as text.

The checks cover:

* At least one workflow file exists
* Required ``ansys/actions`` reusable actions are used
* Action references are pinned to immutable commit SHAs

Concurrency, root permissions, and credential persistence are enforced by the
zizmor check in ``ansys/actions/check-actions-security`` and are not repeated here.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import ClassVar, Final

from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult, all_workflows_content

_NO_WORKFLOWS: Final[str] = "WARNING: No workflow files found under .github/workflows."

_ACTION_PATTERNS: Final[dict[str, re.Pattern[str]]] = {
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
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/doc-style(?:@|\s|$)",
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
        r"^\s*(?:-\s*)?uses:\s*ansys/actions/tests(?:-pytest)?(?:@|\s|$)",
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

_ACTION_USE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.IGNORECASE | re.MULTILINE
)
_SHA_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^@\s]+@[0-9a-f]{40}", re.IGNORECASE)

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
    "CICD",
]


def _check_action_presence(
    repository_root: Path, action_pattern: re.Pattern[str], action_name: str
) -> RuleCheckResult:
    """Check whether a workflow uses the required action.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    action_pattern : re.Pattern[str]
        Compiled pattern matching the required action reference.
    action_name : str
        Action name reported when the action is missing.

    Returns
    -------
    bool or str
        ``True`` when the action is used, otherwise a warning message.
    """
    content = all_workflows_content(repository_root)
    if content is None:
        return _NO_WORKFLOWS
    if action_pattern.search(content):
        return True
    return f"WARNING: {action_name} not found in any workflow file."


class CICD(ABC):
    """CI/CD rule family.

    Base class of the CI/CD quality rules. Each rule is a subclass named
    ``CI<nnn>`` with a static ``check`` method that receives the repository
    root and the name of the detected README file.
    """

    family: ClassVar[str] = "cicd"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a CI/CD rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, or ``None`` when no supported README exists.

        Returns
        -------
        bool or str
            Raw rule result consumed by the quality-report runner.
        """
        raise NotImplementedError


class CI001(CICD):
    """At least one workflow file exists under .github/workflows."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether any workflow file exists in the repository."""
        return all_workflows_content(repository_root) is not None


class CI002(CICD):
    """A labeler action is used in the workflows."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a labeler action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["labeler"], "A labeler action"
        )


class CI003(CICD):
    """The check-vulnerabilities action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the vulnerability check action is used."""
        return _check_action_presence(
            repository_root,
            _ACTION_PATTERNS["vulnerabilities"],
            "ansys/actions/check-vulnerabilities",
        )


class CI004(CICD):
    """The code-style action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the code-style action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["code_style"], "ansys/actions/code-style"
        )


class CI005(CICD):
    """A changelog fragment action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a changelog fragment action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["changelog"], "A changelog fragment action"
        )


class CI006(CICD):
    """The doc-style action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the doc-style action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["doc_style"], "ansys/actions/doc-style"
        )


class CI007(CICD):
    """The doc-build action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the doc-build action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["doc_build"], "ansys/actions/doc-build"
        )


class CI008(CICD):
    """The build-wheelhouse action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the build-wheelhouse action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["wheelhouse"], "ansys/actions/build-wheelhouse"
        )


class CI009(CICD):
    """The pytest tests action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the tests action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["tests"], "ansys/actions/tests"
        )


class CI010(CICD):
    """The release-github action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the release-github action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["release"], "ansys/actions/release-github"
        )


class CI011(CICD):
    """The check-actions-security action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the check-actions-security action is used."""
        return _check_action_presence(
            repository_root,
            _ACTION_PATTERNS["actions_security"],
            "ansys/actions/check-actions-security",
        )


class CI012(CICD):
    """The build-library action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the build-library action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["build_library"], "ansys/actions/build-library"
        )


class CI013(CICD):
    """The doc-deploy-dev action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the doc-deploy-dev action is used."""
        return _check_action_presence(
            repository_root, _ACTION_PATTERNS["doc_deploy_dev"], "ansys/actions/doc-deploy-dev"
        )


class CI014(CICD):
    """The doc-deploy-stable action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the doc-deploy-stable action is used."""
        return _check_action_presence(
            repository_root,
            _ACTION_PATTERNS["doc_deploy_stable"],
            "ansys/actions/doc-deploy-stable",
        )


class CI015(CICD):
    """The doc-deploy-changelog action is used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the doc-deploy-changelog action is used."""
        return _check_action_presence(
            repository_root,
            _ACTION_PATTERNS["doc_deploy_changelog"],
            "ansys/actions/doc-deploy-changelog",
        )


class CI016(CICD):
    """Actions use immutable commit SHAs instead of mutable tags."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether all remote action references are SHA-pinned."""
        content = all_workflows_content(repository_root)
        if content is None:
            return _NO_WORKFLOWS

        # Local actions (``./path``) are repository code and need no SHA pin.
        references = [
            reference
            for reference in _ACTION_USE_PATTERN.findall(content)
            if not reference.startswith("./")
        ]
        unpinned = list(dict.fromkeys(ref for ref in references if not _SHA_PATTERN.fullmatch(ref)))
        if not unpinned:
            return True
        return f"WARNING: Actions are not SHA-pinned: {', '.join(unpinned)}."
