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

"""Tests for the GitHub label quality rule family."""

import json
from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import LABELS_QUALITY_RULES, Labels, repo_review_checks
from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult

_RULE_IDS = tuple(f"LB{number:03d}" for number in range(1, 17))
_LABEL_RULE_IDS = {"LB003": "bug", "LB004": "enhancement", "LB005": "documentation"}
_LABELS_RULE_IDS = ("LB003", "LB004", "LB005", "LB007", "LB008", "LB009", "LB010", "LB011")
_LABELER_RULE_IDS = ("LB006", "LB007", "LB014")
_VALID_LABELS = """\
- name: bug
  description: Something isn't working
  color: d42a34

- name: documentation
  description: Improvements or additions to documentation
  color: 0677ba

- name: enhancement
  description: New features or code improvements
  color: FFD827

- name: dependencies
  description: Related with project dependencies
  color: ffc0cb

- name: ci
  description: Pipelines maintenance related
  color: a9a9a9

- name: tests
  description: Related with improvements of the test suite
  color: ffd8b1

- name: maintenance
  description: Package and maintenance related
  color: f78c37

- name: release
  description: Anything related to an incoming release
  color: '000000'

- name: style:skip
  description: Skip style runs in CI/CD
  color: '#dcbeff'

- name: good first issue
  description: Easy to solve for newcomers
  color: 000000
"""
_VALID_LABELER = """\
# -- Labels based on PR title
enhancement:

documentation:
- changed-files:
  - any-glob-to-any-file: ['doc/source/**/*.rst']

ci:
- changed-files:
  - any-glob-to-any-file: ['.github/workflows/**']
"""
_LABEL_WORKFLOW = """\
jobs:
  label-syncer:
    steps:
      - uses: micnncim/action-label-syncer@3abd5ab72fda571e69fffd97bd4e0033dd5f495c # v1.3.0
"""


def _write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_labels(root: Path, content: str = _VALID_LABELS) -> None:
    _write(root, ".github/labels.yml", content)


def _write_labeler(root: Path, content: str = _VALID_LABELER) -> None:
    _write(root, ".github/labeler.yml", content)


def _write_repository(root: Path) -> None:
    _write_labels(root)
    _write_labeler(root)
    _write(root, ".github/workflows/label.yml", _LABEL_WORKFLOW)


def _check(root: Path, rule_id: str) -> RuleCheckResult:
    return repo_review_checks(["labels"])[rule_id].check(root, None)


def _statuses(root: Path) -> dict[str, str]:
    results = report._run_checks(root, selected_families={"labels"})["results"]
    return {result["id"]: result["status"] for result in results}


def _assert_status(result: RuleCheckResult, prefix: str, *expected: str) -> None:
    assert isinstance(result, str)
    assert result.startswith(f"{prefix}: ")
    for text in expected:
        assert text in result


def test_registry_contains_all_label_rules() -> None:
    rules = repo_review_checks(["labels"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "labels" for rule in rules.values())
    assert len(LABELS_QUALITY_RULES) == 16
    assert all(issubclass(rule, Labels) for rule in LABELS_QUALITY_RULES)


def test_all_rules_pass_for_complete_configuration(tmp_path: Path) -> None:
    _write_repository(tmp_path)

    for rule in repo_review_checks(["labels"]).values():
        assert rule.check(tmp_path, None) is True


def test_missing_configuration_is_an_error(tmp_path: Path) -> None:
    results = report._run_checks(tmp_path, selected_families={"labels"})["results"]
    details = {result["id"]: result["detail"] for result in results}
    statuses = {result["id"]: result["status"] for result in results}

    assert statuses.pop("LB015") == "WARNING"
    assert statuses.pop("LB016") == "PASSED"
    assert set(statuses.values()) == {"ERROR"}
    for rule_id in _LABEL_RULE_IDS:
        assert ".github/labels.yml" in details[rule_id]
    for rule_id in _LABELER_RULE_IDS:
        assert ".github/labeler.yml" in details[rule_id]


@pytest.mark.parametrize(
    ("file_name", "failing"),
    [
        ("labeler.yml", {"LB001", *_LABELER_RULE_IDS}),
        ("labels.yml", {"LB002", *_LABELS_RULE_IDS, "LB012", "LB013"}),
    ],
)
def test_configuration_files_are_checked_independently(
    tmp_path: Path, file_name: str, failing: set[str]
) -> None:
    _write_repository(tmp_path)
    (tmp_path / ".github" / file_name).unlink()

    statuses = _statuses(tmp_path)

    assert {rule_id for rule_id, status in statuses.items() if status == "ERROR"} == failing
    assert {statuses[rule_id] for rule_id in set(statuses) - failing} == {"PASSED"}


def test_configuration_must_be_a_file(tmp_path: Path) -> None:
    (tmp_path / ".github" / "labels.yml").mkdir(parents=True)
    (tmp_path / ".github" / "labeler.yml").mkdir()

    statuses = _statuses(tmp_path)

    assert {statuses[rule_id] for rule_id in _RULE_IDS[:14]} == {"ERROR"}


def test_configuration_symlink_outside_repository_is_an_error(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "labels.yml"
    outside.write_text(_VALID_LABELS, encoding="utf-8")
    (repository / ".github").mkdir(parents=True)
    (repository / ".github" / "labels.yml").symlink_to(outside)

    statuses = _statuses(repository)

    assert {statuses[rule_id] for rule_id in ("LB002", *_LABEL_RULE_IDS)} == {"ERROR"}


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"\xff\xfe", "UTF-8"),
        (b"- name: [bug\n", "Invalid YAML"),
        (b"", "list of labels"),
        (b"'ERROR: not a list'\n", "list of labels"),
        (b"bug: {}\n", "list of labels"),
        (b"- name: bug\n- color: d42a34\n", "list of labels"),
        (b"- name: [bug]\n", "list of labels"),
        (b"- name: ' '\n", "list of labels"),
    ],
)
def test_unreadable_or_invalid_labels_are_an_error(
    tmp_path: Path, content: bytes, expected: str
) -> None:
    _write_labeler(tmp_path)
    (tmp_path / ".github" / "labels.yml").write_bytes(content)

    for rule_id in _LABELS_RULE_IDS:
        _assert_status(_check(tmp_path, rule_id), "ERROR", expected)


@pytest.mark.parametrize(("rule_id", "label"), _LABEL_RULE_IDS.items())
def test_required_labels_are_checked_independently(
    tmp_path: Path, rule_id: str, label: str
) -> None:
    _write_labels(tmp_path, _VALID_LABELS.replace(f"- name: {label}\n", "- name: other\n"))

    statuses = {other: _check(tmp_path, other) for other in _LABEL_RULE_IDS}

    assert statuses.pop(rule_id) == f"ERROR: Add the {label} label to .github/labels.yml."
    assert set(statuses.values()) == {True}


def test_label_names_are_case_insensitive(tmp_path: Path) -> None:
    _write_labels(
        tmp_path,
        "- name: Bug\n- name: ' ENHANCEMENT '\n- name: Documentation\n",
    )

    for rule_id in _LABEL_RULE_IDS:
        assert _check(tmp_path, rule_id) is True


@pytest.mark.parametrize(
    "content",
    [
        b"\xff\xfe",
        b"ci: [\n",
        b"",
        b"- ci\n",
        b"'ERROR: not a mapping'\n",
        b"ci: '.github/**'\n",
    ],
)
def test_invalid_labeler_is_an_error(tmp_path: Path, content: bytes) -> None:
    _write_labels(tmp_path)
    (tmp_path / ".github" / "labeler.yml").write_bytes(content)

    for rule_id in _LABELER_RULE_IDS:
        _assert_status(_check(tmp_path, rule_id), "ERROR", ".github/labeler.yml")


def test_labeler_labels_must_be_declared(tmp_path: Path) -> None:
    _write_labels(tmp_path)
    _write_labeler(tmp_path, f"{_VALID_LABELER}Docs:\n- 'doc/**'\nstyle:\n- 'src/**'\n")

    _assert_status(_check(tmp_path, "LB007"), "ERROR", "Docs, style")


def test_labeler_labels_are_matched_case_insensitively(tmp_path: Path) -> None:
    _write_labels(tmp_path)
    _write_labeler(tmp_path, _VALID_LABELER.replace("documentation:", "Documentation:"))

    assert _check(tmp_path, "LB007") is True


def test_duplicate_labels_are_an_error(tmp_path: Path) -> None:
    _write_labels(tmp_path, f"{_VALID_LABELS}- name: Bug\n- name: ' ci '\n")

    _assert_status(_check(tmp_path, "LB008"), "ERROR", "Bug, ci")


@pytest.mark.parametrize("color", ["", "color: red\n", "color: d42a3\n", "color: '#d42a34ff'\n"])
def test_label_colors_must_be_hexadecimal(tmp_path: Path, color: str) -> None:
    _write_labels(tmp_path, f"{_VALID_LABELS}- name: extra\n  description: Extra\n  {color}")

    _assert_status(_check(tmp_path, "LB009"), "WARNING", "extra")


@pytest.mark.parametrize("description", ["", "description: ''\n", "description: {}\n"])
def test_label_descriptions_are_recommended(tmp_path: Path, description: str) -> None:
    _write_labels(tmp_path, f"{_VALID_LABELS}- name: extra\n  color: d42a34\n  {description}")

    _assert_status(
        _check(tmp_path, "LB010"),
        "RECOMMENDATION",
        "contributors know what each label means: extra",
    )


@pytest.mark.parametrize(
    ("rule_id", "removed", "status", "expected"),
    [
        ("LB011", ("dependencies",), "WARNING", "dependencies label"),
        (
            "LB012",
            ("ci",),
            "RECOMMENDATION",
            "ci label to .github/labels.yml. These labels categorize CI, test, maintenance, "
            "and release work.",
        ),
        (
            "LB012",
            ("tests", "release"),
            "RECOMMENDATION",
            "tests, release labels to .github/labels.yml. These labels categorize CI, test, "
            "maintenance, and release work.",
        ),
        (
            "LB013",
            ("good first issue",),
            "RECOMMENDATION",
            "good first issue label to .github/labels.yml. This helps newcomers find "
            "approachable tasks.",
        ),
    ],
)
def test_recommended_labels_are_checked(
    tmp_path: Path, rule_id: str, removed: tuple[str, ...], status: str, expected: str
) -> None:
    content = _VALID_LABELS
    for label in removed:
        content = content.replace(f"- name: {label}\n", "- name: other\n", 1)
    _write_labels(tmp_path, content)

    _assert_status(_check(tmp_path, rule_id), status, expected)


@pytest.mark.parametrize(
    ("labeler", "uncovered"),
    [
        (_VALID_LABELER, None),
        ("documentation:\n- 'doc/**'\nci:\n- '.github/**/*'\n", None),
        ("documentation:\n- any: ['doc/source/*.rst', '.github/workflows/*.yml']\n", None),
        (
            "ci:\n- head-branch: ['doc/source/index.rst', '.github/workflows/ci_cd.yml']\n",
            "documentation and workflow",
        ),
        ("documentation:\n- '!doc/**'\n- 'src/**'\nci:\n- '.github/*'\n", "documentation and"),
        ("documentation:\n- 'doc/*.rst'\nci:\n- '.github/workflows/**'\n", "documentation"),
        ("ci:\n- 'doc/source/**'\n", "workflow"),
    ],
)
def test_labeler_covers_documentation_and_workflow_changes(
    tmp_path: Path, labeler: str, uncovered: str | None
) -> None:
    _write_labeler(tmp_path, labeler)

    result = _check(tmp_path, "LB014")

    if uncovered is None:
        assert result is True
    else:
        _assert_status(result, "RECOMMENDATION", f"label {uncovered}")


@pytest.mark.parametrize(
    ("step", "passes"),
    [
        ("- uses: micnncim/action-label-syncer@v1", True),
        ("- uses: 'EndBug/label-sync@v2'", True),
        ("- uses: crazy-max/ghaction-github-labeler@v5", True),
        ("- uses: actions/labeler@v5", False),
        ("# - uses: micnncim/action-label-syncer@v1", False),
    ],
)
def test_workflow_must_sync_labels(tmp_path: Path, step: str, passes: bool) -> None:
    _write(tmp_path, ".github/workflows/label.yml", f"jobs:\n  label:\n    steps:\n      {step}\n")

    result = _check(tmp_path, "LB015")

    if passes:
        assert result is True
    else:
        _assert_status(result, "WARNING", "micnncim/action-label-syncer")


@pytest.mark.parametrize("legacy", [".github/labeler.yaml", ".github/labels.yaml"])
def test_legacy_label_files_are_reported(tmp_path: Path, legacy: str) -> None:
    _write_repository(tmp_path)
    _write(tmp_path, legacy, "[]\n")

    _assert_status(
        _check(tmp_path, "LB016"), "RECOMMENDATION", legacy, "use the matching .yml file instead"
    )


def test_cli_lists_label_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert report.main(["--metadata", "--family", "labels"]) == 0

    metadata = json.loads(capsys.readouterr().out)

    assert [rule["id"] for rule in metadata] == list(_RULE_IDS)
    assert all(rule["family"] == "labels" for rule in metadata)


def test_cli_reports_label_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_repository(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "labels"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [result["id"] for result in payload["results"]] == list(_RULE_IDS)
    assert payload["tally"] == {"PASSED": 16, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 0}

    _write_labels(tmp_path, "- name: bug\n")
    assert report.main(["--json", "--family", "labels"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 8, "RECOMMENDATION": 3, "WARNING": 2, "ERROR": 3}
