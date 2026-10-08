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

"""Tests for the initial README quality-report release."""

import json

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import repo_review_checks
from ansys.pre_commit_hooks.quality_rules.readme import RM001, RM003, RM005, RM006, RM007


def test_registry_contains_only_readme_rules():
    """The first release exposes only the README rule family."""
    assert list(repo_review_checks()) == [f"RM{number:03d}" for number in range(8)]


def test_rm003_matches_mit_project_license(tmp_path):
    """The README license badge should match the project license identifier."""
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    assert RM003.check(tmp_path, "README.rst") is True


def test_rm003_warns_on_mismatched_project_license(tmp_path):
    """A badge for a different license should warn."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nlicense = "Apache-2.0"\n', encoding="utf-8"
    )
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("WARN: Apache-2.0")


def test_rm003_warns_without_license_metadata(tmp_path):
    """The license badge cannot be verified without project license metadata."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    result = RM003.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("WARN: No project license found in pyproject.toml")


def test_rm003_warns_with_invalid_pyproject(tmp_path):
    """Invalid TOML should warn instead of crashing the README license check."""
    (tmp_path / "pyproject.toml").write_text("[project\nlicense = 'MIT'\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("WARN: No project license found")


def test_missing_readme_is_reported_by_every_rule(tmp_path, capsys):
    """Without a README no rule is skipped: each one fails or warns."""
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")

    review = report._run_checks(tmp_path)
    statuses = {item["id"]: item["status"] for item in review["results"]}

    assert statuses == {
        "RM000": "fail",
        "RM001": "fail",
        "RM002": "warn",
        "RM003": "warn",
        "RM004": "warn",
        "RM005": "fail",
        "RM006": "fail",
        "RM007": "fail",
    }
    assert review["tally"] == {"pass": 0, "fail": 5, "warn": 3}
    report._print_report(review)
    output = capsys.readouterr().out
    assert "PyPI badge image not found because no README file exists." in output
    assert "na=" not in output


def test_ignored_rules_are_the_only_way_to_skip_a_rule(tmp_path):
    """Ignoring a rule removes it from the report."""
    review = report._run_checks(tmp_path, ignored_codes={"RM001", "RM002"})

    assert "RM001" not in {item["id"] for item in review["results"]}
    assert "RM002" not in {item["id"] for item in review["results"]}


@pytest.mark.parametrize(
    ("rule", "readme"),
    [
        (RM005, "Title\n=====\n\nHow to install\n--------------\n"),
        (RM005, "# Title\n\n## Installation\n"),
        (RM006, "Documentation\n^^^^^^^^^^^^^\n"),
        (RM007, "License\n=======\n"),
        (RM007, "### Licence\n"),
    ],
)
def test_section_rules_accept_headings(tmp_path, rule, readme):
    """A matching RST or Markdown heading satisfies the section rule."""
    (tmp_path / "README.rst").write_text(readme, encoding="utf-8")

    assert rule.check(tmp_path, "README.rst") is True


@pytest.mark.parametrize(
    ("rule", "readme"),
    [
        (RM005, "Title\n=====\n\nRun pip install ansys-demo to get started.\n"),
        (RM006, "Title\n=====\n\nSee the documentation online.\n"),
        (RM007, ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n"),
    ],
)
def test_section_rules_ignore_plain_text_mentions(tmp_path, rule, readme):
    """The term in body text or a badge URL is not a section heading."""
    (tmp_path / "README.rst").write_text(readme, encoding="utf-8")

    assert rule.check(tmp_path, "README.rst") is False


def test_report_uses_actionable_failure_once(tmp_path, capsys):
    """A missing PyAnsys/Ansys badge fails and prints its message once."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    review = report._run_checks(tmp_path, selected_codes={"RM001"})
    report._print_report(review)

    output = capsys.readouterr().out
    message = "PyAnsys or Ansys badge image not found in README.rst."
    assert output.count(message) == 1
    assert f"- [FAIL] RM001 - {message}" in output.splitlines()
    assert review["tally"]["fail"] == 1


@pytest.mark.parametrize(
    "badge",
    [
        ".. image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,AAAA\n",  # noqa: E501
        ".. image:: https://img.shields.io/badge/Ansys-ffc107.svg\n",
        "[![PyAnsys](https://img.shields.io/badge/PyAnsys-ffc107.svg)](https://docs.pyansys.com/)\n",  # noqa: E501
    ],
)
def test_rm001_accepts_pyansys_or_ansys_badge(tmp_path, badge):
    """Either a PyAnsys or an Ansys badge satisfies RM001."""
    (tmp_path / "README.rst").write_text(badge, encoding="utf-8")

    assert RM001.check(tmp_path, "README.rst") is True


def test_rm001_ignores_ansys_github_actions_badge(tmp_path):
    """The Ansys GitHub organization in a CI badge URL is not an Ansys badge."""
    (tmp_path / "README.rst").write_text(
        ".. image:: https://github.com/ansys/demo/actions/workflows/ci.yml/status.svg\n",
        encoding="utf-8",
    )

    result = RM001.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("FAIL: ")


@pytest.mark.parametrize("option", ["--check", "--ignore"])
def test_cli_rejects_unknown_rule_ids(tmp_path, capsys, option):
    """Unknown rule IDs stop the run instead of being silently skipped."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exit_info:
        report.main(["--repo-root", str(tmp_path), option, "RM001,RM999,xx1"])

    error = capsys.readouterr().err
    assert exit_info.value.code == 2
    assert f"unknown rule ID(s) for {option}: RM999, XX1." in error
    assert "Available rules: RM000, RM001" in error


def test_cli_rejects_unknown_rule_ids_with_metadata(capsys):
    """Metadata listing also rejects unknown rule IDs."""
    with pytest.raises(SystemExit) as exit_info:
        report.main(["--metadata", "--check", "RM999"])

    assert exit_info.value.code == 2
    assert "unknown rule ID(s) for --check: RM999." in capsys.readouterr().err


def test_cli_accepts_lowercase_rule_ids(tmp_path, capsys):
    """Rule IDs are case-insensitive."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    result = report.main(["--repo-root", str(tmp_path), "--check", "rm000", "--json"])

    assert result == 0
    assert [item["id"] for item in json.loads(capsys.readouterr().out)["results"]] == ["RM000"]


def test_cli_emits_json_for_selected_rule(tmp_path, capsys):
    """The CLI should support selected checks and JSON output."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    result = report.main(["--repo-root", str(tmp_path), "--check", "RM000", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert [item["id"] for item in payload["results"]] == ["RM000"]
    assert payload["results"][0]["status"] == "pass"


@pytest.mark.parametrize("license_value", ['"MIT"', '{ text = "MIT License" }'])
def test_rm003_supports_license_text_metadata(tmp_path, license_value):
    """The license badge rule accepts PEP 639 text metadata."""
    (tmp_path / "pyproject.toml").write_text(
        f"[project]\nlicense = {license_value}\n", encoding="utf-8"
    )
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    assert RM003.check(tmp_path, "README.rst") is True
