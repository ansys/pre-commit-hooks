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

_RULE_IDS = tuple(f"SEC{number:03d}" for number in range(1, 8))
_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
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
_SECURITY_POLICY = """\
# Security Policy

> [!CAUTION]
> Do not use GitHub issues to report any security vulnerabilities.
"""


def _write(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_repository(root: Path) -> None:
    _write(root, ".github/zizmor.yml", _ZIZMOR)
    _write(root, ".pre-commit-config.yaml", _PRE_COMMIT)
    _write(root, "SECURITY.md", _SECURITY_POLICY)
    _write(root, "pyproject.toml", '[tool.uv]\nexclude-newer = "7 days"\n')
    _write(root, "uv.lock", "version = 1\n")


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
        "SEC004": "ERROR",
        "SEC005": "ERROR",
        "SEC006": "ERROR",
        "SEC007": "ERROR",
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


@pytest.mark.parametrize("path", [".github/SECURITY.md", "docs/SECURITY.md"])
def test_security_policy_must_be_at_the_root_only(tmp_path: Path, path: str) -> None:
    _write(tmp_path, path, _SECURITY_POLICY)
    _assert_status(_check(tmp_path, "SEC004"), "ERROR", "only at the repository root", path)

    _write(tmp_path, "SECURITY.md", _SECURITY_POLICY)
    _assert_status(_check(tmp_path, "SEC004"), "ERROR", path)


def test_security_policy_must_discourage_public_issues(tmp_path: Path) -> None:
    _write(tmp_path, "SECURITY.md", "Open an issue if you find a vulnerability.\n")

    _assert_status(_check(tmp_path, "SEC004"), "ERROR", "SECURITY.md", "public GitHub issues")


def test_pre_commit_repositories_must_be_pinned(tmp_path: Path) -> None:
    _write(
        tmp_path,
        ".pre-commit-config.yaml",
        _PRE_COMMIT + "- repo: https://github.com/a/b\n  rev: v1.0.0\n  hooks:\n  - id: b\n",
    )

    _assert_status(
        _check(tmp_path, "SEC005"), "RECOMMENDATION", "--freeze", ": https://github.com/a/b."
    )


@pytest.mark.parametrize("lockfile", ["uv.lock", "poetry.lock"])
def test_lockfile_is_required(tmp_path: Path, lockfile: str) -> None:
    _assert_status(_check(tmp_path, "SEC006"), "ERROR", "uv.lock or poetry.lock")

    _write(tmp_path, lockfile, "")
    assert _check(tmp_path, "SEC006") is True


def test_uv_lockfile_requires_exact_seven_day_release_age(tmp_path: Path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    _write(tmp_path, "pyproject.toml", '[tool.uv]\nexclude-newer = "7 days"\n')

    assert _check(tmp_path, "SEC007") is True


def test_uv_release_age_must_be_exactly_seven_days(tmp_path: Path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    _write(tmp_path, "pyproject.toml", '[tool.uv]\nexclude-newer = "6 days"\n')

    _assert_status(_check(tmp_path, "SEC007"), "ERROR", 'exclude-newer to exactly 7')


def test_poetry_lockfile_requires_minimum_release_age(tmp_path: Path) -> None:
    _write(tmp_path, "poetry.lock", "")
    _write(tmp_path, "poetry.toml", "[solver]\nmin-release-age = 7\n")

    assert _check(tmp_path, "SEC007") is True


def test_poetry_release_age_must_be_exactly_seven_days(tmp_path: Path) -> None:
    _write(tmp_path, "poetry.lock", "")
    _write(tmp_path, "poetry.toml", f"[solver]\nmin-release-age = 6\n")

    _assert_status(_check(tmp_path, "SEC007"), "ERROR", 'min-release-age to exactly 7')


def test_security_report_includes_release_age_rule(tmp_path: Path) -> None:
    _write(tmp_path, "uv.lock", "version = 1\n")
    _write(tmp_path, "pyproject.toml", '[tool.uv]\nexclude-newer = "7 days"\n')

    result = report._run_checks(tmp_path, selected_rule_ids={"SEC007"})["results"]

    assert len(result) == 1
    assert result[0]["id"] == "SEC007"
    assert result[0]["family"] == "security"
    assert result[0]["status"] == "PASSED"
