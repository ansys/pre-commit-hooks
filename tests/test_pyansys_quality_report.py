# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ast
import os
from pathlib import Path

import git
import pytest

from ansys.pre_commit_hooks import quality_rules
import ansys.pre_commit_hooks.pyansys_quality_report as hook
from ansys.pre_commit_hooks.quality_rules import project_metadata, security
from ansys.pre_commit_hooks.quality_rules.common import workflow_map
from ansys.pre_commit_hooks.quality_rules.project_metadata import (
    PM013,
    PM016,
    PM017,
    PM021,
    PM022,
    PM024,
    PM025,
    PM026,
    PM027,
    PM028,
    PM029,
)


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


@pytest.mark.parametrize(
    ("rule", "workflow_name", "workflow_body"),
    [
        ("CI005", "pr.yml", "- uses: ansys/actions/label"),
        ("CI006", "pr.yml", "- uses: ansys/actions/check-vulnerabilities"),
        ("CI007", "pr.yml", "- uses: ansys/actions/code-style"),
        ("CI008", "pr.yml", "- uses: ansys/actions/check-pr-title"),
        ("CI009", "release.yml", "- uses: ansys/actions/changelog-fragment"),
        ("CI010", "main.yml", "- uses: ansys/actions/check-doc-style"),
        ("CI011", "main.yml", "- uses: ansys/actions/doc-build"),
        ("CI012", "main.yml", "- uses: ansys/actions/build-wheelhouse"),
        ("CI013", "main.yml", "- uses: ansys/actions/tests-pytest"),
        ("CI014", "release.yml", "- uses: ansys/actions/release-github"),
        ("CI015", "main.yml", "- uses: ansys/actions/check-actions-security"),
        ("CI016", "main.yml", "- uses: ansys/actions/build-library"),
        ("CI017", "main.yml", "- uses: ansys/actions/doc-deploy-dev"),
        ("CI018", "release.yml", "- uses: ansys/actions/doc-deploy-stable"),
        ("CI019", "release.yml", "- uses: ansys/actions/doc-deploy-changelog"),
    ],
)
def test_ci_action_rules_require_expected_actions(tmp_path, rule, workflow_name, workflow_body):
    """Action-based CI checks should pass when their required action is present."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / workflow_name).write_text(workflow_body, encoding="utf-8")

    assert getattr(quality_rules, rule).check(tmp_path) is True


def test_ci_rules_live_in_main_ci_family():
    """All CI checks should be grouped under the main CI rule family."""
    families = quality_rules.repo_review_families()

    assert "cicd_files" not in families
    assert families["cicd"]["name"] == "CI/CD"


def test_ci001_ci004_accept_noncanonical_workflow_name(tmp_path):
    """Role checks should work with generic workflow names like cicd.yml."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "cicd.yml").write_text(
        """
name: CI/CD
on: [pull_request]
permissions: {}
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
        """.strip(),
        encoding="utf-8",
    )

    workflows_by_role = workflow_map(tmp_path)
    assert quality_rules.CI001.check(tmp_path) is True
    assert quality_rules.CI002.check(tmp_path, workflows_by_role) is True
    assert quality_rules.CI003.check(tmp_path, workflows_by_role) is True
    assert quality_rules.CI004.check(tmp_path, workflows_by_role) is True


def test_main_lists_quality_check_metadata(capsys):
    """The CLI should list the available quality checks through a metadata flag."""
    exit_code = hook.main(["--metadata"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"id": "PM001"' in output
    assert '"id": "PC001"' in output
    assert '"family": "project_metadata"' in output


def test_main_can_limit_checks_to_selected_codes(tmp_path, capsys):
    """The CLI should allow a subset of checks to be evaluated using a selection flag."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
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

    exit_code = hook.main(["--repo-root", str(repo_path), "--check", "PM010,PM014"])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "PM010" in output or "PM014" in output
    assert "PM001" not in output


def test_main_can_limit_checks_to_selected_family(tmp_path, capsys):
    """The CLI should allow a repository family to be selected instead of individual rule IDs."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
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

    exit_code = hook.main(["--repo-root", str(repo_path), "--family", "documentation", "--all"])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "DOC001" in output
    assert "PM001" not in output


def test_doc008_is_not_applicable_without_gallery_extensions(tmp_path):
    """DOC008 should be N/A when neither sphinx-gallery nor nbsphinx is enabled."""
    docs = tmp_path / "doc" / "source"
    docs.mkdir(parents=True)
    (docs / "conf.py").write_text("extensions = ['sphinx.ext.autodoc']\n", encoding="utf-8")
    (docs / "index.rst").write_text("Home\n====\n", encoding="utf-8")

    assert quality_rules.DOC008.check(tmp_path) is None


def test_doc008_requires_examples_dirs_and_gallery_dirs_for_sphinx_gallery(tmp_path):
    """DOC008 should require examples_dirs and gallery_dirs when sphinx-gallery is enabled."""
    docs = tmp_path / "doc" / "source"
    docs.mkdir(parents=True)

    (docs / "conf.py").write_text(
        """
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_gallery.gen_gallery',
]
sphinx_gallery_conf = {
    'examples_dirs': '../examples',
    'gallery_dirs': 'examples',
}
""".strip() + "\n",
        encoding="utf-8",
    )
    (docs / "index.rst").write_text("Home\n====\n", encoding="utf-8")
    (tmp_path / "doc" / "examples").mkdir(parents=True)
    (tmp_path / "doc" / "examples" / "demo.py").write_text("print('demo')\n", encoding="utf-8")

    assert quality_rules.DOC008.check(tmp_path) is True

    (tmp_path / "doc" / "examples" / "demo.py").unlink()
    assert quality_rules.DOC008.check(tmp_path) is False

    (tmp_path / "doc" / "examples" / "demo.py").write_text("print('demo')\n", encoding="utf-8")

    (docs / "conf.py").write_text(
        """
extensions = [
    'sphinx.ext.autodoc',
    'sphinx_gallery.gen_gallery',
]
sphinx_gallery_conf = {
    'examples_dirs': '../examples',
}
""".strip() + "\n",
        encoding="utf-8",
    )

    assert quality_rules.DOC008.check(tmp_path) is False


def test_doc008_requires_examples_section_for_nbsphinx(tmp_path):
    """DOC008 should require a non-empty examples directory when nbsphinx is enabled."""
    docs = tmp_path / "doc" / "source"
    docs.mkdir(parents=True)
    (docs / "conf.py").write_text(
        "extensions = ['sphinx.ext.autodoc', 'nbsphinx']\n",
        encoding="utf-8",
    )
    (docs / "index.rst").write_text("Home\n====\n", encoding="utf-8")

    assert quality_rules.DOC008.check(tmp_path) is False

    (docs / "index.rst").write_text(
        """
Home
====

.. toctree::
   :maxdepth: 2

   examples/index
""".strip() + "\n",
        encoding="utf-8",
    )

    assert quality_rules.DOC008.check(tmp_path) is False

    examples_dir = docs / "examples"
    examples_dir.mkdir()
    (examples_dir / "index.rst").write_text("Examples\n========\n", encoding="utf-8")

    assert quality_rules.DOC008.check(tmp_path) is True


def test_doc008_logs_where_examples_are_configured_on_pass(tmp_path):
    """DOC008 should record where examples were configured when the check passes."""
    docs = tmp_path / "doc" / "source"
    docs.mkdir(parents=True)
    (docs / "conf.py").write_text(
        "extensions = ['sphinx.ext.autodoc', 'nbsphinx']\n",
        encoding="utf-8",
    )
    (docs / "index.rst").write_text(
        """
Home
====

.. toctree::
   :maxdepth: 2

   examples/index
""".strip() + "\n",
        encoding="utf-8",
    )
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "demo.py").write_text("print('demo')\n", encoding="utf-8")

    assert quality_rules.DOC008.check(tmp_path) is True
    assert "doc/source/conf.py" in quality_rules.DOC008.pass_detail
    assert "examples" in quality_rules.DOC008.pass_detail


def test_db009_warns_when_github_actions_updates_are_not_grouped(tmp_path):
    """DB009 should warn when github-actions updates are configured without groups."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "dependabot.yml").write_text(
        """
version: 2
updates:
    - package-ecosystem: "github-actions"
        directory: "/"
        schedule:
            interval: "weekly"
""".strip() + "\n",
        encoding="utf-8",
    )

    result = quality_rules.DB009.check(tmp_path)
    assert isinstance(result, str)
    assert result.startswith("WARN: ")


def test_db009_passes_when_ansys_actions_updates_are_grouped(tmp_path):
    """DB009 should pass when github-actions updates are grouped for Ansys actions."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "dependabot.yml").write_text(
        """
version: 2
updates:
    - package-ecosystem: "github-actions"
        directory: "/"
        schedule:
            interval: "weekly"
        groups:
            ansys-actions:
                patterns:
                    - "ansys/actions/*"
""".strip() + "\n",
        encoding="utf-8",
    )

    assert quality_rules.DB009.check(tmp_path) is True


def test_db008_warns_when_only_actions_are_grouped(tmp_path):
    """DB008 should warn when pip lacks grouping even if github-actions has grouped wildcard."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "dependabot.yml").write_text(
        """
version: 2
updates:
    - package-ecosystem: "pip"
        directory: "/"
        schedule:
            interval: "weekly"

    - package-ecosystem: "github-actions"
        directory: "/"
        schedule:
            interval: "weekly"
        groups:
            actions:
                patterns:
                    - "*"
""".strip() + "\n",
        encoding="utf-8",
    )

    result = quality_rules.DB008.check(tmp_path)
    assert isinstance(result, str)
    assert result.startswith("WARN: ")


def test_db008_passes_when_pip_updates_are_grouped(tmp_path):
    """DB008 should pass when pip updates are grouped with wildcard pattern."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir(parents=True)
    (github_dir / "dependabot.yml").write_text(
        """
version: 2
updates:
    - package-ecosystem: "pip"
        directory: "/"
        schedule:
            interval: "weekly"
        groups:
            python-deps:
                patterns:
                    - "*"
""".strip() + "\n",
        encoding="utf-8",
    )

    assert quality_rules.DB008.check(tmp_path) is True


def test_pm013_accepts_supported_version_formats(tmp_path):
    """Development versions in Python packaging should be accepted alongside SemVer."""
    for version in ["1.2.3", "1.2.3-rc.1", "1.2.3.dev0", "1.2.3.dev1"]:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(f'[project]\nversion = "{version}"\n', encoding="utf-8")
        assert PM013.check(tmp_path) is True


def test_pm010_accepts_poetry_readme_reference(tmp_path):
    """Poetry projects should validate the README path the same way as other build systems."""
    repo_path = tmp_path / "poetry-project"
    repo_path.mkdir()

    (repo_path / "README.rst").write_text("Poetry\n======\n", encoding="utf-8")
    (repo_path / "pyproject.toml").write_text(
        """
[tool.poetry]
name = "ansys-demo-library"
version = "0.1.0"
description = "Demo"
readme = "README.rst"
""".strip(),
        encoding="utf-8",
    )

    assert project_metadata.PM010.check(repo_path, "README.rst") is True


def test_main_reports_quality_summary(tmp_path, capsys, monkeypatch):
    """The quality report hook should run and print a summary for the repo."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    monkeypatch.chdir(repo_path)
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


def test_fix_missing_runs_quality_report_after_bootstrap(tmp_path, capsys, monkeypatch):
    """--fix-missing should bootstrap the repo and then continue to the quality report."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    monkeypatch.chdir(repo_path)
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


def test_main_colors_status_labels(tmp_path, capsys, monkeypatch):
    """The console report should colorize pass, warn, and fail states."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    monkeypatch.chdir(repo_path)
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


def test_main_shows_passing_checks_by_default(tmp_path, capsys):
    """The text report should include passing checks without requiring --all."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    (repo_path / "doc" / "source").mkdir(parents=True)
    (repo_path / "doc" / "source" / "index.rst").write_text("Home\n====\n", encoding="utf-8")

    exit_code = hook.main(["--repo-root", str(repo_path), "--family", "documentation"])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "DOC001" in output


def test_main_fails_only_hides_passing_checks(tmp_path, capsys):
    """The --fails-only flag should suppress passing checks in text output."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    (repo_path / "doc" / "source").mkdir(parents=True)
    (repo_path / "doc" / "source" / "index.rst").write_text("Home\n====\n", encoding="utf-8")

    exit_code = hook.main(
        ["--repo-root", str(repo_path), "--family", "documentation", "--fails-only"]
    )
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "DOC001" not in output


def test_hook_covers_all_repo_review_checks():
    """The package-level rule registry should expose the complete local check set."""

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


def test_sec004_requires_all_uses_lines_to_be_pinned(tmp_path):
    """Mixed pinned and unpinned GitHub Actions should fail instead of passing on a single SHA."""
    repo_path = tmp_path / "security-project"
    repo_path.mkdir()
    (repo_path / ".github").mkdir()
    (repo_path / ".github" / "workflows").mkdir()
    (repo_path / ".github" / "workflows" / "pr.yml").write_text(
        """
name: PR
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@0123456789abcdef0123456789abcdef01234567
      - uses: actions/cache@v4
""".strip(),
        encoding="utf-8",
    )

    assert security.SEC004.check(repo_path, {"pr": {"path": ".github/workflows/pr.yml"}}) == (
        "WARN: Some GitHub Actions in the PR workflow are not pinned to full commit SHAs. "
        "Use full commit SHAs for all actions."
    )


def test_pm015_accepts_apache_license(tmp_path):
    """Project metadata should accept Apache 2.0 as a valid license text."""
    repo_path = tmp_path / "apache-license-project"
    repo_path.mkdir()

    (repo_path / "LICENSE").write_text(
        "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n",
        encoding="utf-8",
    )

    assert project_metadata.PM015.check(repo_path) is True


def test_pm014_rejects_wrong_author_block_when_maintainer_block_is_valid(tmp_path):
    """Author validation must stay limited to the authors array and not bleed into maintainers."""
    repo_path = tmp_path / "author-bounds-project"
    repo_path.mkdir()

    (repo_path / "pyproject.toml").write_text(
        """
[project]
authors = [{ name = "Wrong Author", email = "wrong@example.com" }]
maintainers = [{ name = "Synopsys, Inc. and ANSYS, Inc.", email = "pyansys-core@synopsys.com" }]
""".strip(),
        encoding="utf-8",
    )

    assert project_metadata.PM014.check(repo_path) == (
        "WARN: author/maintainer metadata does not match "
        "Synopsys, Inc. and ANSYS, Inc. / "
        "pyansys-core@synopsys.com."
    )


def test_pm016_warns_on_empty_codeowners(tmp_path):
    """CODEOWNERS should require at least one actual owner entry."""
    repo_path = tmp_path / "codeowners-project"
    repo_path.mkdir()
    (repo_path / ".github").mkdir()
    (repo_path / ".github" / "CODEOWNERS").write_text("# comment only\n", encoding="utf-8")

    assert PM016.check(repo_path) == "WARN: .github/CODEOWNERS exists but has no owner entries."


def test_pm016_accepts_valid_codeowners(tmp_path):
    """CODEOWNERS with an actual @owner entry should pass."""
    repo_path = tmp_path / "codeowners-project"
    repo_path.mkdir()
    (repo_path / ".github").mkdir()
    (repo_path / ".github" / "CODEOWNERS").write_text("* @ansys/maintainers\n", encoding="utf-8")

    assert PM016.check(repo_path) is True


def test_load_files_keeps_repo_directories_and_task_runner_files_for_virtual_review(tmp_path):
    """Virtual repo reviews should recognize real directories and task-runner files."""
    repo_path = tmp_path / "virtual-review-repo"
    repo_path.mkdir()
    (repo_path / "tests").mkdir()
    (repo_path / "tests" / "test_example.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    (repo_path / "tox.ini").write_text("[tox]\nenvlist = py\n", encoding="utf-8")

    files = hook._load_files(repo_path)
    root = hook.MemoryTraversable(files)

    assert PM022.check(root) is True
    assert PM024.check(root) is True


def test_pyansys_quality_report_ignore_option_skips_selected_checks(tmp_path, capsys):
    """--ignore should remove selected checks from the quality report output."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    os.chdir(repo_path)
    git.Repo.init(repo_path)

    (repo_path / "tests").mkdir()
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

    exit_code = hook.main(["--repo-root", str(repo_path), "--ignore", "PM022,PM024"])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "PM022" not in output
    assert "PM024" not in output


def test_pyansys_quality_report_reads_ignore_from_pyproject_toml(tmp_path, capsys):
    """Ignoring checks in pyproject.toml should suppress those checks in the report."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    os.chdir(repo_path)
    git.Repo.init(repo_path)

    (repo_path / "tests").mkdir()
    (repo_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    (repo_path / "README.rst").write_text("Demo\n=====\n", encoding="utf-8")
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
authors = [{name = "Example", email = "example@example.com"}]
maintainers = [{name = "Example", email = "example@example.com"}]

[tool.ansys-pre-commit-hooks]
ignore = ["PM022", "PM024"]
""".strip(),
        encoding="utf-8",
    )

    exit_code = hook.main(["--repo-root", str(repo_path)])
    output = capsys.readouterr().out

    assert exit_code in (0, 1)
    assert "PM022" not in output
    assert "PM024" not in output


def test_pm021_requires_docs_directory(tmp_path):
    """Projects should have a docs or doc directory for documentation."""
    assert PM021.check(tmp_path) is False

    (tmp_path / "doc").mkdir()
    assert PM021.check(tmp_path) is True


def test_pm022_requires_tests_directory(tmp_path):
    """Projects should have a tests directory."""
    assert PM022.check(tmp_path) is False

    (tmp_path / "tests").mkdir()
    assert PM022.check(tmp_path) is True


def test_pm024_requires_task_runner_configuration(tmp_path):
    """Projects should expose a task runner configuration file for common workflows."""
    assert PM024.check(tmp_path) is False

    (tmp_path / "tox.ini").write_text("[tox]\nenvlist = py\n", encoding="utf-8")
    assert PM024.check(tmp_path) is True


def test_pm025_requires_contact_support_urls_in_pyproject(tmp_path):
    """Project metadata should include support URLs in the project.urls section."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "ansys-demo-library"

[project.urls]
Source = "https://github.com/ansys/demo"
Issues = "https://github.com/ansys/demo/issues"
Discussions = "https://github.com/ansys/demo/discussions"
Documentation = "https://demo.docs.pyansys.com"
""".strip() + "\n",
        encoding="utf-8",
    )

    assert PM025.check(tmp_path) is True


def test_pm026_requires_corporate_entry_in_authors_file(tmp_path):
    """AUTHORS should include at least one ownership entry and the corporate owner line."""
    (tmp_path / "AUTHORS").write_text(
        "# contributors\nSynopsys, Inc. and ANSYS, Inc.\n",
        encoding="utf-8",
    )

    assert PM026.check(tmp_path) is True


def test_pm027_requires_contributors_sections(tmp_path):
    """CONTRIBUTORS should include project lead and individual contributor sections."""
    (tmp_path / "CONTRIBUTORS.md").write_text(
        """
# Contributors

## Project Lead

* [Lead](https://github.com/lead)

## Individual Contributors

* [Contributor](https://github.com/contrib)
""".strip() + "\n",
        encoding="utf-8",
    )

    assert PM027.check(tmp_path) is True


def test_pm017_requires_python_bounds_in_pyproject(tmp_path):
    """Project metadata should require explicit lower and upper bounds for Python support."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nrequires-python = ">=3.10,<4"\n', encoding="utf-8")

    assert PM017.check(tmp_path) is True


def test_pm017_rejects_missing_upper_bound(tmp_path):
    """Lower-only Python support declarations should fail the metadata standard."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nrequires-python = ">=3.10"\n', encoding="utf-8")

    result = PM017.check(tmp_path)
    assert isinstance(result, str)
    assert "supported PyAnsys version range" in result


def test_quality_rules_are_grouped_package():
    """Quality rules should be exposed from a package with one module per check family."""
    assert hasattr(quality_rules, "PM001")
    assert hasattr(quality_rules, "PM016")
    assert hasattr(quality_rules, "PM017")
    assert hasattr(project_metadata, "PM001")
    assert callable(quality_rules.repo_review_checks)


def test_legacy_license_check_accepts_apache_default(tmp_path):
    """The legacy bootstrap should accept Apache content with the default Apache license."""
    license_path = tmp_path / "LICENSE"
    license_path.write_text(
        "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n",
        encoding="utf-8",
    )

    result = hook.check_file_content(
        license_path,
        "Apache License\nVersion 2.0\n",
        True,
        hook.DEFAULT_LICENSE,
    )

    assert result is True


def test_legacy_license_check_accepts_apache_alias(tmp_path):
    """The legacy bootstrap should accept '--license Apache' as Apache-2.0."""
    license_path = tmp_path / "LICENSE"
    license_path.write_text(
        "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n",
        encoding="utf-8",
    )

    result = hook.check_file_content(
        license_path,
        "MIT License\n",
        True,
        "Apache",
    )

    assert result is True


def test_main_accepts_common_apache_typo(tmp_path):
    """The CLI should normalize common Apache typos for legacy bootstrap usage."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
authors = [{name = "Synopsys, Inc. and ANSYS, Inc.", email = "pyansys-core@synopsys.com"}]
maintainers = [{name = "Synopsys, Inc. and ANSYS, Inc.", email = "pyansys-core@synopsys.com"}]
""".strip() + "\n",
        encoding="utf-8",
    )
    (repo_path / "LICENSE").write_text(
        "Apache License\nVersion 2.0, January 2004\n",
        encoding="utf-8",
    )

    exit_code = hook.main(["--repo-root", str(repo_path), "--fix-missing", "--license", "Apace"])
    assert exit_code in (0, 1)


def test_pyproject_license_must_match_selected_license(tmp_path):
    """Pyproject license metadata should match the selected --license value."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()
    (repo_path / "pyproject.toml").write_text(
        """
[project]
name = "ansys-demo-library"
version = "0.1.0"
license = "MIT"
authors = [{name = "Synopsys, Inc. and ANSYS, Inc.", email = "pyansys-core@synopsys.com"}]
maintainers = [{name = "Synopsys, Inc. and ANSYS, Inc.", email = "pyansys-core@synopsys.com"}]
""".strip() + "\n",
        encoding="utf-8",
    )

    is_ok, _ = hook.check_pyproject_toml(
        repo_path,
        hook.DEFAULT_AUTHOR_MAINT_NAME,
        hook.DEFAULT_AUTHOR_MAINT_EMAIL,
        True,
        "Apache",
    )

    assert is_ok is False


def test_main_rejects_mit_license_argument(tmp_path):
    """The CLI should reject MIT because Apache-2.0 is the only supported license."""
    repo_path = tmp_path / "quality-demo"
    repo_path.mkdir()

    with pytest.raises(SystemExit) as exc:
        hook.main(["--repo-root", str(repo_path), "--license", "MIT"])

    assert exc.value.code == 2


def test_pm028_fails_when_pyproject_license_mismatches_selected_license(tmp_path):
    """PM028 should fail when pyproject license does not match --license."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "ansys-demo-library"\nlicense = "MIT"\n',
        encoding="utf-8",
    )

    result = PM028.check(tmp_path, expected_license="Apache-2.0")
    assert isinstance(result, str)
    assert result.startswith("FAIL: ")
    assert "does not match --license=Apache-2.0" in result


def test_pm029_fails_when_license_file_mismatches_selected_license(tmp_path):
    """PM029 should fail when LICENSE content does not match --license."""
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    result = PM029.check(tmp_path, expected_license="Apache-2.0")
    assert result == 'FAIL: "The LICENSE file content is missing "Apache License 2.0"'


def test_normalize_check_result_standardizes_rule_status():
    """Rule evaluation results should normalize to the canonical pass/warn/fail/na model."""
    from ansys.pre_commit_hooks.quality_rules.common import normalize_check_result

    assert normalize_check_result(True) == ("pass", "")
    assert normalize_check_result(None) == ("na", "")
    assert normalize_check_result("WARN: check warning") == ("warn", "check warning")
    assert normalize_check_result(False) == ("fail", "")
