# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import ast
import os
from pathlib import Path

import git

import ansys.pre_commit_hooks.pyansys_quality_report as hook


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
    """The standalone hook must include the full repo-review rule set."""

    repo_root = Path(__file__).resolve().parents[3]
    checks_dir = repo_root / "src" / "pyansys_review" / "checks"

    def class_names(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        return {node.name for node in tree.body if isinstance(node, ast.ClassDef)}

    expected = set()
    for path in checks_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        expected |= class_names(path)

    actual = class_names(Path(hook.__file__))
    assert expected == actual - {"MemoryTraversable"}
