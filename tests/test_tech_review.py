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

import fileinput
import json
import os
import pathlib
import shutil
import sys

import git
import pytest

from ansys.pre_commit_hooks.add_license_headers import check_same_content
import ansys.pre_commit_hooks.tech_review as hook

git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = pathlib.Path(git_repo.git.rev_parse("--show-toplevel"))
TEST_TECH_REVIEW_FILES = REPO_PATH / "tests" / "test_tech_review_files"


def setup_repo(tmp_path):
    """Move to temporary directory, set up git repo, & create test file."""
    # Make "pytechreview" folder in tmp_path
    pathlib.Path.mkdir(tmp_path)
    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_repo(tmp_path)

    # Make .github, src, tests, and doc directories
    dir_list = [".github", "src", "tests", "doc"]
    create_dirs(repo, tmp_path, dir_list)

    # Copy pyproject.toml and LICENSE files
    file_list = ["pyproject.toml", "LICENSE"]
    create_files(repo, tmp_path, file_list)

    return repo


def init_repo(tmp_path):
    """Initialize the repository in the tmp_path."""
    git.Repo.init(tmp_path)
    repo = git.Repo(tmp_path)
    repo.index.commit("initialized git repo for tmp_path")

    return repo


def create_dirs(repo, tmp_path, dir_list):
    """Create directories in the repository and git add them."""
    for directory in dir_list:
        tmp_dir = tmp_path / directory
        os.makedirs(tmp_dir)
        repo.index.add(tmp_dir)


def create_files(repo, tmp_path, file_list):
    """Create files in the repository and git add them."""
    for file in file_list:
        src_path = TEST_TECH_REVIEW_FILES / file
        dest_path = tmp_path / file
        shutil.copyfile(src_path, dest_path)
        repo.index.add(dest_path)


def run_main(custom_args):
    """Git pass in sys.argv arguments and run the hook."""
    # Pass in custom arguments
    sys.argv[1:] = custom_args

    return hook.main()


@pytest.mark.tech_review
def test_pyproject_toml(tmp_path: pytest.TempPathFactory):
    """Test pyproject.toml retrieves all information."""
    author_maint_name = "ANSYS, Inc."
    author_maint_email = "pyansys.core@ansys.com"
    is_compliant = True
    non_compliant_name = False

    tmp_path = tmp_path / "pytechreview"

    setup_repo(tmp_path)
    is_compliant, project_name, config_file = hook.check_config_file(
        tmp_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )
    assert is_compliant

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_setup_py(tmp_path: pytest.TempPathFactory):
    """Test setup.py file is not implemented and some files are generated."""
    custom_args = ["--product=techreview"]
    tmp_path = tmp_path / "pytechreview"

    pathlib.Path.mkdir(tmp_path)
    os.chdir(tmp_path)

    # Initialize repository
    repo = init_repo(tmp_path)

    # Create setup.py file with no configurations
    setup_py_file = tmp_path / "setup.py"
    with open(setup_py_file, "w") as setup_file:
        setup_file.write("# Empty file")

    assert run_main(custom_args) == 1

    # Check the dependabot.yml file was generated for setup.py
    file_list = ["dependabot.yml"]
    check_generated_files(tmp_path, file_list, "setuptools")

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_setup_py_and_pyproject(tmp_path: pytest.TempPathFactory):
    """Test setup.py file is not implemented and some files are generated."""
    custom_args = ["--product=techreview"]
    tmp_path = tmp_path / "pytechreview"

    pathlib.Path.mkdir(tmp_path)
    os.chdir(tmp_path)

    # Initialize repository
    repo = init_repo(tmp_path)

    # Create setup.py file with no configurations
    config_files = ["setup.py", "pyproject.toml"]
    for file in config_files:
        config_file = tmp_path / file
        with open(config_file, "w") as setup_file:
            setup_file.write("# Empty file")

    assert run_main(custom_args) == 1

    # Check the dependabot.yml file was generated for setup.py
    file_list = ["dependabot.yml"]
    check_generated_files(tmp_path, file_list, "setuptools")

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_no_config_files(tmp_path: pytest.TempPathFactory, capsys):
    """Test output message and files that are generated when no configuration files exist."""
    tmp_path = tmp_path / "pytechreview"
    pathlib.Path.mkdir(tmp_path)
    os.chdir(tmp_path)

    # Initialize repository
    init_repo(tmp_path)

    # Ensure hook fails
    hook.main() == 1

    output = capsys.readouterr()
    assert "The pyproject.toml and setup.py files do not exist" in output.out

    # Check files and directories exist
    exists_list = [
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "LICENSE",
        ".github",
        "doc",
        "src",
        "tests",
    ]
    for item in exists_list:
        assert pathlib.Path.exists(tmp_path / item)

    # Check files do not exist due to missing configuration file
    dependabot_file = os.path.join(".github", "dependabot.yml")
    dne_file_list = ["AUTHORS", "README.rst", dependabot_file]
    for item in dne_file_list:
        assert not pathlib.Path.exists(tmp_path / item)

    os.chdir(REPO_PATH)


def replace_line(tmp_path, file, search, replace):
    """Replace line in file."""
    with fileinput.FileInput(tmp_path / file, inplace=True) as pyproj:
        for line in pyproj:
            # Find existing line in file and replace it
            if search in line:
                print(replace, end="\n")
            else:
                print(line, end="")


@pytest.mark.tech_review
def test_non_compliant_name(tmp_path: pytest.TempPathFactory, capsys):
    """Test the error message appears when the project name is non compliant."""
    tmp_path = tmp_path / "pytechreview"
    setup_repo(tmp_path)

    # Replace the name in the pyproject.toml file to be invalid
    search = 'name = "ansys-tech-review"'
    replace = 'name = "ansys-pre-commit-hooks"'
    replace_line(tmp_path, "pyproject.toml", search, replace)

    assert hook.main() == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "Project name does not follow naming conventions" in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_bad_version(tmp_path: pytest.TempPathFactory, capsys):
    """Test the error message appears when the project does not use semantic versioning."""
    tmp_path = tmp_path / "pytechreview"
    setup_repo(tmp_path)

    # Replace the version in the pyproject.toml file to be invalid
    search = 'version = "0.1.0"'
    replace = 'version = "0.1.2.3"'
    replace_line(tmp_path, "pyproject.toml", search, replace)

    assert hook.main() == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "Project version does not follow semantic versioning" in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_dev_version(tmp_path: pytest.TempPathFactory, capsys):
    """Test the error message appears when the project does not use semantic versioning."""
    tmp_path = tmp_path / "pytechreview"
    setup_repo(tmp_path)

    # Replace the version in the pyproject.toml file to be invalid
    search = 'version = "0.1.0"'
    replace = 'version = "11.1.dev1"'
    replace_line(tmp_path, "pyproject.toml", search, replace)

    assert hook.main() == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "Project version does not follow semantic versioning" not in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_bad_author_maint_name_email(tmp_path: pytest.TempPathFactory, capsys):
    """Test the error message appears when author and maintainers name and emails do not exist."""
    tmp_path = tmp_path / "pytechreview"
    setup_repo(tmp_path)

    # Remove name and email from author and maintainer in pyproject.toml
    search = '{name = "ANSYS, Inc.", email = "pyansys.core@ansys.com"},'
    replace = "{},"
    replace_line(tmp_path, "pyproject.toml", search, replace)

    assert hook.main() == 1

    # Check error messages are printed
    output = capsys.readouterr()
    assert "Project authors name does not exist in the pyproject.toml file" in output.out
    assert "Project maintainers name does not exist in the pyproject.toml file" in output.out
    assert "Project authors email does not exist in the pyproject.toml file" in output.out
    assert "Project maintainers email does not exist in the pyproject.toml file" in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_mismatch_author_arg(tmp_path: pytest.TempPathFactory, capsys):
    """Test the error message appears when the author name is different from the pyproject.toml."""
    tmp_path = tmp_path / "pytechreview"
    setup_repo(tmp_path)

    custom_args = ["--author_maint_name=NOTANSYS, Inc."]

    assert run_main(custom_args) == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "Project authors name is not NOTANSYS, Inc." in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_readme_md(tmp_path: pytest.TempPathFactory):
    """Test README.md file exists in repository."""
    tmp_path = tmp_path / "pytechreview"
    repo = setup_repo(tmp_path)
    create_files(repo, tmp_path, ["README.md"])

    custom_args = []
    assert run_main(custom_args) == 1

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_no_readme_n_product(tmp_path: pytest.TempPathFactory, capsys):
    """Test the product argument is not given so the README cannot be generated."""
    tmp_path = tmp_path / "pytechreview"
    repo = setup_repo(tmp_path)

    custom_args = []
    assert run_main(custom_args) == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "The --product argument is required to generate the README file." in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_update_contributors(tmp_path: pytest.TempPathFactory, capsys):
    """Test the CONTRIBUTORS.md file has not changed after it was generated."""
    tmp_path = tmp_path / "pytechreview"
    repo = setup_repo(tmp_path)

    # Generate the missing files
    custom_args = []
    assert run_main(custom_args) == 1

    # Run main again without updating CONTRIBUTORS.md
    assert run_main(custom_args) == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert "Please update your CONTRIBUTORS.md file" in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_bad_license_file(tmp_path: pytest.TempPathFactory, capsys):
    """Test LICENSE file does not contain the correct name."""
    tmp_path = tmp_path / "pytechreview"
    repo = setup_repo(tmp_path)

    # Generate missing files
    custom_args = []
    assert run_main(custom_args) == 1

    # Remove the MIT License line from LICENSE
    search = "MIT License"
    replace = ""
    replace_line(tmp_path, "LICENSE", search, replace)

    assert run_main(custom_args) == 1

    # Check error message is printed
    output = capsys.readouterr()
    assert 'The LICENSE file content is missing "MIT License"' in output.out

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_templates(tmp_path: pytest.TempPathFactory):
    """Test templates are generated correctly when provided with the product argument."""
    custom_args = ["--product=techreview"]
    tmp_path = tmp_path / "pytechreview"

    # Generate missing files
    setup_repo(tmp_path)
    assert run_main(custom_args) == 1

    # Check each of the file's content generated correctly from templates
    file_list = [file.value for file in hook.Filenames]
    file_list.remove("CONTRIBUTORS.md")
    check_generated_files(tmp_path, file_list, "pyproject")

    os.chdir(REPO_PATH)


def check_generated_files(tmp_path, file_list, config_file):
    "Check each of the file's content generated correctly from templates"
    for file in file_list:
        # Get files with correct information already filled out
        correct_file = TEST_TECH_REVIEW_FILES / file
        if "dependabot" in file:
            correct_file = TEST_TECH_REVIEW_FILES / f"{file}".replace(
                file, f"dependabot_{config_file}.yml"
            )
            created_file = tmp_path / ".github" / file
        else:
            if "README" in file:
                if pathlib.Path.exists(tmp_path / f"{file}.md"):
                    file = f"{file}.md"
                else:
                    file = f"{file}.rst"

                correct_file = TEST_TECH_REVIEW_FILES / file

            created_file = tmp_path / file
        # Check the file with correct content is the same as the generated file
        assert check_same_content(correct_file, created_file) == True


@pytest.mark.tech_review
def test_json_download_n_update(tmp_path: pytest.TempPathFactory):
    """Test the licenses.json file is downloaded and updated."""
    url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
    tmp_path = tmp_path / "pytechreview"
    license_json = tmp_path / "license.json"

    # Make pytechreview folder in tmp_path
    pathlib.Path.mkdir(tmp_path)
    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Initialize repository
    repo = init_repo(tmp_path)

    # Assert the license.json file is downloaded and updated
    assert hook.download_license_json(url, license_json) == True

    # Check license.json's key/value is correct for MIT
    with open(license_json, "r") as license:
        existing_json = json.load(license)
        assert existing_json["MIT"] == "MIT License"

    os.chdir(REPO_PATH)


@pytest.mark.tech_review
def test_main():
    """Test main for the ansys/pre-commit-hooks repository."""
    # Set custom arguments for ansys/pre-commit-hooks repository
    custom_args = ["--product=pre-commit-hooks", "--non_compliant_name"]

    assert run_main(custom_args) == 0

    os.chdir(REPO_PATH)
