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

"""Tests for the documentation quality rule family."""

from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import (
    DOCUMENTATION_QUALITY_RULES,
    Documentation,
    repo_review_checks,
)

_RULE_IDS = tuple(f"DOC{number:03d}" for number in range(1, 13))
_VALID_INDEX = """\
Getting Started
===============

API Reference
=============
"""
_VALID_CONF = """\
project = "test-project"
author = "Test Organization"
copyright = f"(c) {datetime.now().year} Test Organization"
cname = os.getenv("DOCS_CNAME", "docs.example.com")
html_theme = "ansys_sphinx_theme"
html_title = html_short_title = "Test project"
html_favicon = ansys_favicon
html_theme_options = {
    "logo": "pyansys",
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
}
extensions = ["numpydoc", "sphinx_design", "sphinx.ext.intersphinx"]
"""


def _write_documentation(
    root: Path,
    *,
    index: str = _VALID_INDEX,
    conf: str = _VALID_CONF,
) -> None:
    source = root / "doc" / "source"
    source.mkdir(parents=True, exist_ok=True)
    (source / "index.rst").write_text(index, encoding="utf-8")
    (source / "conf.py").write_text(conf, encoding="utf-8")


def _rule(rule_id: str):
    return repo_review_checks(["documentation"])[rule_id]


def test_registry_contains_all_documentation_rules() -> None:
    rules = repo_review_checks(["documentation"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "documentation" for rule in rules.values())
    assert len(DOCUMENTATION_QUALITY_RULES) == 12
    assert all(issubclass(rule, Documentation) for rule in DOCUMENTATION_QUALITY_RULES)


def test_documentation_family_runs_by_default(tmp_path: Path) -> None:
    _write_documentation(tmp_path)

    results = report._run_checks(tmp_path)["results"]

    assert any(result["family"] == "documentation" for result in results)


@pytest.mark.parametrize(
    ("rule_id", "relative_path"),
    [("DOC001", "doc/source/index.rst"), ("DOC002", "doc/source/conf.py")],
)
def test_required_documentation_files_are_checked(
    tmp_path: Path, rule_id: str, relative_path: str
) -> None:
    assert _rule(rule_id).check(tmp_path, None) is False

    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Documentation", encoding="utf-8")

    assert _rule(rule_id).check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("rule_id", "setting"),
    [
        ("DOC003", "numpydoc"),
        ("DOC005", "intersphinx"),
    ],
)
def test_sphinx_extensions_are_checked(tmp_path: Path, rule_id: str, setting: str) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")

    assert _rule(rule_id).check(tmp_path, None) is False

    _write_documentation(tmp_path, conf=f"extensions = ['{setting}']\n")

    assert _rule(rule_id).check(tmp_path, None) is True


def test_sphinx_design_is_recommended_but_optional(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC004"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert "Sphinx Design components" in result["detail"]

    _write_documentation(tmp_path, conf="extensions = ['sphinx_design']\n")

    assert _rule("DOC004").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("rule_id", "index"),
    [
        ("DOC006", "Getting Started\n===============\n"),
        ("DOC007", "API Reference\n==============\n"),
    ],
)
def test_documentation_index_sections_are_checked(tmp_path: Path, rule_id: str, index: str) -> None:
    _write_documentation(tmp_path, index=index)

    assert _rule(rule_id).check(tmp_path, None) is True

    _write_documentation(tmp_path, index="Overview\n========\n")

    assert _rule(rule_id).check(tmp_path, None) is False


def test_gallery_check_is_not_applicable_without_gallery_extension(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")

    assert _rule("DOC008").check(tmp_path, None) is True


def test_sphinx_gallery_recommends_configured_example_files(tmp_path: Path) -> None:
    _write_documentation(
        tmp_path,
        conf=(
            "extensions = ['sphinx_gallery.gen_gallery']\n"
            "sphinx_gallery_conf = {'examples_dirs': ['examples'], "
            "'gallery_dirs': 'auto_examples'}\n"
        ),
    )

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC008"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert "example files" in result["detail"]

    examples = tmp_path / "doc" / "source" / "examples" / "basic"
    examples.mkdir(parents=True)
    (examples / "example.py").write_text("print('example')\n", encoding="utf-8")

    assert _rule("DOC008").check(tmp_path, None) is True


def test_nbsphinx_recommends_example_files(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = ['nbsphinx']\n")

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC008"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert "example files" in result["detail"]

    examples = tmp_path / "examples" / "basic"
    examples.mkdir(parents=True)
    (examples / "example.ipynb").write_text("{}\n", encoding="utf-8")

    assert _rule("DOC008").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('html_theme = "ansys_sphinx_theme"', 'html_theme = "sphinx_rtd_theme"'),
        ('"logo": "pyansys"', '"logo": "other"'),
        ("html_favicon = ansys_favicon", 'html_favicon = "favicon.ico"'),
        ('html_theme = "ansys_sphinx_theme"', "# html_theme = 'ansys_sphinx_theme'"),
    ],
)
def test_required_theme_and_brand_settings_are_checked(tmp_path: Path, old: str, new: str) -> None:
    _write_documentation(tmp_path, conf=_VALID_CONF.replace(old, new))

    assert _rule("DOC009").check(tmp_path, None) is False


def test_project_and_page_titles_must_be_nonempty(tmp_path: Path) -> None:
    _write_documentation(
        tmp_path, conf=_VALID_CONF.replace('project = "test-project"', 'project = ""')
    )

    assert _rule("DOC010").check(tmp_path, None) is False

    _write_documentation(
        tmp_path,
        conf=_VALID_CONF.replace(
            'html_title = html_short_title = "Test project"', 'html_title = html_short_title = ""'
        ),
    )

    assert _rule("DOC010").check(tmp_path, None) is False


def test_site_metadata_accepts_dynamic_year_and_cname_fallback(tmp_path: Path) -> None:
    _write_documentation(tmp_path)

    assert _rule("DOC011").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('author = "Test Organization"', 'author = ""'),
        (
            'copyright = f"(c) {datetime.now().year} Test Organization"',
            'copyright = ""',
        ),
        (
            'cname = os.getenv("DOCS_CNAME", "docs.example.com")',
            'cname = "not a hostname"',
        ),
    ],
)
def test_site_metadata_recommends_missing_or_invalid_values(
    tmp_path: Path, old: str, new: str
) -> None:
    _write_documentation(tmp_path, conf=_VALID_CONF.replace(old, new))

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC011"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"


def test_theme_switcher_accepts_dynamic_config_values(tmp_path: Path) -> None:
    _write_documentation(tmp_path)

    assert _rule("DOC012").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ('"json_url": f"https://{cname}/versions.json",\n', ""),
        ('"version_match": get_version_match(__version__),\n', ""),
    ],
)
def test_theme_switcher_recommends_missing_settings(tmp_path: Path, old: str, new: str) -> None:
    _write_documentation(tmp_path, conf=_VALID_CONF.replace(old, new))

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC012"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
