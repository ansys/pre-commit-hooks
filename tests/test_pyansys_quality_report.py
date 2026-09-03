# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ast
import os
from pathlib import Path

import git

import ansys.pre_commit_hooks.pyansys_quality_report as hook
from ansys.pre_commit_hooks.quality_rules.common import workflow_map
from ansys.pre_commit_hooks.quality_rules.project_metadata import PM013


def test_workflow_map_classifies_ci_cd_roles(tmp_path):
    """Workflow filenames like ci_cd_pr.yml should map to their canonical roles."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci_cd_main.yml").write_text("name: main\n", encoding="utf-8")
    (workflows / "ci_cd_pr.yml").write_text("name: pr\n", encoding="utf-8")
    (workflows / "ci_cd_release.yml").write_text("name: release\n", encoding="utf-8")

    result = workflow_map(tmp_path)

    assert set(result) >= {"main", "pr", "release"}
    assert result["pr"]["name"] == "ci_cd_pr.yml"


def test_pm013_accepts_supported_version_formats(tmp_path):
    """Development versions in Python packaging should be accepted alongside SemVer."""
    for version in ["1.2.3", "1.2.3-rc.1", "1.2.3.dev0", "1.2.3.dev1"]:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(f'[project]\nversion = "{version}"\n', encoding="utf-8")
        assert PM013.check(tmp_path) is True


def test_main_reports_quality_summary(tmp_path, capsys):
    """The quality report hook should run and print a summary for the repo."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    os.chdir(repo_path)
    git.Repo.init(repo_path)

    (repo_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (repo_path / "README.rst").write_text("Demo\n=====\n", encoding="utf-8")
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
authors = [{name = "Example", email = "example@example.com"}]
maintainers = [{name = "Example", email = "example@example.com"}]
""".strip(),
        encoding="utf-8",
    )

    exit_code = hook.main(["--repo-root", str(repo_path)])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "PyAnsys quality report" in output
    assert "Score" in output or "Summary" in output


def test_fix_missing_runs_quality_report_after_bootstrap(tmp_path, capsys):
    """--fix-missing should bootstrap the repo and then continue to the quality report."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    os.chdir(repo_path)
    git.Repo.init(repo_path)
    repo = git.Repo(repo_path)
    repo.index.commit("initial")

    (repo_path / ".github").mkdir()
    (repo_path / "src").mkdir()
    (repo_path / "tests").mkdir()
    (repo_path / "doc").mkdir()
    (repo_path / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
authors = [{name = "Example", email = "example@example.com"}]
maintainers = [{name = "Example", email = "example@example.com"}]
""".strip(),
        encoding="utf-8",
    )

    exit_code = hook.main(["--repo-root", str(repo_path), "--fix-missing", "--product=techreview"])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "PyAnsys quality report" in output
    assert "Score" in output or "Summary" in output


def test_main_colors_status_labels(tmp_path, capsys):
    """The console report should colorize pass, warn, and fail states."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    os.chdir(repo_path)
    git.Repo.init(repo_path)

    (repo_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (repo_path / "README.rst").write_text("Demo\n=====\n", encoding="utf-8")
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
""".strip(),
        encoding="utf-8",
    )

    exit_code = hook.main(["--repo-root", str(repo_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "\033[32m" in output
    assert "\033[33m" in output
    assert "\033[31m" in output


def test_hook_covers_all_repo_review_checks():
    """The package-level rule registry should expose the complete local check set."""

    import ansys.pre_commit_hooks.quality_rules as quality_rules

    checks_dir = Path(quality_rules.__file__).resolve().parent

    def class_names(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}

    family_names = {
        "ProjectMetadata",
        "CICDFiles",
        "CICD",
        "Dependabot",
        "Documentation",
        "README",
        "BuildSystem",
        "Security",
        "Labeler",
        "Vale",
        "MCP",
        "PreCommit",
    }

    expected = set()
    for path in checks_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        expected |= class_names(path)

    actual = set(quality_rules.repo_review_checks())
    assert expected - family_names == actual


def test_pm015_accepts_apache_license(tmp_path):
    """Project metadata should accept Apache 2.0 as a valid license text."""
    repo_path = tmp_path / "apache-license-project"
    repo_path.mkdir()

    (repo_path / "LICENSE").write_text(
        "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n",
        encoding="utf-8",
    )

    import ansys.pre_commit_hooks.quality_rules.project_metadata as project_metadata

    assert project_metadata.PM015.check(repo_path) is True


def test_quality_rules_are_grouped_package():
    """Quality rules should be exposed from a package with one module per check family."""
    import ansys.pre_commit_hooks.quality_rules as quality_rules
    import ansys.pre_commit_hooks.quality_rules.project_metadata as project_metadata

    assert hasattr(quality_rules, "PM001")
    assert hasattr(project_metadata, "PM001")
    assert callable(quality_rules.repo_review_checks)


def test_legacy_license_check_accepts_apache_2_0_by_default(tmp_path):
    """The legacy bootstrap should not reject a valid Apache 2.0 LICENSE no configured."""
    license_path = tmp_path / "LICENSE"
    license_path.write_text(
        "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n",
        encoding="utf-8",
    )

    result = hook.check_file_content(
        license_path,
        "MIT License\n",
        True,
        hook.DEFAULT_LICENSE,
    )

    assert result is True


def test_normalize_check_result_standardizes_rule_status():
    """Rule evaluation results should normalize to the canonical pass/warn/fail/na model."""
    from ansys.pre_commit_hooks.quality_rules.common import normalize_check_result

    assert normalize_check_result(True) == ("pass", "")
    assert normalize_check_result(None) == ("na", "")
    assert normalize_check_result("⚠️ check warning") == ("warn", "check warning")
    assert normalize_check_result(False) == ("fail", "")
