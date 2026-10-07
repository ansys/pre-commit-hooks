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
from ansys.pre_commit_hooks.quality_rules.readme import RM003, RM005, RM006, RM007


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


def test_rm003_is_not_applicable_without_license_metadata(tmp_path):
    """The license badge check is not applicable without project license metadata."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    assert RM003.check(tmp_path, "README.rst") is None


def test_rm003_is_not_applicable_with_invalid_pyproject(tmp_path):
    """Invalid TOML should not crash the README license check."""
    (tmp_path / "pyproject.toml").write_text("[project\nlicense = 'MIT'\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    assert RM003.check(tmp_path, "README.rst") is None


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


def test_report_uses_actionable_warning_once(tmp_path, capsys):
    """A missing badge should be printed as the single warning headline."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    review = report._run_checks(tmp_path, selected_codes={"RM001"})
    report._print_report(review)

    output = capsys.readouterr().out
    message = "PyAnsys badge image not found in README.rst."
    assert output.count(message) == 1
    assert f"- [WARN] RM001 - {message}" in output.splitlines()


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
