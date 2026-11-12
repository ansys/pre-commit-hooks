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

"""Dependabot configuration checks.

Validate configuration structure and repository update policies without requiring
specific group names, exclusions, labels, or assignees. Pip and uv are accepted
equally, as are daily and weekly schedules. Policy deviations produce warnings;
missing, unreadable, or structurally invalid configuration produces errors.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import ClassVar, Final

import yaml

from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult, file_content, file_exists

__all__ = [
    "DB001",
    "DB002",
    "DB003",
    "DB004",
    "DB005",
    "DB006",
    "DB007",
    "DB008",
    "DB009",
    "DB010",
    "DB011",
    "DB012",
    "DB013",
    "DB014",
    "DB015",
    "DB016",
    "DB017",
    "DB018",
    "DB019",
    "DB020",
    "DB021",
    "DB022",
    "DB023",
    "DB024",
    "Dependabot",
]

_DEPENDABOT_PATHS: Final[tuple[str, ...]] = (
    ".github/dependabot.yml",
    ".github/dependabot.yaml",
)
_PYTHON_ECOSYSTEMS: Final[frozenset[str]] = frozenset({"pip", "uv"})
_MIN_FREQUENT_ECOSYSTEMS: Final[int] = 2
_COOLDOWN_DAYS: Final[int] = 7
_SCHEDULE_INTERVALS: Final[frozenset[str]] = frozenset({"daily", "weekly", "monthly"})
_COMMIT_PREFIX_POLICY: Final[dict[str, str]] = {
    "pip": "build(deps)",
    "uv": "build(deps)",
    "github-actions": "build(actions)",
    "pre-commit": "build(pre-commit)",
}
_MAX_OPEN_PULL_REQUESTS: Final[int] = 10
_REBASE_STRATEGIES: Final[frozenset[str]] = frozenset({"auto", "disabled"})


def _configuration_path(repository_root: Path) -> str | None:
    """Return the preferred supported Dependabot configuration path."""
    return next((path for path in _DEPENDABOT_PATHS if file_exists(repository_root, path)), None)


def _load_configuration(repository_root: Path) -> Mapping[str, object] | str:
    """Read a YAML mapping or return an actionable configuration error."""
    path = _configuration_path(repository_root)
    if path is None:
        return "ERROR: No .github/dependabot.yml or .github/dependabot.yaml file found."
    content = file_content(repository_root, path)
    if content is None:
        return f"ERROR: Cannot read {path} as UTF-8 within the repository."
    try:
        configuration: object = yaml.safe_load(content)
    except yaml.YAMLError:
        return f"ERROR: Invalid YAML in {path}."
    if not isinstance(configuration, dict) or not all(
        isinstance(key, str) for key in configuration
    ):
        return f"ERROR: {path} must contain a YAML mapping with string keys."
    return configuration


def _load_updates(repository_root: Path) -> list[Mapping[str, object]] | str:
    """Return non-empty, well-formed update mappings or an explicit error."""
    configuration = _load_configuration(repository_root)
    if isinstance(configuration, str):
        return configuration
    updates = configuration.get("updates")
    if not isinstance(updates, list) or not updates:
        return "ERROR: Dependabot must contain a non-empty updates list."
    entries: list[Mapping[str, object]] = []
    for index, entry in enumerate(updates, start=1):
        if not isinstance(entry, dict) or not all(isinstance(key, str) for key in entry):
            return f"ERROR: Dependabot update entry {index} must be a mapping with string keys."
        ecosystem = entry.get("package-ecosystem")
        if not isinstance(ecosystem, str) or not ecosystem.strip():
            return f"ERROR: Dependabot update entry {index} must specify a package-ecosystem."
        entries.append(entry)
    return entries


def _ecosystem_updates(
    updates: Sequence[Mapping[str, object]], ecosystems: frozenset[str]
) -> list[Mapping[str, object]]:
    """Select entries for the requested package ecosystems."""
    return [
        entry
        for entry in updates
        if isinstance(ecosystem := entry.get("package-ecosystem"), str) and ecosystem in ecosystems
    ]


def _check_ecosystem(repository_root: Path, ecosystems: frozenset[str]) -> RuleCheckResult:
    """Check ecosystem presence, warning when no matching entry exists."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    if _ecosystem_updates(updates, ecosystems):
        return True
    return f"WARNING: No {' or '.join(sorted(ecosystems))} Dependabot updates are configured."


def _has_dependency_group(entry: Mapping[str, object]) -> bool:
    """Return whether an entry has a named group with non-empty string patterns."""
    groups = entry.get("groups")
    if not isinstance(groups, dict):
        return False
    for name, group in groups.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(group, dict):
            continue
        patterns = group.get("patterns")
        if (
            isinstance(patterns, list)
            and patterns
            and all(isinstance(pattern, str) and pattern.strip() for pattern in patterns)
        ):
            return True
    return False


def _check_grouping(repository_root: Path, ecosystems: frozenset[str]) -> RuleCheckResult:
    """Require meaningful groups on every matching entry, without fixed names or patterns."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    entries = _ecosystem_updates(updates, ecosystems)
    if not entries:
        return f"WARNING: No {' or '.join(sorted(ecosystems))} updates available to check grouping."
    ungrouped = [
        str(entry["package-ecosystem"]) for entry in entries if not _has_dependency_group(entry)
    ]
    if ungrouped:
        return f"WARNING: Dependency groups missing or invalid for: {', '.join(ungrouped)}."
    return True


def _check_commit_message_prefixes(repository_root: Path) -> RuleCheckResult:
    """Validate ecosystem-specific Dependabot commit-message prefixes."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid: list[str] = []
    for entry in updates:
        ecosystem = entry.get("package-ecosystem")
        if not isinstance(ecosystem, str) or ecosystem not in _COMMIT_PREFIX_POLICY:
            continue
        commit_message = entry.get("commit-message")
        prefix = commit_message.get("prefix") if isinstance(commit_message, dict) else None
        expected = _COMMIT_PREFIX_POLICY[ecosystem]
        if not isinstance(prefix, str) or prefix != expected:
            invalid.append(f"{ecosystem} (expected: {expected})")
    if invalid:
        details = ", ".join(invalid)
        return f"WARNING: Dependabot commit-message prefix missing or invalid for: {details}."
    return True


def _check_target_branch(repository_root: Path) -> RuleCheckResult:
    """Validate that every update entry declares a target branch."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid = [
        str(entry["package-ecosystem"])
        for entry in updates
        if not isinstance(entry.get("target-branch"), str) or not entry["target-branch"].strip()
    ]
    if invalid:
        return f"WARNING: target-branch missing or invalid for: {', '.join(invalid)}."
    return True


def _check_schedule_details(repository_root: Path) -> RuleCheckResult:
    """Validate day, time, and timezone on every update schedule."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid: list[str] = []
    for entry in updates:
        schedule = entry.get("schedule")
        if not isinstance(schedule, dict):
            invalid.append(str(entry["package-ecosystem"]))
            continue
        if not all(
            isinstance(schedule.get(field), str) and schedule[field].strip()
            for field in ("day", "time", "timezone")
        ):
            invalid.append(str(entry["package-ecosystem"]))
    if invalid:
        return (
            "WARNING: schedule.day, schedule.time, or schedule.timezone missing or invalid for: "
            f"{', '.join(invalid)}."
        )
    return True


def _check_open_pull_requests_limit(repository_root: Path) -> RuleCheckResult:
    """Validate open-pull-requests-limit presence and threshold."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid = [
        str(entry["package-ecosystem"])
        for entry in updates
        if not isinstance(limit := entry.get("open-pull-requests-limit"), int)
        or limit < 1
        or limit > _MAX_OPEN_PULL_REQUESTS
    ]
    if invalid:
        return (
            "WARNING: open-pull-requests-limit missing or invalid for "
            f"(must be 1-{_MAX_OPEN_PULL_REQUESTS}): {', '.join(invalid)}."
        )
    return True


def _check_branch_name_separator(repository_root: Path) -> RuleCheckResult:
    """Validate explicit pull-request branch-name separators."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid: list[str] = []
    for entry in updates:
        pull_request = entry.get("pull-request-branch-name")
        separator = pull_request.get("separator") if isinstance(pull_request, dict) else None
        if not isinstance(separator, str) or not separator.strip():
            invalid.append(str(entry["package-ecosystem"]))
    if invalid:
        details = ", ".join(invalid)
        return f"RECOMMENDATION: pull-request-branch-name.separator missing for: {details}."
    return True


def _check_rebase_strategy(repository_root: Path) -> RuleCheckResult:
    """Validate explicit and supported rebase strategies."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid = [
        str(entry["package-ecosystem"])
        for entry in updates
        if not isinstance(strategy := entry.get("rebase-strategy"), str)
        or strategy not in _REBASE_STRATEGIES
    ]
    if invalid:
        strategies = ", ".join(sorted(_REBASE_STRATEGIES))
        return (
            "WARNING: rebase-strategy missing or invalid for "
            f"(supported: {strategies}): {', '.join(invalid)}."
        )
    return True


def _check_duplicate_ecosystem_directories(repository_root: Path) -> RuleCheckResult:
    """Detect duplicate package-ecosystem and directory combinations."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    seen: set[tuple[str, str]] = set()
    duplicates: set[tuple[str, str]] = set()
    for entry in updates:
        ecosystem = str(entry["package-ecosystem"])
        if isinstance(directory := entry.get("directory"), str):
            paths = [directory]
        elif isinstance(directories := entry.get("directories"), list):
            paths = [path for path in directories if isinstance(path, str)]
        else:
            paths = []
        for path in paths:
            key = (ecosystem, path)
            if key in seen:
                duplicates.add(key)
            seen.add(key)
    if duplicates:
        details = ", ".join(f"{ecosystem}:{path}" for ecosystem, path in sorted(duplicates))
        return f"ERROR: Duplicate package-ecosystem and directory combinations found: {details}."
    return True


def _check_labels_and_owners(repository_root: Path) -> RuleCheckResult:
    """Validate labels and ownership metadata for each entry."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid: list[str] = []
    for entry in updates:
        labels = entry.get("labels")
        labels_ok = (
            isinstance(labels, list)
            and labels
            and all(isinstance(label, str) and label.strip() for label in labels)
        )
        assignees = entry.get("assignees")
        reviewers = entry.get("reviewers")
        owners_ok = any(
            isinstance(group, list)
            and group
            and all(isinstance(owner, str) and owner.strip() for owner in group)
            for group in (assignees, reviewers)
        )
        if not labels_ok or not owners_ok:
            invalid.append(str(entry["package-ecosystem"]))
    if invalid:
        details = ", ".join(invalid)
        return f"WARNING: labels or owners (assignees/reviewers) missing or invalid for: {details}."
    return True


def _check_registries_security(repository_root: Path) -> RuleCheckResult:
    """Validate registry mappings and reject insecure registry URLs."""
    configuration = _load_configuration(repository_root)
    if isinstance(configuration, str):
        return configuration
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    registries = configuration.get("registries")
    registry_map = registries if isinstance(registries, dict) else {}
    insecure: list[str] = []
    for name, registry in registry_map.items():
        if not isinstance(name, str) or not isinstance(registry, dict):
            continue
        url = registry.get("url")
        if isinstance(url, str) and url.startswith("http://"):
            insecure.append(name)
    if insecure:
        return f"ERROR: Insecure registry URL(s) found (http://): {', '.join(sorted(insecure))}."
    missing: set[str] = set()
    for entry in updates:
        configured = entry.get("registries")
        if not isinstance(configured, list):
            continue
        for registry_name in configured:
            if not isinstance(registry_name, str) or registry_name == "*":
                continue
            if registry_name not in registry_map:
                missing.add(registry_name)
    if missing:
        return (
            "WARNING: Dependabot update entries reference undefined registries: "
            f"{', '.join(sorted(missing))}."
        )
    return True


def _check_ignore_policy(repository_root: Path) -> RuleCheckResult:
    """Recommend defining at least one explicit ignore policy."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    for entry in updates:
        ignore = entry.get("ignore")
        if not isinstance(ignore, list):
            continue
        for rule in ignore:
            if not isinstance(rule, dict):
                continue
            dependency_name = rule.get("dependency-name")
            if isinstance(dependency_name, str) and dependency_name.strip():
                return True
    return "RECOMMENDATION: Add at least one explicit ignore policy for noisy or major updates."


def _check_full_group_coverage(repository_root: Path) -> RuleCheckResult:
    """Validate groups that fully cover dependencies using '*' patterns."""
    updates = _load_updates(repository_root)
    if isinstance(updates, str):
        return updates
    invalid: list[str] = []
    for entry in updates:
        groups = entry.get("groups")
        if not isinstance(groups, dict):
            invalid.append(str(entry["package-ecosystem"]))
            continue
        covers_all = False
        for group in groups.values():
            if not isinstance(group, dict):
                continue
            patterns = group.get("patterns")
            if isinstance(patterns, list) and any(pattern == "*" for pattern in patterns):
                covers_all = True
                break
        if not covers_all:
            invalid.append(str(entry["package-ecosystem"]))
    if invalid:
        details = ", ".join(invalid)
        return f"WARNING: Full dependency group coverage ('*' pattern) missing for: {details}."
    return True


class Dependabot(ABC):
    """Dependabot rule family with independent, typed repository checks."""

    family: ClassVar[str] = "dependabot"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a Dependabot rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, unused by this family.

        Returns
        -------
        bool or str
            Raw result consumed by the quality-report runner.
        """
        raise NotImplementedError


class DB001(Dependabot):
    """A .github/dependabot.yml or .github/dependabot.yaml file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a supported Dependabot configuration file exists."""
        return _configuration_path(repository_root) is not None


class DB002(Dependabot):
    """Dependabot uses schema version 2."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the schema version is the integer 2."""
        configuration = _load_configuration(repository_root)
        if isinstance(configuration, str):
            return configuration
        version = configuration.get("version")
        if type(version) is int and version == 2:
            return True
        return "ERROR: Dependabot version must be the integer 2."


class DB003(Dependabot):
    """Pip or uv dependency updates are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether either supported Python ecosystem is configured."""
        return _check_ecosystem(repository_root, _PYTHON_ECOSYSTEMS)


class DB004(Dependabot):
    """GitHub Actions dependency updates are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether GitHub Actions updates are configured."""
        return _check_ecosystem(repository_root, frozenset({"github-actions"}))


class DB005(Dependabot):
    """At least two distinct ecosystems use daily or weekly update schedules."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Count distinct ecosystems with a daily or weekly schedule."""
        updates = _load_updates(repository_root)
        if isinstance(updates, str):
            return updates
        ecosystems = {
            str(entry["package-ecosystem"])
            for entry in updates
            if isinstance(schedule := entry.get("schedule"), dict)
            and schedule.get("interval") in ("daily", "weekly")
        }
        if len(ecosystems) >= _MIN_FREQUENT_ECOSYSTEMS:
            return True
        return (
            f"WARNING: Only {len(ecosystems)} distinct ecosystem(s) use daily or weekly "
            f"schedules; expected at least {_MIN_FREQUENT_ECOSYSTEMS}."
        )


class DB006(Dependabot):
    """Every update entry configures a seven-day default cooldown."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check default cooldowns without requiring specific exclusions."""
        updates = _load_updates(repository_root)
        if isinstance(updates, str):
            return updates
        invalid: list[str] = []
        for entry in updates:
            cooldown = entry.get("cooldown")
            days = cooldown.get("default-days") if isinstance(cooldown, dict) else None
            if type(days) is not int or days != _COOLDOWN_DAYS:
                invalid.append(str(entry["package-ecosystem"]))
        if invalid:
            return (
                f"WARNING: Cooldown default-days: {_COOLDOWN_DAYS} missing or invalid for: "
                f"{', '.join(invalid)}."
            )
        return True


class DB007(Dependabot):
    """Every pip or uv entry defines dependency groups."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check Python dependency grouping, accepting selective patterns."""
        return _check_grouping(repository_root, _PYTHON_ECOSYSTEMS)


class DB008(Dependabot):
    """Every GitHub Actions entry defines dependency groups."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check action grouping without requiring specific action names."""
        return _check_grouping(repository_root, frozenset({"github-actions"}))


class DB009(Dependabot):
    """The Dependabot configuration is a valid YAML mapping."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the configuration parses as a string-keyed YAML mapping."""
        configuration = _load_configuration(repository_root)
        return configuration if isinstance(configuration, str) else True


class DB010(Dependabot):
    """Dependabot has a non-empty list of update entries with package ecosystems."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Validate the updates list and each entry's package-ecosystem."""
        updates = _load_updates(repository_root)
        return updates if isinstance(updates, str) else True


class DB011(Dependabot):
    """Every update entry specifies repository-root-relative directories."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Validate directory or directories without requiring paths to exist locally."""
        updates = _load_updates(repository_root)
        if isinstance(updates, str):
            return updates
        for index, entry in enumerate(updates, start=1):
            if ("directory" in entry) == ("directories" in entry):
                return f"ERROR: Entry {index} must define exactly one of directory or directories."
            paths = [entry["directory"]] if "directory" in entry else entry["directories"]
            if (
                not isinstance(paths, list)
                or not paths
                or not all(
                    isinstance(path, str)
                    and path.startswith("/")
                    and "\\" not in path
                    and ".." not in PurePosixPath(path).parts
                    for path in paths
                )
            ):
                return (
                    f"ERROR: Update entry {index} must use non-empty root-relative directory paths."
                )
        return True


class DB012(Dependabot):
    """Every update entry has a supported schedule interval."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Validate schedule structure, including the required cronjob for cron intervals."""
        updates = _load_updates(repository_root)
        if isinstance(updates, str):
            return updates
        for index, entry in enumerate(updates, start=1):
            schedule = entry.get("schedule")
            interval = schedule.get("interval") if isinstance(schedule, dict) else None
            if not isinstance(interval, str) or interval not in _SCHEDULE_INTERVALS:
                return f"ERROR: Update entry {index} must specify a supported schedule.interval."
            if interval == "cron" and isinstance(schedule, dict):
                cronjob = schedule.get("cronjob")
                if not isinstance(cronjob, str) or not cronjob.strip():
                    return f"ERROR: Update entry {index} with a cron schedule must specify cronjob."
        return True


class DB013(Dependabot):
    """Pre-commit dependency updates are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when pre-commit ecosystem updates are absent."""
        return _check_ecosystem(repository_root, frozenset({"pre-commit"}))


class DB014(Dependabot):
    """Ecosystem-specific Dependabot commit-message prefixes are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when required ecosystem commit-message prefixes are missing or invalid."""
        return _check_commit_message_prefixes(repository_root)


class DB015(Dependabot):
    """Every update entry declares target-branch."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when target-branch is missing or invalid."""
        return _check_target_branch(repository_root)


class DB016(Dependabot):
    """Every update entry schedule declares day, time, and timezone."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when schedule day/time/timezone are missing."""
        return _check_schedule_details(repository_root)


class DB017(Dependabot):
    """Every update entry caps open pull requests."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when open-pull-requests-limit is missing or out of policy bounds."""
        return _check_open_pull_requests_limit(repository_root)


class DB018(Dependabot):
    """Every update entry configures pull-request branch-name separators."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend setting pull-request-branch-name.separator."""
        return _check_branch_name_separator(repository_root)


class DB019(Dependabot):
    """Every update entry sets a supported rebase strategy."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when rebase-strategy is missing or unsupported."""
        return _check_rebase_strategy(repository_root)


class DB020(Dependabot):
    """No duplicate package-ecosystem and directory combinations exist."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Error when duplicate ecosystem+directory combinations are detected."""
        return _check_duplicate_ecosystem_directories(repository_root)


class DB021(Dependabot):
    """Every update entry defines labels and at least one owner."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when labels or owners are missing."""
        return _check_labels_and_owners(repository_root)


class DB022(Dependabot):
    """Referenced registries are defined and use secure URLs."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Error on insecure registry URLs and warn on missing registry mappings."""
        return _check_registries_security(repository_root)


class DB023(Dependabot):
    """At least one ignore policy is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend adding ignore policy coverage."""
        return _check_ignore_policy(repository_root)


class DB024(Dependabot):
    """Every update entry has full dependency group coverage."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when no '*' group coverage is defined for an entry."""
        return _check_full_group_coverage(repository_root)
