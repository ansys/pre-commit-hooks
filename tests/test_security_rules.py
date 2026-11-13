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


"""Tests for the security quality rule family."""

from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import (
    SECURITY_QUALITY_RULES,
    Security,
    repo_review_checks,
)
from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult

_RULE_IDS = tuple(f"SEC{number:03d}" for number in range(1, 11))
_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
_DIGEST = "sha256:" + "a" * 64
_ZIZMOR = """\
rules:
  unpinned-uses:
    disable: true
  secrets-outside-env:
    disable: true
"""
_PRE_COMMIT = f"""\
repos:
- repo: https://github.com/gitleaks/gitleaks
  rev: {_SHA}  # v8.30.0
  hooks:
  - id: gitleaks
- repo: local
  hooks:
  - id: custom
    name: custom
    entry: custom
    language: system
"""
_WORKFLOW = f"""\
name: CI
on:
  pull_request:
permissions: {{}}
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@{_SHA} # v4.2.2
        with:
          persist-credentials: false
      - uses: "actions/setup-python@{_SHA}" # v5.6.0
      - uses: ./.github/actions/local
      - uses: docker://alpine@{_DIGEST}
"""
_SECURITY_POLICY = """\
# Security Policy

> [!CAUTION]
> Do not use GitHub issues to report any security vulnerabilities.
"""


def _write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_workflow(root: Path, content: str, name: str = "ci.yml") -> None:
    _write(root, f".github/workflows/{name}", content)


def _write_repository(root: Path) -> None:
    _write(root, ".github/zizmor.yml", _ZIZMOR)
    _write(root, ".pre-commit-config.yaml", _PRE_COMMIT)
    _write(root, "SECURITY.md", _SECURITY_POLICY)
    _write_workflow(root, _WORKFLOW)


def _check(root: Path, rule_id: str) -> RuleCheckResult:
    return repo_review_checks(["security"])[rule_id].check(root, None)


def _assert_status(result: RuleCheckResult, prefix: str, *expected: str) -> None:
    assert isinstance(result, str)
    assert result.startswith(f"{prefix}: ")
    for text in expected:
        assert text in result


def test_registry_contains_all_security_rules() -> None:
    rules = repo_review_checks(["security"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "security" for rule in rules.values())
    assert all(issubclass(rule, Security) for rule in SECURITY_QUALITY_RULES)


def test_all_rules_pass_for_compliant_repository(tmp_path: Path) -> None:
    _write_repository(tmp_path)

    for rule_id, rule in repo_review_checks(["security"]).items():
        assert rule.check(tmp_path, None) is True, rule_id


def test_missing_configuration(tmp_path: Path) -> None:
    results = report._run_checks(tmp_path, selected_families={"security"})["results"]
    statuses = {result["id"]: result["status"] for result in results}

    assert statuses == {
        "SEC001": "RECOMMENDATION",
        "SEC002": "PASSED",
        "SEC003": "ERROR",
        "SEC004": "WARNING",
        "SEC005": "ERROR",
        "SEC006": "WARNING",
        "SEC007": "WARNING",
        "SEC008": "WARNING",
        "SEC009": "WARNING",
        "SEC010": "ERROR",
    }


@pytest.mark.parametrize(
    "content",
    [
        "rules:\n  unpinned-uses:\n    disable: true\n",
        "rules:\n  secrets-outside-env:\n    disable: false\n",
        "secrets-outside-env:\n  disable: true\n",
        "[]\n",
    ],
)
def test_zizmor_config_must_disable_secrets_outside_env(tmp_path: Path, content: str) -> None:
    _write(tmp_path, ".github/zizmor.yml", content)

    _assert_status(_check(tmp_path, "SEC002"), "ERROR", "rules: secrets-outside-env: disable")


def test_invalid_zizmor_config_is_an_error(tmp_path: Path) -> None:
    _write(tmp_path, ".github/zizmor.yml", "rules: [\n")

    _assert_status(_check(tmp_path, "SEC002"), "ERROR", "Invalid YAML in .github/zizmor.yml")


@pytest.mark.parametrize(("hook_id", "passes"), [("gitleaks-docker", True), ("trufflehog", False)])
def test_gitleaks_hook_is_required(tmp_path: Path, hook_id: str, passes: bool) -> None:
    _write(
        tmp_path, ".pre-commit-config.yaml", _PRE_COMMIT.replace("id: gitleaks", f"id: {hook_id}")
    )

    result = _check(tmp_path, "SEC003")

    if passes:
        assert result is True
    else:
        _assert_status(result, "ERROR", "gitleaks hook")


@pytest.mark.parametrize(
    "reference",
    [
        "actions/checkout@v4",
        f"actions/checkout@{_SHA[:7]}",
        "actions/checkout",
        "docker://alpine:3.20",
        "ansys/actions/.github/workflows/build.yml@main",
    ],
)
def test_actions_must_be_pinned_to_a_sha(tmp_path: Path, reference: str) -> None:
    _write_workflow(tmp_path, _WORKFLOW)
    _write_workflow(tmp_path, f"jobs:\n  a:\n    steps:\n      - uses: {reference}\n", "other.yml")

    _assert_status(_check(tmp_path, "SEC004"), "ERROR", f"commit SHA: {reference}.")


@pytest.mark.parametrize("comment", ["", "  # pinned", "  #"])
def test_pinned_actions_need_a_version_comment(tmp_path: Path, comment: str) -> None:
    _write_workflow(tmp_path, f"jobs:\n  a:\n    steps:\n      - uses: a/b@{_SHA}{comment}\n")

    _assert_status(_check(tmp_path, "SEC006"), "RECOMMENDATION", f"a/b@{_SHA}.")
    assert _check(tmp_path, "SEC004") is True


@pytest.mark.parametrize(
    ("path", "content"),
    [
        (".github/SECURITY.md", _SECURITY_POLICY),
        (
            "docs/SECURITY.md",
            "Please don't report security vulnerabilities through public GitHub issues.",
        ),
    ],
)
def test_security_policy_locations_and_wording(tmp_path: Path, path: str, content: str) -> None:
    _write(tmp_path, path, content)

    assert _check(tmp_path, "SEC005") is True


def test_security_policy_must_discourage_public_issues(tmp_path: Path) -> None:
    _write(tmp_path, "SECURITY.md", "Open an issue if you find a vulnerability.\n")

    _assert_status(_check(tmp_path, "SEC005"), "ERROR", "SECURITY.md", "public GitHub issues")


@pytest.mark.parametrize(
    ("workflow", "passes"),
    [
        ("jobs:\n  a:\n    runs-on: x\n", False),
        ("jobs:\n  a:\n    permissions: {}\n  b:\n    runs-on: x\n", False),
        ("jobs:\n  a:\n    permissions: {}\n  b:\n    permissions:\n      contents: read\n", True),
        ("permissions: read-all\njobs: {}\n", True),
    ],
)
def test_workflows_must_declare_permissions(tmp_path: Path, workflow: str, passes: bool) -> None:
    _write_workflow(tmp_path, workflow)

    result = _check(tmp_path, "SEC007")

    if passes:
        assert result is True
    else:
        _assert_status(result, "WARNING", ".github/workflows/ci.yml")


@pytest.mark.parametrize(
    ("options", "passes"),
    [
        ("", False),
        ("\n        with:\n          persist-credentials: true", False),
        ("\n        with:\n          fetch-depth: 0", False),
        ("\n        with:\n          persist-credentials: False", True),
    ],
)
def test_checkout_must_not_persist_credentials(tmp_path: Path, options: str, passes: bool) -> None:
    _write_workflow(
        tmp_path, f"jobs:\n  a:\n    steps:\n      - uses: actions/checkout@{_SHA}{options}\n"
    )

    result = _check(tmp_path, "SEC008")

    if passes:
        assert result is True
    else:
        _assert_status(result, "WARNING", "persist-credentials: false", ".github/workflows/ci.yml")


@pytest.mark.parametrize(
    "trigger",
    [
        "on: pull_request_target\n",
        "on: [push, pull_request_target]\n",
        "on:\n  pull_request_target:\n    types: [opened]\n",
    ],
)
def test_pull_request_target_is_reported(tmp_path: Path, trigger: str) -> None:
    _write_workflow(tmp_path, f"{trigger}jobs: {{}}\n")

    _assert_status(_check(tmp_path, "SEC009"), "WARNING", "pull_request_target", "ci.yml")


def test_invalid_workflow_is_an_error(tmp_path: Path) -> None:
    _write_workflow(tmp_path, "jobs: [\n")

    _assert_status(_check(tmp_path, "SEC007"), "ERROR", "Invalid YAML in .github/workflows/ci.yml")


def test_pre_commit_repositories_must_be_pinned(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".pre-commit-config.yaml",
        _PRE_COMMIT + "- repo: https://github.com/a/b\n  rev: v1.0.0\n  hooks:\n  - id: b\n",
    )

    _assert_status(
        _check(tmp_path, "SEC010"), "RECOMMENDATION", "--freeze", ": https://github.com/a/b."
    )
