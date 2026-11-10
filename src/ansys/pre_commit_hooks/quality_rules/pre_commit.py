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

"""Pre-commit configuration checks.

This rule set validates the repository pre-commit configuration.

The checks cover:

* The ``.pre-commit-config.yaml`` file exists
* The ``ruff-pre-commit`` and ``ansys/pre-commit-hooks`` repositories are
  configured
* Optional hooks are configured: ``zizmor`` (with pedantic mode), ``codespell``,
  a type checker (``pyright``, ``mypy`` or ``ty``), and the
  ``check-merge-conflict``, ``debug-statements``, ``check-yaml`` and
  ``trailing-whitespace`` hooks

A missing required item is reported as an ``ERROR``. A missing optional hook is
reported as a ``RECOMMENDATION`` that explains the benefit of adding it. A
recommendation never fails the report.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import ClassVar, Final

import yaml

from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult, file_content, file_exists

__all__ = [
    "PC001",
    "PC002",
    "PC003",
    "PC004",
    "PC005",
    "PC006",
    "PC007",
    "PC008",
    "PC009",
    "PC010",
    "PreCommit",
]

_PRE_COMMIT_CONFIG: Final[str] = ".pre-commit-config.yaml"
_TYPE_CHECKER_IDS: Final[frozenset[str]] = frozenset({"pyright", "mypy", "ty"})


def _load_configuration(repository_root: Path) -> Mapping[str, object] | str:
    """Load and validate the pre-commit configuration.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    collections.abc.Mapping[str, object] or str
        The parsed configuration, or an ``"ERROR: ..."`` message when the file
        cannot be read, is not valid YAML, is not a mapping with string keys,
        or has no ``repos`` list.
    """
    content = file_content(repository_root, _PRE_COMMIT_CONFIG)
    if content is None:
        return f"ERROR: Cannot read {_PRE_COMMIT_CONFIG} as UTF-8 within the repository."
    try:
        configuration: object = yaml.safe_load(content)
    except yaml.YAMLError:
        return f"ERROR: Invalid YAML in {_PRE_COMMIT_CONFIG}."
    if not isinstance(configuration, dict) or not all(
        isinstance(key, str) for key in configuration
    ):
        return f"ERROR: {_PRE_COMMIT_CONFIG} must contain a YAML mapping with string keys."
    if not isinstance(configuration.get("repos"), list):
        return f"ERROR: {_PRE_COMMIT_CONFIG} must contain a repos list."
    return configuration


def _configured_repositories(
    configuration: Mapping[str, object],
) -> Iterator[Mapping[str, object]]:
    """Yield repository mappings that contain a hooks list.

    Parameters
    ----------
    configuration : collections.abc.Mapping[str, object]
        Parsed pre-commit configuration.

    Yields
    ------
    collections.abc.Mapping[str, object]
        Each repository entry whose ``hooks`` value is a list.
    """
    repositories = configuration.get("repos")
    if isinstance(repositories, list):
        for repository in repositories:
            if isinstance(repository, dict) and isinstance(repository.get("hooks"), list):
                yield repository


def _configured_hooks(configuration: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    """Yield hook mappings from the configured repositories.

    Parameters
    ----------
    configuration : collections.abc.Mapping[str, object]
        Parsed pre-commit configuration.

    Yields
    ------
    collections.abc.Mapping[str, object]
        Each hook entry that is a mapping.
    """
    for repository in _configured_repositories(configuration):
        hooks = repository.get("hooks")
        if isinstance(hooks, list):
            for hook in hooks:
                if isinstance(hook, dict):
                    yield hook


def _check_repository(repository_root: Path, repository_name: str) -> RuleCheckResult:
    """Check whether a required repository has at least one configured hook.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    repository_name : str
        Repository path suffix to match, for example ``"ansys/pre-commit-hooks"``.

    Returns
    -------
    bool or str
        ``True`` when a matching repository defines a hook with an ID,
        ``False`` when it does not, or an ``"ERROR: ..."`` message when the
        configuration is invalid.
    """
    configuration = _load_configuration(repository_root)
    if isinstance(configuration, str):
        return configuration
    for repository in _configured_repositories(configuration):
        repository_url = repository.get("repo")
        hooks = repository.get("hooks")
        if (
            isinstance(repository_url, str)
            and repository_url.rstrip("/").removesuffix(".git").endswith(f"/{repository_name}")
            and isinstance(hooks, list)
            and any(isinstance(hook, dict) and isinstance(hook.get("id"), str) for hook in hooks)
        ):
            return True
    return False


def _check_hook(repository_root: Path, hook_ids: frozenset[str]) -> RuleCheckResult:
    """Check whether any of the given hook IDs is configured.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    hook_ids : frozenset[str]
        Hook IDs to look for. IDs must match exactly.

    Returns
    -------
    bool or str
        ``True`` when one of the hook IDs is configured, ``False`` when none
        is, or an ``"ERROR: ..."`` message when the configuration is invalid.
    """
    configuration = _load_configuration(repository_root)
    if isinstance(configuration, str):
        return configuration
    for hook in _configured_hooks(configuration):
        hook_id = hook.get("id")
        if isinstance(hook_id, str) and hook_id in hook_ids:
            return True
    return False


def _recommend(action: str, benefit: str) -> str:
    """Format a recommendation that explains why the suggested change helps.

    Parameters
    ----------
    action : str
        What to change, for example ``"Add a codespell hook;"``.
    benefit : str
        Why the change is worthwhile.

    Returns
    -------
    str
        A ``"RECOMMENDATION: ..."`` message.
    """
    return f"RECOMMENDATION: {action} {benefit}"


def _check_recommended_hook(
    repository_root: Path, hook_ids: frozenset[str], action: str, benefit: str
) -> RuleCheckResult:
    """Recommend a hook when none of the given IDs is configured.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    hook_ids : frozenset[str]
        Hook IDs that satisfy the recommendation.
    action : str
        What to add, used when the hook is missing.
    benefit : str
        Why the hook is worthwhile, used when the hook is missing.

    Returns
    -------
    bool or str
        ``True`` when a hook is configured, a ``"RECOMMENDATION: ..."`` message
        when it is missing, or an ``"ERROR: ..."`` message when the
        configuration is invalid.
    """
    result = _check_hook(repository_root, hook_ids)
    if result is False:
        return _recommend(action, benefit)
    return result


class PreCommit(ABC):
    """Pre-commit rule family.

    Base class of the pre-commit quality rules. Each rule is a subclass named
    ``PC<nnn>`` with a static ``check`` method that evaluates the repository's
    pre-commit configuration independently. Missing or unreadable configuration
    is reported as an error rather than skipped. Rules for optional hooks report
    a ``RECOMMENDATION`` instead of an error when the hook is absent.
    """

    family: ClassVar[str] = "pre_commit"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a pre-commit rule.

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
            prefixed with ``"RECOMMENDATION: "`` or ``"ERROR: "``.
        """
        raise NotImplementedError


class PC001(PreCommit):
    """The .pre-commit-config.yaml file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the pre-commit configuration exists."""
        return file_exists(repository_root, _PRE_COMMIT_CONFIG)


class PC002(PreCommit):
    """Ruff-pre-commit is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the Ruff repository has configured hooks."""
        return _check_repository(repository_root, "ruff-pre-commit")


class PC003(PreCommit):
    """Zizmor is configured with --pedantic or --persona=pedantic."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a zizmor hook with pedantic mode.

        Returns
        -------
        bool or str
            ``True`` when a zizmor hook sets ``--pedantic`` or
            ``--persona=pedantic``, otherwise a recommendation to add the hook
            or enable pedantic mode.
        """
        configuration = _load_configuration(repository_root)
        if isinstance(configuration, str):
            return configuration
        has_zizmor = False
        for hook in _configured_hooks(configuration):
            if hook.get("id") != "zizmor":
                continue
            has_zizmor = True
            arguments = hook.get("args")
            if isinstance(arguments, list) and any(
                argument in ("--pedantic", "--persona=pedantic") for argument in arguments
            ):
                return True
        if has_zizmor:
            return _recommend(
                "Enable --pedantic (or --persona=pedantic) for the zizmor hook;",
                "it reports additional GitHub Actions security findings during commits.",
            )
        return _recommend(
            "Add a zizmor hook;",
            "it catches insecure GitHub Actions workflows locally before CI runs.",
        )


class PC004(PreCommit):
    """Codespell is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a codespell hook when none is configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"codespell"}),
            "Add a codespell hook;",
            "it catches spelling mistakes in code and documentation before they are merged.",
        )


class PC005(PreCommit):
    """Ansys/pre-commit-hooks is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the shared Ansys repository has configured hooks."""
        return _check_repository(repository_root, "ansys/pre-commit-hooks")


class PC006(PreCommit):
    """A pyright, mypy, or ty type-checking hook is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a pyright, mypy, or ty hook when none is configured."""
        return _check_recommended_hook(
            repository_root,
            _TYPE_CHECKER_IDS,
            "Add a pyright, mypy, or ty hook;",
            "static type checking finds type errors before code is committed.",
        )


class PC007(PreCommit):
    """Check-merge-conflict is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the check-merge-conflict hook when it is not configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"check-merge-conflict"}),
            "Add the check-merge-conflict hook;",
            "it blocks commits that still contain merge conflict markers.",
        )


class PC008(PreCommit):
    """Debug-statements is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the debug-statements hook when it is not configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"debug-statements"}),
            "Add the debug-statements hook;",
            "it prevents leftover breakpoints and debugger imports from being committed.",
        )


class PC009(PreCommit):
    """Check-yaml is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the check-yaml hook when it is not configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"check-yaml"}),
            "Add the check-yaml hook;",
            "it rejects invalid YAML before it breaks CI or tooling configuration.",
        )


class PC010(PreCommit):
    """Trailing-whitespace is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the trailing-whitespace hook when it is not configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"trailing-whitespace"}),
            "Add the trailing-whitespace hook;",
            "it removes stray whitespace so diffs stay clean and focused.",
        )
