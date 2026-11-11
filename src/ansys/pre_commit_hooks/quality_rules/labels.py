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

"""GitHub label configuration checks.

This rule set validates the label files used by the PyAnsys labeler
workflows: ``.github/labels.yml`` declares the repository labels and
``.github/labeler.yml`` assigns them to pull requests.

The checks cover:

* Both files exist, and ``.github/labeler.yml`` is a mapping of labels to
  match rules
* Every label assigned by ``.github/labeler.yml`` is declared in
  ``.github/labels.yml``
* Declared labels are unique and have a valid color and a description
* The ``bug``, ``enhancement``, ``documentation``, ``dependencies``, ``ci``,
  ``tests``, ``maintenance``, ``release``, ``style:skip``, and
  ``good first issue`` labels are declared
* ``.github/labeler.yml`` labels documentation and workflow changes
* A workflow synchronizes the declared labels with GitHub
* No legacy ``.yaml`` copies of the label files remain

Label names are compared case-insensitively, as GitHub does. Both files are
parsed with :class:`yaml.BaseLoader`, so every scalar, including colors such
as ``000000``, is read as a string. Missing, unreadable, or invalid
configuration is reported as an ``ERROR``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path
import re
from typing import ClassVar, Final

import yaml

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    all_workflows_content,
    file_content,
    file_exists,
)

__all__ = [
    "LB001",
    "LB002",
    "LB003",
    "LB004",
    "LB005",
    "LB006",
    "LB007",
    "LB008",
    "LB009",
    "LB010",
    "LB011",
    "LB012",
    "LB013",
    "LB014",
    "LB015",
    "LB016",
    "LB017",
    "Labels",
]

_LABELER_CONFIG: Final[str] = ".github/labeler.yml"
_LABELS_CONFIG: Final[str] = ".github/labels.yml"
_LEGACY_CONFIGS: Final[tuple[str, ...]] = (".github/labeler.yaml", ".github/labels.yaml")
_COLOR: Final[re.Pattern[str]] = re.compile(r"#?[0-9A-Fa-f]{6}")
_RECOMMENDED_LABELS: Final[tuple[str, ...]] = ("ci", "tests", "maintenance", "release")
# Keys whose values are branch-name regular expressions rather than file globs.
_BRANCH_KEYS: Final[frozenset[str]] = frozenset({"head-branch", "base-branch"})
_COVERED_PATHS: Final[dict[str, str]] = {
    "documentation": "doc/source/index.rst",
    "workflow": ".github/workflows/ci_cd.yml",
}
_LABEL_SYNC_ACTION: Final[re.Pattern[str]] = re.compile(
    r"^\s*(?:-\s*)?uses:\s*['\"]?[^\s#'\"]*/(?:action-label-syncer|label-sync"
    r"|ghaction-github-labeler|action-manage-label|issue-label-manager-action)\b",
    re.IGNORECASE | re.MULTILINE,
)


def _load_yaml(repository_root: Path, relative_path: str) -> tuple[object, str | None]:
    """Read a YAML file with every scalar loaded as a string.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    relative_path : str
        File path relative to ``repository_root``.

    Returns
    -------
    tuple[object, str or None]
        The parsed document and ``None``, or ``None`` and an ``"ERROR: ..."``
        message when the file cannot be read or is not valid YAML.
    """
    content = file_content(repository_root, relative_path)
    if content is None:
        return None, f"ERROR: Cannot read {relative_path} as UTF-8 within the repository."
    try:
        return yaml.load(content, Loader=yaml.BaseLoader), None  # nosec B506
    except yaml.YAMLError:
        return None, f"ERROR: Invalid YAML in {relative_path}."


def _load_labels(repository_root: Path) -> list[dict[str, object]] | str:
    """Load the labels declared in ``.github/labels.yml``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    list[dict[str, object]] or str
        The label mappings, or an ``"ERROR: ..."`` message when the file
        cannot be loaded or is not a list of mappings with a non-empty
        ``name``.
    """
    labels, error = _load_yaml(repository_root, _LABELS_CONFIG)
    if error is not None:
        return error
    if not isinstance(labels, list) or not all(
        isinstance(label, dict) and isinstance(label.get("name"), str) and label["name"].strip()
        for label in labels
    ):
        return f"ERROR: {_LABELS_CONFIG} must contain a list of labels with a name."
    return labels


def _normalize(name: str) -> str:
    """Return the comparison key of a label name.

    Parameters
    ----------
    name : str
        Label name.

    Returns
    -------
    str
        The stripped, case-folded name.
    """
    return name.strip().casefold()


def _label_names(repository_root: Path) -> set[str] | str:
    """Return the normalized names of the declared labels.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    set[str] or str
        The normalized label names, or an ``"ERROR: ..."`` message.
    """
    labels = _load_labels(repository_root)
    if isinstance(labels, str):
        return labels
    return {_normalize(str(label["name"])) for label in labels}


def _load_labeler(repository_root: Path) -> dict[str, object] | str:
    """Load the label rules declared in ``.github/labeler.yml``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    dict[str, object] or str
        The mapping of label names to match rules, or an ``"ERROR: ..."``
        message when the file cannot be loaded or is not a non-empty mapping
        whose values are empty, lists, or mappings.
    """
    labeler, error = _load_yaml(repository_root, _LABELER_CONFIG)
    if error is not None:
        return error
    if (
        not isinstance(labeler, dict)
        or not labeler
        or not all(isinstance(rules, (list, dict)) or rules == "" for rules in labeler.values())
    ):
        return f"ERROR: {_LABELER_CONFIG} must map label names to lists or mappings of match rules."
    return labeler


def _check_labels(
    repository_root: Path, label_names: tuple[str, ...], status: str
) -> RuleCheckResult:
    """Check whether ``.github/labels.yml`` declares the given labels.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    label_names : tuple[str, ...]
        Required label names.
    status : str
        ``"ERROR"``, ``"WARNING"``, or ``"RECOMMENDATION"``, used when a label
        is missing.

    Returns
    -------
    bool or str
        ``True`` when every label is declared, otherwise a message with the
        given status that names the missing labels.
    """
    names = _label_names(repository_root)
    if isinstance(names, str):
        return names
    missing = [name for name in label_names if _normalize(name) not in names]
    if not missing:
        return True
    plural = "label" if len(missing) == 1 else "labels"
    return f"{status}: Add the {', '.join(missing)} {plural} to {_LABELS_CONFIG}."


def _file_globs(rules: object, key: str | None = None) -> Iterator[str]:
    """Yield the file globs of a labeler match rule.

    Parameters
    ----------
    rules : object
        Match rules of one label, in the current or legacy labeler format.
    key : str or None, default: None
        Key under which ``rules`` is nested.

    Yields
    ------
    str
        Every string that is not a branch pattern.
    """
    if key in _BRANCH_KEYS:
        return
    if isinstance(rules, str):
        if rules:
            yield rules
    elif isinstance(rules, list):
        for rule in rules:
            yield from _file_globs(rule, key)
    elif isinstance(rules, dict):
        for nested_key, nested_rules in rules.items():
            yield from _file_globs(nested_rules, str(nested_key))


def _glob_regex(glob: str) -> re.Pattern[str]:
    """Translate a labeler glob into a regular expression.

    Parameters
    ----------
    glob : str
        Glob in the minimatch syntax that the labeler action uses, where
        ``**`` crosses directories and ``*`` does not.

    Returns
    -------
    re.Pattern[str]
        A pattern that matches whole repository-relative paths.
    """
    parts = []
    index = 0
    while index < len(glob):
        if glob.startswith("**/", index):
            parts.append("(?:.*/)?")
            index += 3
        elif glob.startswith("**", index):
            parts.append(".*")
            index += 2
        elif glob[index] == "*":
            parts.append("[^/]*")
            index += 1
        elif glob[index] == "?":
            parts.append("[^/]")
            index += 1
        else:
            parts.append(re.escape(glob[index]))
            index += 1
    return re.compile("".join(parts))


class Labels(ABC):
    """GitHub label rule family.

    Base class of the label quality rules. Each rule is a subclass named
    ``LB<nnn>`` with a static ``check`` method that evaluates the label
    configuration independently. Missing or unreadable configuration is
    reported as an error rather than skipped.
    """

    family: ClassVar[str] = "labels"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a label rule.

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
            prefixed with ``"ERROR: "``, ``"WARNING: "``, or
            ``"RECOMMENDATION: "``.
        """
        raise NotImplementedError


class LB001(Labels):
    """The .github/labeler.yml file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the labeler configuration exists."""
        return file_exists(repository_root, _LABELER_CONFIG)


class LB002(Labels):
    """The .github/labels.yml file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the labels configuration exists."""
        return file_exists(repository_root, _LABELS_CONFIG)


class LB003(Labels):
    """Labels.yml has a bug label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the bug label is declared."""
        return _check_labels(repository_root, ("bug",), "ERROR")


class LB004(Labels):
    """Labels.yml has an enhancement label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the enhancement label is declared."""
        return _check_labels(repository_root, ("enhancement",), "ERROR")


class LB005(Labels):
    """Labels.yml has a documentation label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation label is declared."""
        return _check_labels(repository_root, ("documentation",), "ERROR")


class LB006(Labels):
    """Labeler.yml maps labels to match rules."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the labeler configuration has a valid structure."""
        labeler = _load_labeler(repository_root)
        return labeler if isinstance(labeler, str) else True


class LB007(Labels):
    """Labeler.yml only assigns labels declared in labels.yml."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every labeler label is declared in labels.yml."""
        labeler = _load_labeler(repository_root)
        if isinstance(labeler, str):
            return labeler
        names = _label_names(repository_root)
        if isinstance(names, str):
            return names
        undeclared = [str(label) for label in labeler if _normalize(str(label)) not in names]
        if not undeclared:
            return True
        return (
            f"ERROR: {_LABELER_CONFIG} assigns labels missing from {_LABELS_CONFIG}: "
            f"{', '.join(undeclared)}."
        )


class LB008(Labels):
    """Labels.yml has no duplicate labels."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that label names are unique, ignoring case."""
        labels = _load_labels(repository_root)
        if isinstance(labels, str):
            return labels
        seen: set[str] = set()
        duplicates: list[str] = []
        for label in labels:
            name = str(label["name"]).strip()
            if _normalize(name) in seen:
                duplicates.append(name)
            seen.add(_normalize(name))
        if not duplicates:
            return True
        return f"ERROR: {_LABELS_CONFIG} declares duplicate labels: {', '.join(duplicates)}."


class LB009(Labels):
    """Labels.yml labels have a valid color."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every label has a six-digit hexadecimal color."""
        labels = _load_labels(repository_root)
        if isinstance(labels, str):
            return labels
        invalid = [
            str(label["name"]).strip()
            for label in labels
            if not isinstance(label.get("color"), str)
            or not _COLOR.fullmatch(str(label["color"]).strip())
        ]
        if not invalid:
            return True
        return (
            f"WARNING: Set a six-digit hexadecimal color for these labels in {_LABELS_CONFIG}: "
            f"{', '.join(invalid)}."
        )


class LB010(Labels):
    """Labels.yml labels have a description."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every label has a non-empty description."""
        labels = _load_labels(repository_root)
        if isinstance(labels, str):
            return labels
        undescribed = [
            str(label["name"]).strip()
            for label in labels
            if not isinstance(label.get("description"), str)
            or not str(label["description"]).strip()
        ]
        if not undescribed:
            return True
        return (
            f"RECOMMENDATION: Describe these labels in {_LABELS_CONFIG}: {', '.join(undescribed)}."
        )


class LB011(Labels):
    """Labels.yml has a dependencies label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the dependencies label used by Dependabot is declared."""
        return _check_labels(repository_root, ("dependencies",), "WARNING")


class LB012(Labels):
    """Labels.yml has ci, tests, maintenance, and release labels."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the recommended project labels are declared."""
        return _check_labels(repository_root, _RECOMMENDED_LABELS, "RECOMMENDATION")


class LB013(Labels):
    """Labels.yml has a style:skip label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the label that skips style checks is declared."""
        return _check_labels(repository_root, ("style:skip",), "RECOMMENDATION")


class LB014(Labels):
    """Labels.yml has a good first issue label."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the label for newcomer issues is declared."""
        return _check_labels(repository_root, ("good first issue",), "RECOMMENDATION")


class LB015(Labels):
    """Labeler.yml labels documentation and workflow changes."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that file globs match documentation and workflow files.

        Returns
        -------
        bool or str
            ``True`` when globs match both ``doc/source/index.rst`` and
            ``.github/workflows/ci_cd.yml``, otherwise a
            ``"RECOMMENDATION: ..."`` message naming the uncovered changes.
        """
        labeler = _load_labeler(repository_root)
        if isinstance(labeler, str):
            return labeler
        patterns = [
            _glob_regex(glob)
            for rules in labeler.values()
            for glob in _file_globs(rules)
            if not glob.startswith("!")
        ]
        uncovered = [
            change
            for change, path in _COVERED_PATHS.items()
            if not any(pattern.fullmatch(path) for pattern in patterns)
        ]
        if not uncovered:
            return True
        return (
            f"RECOMMENDATION: Add {_LABELER_CONFIG} rules that label "
            f"{' and '.join(uncovered)} changes."
        )


class LB016(Labels):
    """A workflow syncs labels.yml to GitHub."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a workflow uses a label synchronization action."""
        workflows = all_workflows_content(repository_root)
        if workflows is not None and _LABEL_SYNC_ACTION.search(workflows):
            return True
        return (
            f"WARNING: No workflow syncs {_LABELS_CONFIG} to GitHub. "
            "Use an action such as micnncim/action-label-syncer."
        )


class LB017(Labels):
    """No legacy .yaml label files remain."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check for ``.yaml`` copies of the label configuration files."""
        legacy = [path for path in _LEGACY_CONFIGS if file_exists(repository_root, path)]
        if not legacy:
            return True
        return (
            f"RECOMMENDATION: Remove {', '.join(legacy)}; the labeler workflows read "
            f"{_LABELER_CONFIG} and {_LABELS_CONFIG}."
        )
