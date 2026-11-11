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

"""Tests for the Vale quality rule family."""

import json
from pathlib import Path

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import VALE_QUALITY_RULES, Vale, repo_review_checks
from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult

_RULE_IDS = tuple(f"VL{number:03d}" for number in range(1, 20))
_CONFIG_RULE_IDS = tuple(rule_id for rule_id in _RULE_IDS if rule_id != "VL019")
_VOCABULARY_DIRECTORY = "doc/styles/config/vocabularies/ANSYS"
_VALID_CONFIGURATION = r'''# Core settings
# =============

# Location of our `styles`
StylesPath = "styles"

# The options are `suggestion`, `warning`, or `error` (defaults to "warning").
MinAlertLevel = warning

# By default, `code` and `tt` are ignored.
IgnoredScopes = code, tt

# By default, `script`, `style`, `pre`, and `figure` are ignored.
SkippedScopes = script, style, pre, figure

# WordTemplate specifies what Vale will consider to be an individual word.
WordTemplate = \b(?:%s)\b

# List of Packages to be used for our guidelines
Packages = Google

# Define the Ansys vocabulary
Vocab = ANSYS

[formats]
# Python + Markdown
py = md

[*.{py,md,rst}]

# Apply the following styles
BasedOnStyles = Vale, Google
Google.Headings = NO
Vale.Terms = NO
TokenIgnores = (\$+[^\n$]+\$+), (:.*:`.*`)|(<.*>)
BlockIgnores = (?s) """([^"]*)"""
'''
_STYLES_GITIGNORE = """\
*
!**/ANSYS/accept.txt
!**/ANSYS/reject.txt
!.gitignore
"""


def _write_configuration(root: Path, content: str = _VALID_CONFIGURATION) -> None:
    (root / "doc").mkdir(exist_ok=True)
    (root / "doc" / ".vale.ini").write_text(content, encoding="utf-8")


def _write_vocabulary(root: Path, directory: str = _VOCABULARY_DIRECTORY) -> None:
    vocabulary = root / directory
    vocabulary.mkdir(parents=True, exist_ok=True)
    (vocabulary / "accept.txt").write_text("PyAnsys\n", encoding="utf-8")
    (vocabulary / "reject.txt").write_text("", encoding="utf-8")


def _write_repository(root: Path, content: str = _VALID_CONFIGURATION) -> None:
    _write_configuration(root, content)
    _write_vocabulary(root)
    (root / "doc" / "styles" / ".gitignore").write_text(_STYLES_GITIGNORE, encoding="utf-8")


def _statuses(root: Path) -> dict[str, str]:
    results = report._run_checks(root, selected_families={"vale"})["results"]
    return {result["id"]: result["status"] for result in results}


def _check(root: Path, rule_id: str) -> RuleCheckResult:
    return repo_review_checks(["vale"])[rule_id].check(root, None)


def test_registry_contains_all_vale_rules() -> None:
    rules = repo_review_checks(["vale"])

    assert tuple(rules) == _RULE_IDS
    assert all(rule.family == "vale" for rule in rules.values())
    assert len(VALE_QUALITY_RULES) == 19
    assert all(issubclass(rule, Vale) for rule in VALE_QUALITY_RULES)


def test_all_rules_pass_for_complete_configuration(tmp_path: Path) -> None:
    _write_repository(tmp_path)

    for rule in repo_review_checks(["vale"]).values():
        assert rule.check(tmp_path, None) is True


@pytest.mark.parametrize("rule_id", _CONFIG_RULE_IDS)
def test_missing_configuration_is_an_error(tmp_path: Path, rule_id: str) -> None:
    results = report._run_checks(tmp_path, selected_rule_ids={rule_id})["results"]

    assert len(results) == 1
    assert results[0]["status"] == "ERROR"
    assert "doc/.vale.ini" in results[0]["detail"]


def test_configuration_must_be_a_file(tmp_path: Path) -> None:
    (tmp_path / "doc" / ".vale.ini").mkdir(parents=True)

    statuses = _statuses(tmp_path)

    assert statuses.pop("VL019") == "PASSED"
    assert set(statuses.values()) == {"ERROR"}


def test_configuration_symlink_outside_repository_is_an_error(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside.ini"
    outside.write_text(_VALID_CONFIGURATION, encoding="utf-8")
    (repository / "doc").mkdir(parents=True)
    (repository / "doc" / ".vale.ini").symlink_to(outside)
    _write_vocabulary(repository)

    statuses = _statuses(repository)

    assert statuses.pop("VL019") == "PASSED"
    assert set(statuses.values()) == {"ERROR"}


@pytest.mark.parametrize("content", [b"\xff\xfe", b"[unterminated\nPackages = Google\n"])
def test_unreadable_or_invalid_configuration_is_an_error(tmp_path: Path, content: bytes) -> None:
    (tmp_path / "doc").mkdir()
    (tmp_path / "doc" / ".vale.ini").write_bytes(content)
    _write_vocabulary(tmp_path)

    statuses = _statuses(tmp_path)

    assert statuses.pop("VL001") == "PASSED"
    assert statuses.pop("VL019") == "PASSED"
    assert set(statuses.values()) == {"ERROR"}


@pytest.mark.parametrize(
    ("old", "new", "expected"),
    [
        ("Packages = Google", "Packages = Microsoft", "Packages"),
        ("Packages = Google\n", "", "Packages"),
        ("Packages = Google", "Packages = google", "Packages"),
        ("BasedOnStyles = Vale, Google", "BasedOnStyles = Vale", "BasedOnStyles"),
    ],
)
def test_google_package_must_be_installed_and_applied(
    tmp_path: Path, old: str, new: str, expected: str
) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace(old, new))

    result = _check(tmp_path, "VL002")

    assert isinstance(result, str)
    assert result.startswith("ERROR: ")
    assert expected in result


def test_google_package_can_be_a_download_url(tmp_path: Path) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace(
            "Packages = Google",
            "Packages = Microsoft, "
            "https://github.com/errata-ai/Google/releases/download/v0.6.1/Google.zip",
        ),
    )

    assert _check(tmp_path, "VL002") is True


@pytest.mark.parametrize(
    ("vocab", "passes"),
    [
        ("Vocab = ANSYS", True),
        ("Vocab = Base, ANSYS", True),
        ("Vocab = Ansys", False),
        ("Vocab = Base", False),
        ("", False),
    ],
)
def test_ansys_vocabulary_must_be_enabled(tmp_path: Path, vocab: str, passes: bool) -> None:
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace("Vocab = ANSYS", vocab))

    result = _check(tmp_path, "VL003")

    assert (result is True) is passes


@pytest.mark.parametrize(
    ("rule_id", "file_name"), [("VL004", "accept.txt"), ("VL005", "reject.txt")]
)
def test_missing_vocabulary_file_is_an_error(tmp_path: Path, rule_id: str, file_name: str) -> None:
    _write_configuration(tmp_path)
    _write_vocabulary(tmp_path)
    (tmp_path / _VOCABULARY_DIRECTORY / file_name).unlink()

    result = _check(tmp_path, rule_id)

    assert isinstance(result, str)
    assert result.startswith("ERROR: ")
    assert f"{_VOCABULARY_DIRECTORY}/{file_name}" in result


@pytest.mark.parametrize(
    ("styles_path", "vocabulary_directory"),
    [
        ("styles", _VOCABULARY_DIRECTORY),
        ("_vale", "doc/_vale/config/vocabularies/ANSYS"),
        ("styles", "doc/styles/Vocab/ANSYS"),
    ],
)
def test_vocabulary_is_found_under_styles_path(
    tmp_path: Path, styles_path: str, vocabulary_directory: str
) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace('StylesPath = "styles"', f"StylesPath = {styles_path}"),
    )
    _write_vocabulary(tmp_path, vocabulary_directory)

    statuses = _statuses(tmp_path)

    assert statuses["VL004"] == "PASSED"
    assert statuses["VL005"] == "PASSED"


@pytest.mark.parametrize("styles_line", ["", "StylesPath = ../../outside\n"])
def test_vocabulary_requires_styles_path_inside_repository(
    tmp_path: Path, styles_line: str
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    _write_configuration(
        repository, _VALID_CONFIGURATION.replace('StylesPath = "styles"\n', styles_line)
    )
    _write_vocabulary(repository)
    _write_vocabulary(tmp_path, "outside/config/vocabularies/ANSYS")

    statuses = _statuses(repository)

    assert statuses["VL004"] == "ERROR"
    assert statuses["VL005"] == "ERROR"


def test_cli_lists_vale_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert report.main(["--metadata", "--family", "vale"]) == 0

    metadata = json.loads(capsys.readouterr().out)

    assert [rule["id"] for rule in metadata] == list(_RULE_IDS)
    assert all(rule["family"] == "vale" for rule in metadata)


def test_cli_reports_vale_family(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_repository(tmp_path)
    monkeypatch.chdir(tmp_path)

    assert report.main(["--json", "--family", "vale"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert [result["id"] for result in payload["results"]] == list(_RULE_IDS)
    assert payload["tally"] == {"PASSED": 19, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 0}

    (tmp_path / _VOCABULARY_DIRECTORY / "reject.txt").unlink()
    assert report.main(["--json", "--family", "vale"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["tally"] == {"PASSED": 18, "RECOMMENDATION": 0, "WARNING": 0, "ERROR": 1}


def _assert_status(result: RuleCheckResult, prefix: str, *expected: str) -> None:
    assert isinstance(result, str)
    assert result.startswith(f"{prefix}: ")
    for text in expected:
        assert text in result


@pytest.mark.parametrize(
    ("styles_line", "passes"),
    [
        ('StylesPath = "styles"', True),
        ("StylesPath = ./styles", True),
        ("StylesPath = _vale", False),
    ],
)
def test_styles_path_is_styles(tmp_path: Path, styles_line: str, passes: bool) -> None:
    _write_configuration(
        tmp_path, _VALID_CONFIGURATION.replace('StylesPath = "styles"', styles_line)
    )

    result = _check(tmp_path, "VL006")

    if passes:
        assert result is True
    else:
        _assert_status(result, "WARNING", "StylesPath")


@pytest.mark.parametrize(
    ("level_line", "passes"),
    [
        ("MinAlertLevel = warning", True),
        ("MinAlertLevel = Error", True),
        ("MinAlertLevel = suggestion", False),
        ("MinAlertLevel = loud", False),
        ("", False),
    ],
)
def test_min_alert_level_is_warning_or_stricter(
    tmp_path: Path, level_line: str, passes: bool
) -> None:
    _write_configuration(
        tmp_path, _VALID_CONFIGURATION.replace("MinAlertLevel = warning", level_line)
    )

    result = _check(tmp_path, "VL007")

    if passes:
        assert result is True
    else:
        _assert_status(result, "WARNING", "MinAlertLevel")


@pytest.mark.parametrize(
    ("rule_id", "old", "new", "expected"),
    [
        ("VL008", "IgnoredScopes = code, tt", "IgnoredScopes = code", "tt to IgnoredScopes"),
        ("VL008", "IgnoredScopes = code, tt\n", "", "code, tt to IgnoredScopes"),
        (
            "VL009",
            "SkippedScopes = script, style, pre, figure",
            "SkippedScopes = script, style",
            "pre, figure to SkippedScopes",
        ),
        ("VL010", r"WordTemplate = \b(?:%s)\b", "WordTemplate = %s", "WordTemplate"),
        ("VL012", "py = md", "py = rst", "py = md"),
        ("VL012", "[formats]\n# Python + Markdown\npy = md\n", "", "[formats]"),
        ("VL014", "Vale.Terms = NO", "Vale.Terms = YES", "Vale.Terms = NO"),
        ("VL015", 'BlockIgnores = (?s) """([^"]*)"""\n', "", "Set BlockIgnores in"),
    ],
)
def test_template_settings_are_recommended(
    tmp_path: Path, rule_id: str, old: str, new: str, expected: str
) -> None:
    assert old in _VALID_CONFIGURATION
    _write_configuration(tmp_path, _VALID_CONFIGURATION.replace(old, new))

    _assert_status(_check(tmp_path, rule_id), "RECOMMENDATION", expected)


def test_scope_lists_may_include_extra_scopes(tmp_path: Path) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace("IgnoredScopes = code, tt", "IgnoredScopes = tt, code, kbd"),
    )

    assert _check(tmp_path, "VL008") is True


@pytest.mark.parametrize(
    ("sections", "missing"),
    [
        ("[*.{py,md,rst}]\nBasedOnStyles = Vale, Google\n", None),
        ("[*.py]\nBasedOnStyles = Google\n[*.{md,rst}]\nBasedOnStyles = Vale\n", None),
        ("[*]\nBasedOnStyles = Vale, Google\n", None),
        ("[*.{rst}]\nBasedOnStyles = Vale, Google\n", "*.py, *.md"),
        ("[*.{py,md}]\nVale.Terms = NO\n[*.rst]\nBasedOnStyles = Vale\n", "*.py, *.md"),
    ],
)
def test_styles_apply_to_python_markdown_and_rst(
    tmp_path: Path, sections: str, missing: str | None
) -> None:
    _write_configuration(tmp_path, f"StylesPath = styles\n{sections}")

    result = _check(tmp_path, "VL011")

    if missing is None:
        assert result is True
    else:
        _assert_status(result, "WARNING", missing)


def test_vale_style_must_be_applied(tmp_path: Path) -> None:
    _write_configuration(
        tmp_path,
        _VALID_CONFIGURATION.replace("BasedOnStyles = Vale, Google", "BasedOnStyles = Google"),
    )

    _assert_status(_check(tmp_path, "VL013"), "WARNING", "Vale through BasedOnStyles")
    assert _check(tmp_path, "VL002") is True


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (None, "does not exist"),
        ("*\n!vocabularies\n!vocabularies/**\n!.gitignore\n", "!**/ANSYS/accept.txt"),
    ],
)
def test_styles_gitignore_keeps_only_the_vocabulary(
    tmp_path: Path, content: str | None, expected: str
) -> None:
    _write_repository(tmp_path)
    gitignore = tmp_path / "doc" / "styles" / ".gitignore"
    if content is None:
        gitignore.unlink()
    else:
        gitignore.write_text(content, encoding="utf-8")

    _assert_status(_check(tmp_path, "VL016"), "WARNING", "doc/styles/.gitignore", expected)


@pytest.mark.parametrize(
    ("content", "rule_id", "expected"),
    [
        ("", "VL017", "Add project terms"),
        ("\n  \n", "VL017", "Add project terms"),
        ("PyAnsys\n\nMAPDL\nPyAnsys\nMAPDL\n", "VL018", "duplicate entries PyAnsys, MAPDL"),
        ("PyAnsys\n\nMAPDL\n", "VL018", "1 blank line(s)"),
    ],
)
def test_accept_vocabulary_content_is_checked(
    tmp_path: Path, content: str, rule_id: str, expected: str
) -> None:
    _write_repository(tmp_path)
    (tmp_path / _VOCABULARY_DIRECTORY / "accept.txt").write_text(content, encoding="utf-8")

    _assert_status(_check(tmp_path, rule_id), "RECOMMENDATION", expected)


@pytest.mark.parametrize("rule_id", ["VL017", "VL018"])
def test_missing_accept_vocabulary_is_an_error(tmp_path: Path, rule_id: str) -> None:
    _write_configuration(tmp_path)

    _assert_status(_check(tmp_path, rule_id), "ERROR", "accept.txt")


@pytest.mark.parametrize("file_name", [".codespell.exclude", ".codespell.ignore"])
def test_legacy_codespell_lists_are_reported(tmp_path: Path, file_name: str) -> None:
    (tmp_path / file_name).write_text("pyansys\n", encoding="utf-8")

    _assert_status(_check(tmp_path, "VL019"), "RECOMMENDATION", file_name)
