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

"""Security configuration checks.

This rule set validates the security configuration of a repository: the
zizmor and gitleaks tooling, the ``SECURITY.md`` policy, the pinning of the
pre-commit repositories, and the dependency lockfile.

The checks cover:

* ``.github/zizmor.yml`` exists and disables the ``secrets-outside-env`` audit
* The ``gitleaks`` pre-commit hook is configured
* ``SECURITY.md`` exists only at the root and tells reporters not to open
  public issues
* Pre-commit repositories are pinned to commit SHAs
* A ``uv.lock`` or ``poetry.lock`` lockfile pins the dependencies

GitHub Actions workflow hardening, such as pinning actions to commit SHAs,
version comments, token permissions, credential persistence, and dangerous
triggers, is left to the zizmor audits. Missing, unreadable, or invalid
configuration is reported as an ``ERROR``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import ClassVar, Final

import yaml

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    file_content,
    file_exists,
)
from ansys.pre_commit_hooks.quality_rules.pre_commit import (
    _configured_hooks,
    _configured_repositories,
    _load_configuration,
)

__all__ = [
    "SEC001",
    "SEC002",
    "SEC003",
    "SEC004",
    "SEC005",
    "SEC006",
    "Security",
]

_ZIZMOR_CONFIG: Final[str] = ".github/zizmor.yml"
_SECRETS_OUTSIDE_ENV: Final[str] = "secrets-outside-env"
_GITLEAKS_HOOK_IDS: Final[frozenset[str]] = frozenset(
    {"gitleaks", "gitleaks-docker", "gitleaks-system"}
)
_SECURITY_POLICY: Final[str] = "SECURITY.md"
_MISPLACED_SECURITY_POLICIES: Final[tuple[str, ...]] = (
    ".github/SECURITY.md",
    "docs/SECURITY.md",
)
_PRE_COMMIT_CONFIG: Final[str] = ".pre-commit-config.yaml"
_LOCKFILES: Final[tuple[str, ...]] = ("uv.lock", "poetry.lock")
_LOCAL_PRE_COMMIT_REPOSITORIES: Final[frozenset[str]] = frozenset({"local", "meta"})

_COMMIT_SHA: Final[re.Pattern[str]] = re.compile(r"[0-9a-f]{40}", re.IGNORECASE)
_PUBLIC_ISSUE_WARNING: Final[re.Pattern[str]] = re.compile(
    r"\b(?:do\s+not|don['\u2019]t|never|must\s+not|should\s+not|avoid)\b[^.\n]{0,100}?\bissues?\b",
    re.IGNORECASE,
)


class Security(ABC):
    """Security rule family.

    Base class of the security quality rules. Each rule is a subclass named
    ``SEC<nnn>`` with a static ``check`` method that evaluates one security
    control of the repository independently.
    """

    family: ClassVar[str] = "security"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a security rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, unused by this rule family.

        Returns
        -------
        bool or str
            ``True`` when the rule passes, ``False`` for an error, or a string
            prefixed with ``"RECOMMENDATION: "``, ``"WARNING: "``, or
            ``"ERROR: "``.
        """
        raise NotImplementedError


class SEC001(Security):
    """The .github/zizmor.yml file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a zizmor configuration file when none exists."""
        if file_exists(repository_root, _ZIZMOR_CONFIG):
            return True
        return (
            f"RECOMMENDATION: Add {_ZIZMOR_CONFIG}. It configures the zizmor audits, "
            f"for example to disable {_SECRETS_OUTSIDE_ENV}."
        )


class SEC002(Security):
    """The zizmor config includes the secrets-outside-env rule."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that the zizmor configuration disables secrets-outside-env.

        Returns
        -------
        bool or str
            ``True`` when ``.github/zizmor.yml`` sets
            ``rules.secrets-outside-env.disable`` to ``true`` or does not exist
            (SEC001 reports a missing file), otherwise an error.
        """
        if not file_exists(repository_root, _ZIZMOR_CONFIG):
            return True
        content = file_content(repository_root, _ZIZMOR_CONFIG)
        if content is None:
            return f"ERROR: Cannot read {_ZIZMOR_CONFIG} as UTF-8 within the repository."
        try:
            configuration: object = yaml.safe_load(content)
        except yaml.YAMLError:
            return f"ERROR: Invalid YAML in {_ZIZMOR_CONFIG}."
        rules = configuration.get("rules") if isinstance(configuration, dict) else None
        rule = rules.get(_SECRETS_OUTSIDE_ENV) if isinstance(rules, dict) else None
        if isinstance(rule, dict) and rule.get("disable") is True:
            return True
        return (
            f"ERROR: Disable the {_SECRETS_OUTSIDE_ENV} rule in {_ZIZMOR_CONFIG} with "
            f"rules: {_SECRETS_OUTSIDE_ENV}: disable: true."
        )


class SEC003(Security):
    """The gitleaks hook is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that a gitleaks pre-commit hook is configured."""
        configuration = _load_configuration(repository_root)
        if isinstance(configuration, str):
            return configuration
        if any(hook.get("id") in _GITLEAKS_HOOK_IDS for hook in _configured_hooks(configuration)):
            return True
        return (
            f"ERROR: Add the gitleaks hook to {_PRE_COMMIT_CONFIG}. It blocks commits "
            "that contain secrets such as tokens and private keys."
        )


class SEC004(Security):
    """SECURITY.md discourages public issue reporting."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that the security policy steers reporters away from issues.

        Returns
        -------
        bool or str
            ``True`` when the root ``SECURITY.md`` is the only policy file and tells
            reporters not to use (public) issues, otherwise an error.
        """
        policy = _SECURITY_POLICY
        misplaced = [
            path for path in _MISPLACED_SECURITY_POLICIES if file_exists(repository_root, path)
        ]
        if misplaced:
            return (
                f"ERROR: Keep the security policy only at the repository root as {policy}; "
                f"remove {', '.join(misplaced)}."
            )
        if not file_exists(repository_root, policy):
            return (
                "ERROR: Add a SECURITY.md file at the repository root that explains how to "
                "report vulnerabilities privately instead of in public issues."
            )
        content = file_content(repository_root, policy)
        if content is None:
            return f"ERROR: Cannot read {policy} as UTF-8 within the repository."
        if _PUBLIC_ISSUE_WARNING.search(content):
            return True
        return (
            f"ERROR: State in {policy} that vulnerabilities must not be reported in public "
            "GitHub issues."
        )


class SEC005(Security):
    """Pre-commit repositories pin revisions to commit SHAs."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend pinning each remote pre-commit repository to a commit SHA.

        Returns
        -------
        bool or str
            ``True`` when every remote repository ``rev`` is a full commit SHA,
            a recommendation naming the repositories pinned to tags or
            branches, or an ``"ERROR: ..."`` message when the configuration is
            invalid.
        """
        configuration = _load_configuration(repository_root)
        if isinstance(configuration, str):
            return configuration
        unpinned = [
            str(repository.get("repo"))
            for repository in _configured_repositories(configuration)
            if repository.get("repo") not in _LOCAL_PRE_COMMIT_REPOSITORIES
            and not (
                isinstance(repository.get("rev"), str)
                and _COMMIT_SHA.fullmatch(str(repository.get("rev")))
            )
        ]
        if not unpinned:
            return True
        return (
            "RECOMMENDATION: Pin these pre-commit repositories to a commit SHA with "
            f"pre-commit autoupdate --freeze, because tags can be moved: {', '.join(unpinned)}."
        )


class SEC006(Security):
    """A dependency lockfile exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Report an error when neither uv.lock nor poetry.lock exists at the root.

        Returns
        -------
        bool or str
            ``True`` when a lockfile exists, otherwise an error. A lockfile
            keeps development and CI environments reproducible and prevents
            unreviewed dependencies from being installed.
        """
        if any(file_exists(repository_root, lockfile) for lockfile in _LOCKFILES):
            return True
        return (
            "ERROR: Commit a uv.lock or poetry.lock file at the repository root so "
            "development and CI use a controlled, reviewed set of dependencies."
        )
