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
from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import repo_review_checks
from ansys.pre_commit_hooks.quality_rules.common import normalize_check_result
from ansys.pre_commit_hooks.quality_rules.readme import (
    RM001,
    RM002,
    RM003,
    RM004,
    RM005,
    RM006,
    RM007,
)


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
    assert result.startswith("WARNING: Apache-2.0")


def test_rm003_warns_without_license_metadata(tmp_path):
    """The license badge cannot be verified without project license metadata."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    result = RM003.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("WARNING: No project license found in pyproject.toml")


def test_rm003_warns_with_invalid_pyproject(tmp_path):
    """Invalid TOML should warn instead of crashing the README license check."""
    (tmp_path / "pyproject.toml").write_text("[project\nlicense = 'MIT'\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")
    assert isinstance(result, str)
    assert result.startswith("WARNING: No project license found")


def test_missing_readme_is_reported_by_every_rule(tmp_path, capsys):
    """Without a README no rule is skipped: each one fails or warns."""
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")

    review = report._run_checks(tmp_path)
    statuses = {item["id"]: item["status"] for item in review["results"]}

    assert statuses == {
        "RM000": "ERROR",
        "RM001": "ERROR",
        "RM002": "WARNING",
        "RM003": "WARNING",
        "RM004": "WARNING",
        "RM005": "ERROR",
        "RM006": "ERROR",
        "RM007": "ERROR",
    }
    assert review["tally"] == {"PASSED": 0, "WARNING": 3, "ERROR": 5}
    report._print_report(review)
    output = capsys.readouterr().out
    assert "PyPI badge image not found because no README file exists." in output
    assert "na=" not in output


def test_report_exposes_only_supported_statuses(tmp_path):
    """Every rule result and tally should use the public status vocabulary."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")

    review = report._run_checks(tmp_path)

    assert {item["status"] for item in review["results"]} <= {
        "PASSED",
        "WARNING",
        "ERROR",
    }
    assert set(review["tally"]) == {"PASSED", "WARNING", "ERROR"}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (True, "PASSED"),
        (False, "ERROR"),
        ("WARNING: needs attention", "WARNING"),
        ("ERROR: invalid", "ERROR"),
        ("unsupported", "ERROR"),
        (None, "ERROR"),
    ],
)
def test_result_normalization_cannot_create_an_unsupported_status(raw, expected):
    """Unexpected rule return values should become errors."""
    check = repo_review_checks()["RM000"]

    status, _ = normalize_check_result(raw, check)

    assert status == expected


def test_ignored_rules_are_the_only_way_to_skip_a_rule(tmp_path):
    """Ignoring a rule removes it from the report."""
    review = report._run_checks(tmp_path, ignored_rule_ids={"RM001", "RM002"})

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
    review = report._run_checks(tmp_path, selected_rule_ids={"RM001"})
    report._print_report(review)

    output = capsys.readouterr().out
    message = "PyAnsys or Ansys badge image not found in README.rst."
    assert output.count(message) == 1
    assert f"- [ERROR] RM001 - {message}" in output.splitlines()
    assert review["tally"]["ERROR"] == 1


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
    assert result.startswith("ERROR: ")


@pytest.mark.parametrize(
    ("rule", "badge"),
    [
        (RM001, '<img alt="PyAnsys" src="https://img.shields.io/badge/PyAnsys-yellow.svg">\n'),
        (
            RM002,
            "![PyPI][package]\n\n[package]: https://img.shields.io/pypi/v/ansys-demo.svg\n",
        ),
        (
            RM004,
            "![CI](https://github.com/ansys/demo/actions/workflows/ci.yml/badge.svg)\n",
        ),
    ],
)
def test_badge_rules_accept_supported_image_markup(tmp_path, rule, badge):
    """Badge checks should support HTML and Markdown image declarations."""
    (tmp_path / "README.rst").write_text(badge, encoding="utf-8")

    assert rule.check(tmp_path, "README.rst") is True


@pytest.mark.parametrize(
    ("rule", "prose"),
    [
        (RM001, "PyAnsys project"),
        (RM002, "Published on PyPI"),
        (RM004, "GitHub Actions"),
    ],
)
def test_badge_rules_do_not_cross_from_an_unrelated_image_into_prose(tmp_path, rule, prose):
    """Text after an unrelated image should not satisfy a badge check."""
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/build-passing-green.svg\n" f"\n{prose}\n",
        encoding="utf-8",
    )

    assert rule.check(tmp_path, "README.rst") is not True


def test_rm002_ignores_pypi_link_around_unrelated_image(tmp_path):
    """A PyPI target URL should not turn an unrelated image into a PyPI badge."""
    (tmp_path / "README.md").write_text(
        "[![build](https://img.shields.io/badge/build-passing-green.svg)]"
        "(https://pypi.org/project/ansys-demo/)\n",
        encoding="utf-8",
    )

    result = RM002.check(tmp_path, "README.md")

    assert isinstance(result, str)
    assert result.startswith("WARNING: ")


def test_badge_rules_ignore_malformed_image_urls(tmp_path):
    """A malformed unrelated URL should not abort a badge check."""
    (tmp_path / "README.md").write_text("![broken](https://[invalid)\n", encoding="utf-8")

    result = RM002.check(tmp_path, "README.md")

    assert isinstance(result, str)
    assert result.startswith("WARNING: ")


@pytest.mark.parametrize(
    "readme",
    [
        "<!-- ![PyAnsys](https://img.shields.io/badge/PyAnsys-yellow.svg) -->\n",
        "```markdown\n![PyAnsys](https://img.shields.io/badge/PyAnsys-yellow.svg)\n```\n",
    ],
)
def test_badge_rules_ignore_non_rendered_markdown(tmp_path, readme):
    """Commented badges and badge examples should not satisfy a rule."""
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")

    result = RM001.check(tmp_path, "README.md")

    assert isinstance(result, str)
    assert result.startswith("ERROR: ")


@pytest.mark.parametrize("option", ["--check", "--ignore"])
def test_cli_rejects_unknown_rule_ids(tmp_path, monkeypatch, capsys, option):
    """Unknown rule IDs stop the run instead of being silently skipped."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as exit_info:
        report.main([option, "RM001,RM999,xx1"])

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


def test_cli_accepts_lowercase_rule_ids(tmp_path, monkeypatch, capsys):
    """Rule IDs are case-insensitive."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = report.main(["--check", "rm000", "--json"])

    assert result == 0
    assert [item["id"] for item in json.loads(capsys.readouterr().out)["results"]] == ["RM000"]


def test_find_project_root_uses_nearest_pyproject(tmp_path):
    """The root is the closest parent that contains a pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)
    (tmp_path / "src" / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    assert report._find_project_root(nested) == tmp_path / "src"
    assert report._find_project_root(tmp_path) == tmp_path


def test_find_project_root_falls_back_to_start(tmp_path, monkeypatch):
    """Without any pyproject.toml the starting directory is the root."""
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    assert report._find_project_root(tmp_path / "a" / "b") == tmp_path / "a" / "b"


def test_cli_finds_project_root_from_subdirectory(tmp_path, monkeypatch, capsys):
    """Running from a subdirectory reviews the project that contains it."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = report.main(["--check", "RM000", "--json"])

    assert result == 0
    assert json.loads(capsys.readouterr().out)["results"][0]["status"] == "PASSED"


def test_cli_emits_json_for_selected_rule(tmp_path, monkeypatch, capsys):
    """The CLI should support selected checks and JSON output."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = report.main(["--check", "RM000", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert [item["id"] for item in payload["results"]] == ["RM000"]
    assert payload["results"][0]["status"] == "PASSED"


def test_cli_exit_code_distinguishes_warnings_from_errors(tmp_path, monkeypatch, capsys):
    """Warnings should exit successfully, while errors should exit with one."""
    (tmp_path / "README.rst").write_text("Project\n=======\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    warning_exit = report.main(["--check", "RM002", "--json"])
    warning_payload = json.loads(capsys.readouterr().out)
    error_exit = report.main(["--check", "RM001", "--json"])
    error_payload = json.loads(capsys.readouterr().out)

    assert warning_exit == 0
    assert warning_payload["results"][0]["status"] == "WARNING"
    assert error_exit == 1
    assert error_payload["results"][0]["status"] == "ERROR"


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


def test_rm003_does_not_match_license_in_plain_text(tmp_path):
    """License prose after an unrelated badge should not satisfy RM003."""
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/build-passing-green.svg\n"
        "\nReleased under the MIT license.\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")

    assert isinstance(result, str)
    assert result.startswith("WARNING: MIT")


def test_rm003_rejects_a_mismatched_apache_version(tmp_path):
    """An Apache 1.1 badge should not satisfy Apache-2.0 metadata."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nlicense = "Apache-2.0"\n', encoding="utf-8"
    )
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-Apache_1.1-blue.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")

    assert isinstance(result, str)
    assert result.startswith("WARNING: Apache-2.0")


@pytest.mark.parametrize(
    ("identifier", "badge_identifier"),
    [
        ("MIT-0", "MIT"),
        ("BSD-3-Clause-Clear", "BSD--3--Clause"),
        ("MIT OR Apache-2.0", "MIT"),
    ],
)
def test_rm003_does_not_collapse_distinct_license_identifiers(
    tmp_path, identifier, badge_identifier
):
    """A badge for a related license should not satisfy a distinct SPDX ID."""
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nlicense = "{identifier}"\n', encoding="utf-8"
    )
    (tmp_path / "README.rst").write_text(
        f".. image:: https://img.shields.io/badge/License-{badge_identifier}-blue.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")

    assert isinstance(result, str)
    assert result.startswith(f"WARNING: {identifier}")


@pytest.mark.parametrize("license_content", [None, ""])
def test_rm003_does_not_match_when_license_file_is_unreadable_or_empty(tmp_path, license_content):
    """Missing and empty license files should leave the license unverifiable."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nlicense = {file = "LICENSE"}\n', encoding="utf-8"
    )
    if license_content is not None:
        (tmp_path / "LICENSE").write_text(license_content, encoding="utf-8")
    (tmp_path / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/build-passing-green.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(tmp_path, "README.rst")

    assert isinstance(result, str)
    assert result.startswith("WARNING: No project license found")


def test_rm003_does_not_read_license_files_outside_the_repository(tmp_path):
    """A license.file path should not escape the repository root."""
    repository = tmp_path / "repository"
    repository.mkdir()
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    (repository / "pyproject.toml").write_text(
        '[project]\nlicense = {file = "../LICENSE"}\n', encoding="utf-8"
    )
    (repository / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(repository, "README.rst")

    assert isinstance(result, str)
    assert result.startswith("WARNING: No project license found")


def test_rm003_does_not_follow_a_license_symlink_outside_the_repository(tmp_path):
    """A license.file symlink should not escape the repository root."""
    repository = tmp_path / "repository"
    repository.mkdir()
    outside_license = tmp_path / "LICENSE"
    outside_license.write_text("MIT License\n", encoding="utf-8")
    try:
        (repository / "LICENSE").symlink_to(outside_license)
    except OSError as exc:
        pytest.skip(f"symlinks are unavailable: {exc}")
    (repository / "pyproject.toml").write_text(
        '[project]\nlicense = {file = "LICENSE"}\n', encoding="utf-8"
    )
    (repository / "README.rst").write_text(
        ".. image:: https://img.shields.io/badge/License-MIT-yellow.svg\n",
        encoding="utf-8",
    )

    result = RM003.check(repository, "README.rst")

    assert isinstance(result, str)
    assert result.startswith("WARNING: No project license found")


def test_unreadable_readme_is_an_error_for_every_content_rule(tmp_path):
    """Invalid UTF-8 should produce an error instead of a missing-badge warning."""
    (tmp_path / "pyproject.toml").write_text('[project]\nlicense = "MIT"\n', encoding="utf-8")
    (tmp_path / "README.rst").write_bytes(b"\xff")

    review = report._run_checks(tmp_path)
    statuses = {item["id"]: item["status"] for item in review["results"] if item["id"] != "RM000"}

    assert set(statuses.values()) == {"ERROR"}
