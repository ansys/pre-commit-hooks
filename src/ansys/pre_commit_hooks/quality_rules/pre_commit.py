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

Validate the presence of ``.pre-commit-config.yaml``, required hook repositories,
spelling and type-checking hooks, zizmor pedantic mode, and standard repository
hygiene hooks. Missing merge-conflict, debug-statement, YAML, and trailing-whitespace
hooks produce warnings.
Configuration is parsed as YAML so comments do not satisfy the checks.
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
    """Load a pre-commit configuration or return an explicit error message."""
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
    """Yield repository mappings that contain a hooks list."""
    repositories = configuration.get("repos")
    if isinstance(repositories, list):
        for repository in repositories:
            if isinstance(repository, dict) and isinstance(repository.get("hooks"), list):
                yield repository


def _configured_hooks(configuration: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    """Yield hook mappings from the configured repositories."""
    for repository in _configured_repositories(configuration):
        hooks = repository.get("hooks")
        if isinstance(hooks, list):
            for hook in hooks:
                if isinstance(hook, dict):
                    yield hook


def _check_repository(repository_root: Path, repository_name: str) -> RuleCheckResult:
    """Check whether a required repository has at least one configured hook."""
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
    """Check whether any supported hook ID is configured."""
    configuration = _load_configuration(repository_root)
    if isinstance(configuration, str):
        return configuration
    for hook in _configured_hooks(configuration):
        hook_id = hook.get("id")
        if isinstance(hook_id, str) and hook_id in hook_ids:
            return True
    return False


def _recommend(action: str, benefit: str) -> str:
    """Format a recommendation that explains why the suggested change helps."""
    return f"RECOMMENDATION: {action} {benefit}"


def _check_recommended_hook(
    repository_root: Path, hook_ids: frozenset[str], action: str, benefit: str
) -> RuleCheckResult:
    """Recommend an absent hook, preserving configuration errors."""
    result = _check_hook(repository_root, hook_ids)
    if result is False:
        return _recommend(action, benefit)
    return result


class PreCommit(ABC):
    """Pre-commit rule family.

    Each ``PC<nnn>`` rule evaluates the repository's pre-commit configuration
    independently. Missing or unreadable configuration is reported, not skipped.
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
            Raw rule result consumed by the quality-report runner.
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
        """Return whether a zizmor hook enables pedantic mode."""
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
        """Return whether a codespell hook is configured."""
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
        """Return whether a supported type-checking hook is configured."""
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
        """Return whether a check-merge-conflict hook is configured."""
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
        """Return whether a debug-statements hook is configured."""
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
        """Return whether a check-yaml hook is configured."""
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
        """Return whether a trailing-whitespace hook is configured."""
        return _check_recommended_hook(
            repository_root,
            frozenset({"trailing-whitespace"}),
            "Add the trailing-whitespace hook;",
            "it removes stray whitespace so diffs stay clean and focused.",
        )
