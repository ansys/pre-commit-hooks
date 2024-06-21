# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import os
import pathlib
import shutil
import sys

import git
import pytest

import ansys.pre_commit_hooks.tech_review as hook

git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = pathlib.Path(git_repo.git.rev_parse("--show-toplevel"))
TEMPLATE_PATH = REPO_PATH / "tests" / "test_tech_review_files"


def setup_repo(tmp_path):
    """Move to temporary directory, set up git repo, & create test file."""
    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    # repo = init_repo(tmp_path)
    git.Repo.init(tmp_path)
    repo = git.Repo(tmp_path)
    repo.index.commit("initialized git repo for tmp_path")

    # Make .github, src, tests, and doc directories
    dir_list = [".github", "src", "tests", "doc"]
    create_dirs(repo, tmp_path, dir_list)

    # Copy pyproject.toml and LICENSE files
    file_list = ["pyproject.toml", "LICENSE"]
    create_files(repo, tmp_path, file_list)

    return repo


def create_dirs(repo, tmp_path, dir_list):
    for directory in dir_list:
        tmp_dir = tmp_path / directory
        os.makedirs(tmp_dir)
        repo.index.add(tmp_dir)


def create_files(repo, tmp_path, file_list):
    for file in file_list:
        src_path = TEMPLATE_PATH / file
        dest_path = tmp_path / file
        shutil.copyfile(src_path, dest_path)
        repo.index.add(dest_path)


def run_main(custom_args):
    """Git add tmp_file, pass in sys.argv arguments, and run the hook."""
    # Pass in custom arguments
    sys.argv[1:] = custom_args

    return hook.main()


@pytest.mark.tech_review
def test_pyproject_data(tmp_path: pytest.TempPathFactory):
    # custom_args = ["--product=test"]
    author_maint_name = "ANSYS, Inc."
    author_maint_email = "pyansys.core@ansys.com"
    is_compliant = True
    non_compliant_name = False

    repo = setup_repo(tmp_path)
    print(os.listdir(tmp_path))
    is_compliant, project_name, config_file = hook.check_config_file(
        tmp_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )
    assert is_compliant == True

    os.chdir(REPO_PATH)


# Tests for
# name = "ansys-pre-commit-hooks"
# name2 = "ansys-precommit-hooks"
# name3 = "mechanical-precommit-hook"
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name)) # False
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name2)) # True
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name3)) # False
