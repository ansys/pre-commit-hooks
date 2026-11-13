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
zizmor and gitleaks tooling, the ``SECURITY.md`` policy, and the hardening of
the GitHub Actions workflows directly under ``.github/workflows``.

The checks cover:

* ``.github/zizmor.yml`` exists and disables the ``secrets-outside-env`` audit
* The ``gitleaks`` pre-commit hook is configured
* Remote actions are pinned to commit SHAs that carry a version comment
* ``SECURITY.md`` tells reporters not to open public issues
* Workflows declare their permissions, ``actions/checkout`` does not persist
  credentials, and no workflow is triggered by ``pull_request_target``
* Pre-commit repositories are pinned to commit SHAs

Workflows are parsed with :class:`yaml.BaseLoader`, so every scalar is read as
a string and the ``on`` key is not converted to a boolean. Missing, unreadable,
or invalid configuration is reported as an ``ERROR``, except a missing
workflow directory, which is a ``WARNING`` as in the CI/CD rules.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
import re
from typing import ClassVar, Final

import yaml

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    file_content,
    file_exists,
    workflow_contents,
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
    "SEC007",
    "SEC008",
    "SEC009",
    "SEC010",
    "Security",
]

_ZIZMOR_CONFIG: Final[str] = ".github/zizmor.yml"
_SECRETS_OUTSIDE_ENV: Final[str] = "secrets-outside-env"
_GITLEAKS_HOOK_IDS: Final[frozenset[str]] = frozenset(
    {"gitleaks", "gitleaks-docker", "gitleaks-system"}
)
# Locations where GitHub looks for a security policy, in lookup order.
_SECURITY_POLICIES: Final[tuple[str, ...]] = (
    "SECURITY.md",
    ".github/SECURITY.md",
    "docs/SECURITY.md",
)
_NO_WORKFLOWS: Final[str] = "WARNING: No workflow files found under .github/workflows."
_PRE_COMMIT_CONFIG: Final[str] = ".pre-commit-config.yaml"
_LOCAL_PRE_COMMIT_REPOSITORIES: Final[frozenset[str]] = frozenset({"local", "meta"})

_USES_LINE: Final[re.Pattern[str]] = re.compile(
    r"""^\s*(?:-\s*)?uses:\s*["']?(?P<reference>[^\s#"']+)["']?\s*(?:\#(?P<comment>.*))?$""",
    re.MULTILINE,
)
_COMMIT_SHA: Final[re.Pattern[str]] = re.compile(r"[0-9a-f]{40}", re.IGNORECASE)
_DOCKER_DIGEST: Final[re.Pattern[str]] = re.compile(
    r"docker://[^@\s]+@sha256:[0-9a-f]{64}", re.IGNORECASE
)
_VERSION_COMMENT: Final[re.Pattern[str]] = re.compile(r"\S*\d")
_PUBLIC_ISSUE_WARNING: Final[re.Pattern[str]] = re.compile(
    r"\b(?:do\s+not|don['\u2019]t|never|must\s+not|should\s+not|avoid)\b[^.\n]{0,100}?\bissues?\b",
    re.IGNORECASE,
)


def _action_references(repository_root: Path) -> list[tuple[str, str | None]] | str:
    """Collect the remote action references used by the workflows.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    list[tuple[str, str or None]] or str
        Unique ``(reference, comment)`` pairs in file order, excluding local
        ``./`` actions, or a ``"WARNING: ..."`` message when no workflow
        exists.
    """
    contents = workflow_contents(repository_root)
    if not contents:
        return _NO_WORKFLOWS
    references: dict[tuple[str, str | None], None] = {}
    for content in contents.values():
        for match in _USES_LINE.finditer(content):
            reference = match["reference"]
            if reference.startswith("./"):
                continue
            comment = match["comment"].strip() if match["comment"] else None
            references[(reference, comment)] = None
    return list(references)


def _is_pinned(reference: str) -> bool:
    """Return whether an action reference is immutable.

    Parameters
    ----------
    reference : str
        Value of a ``uses`` key, for example ``"actions/checkout@<sha>"``.

    Returns
    -------
    bool
        ``True`` for a Docker image pinned to a ``sha256`` digest or an action
        pinned to a full 40-character commit SHA.
    """
    if reference.casefold().startswith("docker://"):
        return _DOCKER_DIGEST.fullmatch(reference) is not None
    _, separator, version = reference.rpartition("@")
    return bool(separator) and _COMMIT_SHA.fullmatch(version) is not None


def _load_workflows(repository_root: Path) -> dict[str, Mapping[str, object]] | str:
    """Parse every workflow file.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    dict[str, collections.abc.Mapping[str, object]] or str
        Parsed workflows keyed by repository-relative path, a ``"WARNING: ..."``
        message when no workflow exists, or an ``"ERROR: ..."`` message naming
        the first workflow that is not a valid YAML mapping.
    """
    contents = workflow_contents(repository_root)
    if not contents:
        return _NO_WORKFLOWS
    workflows: dict[str, Mapping[str, object]] = {}
    for path, content in contents.items():
        try:
            # BaseLoader keeps every scalar as a string and builds no objects.
            workflow: object = yaml.load(content, Loader=yaml.BaseLoader)  # nosec B506
        except yaml.YAMLError:
            return f"ERROR: Invalid YAML in {path}."
        if not isinstance(workflow, dict):
            return f"ERROR: {path} must contain a YAML mapping."
        workflows[path] = workflow
    return workflows


def _jobs(workflow: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    """Yield the job mappings of a workflow.

    Parameters
    ----------
    workflow : collections.abc.Mapping[str, object]
        Parsed workflow.

    Yields
    ------
    collections.abc.Mapping[str, object]
        Each job definition that is a mapping.
    """
    jobs = workflow.get("jobs")
    if isinstance(jobs, dict):
        for job in jobs.values():
            if isinstance(job, dict):
                yield job


def _steps(workflow: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    """Yield the step mappings of every job in a workflow.

    Parameters
    ----------
    workflow : collections.abc.Mapping[str, object]
        Parsed workflow.

    Yields
    ------
    collections.abc.Mapping[str, object]
        Each step definition that is a mapping.
    """
    for job in _jobs(workflow):
        steps = job.get("steps")
        if isinstance(steps, list):
            for step in steps:
                if isinstance(step, dict):
                    yield step


def _triggers(workflow: Mapping[str, object]) -> set[str]:
    """Return the event names that trigger a workflow.

    Parameters
    ----------
    workflow : collections.abc.Mapping[str, object]
        Parsed workflow.

    Returns
    -------
    set[str]
        Event names from the ``on`` key, which may be a string, a list, or a
        mapping.
    """
    events = workflow.get("on")
    if isinstance(events, str):
        return {events}
    if isinstance(events, list):
        return {event for event in events if isinstance(event, str)}
    if isinstance(events, dict):
        return set(events)
    return set()


def _check_workflows(
    repository_root: Path,
    is_compliant: Callable[[Mapping[str, object]], bool],
    message: str,
) -> RuleCheckResult:
    """Report the workflows that fail a per-workflow condition.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    is_compliant : collections.abc.Callable[[Mapping[str, object]], bool]
        Predicate that receives a parsed workflow and returns whether it
        complies.
    message : str
        Message prefix, including the status, followed by the failing paths.

    Returns
    -------
    bool or str
        ``True`` when every workflow complies, otherwise the message followed
        by the failing workflow paths, or the workflow loading message.
    """
    workflows = _load_workflows(repository_root)
    if isinstance(workflows, str):
        return workflows
    failing = [path for path, workflow in workflows.items() if not is_compliant(workflow)]
    if not failing:
        return True
    return f"{message} {', '.join(failing)}."


def _declares_permissions(workflow: Mapping[str, object]) -> bool:
    """Return whether a workflow sets permissions at the top or in every job.

    Parameters
    ----------
    workflow : collections.abc.Mapping[str, object]
        Parsed workflow.

    Returns
    -------
    bool
        ``True`` when the workflow has a top-level ``permissions`` key, or when
        it has jobs and each of them sets ``permissions``.
    """
    if "permissions" in workflow:
        return True
    jobs = list(_jobs(workflow))
    return bool(jobs) and all("permissions" in job for job in jobs)


def _checkout_drops_credentials(workflow: Mapping[str, object]) -> bool:
    """Return whether every checkout step disables credential persistence.

    Parameters
    ----------
    workflow : collections.abc.Mapping[str, object]
        Parsed workflow.

    Returns
    -------
    bool
        ``True`` when every ``actions/checkout`` step sets
        ``persist-credentials: false``.
    """
    for step in _steps(workflow):
        uses = step.get("uses")
        if not isinstance(uses, str) or not uses.casefold().startswith("actions/checkout@"):
            continue
        options = step.get("with")
        persist = options.get("persist-credentials") if isinstance(options, dict) else None
        if not isinstance(persist, str) or persist.strip().casefold() != "false":
            return False
    return True


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
    """Workflows pin action SHAs."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every remote action is pinned to an immutable version.

        Returns
        -------
        bool or str
            ``True`` when every remote action uses a full commit SHA and every
            Docker action uses a ``sha256`` digest, otherwise an error naming
            the mutable references.
        """
        references = _action_references(repository_root)
        if isinstance(references, str):
            return references
        unpinned = list(
            dict.fromkeys(reference for reference, _ in references if not _is_pinned(reference))
        )
        if not unpinned:
            return True
        return f"ERROR: Pin these actions to a full commit SHA: {', '.join(unpinned)}."


class SEC005(Security):
    """SECURITY.md discourages public issue reporting."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that the security policy steers reporters away from issues.

        Returns
        -------
        bool or str
            ``True`` when the first ``SECURITY.md`` that GitHub would use tells
            reporters not to use (public) issues, otherwise an error.
        """
        policy = next(
            (path for path in _SECURITY_POLICIES if file_exists(repository_root, path)), None
        )
        if policy is None:
            return (
                "ERROR: Add a SECURITY.md file that explains how to report vulnerabilities "
                "privately instead of in public issues."
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


class SEC006(Security):
    """Pinned action SHAs have a version comment."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a version comment after each SHA-pinned action.

        Returns
        -------
        bool or str
            ``True`` when every SHA-pinned action is followed by a comment that
            contains a version number, such as ``# v4.2.2``, otherwise a
            recommendation naming the uncommented references.
        """
        references = _action_references(repository_root)
        if isinstance(references, str):
            return references
        uncommented = list(
            dict.fromkeys(
                reference
                for reference, comment in references
                if _is_pinned(reference)
                and not reference.casefold().startswith("docker://")
                and not (comment and _VERSION_COMMENT.match(comment))
            )
        )
        if not uncommented:
            return True
        return (
            "RECOMMENDATION: Add a version comment, such as # v1.2.3, after these pinned "
            f"actions so reviewers and Dependabot can track them: {', '.join(uncommented)}."
        )


class SEC007(Security):
    """Workflows declare their GITHUB_TOKEN permissions."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every workflow limits the GITHUB_TOKEN permissions."""
        return _check_workflows(
            repository_root,
            _declares_permissions,
            "WARNING: Declare permissions at the top level (for example, permissions: {}) "
            "or in every job of:",
        )


class SEC008(Security):
    """Checkout steps set persist-credentials to false."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that actions/checkout does not leave the token in .git/config."""
        return _check_workflows(
            repository_root,
            _checkout_drops_credentials,
            "WARNING: Set persist-credentials: false on every actions/checkout step in:",
        )


class SEC009(Security):
    """Workflows are not triggered by pull_request_target."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn about workflows that run fork code with repository secrets."""
        return _check_workflows(
            repository_root,
            lambda workflow: "pull_request_target" not in _triggers(workflow),
            "WARNING: Replace the pull_request_target trigger, which runs with repository "
            "secrets and write access on pull requests from forks, in:",
        )


class SEC010(Security):
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
