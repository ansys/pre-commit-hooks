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

"""Dependabot checks.

This rule set validates the repository Dependabot configuration and expected
update automation settings.

The checks cover:

* Dependabot config presence
* schema version validation
* ecosystem configuration
* update schedule and grouping policy
* security-relevant dependency settings
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

import yaml

from ansys.pre_commit_hooks.quality_rules.common import file_content, file_exists

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
    "Dependabot",
]


_PATH_DEPENDABOT = ".github/dependabot.yml"
MIN_WEEKLY_ECOSYSTEMS = 2
REQUIRED_COOLDOWN_DAYS = 7
PIP_VERSIONING_STRATEGY = "lockfile-only"


@cache
def _cached_dependabot_config(
    root: Path, modified_ns: int, size: int
) -> tuple[bool, bool, dict | None]:
    """Return whether the config exists, is valid YAML, and its mapping."""
    try:
        config = yaml.safe_load(file_content(root, _PATH_DEPENDABOT))
    except yaml.YAMLError:
        return True, False, None

    if not isinstance(config, dict):
        return True, False, None
    return True, True, config


def _dependabot_config(root) -> tuple[bool, bool, dict | None]:
    """Return the cached parsed configuration, invalidating when the file changes."""
    root = Path(root)
    path = root / _PATH_DEPENDABOT
    if not file_exists(root, _PATH_DEPENDABOT):
        return False, False, None
    stat = path.stat()
    return _cached_dependabot_config(root, stat.st_mtime_ns, stat.st_size)


def _updates(root) -> list[dict] | None:
    """Return configured update entries when the file is present and valid."""
    present, valid, config = _dependabot_config(root)
    if not present or not valid:
        return None
    if config is None:
        return None
    updates = config.get("updates")
    if not isinstance(updates, list) or not all(isinstance(entry, dict) for entry in updates):
        return None
    return updates


def _ecosystem_updates(updates: list[dict], ecosystem: str) -> list[dict]:
    """Return update entries for one package ecosystem."""
    return [entry for entry in updates if entry.get("package-ecosystem") == ecosystem]


class Dependabot:
    """Dependabot rule family."""

    family = "dependabot"


class DB001(Dependabot):
    """The .github/dependabot.yml file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the Dependabot config file exists."""
        return file_exists(root, _PATH_DEPENDABOT)


class DB002(Dependabot):
    """Dependabot.yml sets version 2."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Dependabot config uses the expected schema version."""
        present, valid, config = _dependabot_config(root)
        if not present:
            return None
        if not valid or config is None:
            return False
        version = config.get("version")
        return isinstance(version, int) and version == 2


class DB003(Dependabot):
    """Pip or uv ecosystem is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether a supported dependency ecosystem is configured."""
        updates = _updates(root)
        if updates is None:
            return None

        has_pip = bool(_ecosystem_updates(updates, "pip"))
        has_uv = bool(_ecosystem_updates(updates, "uv"))

        if has_pip:
            return True

        if has_uv:
            return "WARN: uv ecosystem configured " "(pip preferred for PyAnsys standard)."

        return False


class DB004(Dependabot):
    """The GitHub Actions ecosystem is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the GitHub Actions ecosystem is configured."""
        updates = _updates(root)
        return None if updates is None else bool(_ecosystem_updates(updates, "github-actions"))


class DB005(Dependabot):
    """A weekly update interval is set."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the weekly update interval is configured for enough ecosystems."""
        updates = _updates(root)
        if updates is None:
            return None

        count = sum(
            entry.get("schedule", {}).get("interval") == "weekly"
            for entry in updates
            if isinstance(entry.get("schedule"), dict)
        )

        if count >= MIN_WEEKLY_ECOSYSTEMS:
            return True

        return (
            f"WARN: Only {count} ecosystem(s) use weekly interval "
            f"(expected ≥{MIN_WEEKLY_ECOSYSTEMS})."
        )


class DB006(Dependabot):
    """Cooldown default-days: 7 is configured."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the Dependabot cooldown policy is set to seven days."""
        updates = _updates(root)
        if updates is None:
            return None
        cooldowns = [
            (entry.get("package-ecosystem", "<unknown>"), entry["cooldown"])
            for entry in updates
            if isinstance(entry.get("cooldown"), dict)
        ]
        if not cooldowns:
            return f"WARN: Cooldown default-days: {REQUIRED_COOLDOWN_DAYS} not found in dependabot.yml."  # noqa: E501

        invalid = [
            ecosystem
            for ecosystem, cooldown in cooldowns
            if cooldown.get("default-days") != REQUIRED_COOLDOWN_DAYS
        ]
        if not invalid:
            return True

        return (
            f"WARN: Cooldown default-days: {REQUIRED_COOLDOWN_DAYS} "
            f"missing or invalid for: {', '.join(invalid)}."
        )


class DB007(Dependabot):
    """Pip uses the lockfile-only versioning strategy."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether pip uses the lockfile-only versioning strategy."""
        updates = _updates(root)
        if updates is None:
            return None
        pip_updates = _ecosystem_updates(updates, "pip")
        if not pip_updates:
            return None

        invalid = [
            entry.get("package-ecosystem", "<unknown>")
            for entry in pip_updates
            if entry.get("versioning-strategy") != PIP_VERSIONING_STRATEGY
        ]
        if not invalid:
            return True

        return (
            f"WARN: versioning-strategy: {PIP_VERSIONING_STRATEGY} "
            f"missing or invalid for: {', '.join(invalid)}."
        )


class DB008(Dependabot):
    """Pip groups all dependencies together."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the pip ecosystem groups dependency updates with a wildcard."""
        updates = _updates(root)
        if updates is None:
            return None
        pip_updates = _ecosystem_updates(updates, "pip")
        if not pip_updates:
            return None

        if any(
            isinstance(entry.get("groups"), dict)
            and any(
                "*" in group.get("patterns", [])
                for group in entry["groups"].values()
                if isinstance(group, dict) and isinstance(group.get("patterns"), list)
            )
            for entry in pip_updates
        ):
            return True

        return (
            "WARN: Pip updates are not grouped in the pip dependabot block. "
            "Add groups with wildcard pattern '*' under package-ecosystem: pip."
        )


class DB009(Dependabot):
    """GitHub Actions updates are grouped to reduce PR noise."""

    requires = {"DB001", "DB004"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether GitHub Actions updates are grouped for Ansys actions or all actions."""
        updates = _updates(root)
        if updates is None:
            return None
        action_updates = _ecosystem_updates(updates, "github-actions")
        if not action_updates:
            return None

        if any(
            isinstance(entry.get("groups"), dict)
            and any(
                pattern in {"*", "ansys/actions/*"}
                for group in entry["groups"].values()
                if isinstance(group, dict)
                for pattern in group.get("patterns", [])
            )
            for entry in action_updates
        ):
            return True

        return (
            "WARN: GitHub Actions updates are not grouped in .github/dependabot.yml. "
            "Add groups with patterns '*' or 'ansys/actions/*' to reduce PR volume."
        )


class DB010(Dependabot):
    """The Dependabot configuration is valid YAML."""

    requires = {"DB001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Dependabot file parses to a YAML mapping."""
        present, valid, _ = _dependabot_config(root)
        if not present:
            return None
        return valid


class DB011(Dependabot):
    """The Dependabot configuration has a non-empty updates section."""

    requires = {"DB001", "DB010"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the updates section exists and contains entries."""
        present, valid, config = _dependabot_config(root)
        if not present or not valid:
            return None
        updates = config.get("updates")
        return isinstance(updates, list) and bool(updates)
