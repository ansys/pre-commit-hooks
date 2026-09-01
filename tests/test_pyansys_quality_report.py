# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

from __future__ import annotations

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
