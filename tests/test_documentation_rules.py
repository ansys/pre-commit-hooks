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

_RULE_IDS = tuple(f"DOC{number:03d}" for number in range(1, 31))
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


def _assert_warning(result: object, detail: str) -> None:
    assert isinstance(result, str)
    assert result.startswith("WARNING: ")
    assert detail in result


def test_registry_contains_all_documentation_rules() -> None:
    rules = repo_review_checks(["documentation"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "documentation" for rule in rules.values())
    assert len(DOCUMENTATION_QUALITY_RULES) == 30
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
    ("rule_id", "setting", "reason"),
    [
        ("DOC003", "numpydoc", "NumPy-style API documentation"),
        ("DOC004", "intersphinx", "external documentation"),
    ],
)
def test_sphinx_extensions_are_recommended(
    tmp_path: Path, rule_id: str, setting: str, reason: str
) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")

    result = report._run_checks(
        tmp_path, selected_rule_ids={rule_id}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert reason in result["detail"]

    _write_documentation(tmp_path, conf=f"extensions = ['{setting}']\n")

    assert _rule(rule_id).check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("rule_id", "index"),
    [
        ("DOC005", "Getting Started\n===============\n"),
        ("DOC006", "API Reference\n==============\n"),
    ],
)
def test_documentation_index_sections_are_checked(tmp_path: Path, rule_id: str, index: str) -> None:
    _write_documentation(tmp_path, index=index)

    assert _rule(rule_id).check(tmp_path, None) is True

    _write_documentation(tmp_path, index="Overview\n========\n")

    assert _rule(rule_id).check(tmp_path, None) is False


def test_gallery_check_is_not_applicable_without_gallery_extension(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")

    assert _rule("DOC007").check(tmp_path, None) is True


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
        tmp_path, selected_rule_ids={"DOC007"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert "example files" in result["detail"]

    examples = tmp_path / "doc" / "source" / "examples" / "basic"
    examples.mkdir(parents=True)
    (examples / "example.py").write_text("print('example')\n", encoding="utf-8")

    assert _rule("DOC007").check(tmp_path, None) is True


def test_nbsphinx_recommends_example_files(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = ['nbsphinx']\n")

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC007"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert "example files" in result["detail"]

    examples = tmp_path / "examples" / "basic"
    examples.mkdir(parents=True)
    (examples / "example.ipynb").write_text("{}\n", encoding="utf-8")

    assert _rule("DOC007").check(tmp_path, None) is True


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

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC008"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "WARNING"
    assert "pyansys logo" in result["detail"]


def test_project_and_page_titles_must_be_nonempty(tmp_path: Path) -> None:
    _write_documentation(
        tmp_path, conf=_VALID_CONF.replace('project = "test-project"', 'project = ""')
    )

    assert _rule("DOC009").check(tmp_path, None) is False

    _write_documentation(
        tmp_path,
        conf=_VALID_CONF.replace(
            'html_title = html_short_title = "Test project"', 'html_title = html_short_title = ""'
        ),
    )

    assert _rule("DOC009").check(tmp_path, None) is False


def test_site_metadata_accepts_dynamic_year_and_cname_fallback(tmp_path: Path) -> None:
    _write_documentation(tmp_path)

    assert _rule("DOC010").check(tmp_path, None) is True


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
        tmp_path, selected_rule_ids={"DOC010"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"


def test_theme_switcher_accepts_dynamic_config_values(tmp_path: Path) -> None:
    _write_documentation(tmp_path)

    assert _rule("DOC011").check(tmp_path, None) is True


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
        tmp_path, selected_rule_ids={"DOC011"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"


def _index_with_cards(targets: tuple[str, ...]) -> str:
    """Return an index containing document-link cards for the given targets."""
    cards = "\n".join(
        f"   .. grid-item-card:: {target}\n      :link: {target}\n      :link-type: doc"
        for target in targets
    )
    return f"Index\n=====\n\n.. grid::\n\n{cards}\n"


def test_index_requires_cards_for_each_top_level_document(tmp_path: Path) -> None:
    targets = (
        "getting-started",
        "user-guide",
        "api",
        "examples",
        "contribute",
        "changelog",
    )
    _write_documentation(tmp_path, index=_index_with_cards(targets))

    assert _rule("DOC012").check(tmp_path, None) is True

    _write_documentation(tmp_path, index=_index_with_cards(targets[:-1]))
    _assert_warning(_rule("DOC012").check(tmp_path, None), "changelog")


def test_index_cards_accept_section_index_targets(tmp_path: Path) -> None:
    targets = (
        "getting-started/index",
        "user-guide",
        "api/index",
        "examples",
        "contribute/index",
        "changelog",
    )
    _write_documentation(tmp_path, index=_index_with_cards(targets))

    assert _rule("DOC012").check(tmp_path, None) is True


def test_authored_rst_filenames_use_lowercase_hyphens(tmp_path: Path) -> None:
    _write_documentation(tmp_path)
    (tmp_path / "doc/source/good-page.rst").write_text("Page\n====\n", encoding="utf-8")

    assert _rule("DOC013").check(tmp_path, None) is True

    (tmp_path / "doc/source/bad_page.rst").write_text("Page\n====\n", encoding="utf-8")
    result = _rule("DOC013").check(tmp_path, None)
    _assert_warning(result, "bad_page.rst")


def test_rst_filename_rule_ignores_generated_autoapi_files(tmp_path: Path) -> None:
    _write_documentation(tmp_path)
    generated = tmp_path / "doc/source/api/src/pkg"
    generated.mkdir(parents=True)
    (generated / "Generated_API.rst").write_text("API\n===\n", encoding="utf-8")

    assert _rule("DOC013").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("rule_id", "relative_path", "is_section", "status"),
    [
        ("DOC014", "getting-started.rst", False, "RECOMMENDATION"),
        ("DOC015", "user-guide.rst", False, "RECOMMENDATION"),
        ("DOC016", "api.rst", False, "RECOMMENDATION"),
        ("DOC017", "examples.rst", False, "RECOMMENDATION"),
        ("DOC018", "contribute.rst", False, "RECOMMENDATION"),
        ("DOC019", "changelog.rst", False, "RECOMMENDATION"),
        ("DOC020", "getting-started", True, "RECOMMENDATION"),
        ("DOC021", "user-guide", True, "RECOMMENDATION"),
        ("DOC022", "api", True, "RECOMMENDATION"),
        ("DOC023", "examples", True, "RECOMMENDATION"),
        ("DOC024", "contribute", True, "RECOMMENDATION"),
        ("DOC025", "contribute/user.rst", False, "RECOMMENDATION"),
        ("DOC026", "contribute/documentarian.rst", False, "RECOMMENDATION"),
        ("DOC027", "contribute/developer.rst", False, "RECOMMENDATION"),
    ],
)
def test_each_documentation_layout_item_reports_missing_severity(
    tmp_path: Path, rule_id: str, relative_path: str, is_section: bool, status: str
) -> None:
    _write_documentation(tmp_path)
    result = report._run_checks(
        tmp_path, selected_rule_ids={rule_id}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == status

    path = tmp_path / "doc/source" / relative_path
    if is_section:
        path.mkdir(parents=True)
        (path / "index.rst").write_text("Section\n=======\n", encoding="utf-8")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Page\n====\n", encoding="utf-8")

    assert _rule(rule_id).check(tmp_path, None) is True


def test_getting_started_section_index_satisfies_root_page_rule(tmp_path: Path) -> None:
    _write_documentation(tmp_path)
    section_index = tmp_path / "doc/source/getting-started/index.rst"
    section_index.parent.mkdir(parents=True)
    section_index.write_text("Getting started\n===============\n", encoding="utf-8")

    assert _rule("DOC014").check(tmp_path, None) is True


@pytest.mark.parametrize(
    ("rule_id", "section"),
    [
        ("DOC015", "user-guide"),
        ("DOC016", "api"),
        ("DOC017", "examples"),
        ("DOC018", "contribute"),
    ],
)
def test_nested_section_indexes_satisfy_root_page_rules(
    tmp_path: Path, rule_id: str, section: str
) -> None:
    _write_documentation(tmp_path)
    section_index = tmp_path / "doc/source" / section / "index.rst"
    section_index.parent.mkdir(parents=True)
    section_index.write_text("Section\n=======\n", encoding="utf-8")

    assert _rule(rule_id).check(tmp_path, None) is True


def test_interrogate_hook_is_recommended_and_detected(tmp_path: Path) -> None:
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC028"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "WARNING"
    assert "docstring coverage" in result["detail"]

    (tmp_path / ".pre-commit-config.yaml").write_text(
        "repos:\n- repo: local\n  hooks:\n  - id: interrogate\n", encoding="utf-8"
    )
    assert _rule("DOC028").check(tmp_path, None) is True


@pytest.mark.parametrize("extension", ["ansys_sphinx_theme.extension.autoapi", "autoapi.extension"])
def test_sphinx_autoapi_extension_is_detected(tmp_path: Path, extension: str) -> None:
    _write_documentation(tmp_path, conf="extensions = []\n")
    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC029"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "WARNING"
    assert "API page" in result["detail"]

    _write_documentation(
        tmp_path, conf=f"extensions = get_extensions()\nextensions.append('{extension}')\n"
    )
    assert _rule("DOC029").check(tmp_path, None) is True


def test_sphinx_autoapi_marker_is_detected_anywhere_in_config(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf='SPHINX_AUTOAPI = "sphinx_autoapi"\n')

    assert _rule("DOC029").check(tmp_path, None) is True


@pytest.mark.parametrize("api_page", ["api.rst", "api/index.rst"])
def test_api_page_satisfies_autoapi_rule(tmp_path: Path, api_page: str) -> None:
    _write_documentation(tmp_path, conf="extensions = get_extensions()\n")
    path = tmp_path / "doc/source" / api_page
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("API Reference\n=============\n", encoding="utf-8")

    assert _rule("DOC029").check(tmp_path, None) is True


def test_dynamic_extensions_without_api_page_warn(tmp_path: Path) -> None:
    _write_documentation(tmp_path, conf="extensions = get_extensions()\n")

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC029"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "WARNING"
    assert "Sphinx AutoAPI was not found" in result["detail"]


def test_cheatsheet_configuration_is_recommended_and_recognized(tmp_path: Path) -> None:
    _write_documentation(tmp_path)
    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC030"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert result["detail"] == "Add a cheatsheet to the documentation."

    conf = _VALID_CONF.replace(
        '    "logo": "pyansys",',
        '    "logo": "pyansys",\n'
        '    "cheatsheet": {"file": "cheat_sheet/cheat_sheet.qmd", '
        '"title": "Project cheat sheet", "version": f"{version}", '
        '"pages": ["index"]},',
    )
    _write_documentation(tmp_path, conf=conf)

    assert _rule("DOC030").check(tmp_path, None) is True


def test_cheatsheet_recommends_missing_required_fields(tmp_path: Path) -> None:
    conf = _VALID_CONF.replace(
        '    "logo": "pyansys",',
        '    "logo": "pyansys",\n    "cheatsheet": {"file": "", "pages": []},',
    )
    _write_documentation(tmp_path, conf=conf)

    result = report._run_checks(
        tmp_path, selected_rule_ids={"DOC030"}, selected_families={"documentation"}
    )["results"][0]
    assert result["status"] == "RECOMMENDATION"
    assert result["detail"] == "Add a cheatsheet to the documentation."
