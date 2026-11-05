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

"""Tests for the pre-commit quality rule family."""

import json
from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import (
    PRE_COMMIT_QUALITY_RULES,
    PreCommit,
    repo_review_checks,
)

_RULE_IDS = tuple(f"PC{number:03d}" for number in range(1, 11))
_RECOMMENDED_HOOKS = {
    "PC007": "check-merge-conflict",
    "PC008": "debug-statements",
    "PC009": "check-yaml",
    "PC010": "trailing-whitespace",
}
_VALID_CONFIGURATION = """\
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  hooks:
  - id: ruff-check
  - id: ruff-format
- repo: https://github.com/zizmorcore/zizmor-pre-commit
  hooks:
  - id: zizmor
    args: [--pedantic]
- repo: https://github.com/codespell-project/codespell
  hooks:
  - id: codespell
- repo: https://github.com/ansys/pre-commit-hooks
  hooks:
  - id: pyansys-quality-report
- repo: local
  hooks:
  - id: mypy
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: 3e8a8703264a2f4a69428a0aa4dcb512790b2c8c  # frozen: v6.0.0
  hooks:
  - id: check-merge-conflict
  - id: debug-statements
  - id: check-yaml
  - id: trailing-whitespace
"""


def _write_configuration(root: Path, content: str = _VALID_CONFIGURATION) -> None:
    (root / ".pre-commit-config.yaml").write_text(content, encoding="utf-8")


def test_registry_contains_all_pre_commit_rules() -> None:
    rules = repo_review_checks(["pre_commit"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "pre_commit" for rule in rules.values())
    assert len(PRE_COMMIT_QUALITY_RULES) == 10
    assert all(issubclass(rule, PreCommit) for rule in PRE_COMMIT_QUALITY_RULES)


def test_all_rules_pass_for_complete_configuration(tmp_path: Path) -> None:
    _write_configuration(tmp_path)

    for rule in repo_review_checks(["pre_commit"]).values():
        assert rule.check(tmp_path, None) is True


def test_pre_commit_runs_by_default_without_removing_existing_families(tmp_path: Path) -> None:
    _write_configuration(tmp_path)

    results = report._run_checks(tmp_path)["results"]
    pre_commit_results = [result for result in results if result["family"] == "pre_commit"]

    assert {result["family"] for result in results} == {
        "readme",
        "project_metadata",
        "cicd",
        "pre_commit",
        "dependabot",
    }
    assert tuple(result["id"] for result in pre_commit_results) == _RULE_IDS
    assert all(result["status"] == "PASSED" for result in pre_commit_results)


@pytest.mark.parametrize("rule_id", _RULE_IDS)
def test_missing_configuration_is_an_error(tmp_path: Path, rule_id: str) -> None:
    results = report._run_checks(tmp_path, selected_rule_ids={rule_id})["results"]

    assert len(results) == 1
    assert results[0]["status"] == "ERROR"
    assert ".pre-commit-config.yaml" in results[0]["detail"]


def test_configuration_must_be_a_file(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").mkdir()

    results = report._run_checks(tmp_path, selected_families={"pre_commit"})["results"]

    assert all(result["status"] == "ERROR" for result in results)


@pytest.mark.parametrize(
    "content",
    [
        "",
        "null\n",
        "[]\n",
        "true\n",
        "repos: [\n",
        "repos: null\n",
        "repos: {}\n",
        "ci: {autofix_prs: true}\n",
        "1: value\nrepos: []\n",
        "!!python/object/apply:builtins.print [unsafe]\n",
    ],
)
def test_invalid_configuration_reports_errors(tmp_path: Path, content: str) -> None:
    _write_configuration(tmp_path, content)

    review = report._run_checks(tmp_path, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 1, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 9}
    assert all(result["detail"] for result in review["results"] if result["id"] != "PC001")


def test_non_utf8_configuration_reports_errors(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_bytes(b"\xff")

    review = report._run_checks(tmp_path, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 1, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 9}


def test_configuration_cannot_escape_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside_file = tmp_path / "outside.yaml"
    outside_file.write_text(_VALID_CONFIGURATION, encoding="utf-8")
    (repository / ".pre-commit-config.yaml").symlink_to(outside_file)

    review = report._run_checks(repository, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 0, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 10}


@pytest.mark.parametrize("option", ["--pedantic", "--persona=pedantic"])
def test_zizmor_accepts_each_pedantic_option(tmp_path: Path, option: str) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace("--pedantic", option))

    assert repo_review_checks()["PC003"].check(tmp_path, None) is True


@pytest.mark.parametrize(
    "arguments",
    ["[]", "null", "--pedantic", "{}", "[--persona=regular]", "[null, {}, false]"],
)
def test_zizmor_warns_without_pedantic_list_argument(tmp_path: Path, arguments: str) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace("[--pedantic]", arguments))

    result = repo_review_checks()["PC003"].check(tmp_path, None)

    assert isinstance(result, str)
    assert result.startswith("RECOMMENDATION: Enable --pedantic")


def test_zizmor_accepts_any_pedantic_hook(tmp_path: Path) -> None:
    _write_configuration(
        tmp_path,
        "repos:\n- repo: local\n  hooks:\n  - id: zizmor\n  - id: zizmor\n    args: [--pedantic]\n",
    )

    assert repo_review_checks()["PC003"].check(tmp_path, None) is True


@pytest.mark.parametrize("hook_id", ["pyright", "mypy", "ty"])
def test_each_supported_type_checker_passes(tmp_path: Path, hook_id: str) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace("id: mypy", f"id: {hook_id}"))

    assert repo_review_checks()["PC006"].check(tmp_path, None) is True


@pytest.mark.parametrize(
    "hooks",
    [
        "[]",
        "[null, 1, invalid]",
        "[{id: mypy-wrapper}]",
        "[{id: [mypy]}]",
        "[{id: other, additional_dependencies: [mypy]}]",
    ],
)
def test_type_checker_requires_exact_hook_id(tmp_path: Path, hooks: str) -> None:
    _write_configuration(tmp_path, f"repos:\n- repo: local\n  hooks: {hooks}\n")

    result = repo_review_checks()["PC006"].check(tmp_path, None)

    assert isinstance(result, str)
    assert result.startswith("RECOMMENDATION: Add a pyright, mypy, or ty hook; ")


@pytest.mark.parametrize("suffix", ["", "/", ".git", ".git/"])
@pytest.mark.parametrize("rule_id", ["PC002", "PC005"])
def test_repository_url_suffixes_are_supported(tmp_path: Path, suffix: str, rule_id: str) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace("ruff-pre-commit\n", f"ruff-pre-commit{suffix}\n").replace(
            "ansys/pre-commit-hooks\n", f"ansys/pre-commit-hooks{suffix}\n"
        ),
    )

    assert repo_review_checks()[rule_id].check(tmp_path, None) is True


@pytest.mark.parametrize(
    "repository",
    [
        "null",
        "local",
        "https://example.com/not-ruff-pre-commit",
        "https://github.com/other/pre-commit-hooks",
    ],
)
@pytest.mark.parametrize("rule_id", ["PC002", "PC005"])
def test_repository_checks_reject_unrelated_repositories(
    tmp_path: Path, repository: str, rule_id: str
) -> None:
    _write_configuration(tmp_path, f"repos:\n- repo: {repository}\n  hooks: [{{id: example}}]\n")

    assert repo_review_checks()[rule_id].check(tmp_path, None) is False


@pytest.mark.parametrize("hooks", ["[]", "null", "{}", "[null]", "[{name: example}]"])
@pytest.mark.parametrize("rule_id", ["PC002", "PC005"])
def test_repository_checks_require_configured_hooks(
    tmp_path: Path, hooks: str, rule_id: str
) -> None:
    _write_configuration(
        tmp_path,
        f"repos:\n- repo: https://github.com/astral-sh/ruff-pre-commit\n  hooks: {hooks}\n"
        f"- repo: https://github.com/ansys/pre-commit-hooks\n  hooks: {hooks}\n",
    )

    assert repo_review_checks()[rule_id].check(tmp_path, None) is False


def test_comments_and_unrelated_values_do_not_satisfy_checks(tmp_path: Path) -> None:
    commented_configuration = "\n".join(f"# {line}" for line in _VALID_CONFIGURATION.splitlines())
    _write_configuration(
        tmp_path,
        f"{commented_configuration}\nrepos: []\n"
        "autofix_prs: true\nautoupdate_schedule: weekly\n"
        "description: ruff-pre-commit codespell ansys/pre-commit-hooks pyright zizmor --pedantic\n",
    )

    review = report._run_checks(tmp_path, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 1, "RECOMMENDATION": 7, "WARNING": 0, "ERROR": 2}


@pytest.mark.parametrize(
    "ci_settings",
    [
        "",
        "ci: null",
        "ci: []",
        "ci: {}",
        "ci: {autofix_prs: false, autoupdate_schedule: monthly}",
        'ci: {autofix_prs: "true", autoupdate_schedule: "weekly-ish"}',
        "ci: {autofix_prs: 1, autoupdate_schedule: [weekly]}",
    ],
)
def test_ci_settings_are_not_checked(tmp_path: Path, ci_settings: str) -> None:
    _write_configuration(tmp_path, f"{_VALID_CONFIGURATION}\n{ci_settings}\n")

    review = report._run_checks(tmp_path, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 10, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 0}
    assert tuple(result["id"] for result in review["results"]) == _RULE_IDS


def test_malformed_repository_entries_do_not_crash_rules(tmp_path: Path) -> None:
    _write_configuration(
        tmp_path,
        "repos: [null, invalid, {}, {hooks: null}, {hooks: {}}, "
        "{repo: local, hooks: [null, invalid, {}, {id: [mypy]}]}]\n",
    )

    review = report._run_checks(tmp_path, selected_families={"pre_commit"})

    assert review["tally"] == {"PASSED": 1, "RECOMMENDATION": 7, "WARNING": 0, "ERROR": 2}


def test_cli_lists_pre_commit_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert report.main(["--metadata", "--family", "pre_commit"]) == 0

    metadata = json.loads(capsys.readouterr().out)

    assert [rule["id"] for rule in metadata] == list(_RULE_IDS)
    assert all(rule["family"] == "pre_commit" for rule in metadata)


def test_cli_supports_pre_commit_family_and_rule_filtering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_configuration(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "pre_commit", "--ignore", "PC006"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [result["id"] for result in payload["results"]] == [
        rule_id for rule_id in _RULE_IDS if rule_id != "PC006"
    ]
    assert payload["tally"] == {"PASSED": 9, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 0}

    assert report.main(["--json", "--check", "PC006"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [result["id"] for result in payload["results"]] == ["PC006"]


@pytest.mark.parametrize(
    ("content", "expected_exit_code", "expected_tally"),
    [
        ("repos: []\n", 1, {"PASSED": 1, "RECOMMENDATION": 7, "WARNING": 0, "ERROR": 2}),
        (
            _VALID_CONFIGURATION.replace("args: [--pedantic]", "args: []"),
            0,
            {"PASSED": 9, "RECOMMENDATION": 1, "WARNING": 0, "ERROR": 0},
        ),
    ],
)
def test_cli_exit_code_distinguishes_errors_from_warnings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    content: str,
    expected_exit_code: int,
    expected_tally: dict[str, int],
) -> None:
    _write_configuration(tmp_path, content)
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "pre_commit"]) == expected_exit_code

    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == expected_tally


def test_missing_optional_hooks_only_warn(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace("id: zizmor", "id: other").replace("id: mypy", "id: other"),
    )
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "pre_commit"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 8, "RECOMMENDATION": 2, "WARNING": 0, "ERROR": 0}
    statuses = {result["id"]: result["status"] for result in payload["results"]}
    assert statuses["PC003"] == "RECOMMENDATION"
    assert statuses["PC006"] == "RECOMMENDATION"


@pytest.mark.parametrize(("rule_id", "hook_id"), _RECOMMENDED_HOOKS.items())
def test_recommended_hooks_are_checked_independently(
    tmp_path: Path, rule_id: str, hook_id: str
) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace(f"  - id: {hook_id}\n", ""))

    results = {
        result["id"]: result
        for result in report._run_checks(tmp_path, selected_families={"pre_commit"})["results"]
    }

    assert results[rule_id]["status"] == "RECOMMENDATION"
    assert results[rule_id]["detail"].startswith(f"Add the {hook_id} hook; it ")
    assert all(
        result["status"] == "PASSED" for other_id, result in results.items() if other_id != rule_id
    )


@pytest.mark.parametrize(("rule_id", "hook_id"), _RECOMMENDED_HOOKS.items())
@pytest.mark.parametrize(
    "hook_entry",
    [
        "# - id: {hook_id}",
        "- id: {hook_id}-wrapper",
        "- id: other\n    name: {hook_id}",
        "- id: other\n    additional_dependencies: [{hook_id}]",
        "- id: [{hook_id}]",
    ],
)
def test_recommended_hooks_require_exact_ids(
    tmp_path: Path, rule_id: str, hook_id: str, hook_entry: str
) -> None:
    _write_configuration(
        tmp_path,
        "repos:\n- repo: https://github.com/pre-commit/pre-commit-hooks\n  hooks:\n  "
        + hook_entry.format(hook_id=hook_id)
        + "\n",
    )

    result = repo_review_checks()[rule_id].check(tmp_path, None)

    assert isinstance(result, str)
    assert result.startswith(f"RECOMMENDATION: Add the {hook_id} hook; it ")


def test_missing_recommended_hooks_do_not_fail_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    content = _VALID_CONFIGURATION
    for hook_id in _RECOMMENDED_HOOKS.values():
        content = content.replace(f"  - id: {hook_id}\n", "")
    _write_configuration(tmp_path, content)
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "pre_commit"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 6, "RECOMMENDATION": 4, "WARNING": 0, "ERROR": 0}
