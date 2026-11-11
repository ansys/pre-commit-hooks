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

"""Tests for Dependabot quality rules and report integration."""

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import (
    DEPENDABOT_QUALITY_RULES,
    Dependabot,
    repo_review_checks,
)

_RULE_IDS = tuple(f"DB{number:03d}" for number in range(1, 15))
_SAMPLE = """\
version: 2
updates:
- package-ecosystem: uv
  directory: /
  schedule: {interval: daily}
  cooldown:
    default-days: 7
    semver-major-days: 30
    semver-minor-days: 7
    semver-patch-days: 3
    exclude: [ansys-api-discovery, ansys-sphinx-theme]
  labels: [maintenance, dependencies]
  assignees: [pyansys-ci-bot]
  commit-message: {prefix: 'build(deps)'}
  groups:
    grpc-deps: {patterns: ['grpc*', protobuf]}
    docs-deps: {patterns: ['ansys-sphinx-theme*', 'sphinx*']}
- package-ecosystem: github-actions
  directory: /
  schedule: {interval: daily}
  cooldown: {default-days: 7, exclude: ['ansys/actions/*']}
  labels: [maintenance]
  assignees: [pyansys-ci-bot]
  commit-message: {prefix: 'build(actions)'}
  groups:
    actions: {patterns: ['*']}
- package-ecosystem: pre-commit
  directory: /
  schedule: {interval: daily}
  cooldown: {default-days: 7, exclude: ['ansys/pre-commit-hooks/*']}
  labels: [maintenance]
  assignees: [pyansys-ci-bot]
  commit-message: {prefix: 'build(pre-commit)'}
  groups:
    pre-commit-hooks: {patterns: ['*']}
"""


def _write(root: Path, content: str = _SAMPLE, filename: str = "dependabot.yml") -> None:
    directory = root / ".github"
    directory.mkdir(exist_ok=True)
    (directory / filename).write_text(content, encoding="utf-8")


def _check(root: Path, rule_id: str) -> bool | str:
    return repo_review_checks(["dependabot"])[rule_id].check(root, None)


def test_registry_and_default_execution(tmp_path: Path) -> None:
    _write(tmp_path)
    rules = repo_review_checks(["dependabot"])

    assert tuple(rules) == _RULE_IDS
    assert len(DEPENDABOT_QUALITY_RULES) == 14
    assert all(issubclass(rule, Dependabot) for rule in DEPENDABOT_QUALITY_RULES)
    assert all(rule.family == "dependabot" for rule in rules.values())
    results = report._run_checks(tmp_path)["results"]
    assert (
        tuple(result["id"] for result in results if result["family"] == "dependabot") == _RULE_IDS
    )


@pytest.mark.parametrize("filename", ["dependabot.yml", "dependabot.yaml"])
def test_sample_passes_every_rule(tmp_path: Path, filename: str) -> None:
    _write(tmp_path, filename=filename)

    assert all(_check(tmp_path, rule_id) is True for rule_id in _RULE_IDS)


def test_yaml_path_preference_is_deterministic(tmp_path: Path) -> None:
    _write(tmp_path, "version: [\n")
    _write(tmp_path, filename="dependabot.yaml")

    assert str(_check(tmp_path, "DB009")).startswith("ERROR: Invalid YAML")


@pytest.mark.parametrize("rule_id", _RULE_IDS)
def test_missing_configuration_is_error(tmp_path: Path, rule_id: str) -> None:
    review = report._run_checks(tmp_path, selected_rule_ids={rule_id})

    assert review["tally"] == {"PASSED": 0, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 1}
    assert "dependabot" in review["results"][0]["detail"]


@pytest.mark.parametrize(
    "content",
    [
        "",
        "null",
        "[]",
        "true",
        "version: [",
        "1: value",
        "!!python/object/apply:builtins.print [unsafe]",
    ],
)
def test_invalid_yaml_mapping_is_error(tmp_path: Path, content: str) -> None:
    _write(tmp_path, content)
    review = report._run_checks(tmp_path, selected_families={"dependabot"})

    assert review["tally"] == {"PASSED": 1, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 13}
    assert all(result["detail"] for result in review["results"] if result["id"] != "DB001")


def test_non_utf8_configuration_is_error(tmp_path: Path) -> None:
    _write(tmp_path)
    (tmp_path / ".github/dependabot.yml").write_bytes(b"\xff")

    assert str(_check(tmp_path, "DB009")).startswith("ERROR: Cannot read")


def test_directory_and_external_symlink_do_not_count_as_configuration(tmp_path: Path) -> None:
    root = tmp_path / "repository"
    (root / ".github/dependabot.yml").mkdir(parents=True)
    assert _check(root, "DB001") is False

    external = tmp_path / "external.yaml"
    external.write_text(_SAMPLE, encoding="utf-8")
    (root / ".github/dependabot.yaml").symlink_to(external)
    assert _check(root, "DB001") is False
    assert str(_check(root, "DB009")).startswith("ERROR:")


@pytest.mark.parametrize("version", ["true", "1", "2.0", "'2'", "null", "[]"])
def test_schema_version_requires_integer_two(tmp_path: Path, version: str) -> None:
    _write(tmp_path, _SAMPLE.replace("version: 2", f"version: {version}"))

    assert _check(tmp_path, "DB002") == "ERROR: Dependabot version must be the integer 2."


@pytest.mark.parametrize(
    "updates",
    [
        "null",
        "[]",
        "{}",
        "[null]",
        "[invalid]",
        "[{}]",
        "[{package-ecosystem: []}]",
        "[{package-ecosystem: ''}]",
        "[{package-ecosystem: pip, 1: invalid}]",
    ],
)
def test_updates_require_ecosystem_mappings(tmp_path: Path, updates: str) -> None:
    _write(tmp_path, f"version: 2\nupdates: {updates}\n")

    assert _check(tmp_path, "DB009") is True
    assert str(_check(tmp_path, "DB010")).startswith("ERROR:")
    assert str(_check(tmp_path, "DB006")).startswith("ERROR:")


def test_pip_weekly_configuration_passes_without_versioning_strategy(tmp_path: Path) -> None:
    _write(
        tmp_path,
        _SAMPLE.replace("package-ecosystem: uv", "package-ecosystem: pip").replace(
            "interval: daily", "interval: weekly"
        ),
    )

    assert all(_check(tmp_path, rule_id) is True for rule_id in _RULE_IDS)


@pytest.mark.parametrize(
    ("ecosystem", "rule_id"),
    [("uv", "DB003"), ("github-actions", "DB004"), ("pre-commit", "DB013")],
)
def test_missing_ecosystems_warn(tmp_path: Path, ecosystem: str, rule_id: str) -> None:
    _write(tmp_path, _SAMPLE.replace(f"package-ecosystem: {ecosystem}", "package-ecosystem: npm"))

    assert str(_check(tmp_path, rule_id)).startswith("WARNING:")


def test_frequency_counts_distinct_ecosystems(tmp_path: Path) -> None:
    entry = yaml.safe_load(_SAMPLE)["updates"][0]
    _write(tmp_path, yaml.safe_dump({"version": 2, "updates": [entry, entry]}))

    assert str(_check(tmp_path, "DB005")).startswith("WARNING: Only 1 distinct")
    _write(tmp_path, _SAMPLE.replace("interval: daily", "interval: monthly"))
    assert str(_check(tmp_path, "DB005")).startswith("WARNING: Only 0 distinct")
    assert _check(tmp_path, "DB012") is True


@pytest.mark.parametrize(
    "cooldown", ["null", "{}", "{default-days: '7'}", "{default-days: true}", "{default-days: 3}"]
)
def test_every_entry_requires_seven_day_cooldown(tmp_path: Path, cooldown: str) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    configuration["updates"][1]["cooldown"] = yaml.safe_load(cooldown)
    _write(tmp_path, yaml.safe_dump(configuration))

    assert str(_check(tmp_path, "DB006")).endswith("github-actions.")


def test_sample_specific_metadata_is_not_required(tmp_path: Path) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    for entry in configuration["updates"]:
        for key in ("labels", "assignees"):
            del entry[key]
        entry["cooldown"] = {"default-days": 7}
        entry["groups"] = {"custom-name": {"patterns": ["custom-dependency*"]}}
    _write(tmp_path, yaml.safe_dump(configuration))

    assert all(_check(tmp_path, rule_id) is True for rule_id in _RULE_IDS)


@pytest.mark.parametrize(
    ("ecosystem", "prefix"),
    [
        ("uv", "chore"),
        ("github-actions", "ci(actions)"),
        ("pre-commit", "chore(pre-commit)"),
    ],
)
def test_commit_message_prefix_policy(tmp_path: Path, ecosystem: str, prefix: str) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    for entry in configuration["updates"]:
        if entry["package-ecosystem"] == ecosystem:
            entry["commit-message"]["prefix"] = prefix
    _write(tmp_path, yaml.safe_dump(configuration))

    assert str(_check(tmp_path, "DB014")).startswith("WARNING:")


@pytest.mark.parametrize("ecosystem", ["uv", "github-actions"])
@pytest.mark.parametrize(
    "groups",
    [
        "null",
        "{}",
        "{custom: null}",
        "{custom: {patterns: '*'}}",
        "{custom: {patterns: []}}",
        "{custom: {patterns: [null]}}",
        "{custom: {patterns: ['']}}",
    ],
)
def test_groups_require_real_pattern_lists(tmp_path: Path, ecosystem: str, groups: str) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    index = 0 if ecosystem == "uv" else 1
    entry = configuration["updates"][index]
    duplicate = deepcopy(entry)
    duplicate["directory"] = "/other"
    duplicate["groups"] = yaml.safe_load(groups)
    configuration["updates"].append(duplicate)
    _write(tmp_path, yaml.safe_dump(configuration))

    assert str(_check(tmp_path, "DB007" if ecosystem == "uv" else "DB008")).startswith("WARNING:")


@pytest.mark.parametrize(
    "directory_settings",
    [
        {},
        {"directory": "relative"},
        {"directory": None},
        {"directory": ["/"]},
        {"directories": []},
        {"directories": "/"},
        {"directories": ["/", None]},
        {"directory": "/", "directories": ["/other"]},
        {"directory": "/../outside"},
        {"directory": "/path\\outside"},
    ],
)
def test_invalid_directories_are_errors(
    tmp_path: Path, directory_settings: dict[str, object]
) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    entry = configuration["updates"][0]
    del entry["directory"]
    entry.update(directory_settings)
    _write(tmp_path, yaml.safe_dump(configuration))

    assert str(_check(tmp_path, "DB011")).startswith("ERROR:")


def test_multiple_root_relative_directories_are_supported(tmp_path: Path) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    entry = configuration["updates"][0]
    del entry["directory"]
    entry["directories"] = ["/", "/packages/*"]
    _write(tmp_path, yaml.safe_dump(configuration))

    assert _check(tmp_path, "DB011") is True


@pytest.mark.parametrize(
    "schedule",
    [
        "null",
        "[]",
        "{}",
        "{interval: null}",
        "{interval: [daily]}",
        "{interval: hourly}",
        "{interval: cron}",
        "{interval: cron, cronjob: ''}",
    ],
)
def test_invalid_schedule_structure_is_error(tmp_path: Path, schedule: str) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    configuration["updates"][0]["schedule"] = yaml.safe_load(schedule)
    _write(tmp_path, yaml.safe_dump(configuration))

    assert str(_check(tmp_path, "DB012")).startswith("ERROR:")


def test_monthly_schedule_is_accepted(tmp_path: Path) -> None:
    configuration = yaml.safe_load(_SAMPLE)
    configuration["updates"][0]["schedule"] = {"interval": "monthly"}
    _write(tmp_path, yaml.safe_dump(configuration))

    assert _check(tmp_path, "DB012") is True


def test_configuration_changes_are_not_hidden_by_cache(tmp_path: Path) -> None:
    _write(tmp_path)
    assert _check(tmp_path, "DB002") is True
    _write(tmp_path, _SAMPLE.replace("version: 2", "version: 1"))
    assert str(_check(tmp_path, "DB002")).startswith("ERROR:")


def test_cli_metadata_and_filtering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert report.main(["--metadata", "--family", "dependabot"]) == 0
    metadata = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in metadata] == list(_RULE_IDS)
    _write(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert report.main(["--json", "--family", "dependabot", "--ignore", "DB007"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 13, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 0}
    assert report.main(["--json", "--check", "DB003"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in payload["results"]] == ["DB003"]


def test_policy_warnings_do_not_fail_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(
        tmp_path,
        """\
version: 2
updates:
- package-ecosystem: pip
  directory: /
  schedule: {interval: monthly}
""",
    )
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "dependabot"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 7, "RECOMMENDATION": 0, "WARNING": 7, "ERROR": 0}
    _write(tmp_path, "version: 2\nupdates: []\n")
    assert report.main(["--json", "--family", "dependabot"]) == 1
