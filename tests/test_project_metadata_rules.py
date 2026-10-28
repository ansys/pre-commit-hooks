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

"""Regression tests for structured project metadata validation."""

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules.project_metadata import (
    PM002,
    PM009,
    PM016,
    PM020,
    PM023,
)


def _write_pyproject(root, content):
    """Write a TOML fixture at the repository root."""
    (root / "pyproject.toml").write_text(content, encoding="utf-8")


def _assert_warning(result, message):
    """Check that the result contains an explicit warning."""
    assert isinstance(result, str)
    assert result.startswith("WARNING: ")
    assert message in result


@pytest.mark.parametrize("key_style", ["{key}", '"{key}"', "'{key}'"])
def test_support_urls_accept_quoted_and_unquoted_keys(tmp_path, key_style):
    """Parse URL keys according to TOML syntax."""
    entries = "\n".join(
        f'{key_style.format(key=key)} = "https://example.com/{key}"'
        for key in ("Issues", "Discussions", "Documentation")
    )
    _write_pyproject(tmp_path, f"[project.urls]\n{entries}\n")

    assert PM020.check(tmp_path, None) is True


@pytest.mark.parametrize(
    "content",
    [
        '[tool.other]\nIssues="https://example.com"\nDiscussions="https://example.com"\n'
        'Documentation="https://example.com"\n[project]\n',
        '[project]\ndescription = """\nIssues="https://example.com"\n'
        'Discussions="https://example.com"\nDocumentation="https://example.com"\n"""\n',
        '[project.urls]\nIssues="ftp://example.com"\nDiscussions=3\nDocumentation=""\n',
        '[project.urls]\nIssues="https://example.com"\n',
    ],
)
def test_support_urls_reject_wrong_tables_and_invalid_values(tmp_path, content):
    """Reject URL-like text outside the correct table and invalid URL values."""
    _write_pyproject(tmp_path, content)

    _assert_warning(PM020.check(tmp_path, None), "URLs")


@pytest.mark.parametrize(
    ("spec", "valid"),
    [
        (">=3.10,<4", True),
        (">=3.10", True),
        (">3.9", True),
        (">3.9,<=3.14", True),
        (" <4 , >=3.10 ", True),
        (">=3.10,!=3.11.*", True),
        ("<4", False),
        (">-3.10", False),
        (">=3.10,3.14", False),
        (">=3.10,<garbage", False),
        ("~=3.10", False),
        ("==3.10.*", False),
        ("", False),
    ],
)
def test_requires_python_parses_strict_specifiers(tmp_path, spec, valid):
    """Require valid syntax and a lower bound while allowing an optional upper bound."""
    _write_pyproject(tmp_path, f'[project]\nrequires-python = "{spec}"\n')
    result = PM016.check(tmp_path, None)

    if valid:
        assert result is True
    else:
        _assert_warning(result, "requires-python")


def test_requires_python_ignores_other_tables(tmp_path):
    """Do not accept unrelated requires-python keys."""
    _write_pyproject(tmp_path, '[project]\n[tool.other]\nrequires-python = ">=3.10,<4"\n')
    _assert_warning(PM016.check(tmp_path, None), "not declared")


@pytest.mark.parametrize("spec", [">=3.10", ">=3.10,<4"])
def test_requires_python_preserves_setup_fallback(tmp_path, spec):
    """Retain validation of legacy setup.py declarations."""
    (tmp_path / "setup.py").write_text(f'setup(python_requires="{spec}")', encoding="utf-8")
    assert PM016.check(tmp_path, None) is True


@pytest.mark.parametrize(
    "declaration",
    ['"README.md"', '{file = "README.md", content-type = "text/markdown"}'],
)
def test_readme_references_must_exist(tmp_path, declaration):
    """Require a regular file for both README declaration forms."""
    _write_pyproject(tmp_path, f"[project]\nreadme = {declaration}\n")
    _assert_warning(PM009.check(tmp_path, None), "README.md")

    (tmp_path / "README.md").mkdir()
    _assert_warning(PM009.check(tmp_path, None), "README.md")
    (tmp_path / "README.md").rmdir()
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    assert PM009.check(tmp_path, None) is True


def test_readme_mentions_elsewhere_do_not_count(tmp_path):
    """Do not confuse a description with a README declaration."""
    _write_pyproject(tmp_path, '[project]\ndescription = "See README.md"\n')
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    assert PM009.check(tmp_path, "README.md") is False


def test_readme_inline_and_dynamic_setuptools_metadata(tmp_path):
    """Accept inline text and validate every dynamic setuptools file."""
    _write_pyproject(
        tmp_path, '[project]\nreadme = {text = "Project overview", content-type = "text/plain"}\n'
    )
    assert PM009.check(tmp_path, None) is True
    _write_pyproject(
        tmp_path,
        '[project]\ndynamic = ["readme"]\n[tool.setuptools.dynamic]\n'
        'readme = {file = ["README.rst", "DETAILS.rst"]}\n',
    )
    (tmp_path / "README.rst").write_text("Overview", encoding="utf-8")
    _assert_warning(PM009.check(tmp_path, None), "DETAILS.rst")
    (tmp_path / "DETAILS.rst").write_text("Details", encoding="utf-8")
    assert PM009.check(tmp_path, None) is True


def test_readme_rejects_external_symlink(tmp_path):
    """Reject README symlinks that escape the repository."""
    repository = tmp_path / "repo"
    repository.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("Outside", encoding="utf-8")
    (repository / "README.md").symlink_to(outside)
    _write_pyproject(repository, '[project]\nreadme = "README.md"\n')
    _assert_warning(PM009.check(repository, None), "not found in repository")


@pytest.mark.parametrize(
    ("declaration", "message"),
    [
        ("42", "project.readme"),
        ('["README.md"]', "project.readme"),
        ('{text=""}', "project.readme.text"),
        ('{file="README.md", text="Inline"}', "both file and text"),
    ],
)
def test_readme_rejects_invalid_declarations(tmp_path, declaration, message):
    """Report malformed README declarations explicitly."""
    _write_pyproject(tmp_path, f"[project]\nreadme = {declaration}\n")
    _assert_warning(PM009.check(tmp_path, None), message)


@pytest.mark.parametrize(
    ("spec", "versions", "valid"),
    [
        (">=3.10,<3.13", ["3.10", "3.11", "3.12"], True),
        (">=3.12", ["3.12", "3.13", "3.14"], True),
        (">=3.12", ["3.11"], False),
        (">=3.10,<3.13", ["3.9", "3.13"], False),
        (">=3.10,<4,!=3.11.*", ["3.11"], False),
        (">=3.10.2,<3.11", ["3.10"], True),
        (">=3.10,<3.11,!=3.10.0", ["3.10"], True),
        (">=3.10.2,<3.10.2", ["3.10"], False),
        (">=3.10,<4,===not-a-version", ["3.10"], False),
        (">=3.10,<4", [], False),
    ],
)
def test_python_classifiers_match_supported_minor_series(tmp_path, spec, versions, valid):
    """Validate minor classifiers without rejecting supported patch-only ranges."""
    classifiers = ", ".join(f'"Programming Language :: Python :: {v}"' for v in versions)
    _write_pyproject(
        tmp_path, f'[project]\nrequires-python = "{spec}"\nclassifiers = [{classifiers}]\n'
    )
    result = PM023.check(tmp_path, None)
    if valid:
        assert result is True
    else:
        _assert_warning(result, "classifiers")


def test_dynamic_classifiers_warn_instead_of_passing(tmp_path):
    """Do not claim to validate build-backend-generated classifiers."""
    _write_pyproject(tmp_path, '[project]\nrequires-python = ">=3.10,<4"\ndynamic=["classifiers"]')
    _assert_warning(PM023.check(tmp_path, None), "cannot be verified statically")


@pytest.mark.parametrize("rule", [PM009, PM016, PM020, PM023])
def test_structured_rules_report_invalid_toml(tmp_path, rule):
    """Expose TOML parsing errors as warnings."""
    _write_pyproject(tmp_path, "[project\n")
    _assert_warning(rule.check(tmp_path, None), "not valid TOML")


@pytest.mark.parametrize("rule", [PM009, PM016, PM020, PM023])
@pytest.mark.parametrize("content", ["project = 42", "[project]\ndynamic = false"])
def test_structured_rules_report_invalid_table_shapes(tmp_path, rule, content):
    """Report malformed metadata types instead of raising runtime errors."""
    _write_pyproject(tmp_path, content)
    _assert_warning(rule.check(tmp_path, None), "project")


@pytest.mark.parametrize(
    ("content", "valid"),
    [
        ("", False),
        ("Release notes\n", False),
        ("Release notes\n===\n\nFixed a bug.", False),
        ("Release notes\n=============\n", False),
        ("Release notes\n=============\n\nTODO\n", False),
        ("Release notes\n=============\n\nUnreleased\n----------\n", False),
        ("Release notes\n=============\n\n.. towncrier release notes start\n", False),
        ("Release notes\n=============\n\n1.0.0\n-----\nFixed a bug.\n", True),
        (".. _release_notes:\n\nRelease notes\n#############\n\nAdded a feature.\n", True),
    ],
)
def test_rst_changelog_requires_title_and_real_content(tmp_path, content, valid):
    """Reject empty, untitled, and placeholder RST changelogs."""
    changelog = tmp_path / "doc" / "source" / "changelog.rst"
    changelog.parent.mkdir(parents=True)
    changelog.write_text(content, encoding="utf-8")
    result = PM002.check(tmp_path, None)
    if valid:
        assert result is True
    else:
        _assert_warning(result, "valid RST title")


def test_markdown_changelog_still_takes_precedence(tmp_path):
    """Preserve the existing Markdown-first changelog behavior."""
    (tmp_path / "CHANGELOG.md").touch()
    assert PM002.check(tmp_path, None) is True


def test_new_classifier_rule_is_registered(tmp_path):
    """Expose PM023 through the quality-report registry."""
    results = report._run_checks(tmp_path, selected_rule_ids={"PM023"})["results"]
    assert len(results) == 1
    assert results[0]["id"] == "PM023"
    assert results[0]["status"] == "WARNING"
