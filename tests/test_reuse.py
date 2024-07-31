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

import argparse
from datetime import date as dt
import os
import shutil
import sys
from tempfile import NamedTemporaryFile

import git
import pytest

import ansys.pre_commit_hooks.add_license_headers as hook

git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = git_repo.git.rev_parse("--show-toplevel")
START_YEAR = "2023"


def set_up_repo(tmp_path, template_path, template_name, license_path, license_name):
    """Move to temporary directory, set up git repo, & create test file."""
    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_repo(tmp_path)

    # Make asset directories if using a custom license or template
    # Asset directories are .reuse and LICENSES
    make_asset_dirs(tmp_path, template_path, template_name, license_path, license_name)

    # Copy the LICENSE file to the tmp_path repo
    cp_LICENSE_file(tmp_path)

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)

    return repo, tmp_file


def init_repo(tmp_path):
    # Set up git repository in tmp_path
    git.Repo.init(tmp_path)
    repo = git.Repo(tmp_path)
    repo.index.commit("initialized git repo for tmp_path")

    return repo


def make_asset_dirs(tmp_path, template_path, template_name, license_path, license_name):
    """Make asset directories if using a custom license or template."""
    if template_name != "ansys.jinja2":
        reuse_dir = os.path.join(tmp_path, ".reuse", "templates")
        os.makedirs(reuse_dir)
        shutil.copyfile(template_path, f"{reuse_dir}/{template_name}")

    if license_name != "MIT.txt":
        license_dir = os.path.join(tmp_path, "LICENSES")
        os.makedirs(license_dir)
        shutil.copyfile(license_path, f"{license_dir}/{license_name}")


def cp_LICENSE_file(tmp_path):
    # Create LICENSE file in tmp_path repo
    license = "LICENSE"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "LICENSES", license)
    tmp_license = os.path.join(tmp_path, license)

    os.chdir(tmp_path)

    # Copy the LICENSE file to the tmp_path
    shutil.copyfile(template_path, tmp_license)


def create_test_file(tmp_path):
    """Create temporary file for reuse testing."""
    with NamedTemporaryFile(mode="w", delete=False, dir=tmp_path) as tmp:
        tmp.write("# test message")
        tmp.close()
        filename = tmp.name

    # Rename temporary file as a python file
    py_filename = f"{filename}.py"
    os.rename(filename, py_filename)

    return py_filename


def add_argv_run(repo, tmp_file, custom_args):
    """Git add tmp_file, pass in sys.argv arguments, and run the hook."""
    # Stage temporary python file (git add)
    repo.index.add(tmp_file)

    # Pass in custom arguments
    sys.argv[1:] = custom_args

    return hook.main()


def check_ansys_header(file_name):
    """Check file contains all copyright and license header components."""
    file = open(file_name, "r", encoding="utf8")
    count = 0
    for line in file:
        count += 1
        if count == 1:
            assert "ANSYS, Inc. and/or its affiliates" in line
        if count == 2:
            assert "MIT" in line
        if count == 5:
            assert "Permission is hereby granted" in line
        if count > 5:
            break
    file.close()


@pytest.mark.license_headers
def test_custom_start_year(tmp_path: pytest.TempPathFactory):
    """Test custom start year is in copyright line."""
    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    custom_args = [tmp_file, f"--start_year={START_YEAR}"]

    # Assert the hook fails because it added the header
    assert add_argv_run(repo, tmp_file, custom_args) == 1

    file = open(tmp_file, "r")
    count = 0
    for line in file:
        count += 1
        # Assert the copyright line's time range is
        # from 2023 to the current year
        if count == 1:
            assert f"{START_YEAR} - {dt.today().year}" in line
        if count > 1:
            break
    file.close()

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_start_year_same_as_current(tmp_path: pytest.TempPathFactory):
    """Test custom start year is in copyright line."""
    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)

    # Assert the hook fails because it added the header
    assert add_argv_run(repo, tmp_file, [tmp_file]) == 1

    file = open(tmp_file, "r")
    count = 0
    for line in file:
        count += 1
        # Assert the copyright line's time range is from 2023 to the current year
        if count == 1:
            assert f"Copyright (C) {dt.today().year} ANSYS, Inc." in line
        if count > 1:
            break
    file.close()

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_custom_args(tmp_path: pytest.TempPathFactory):
    """Test custom arguments for loc, copyright, template, and license."""
    # Set template and license names
    template_name = "test_template.jinja2"
    license_name = "ECL-1.0.txt"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)

    # Add custom arguments for sys.argv[1:]
    custom_args = [
        tmp_file,
        '--custom_copyright="Super cool copyright"',
        "--custom_template=test_template",
        "--custom_license=ECL-1.0",
    ]

    # Git add tmp_file and run hook with custom arguments
    add_argv_run(repo, tmp_file, custom_args)

    # Check that custom copyright, template, and license are in the tmp_file header
    file = open(tmp_file, "r")
    count = 0
    for line in file:
        count += 1
        if count == 1:
            assert "The Educational Community License" in line
        if count == 5:
            assert "Super cool copyright" in line
        if count == 6:
            assert "ECL-1.0" in line
        if count > 6:
            break
    file.close()

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_multiple_files(tmp_path: pytest.TempPathFactory):
    """Test reuse is run on files without headers, when one file already has header."""
    # List of files to be git added
    new_files = []

    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    new_files.append(tmp_file)

    # Git add tmp_file and run hook with custom arguments
    add_argv_run(repo, new_files, new_files)

    repo.index.add([tmp_file])

    # Create two new files to run REUSE
    for i in range(0, 2):
        # Create temporary python file
        tmp_file = create_test_file(tmp_path)
        # Git add new file
        repo.index.add(tmp_file)
        # Append file to new_files list
        new_files.append(tmp_file)

    assert add_argv_run(repo, new_files, new_files) == 1

    for file in new_files:
        check_ansys_header(file)

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    custom_args = [tmp_file, f"--start_year={START_YEAR}"]

    assert add_argv_run(repo, tmp_file, custom_args) == 1

    check_ansys_header(tmp_file)

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_main_passes():
    """Test all files are compliant."""
    sys.argv[1:] = [f"--start_year={START_YEAR}"]

    # Assert main runs successfully
    assert hook.main() == 0

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_license_check():
    """Test license is checked in the header."""
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == False


@pytest.mark.license_headers
def test_no_license_check(tmp_path: pytest.TempPathFactory):
    """Test license check is ignored."""
    # Set template and license names
    template_name = "copyright_only.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    custom_args = [tmp_file, "--ignore_license_check", "--custom_template=copyright_only"]

    assert add_argv_run(repo, tmp_file, custom_args) == 1

    file = open(tmp_file, "r")
    count = 0
    for line in file:
        count += 1
        # Assert that only the copyright line is in the file
        if count == 1:
            assert "ANSYS, Inc. and/or its affiliates" in line
        if count == 2:
            assert "MIT" not in line
        if count == 5:
            assert "Permission is hereby granted" not in line
        if count > 5:
            break
    file.close()

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_header_doesnt_change(tmp_path: pytest.TempPathFactory):
    """Test update header."""
    # List of files to be git added
    new_files = []

    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    new_files.append(tmp_file)

    # Add header to tmp_file
    add_argv_run(repo, new_files, new_files)

    # Update header file that has no changes
    assert add_argv_run(repo, new_files, new_files) == 0

    file = open(tmp_file, "r")
    count = 0
    for line in file:
        count += 1
        if count == 2:
            assert "MIT" in line
        # Ensure header was updated correctly and didn't add
        # an extra SPDX-Identifier line
        if count == 3:
            assert "MIT" not in line
        if count > 3:
            break
    file.close()

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_update_changed_header(tmp_path: pytest.TempPathFactory):
    """Test that header is updated when the jinja file changes."""
    # List of files to be git added
    new_files = []

    # Set template and license names
    template_name = "test_template.jinja2"
    license_name = "ECL-1.0.txt"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    new_files.append(tmp_file)

    # Set custom args with all files, test_template, and license
    custom_args = []

    for file in new_files:
        custom_args.append(file)

    custom_args.append("--custom_template=test_template")
    custom_args.append("--custom_license=ECL-1.0")

    add_argv_run(repo, new_files, custom_args)

    # Change jinja file
    orig_jinja = os.path.join(tmp_path, ".reuse", "templates", template_name)
    tmp_jinja = open("tmp_jinja", "w")

    with open(orig_jinja, "r+") as f:
        for line in f:
            if line.startswith("The Educational Community"):
                line = line.replace("The Educational Community", "The PyAnsys Community")
            tmp_jinja.write(line)
        tmp_jinja.close()
        f.close()

    shutil.copyfile("tmp_jinja", orig_jinja)
    os.remove("tmp_jinja")

    # Add jinja file to list of files that have been changed
    new_files.append(orig_jinja)

    # Set custom args with all files, test_template, and license
    custom_args = []

    for file in new_files:
        custom_args.append(file)

    custom_args.append("--custom_template=test_template")
    custom_args.append("--custom_license=ECL-1.0")

    add_argv_run(repo, new_files, custom_args)

    # Check that "New Permission" is in the tmp file header
    file = open(tmp_file, "r")
    for line in file:
        if "The PyAnsys Community" in line:
            assert "The PyAnsys Community" in line

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_copy_assets(tmp_path: pytest.TempPathFactory):
    """Test .reuse and LICENSES folders are copied."""
    # List of files to be git added
    new_files = []

    # Set up git repository in tmp_path with temporary file
    os.chdir(tmp_path)

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)

    # Initialize tmp_path as a git repository
    repo = init_repo(tmp_path)

    # Copy LICENSE file to tmp_path repo
    cp_LICENSE_file(tmp_path)

    new_files.append(tmp_file)

    # Add header to tmp_file
    assert add_argv_run(repo, new_files, new_files) == 1

    check_ansys_header(tmp_file)


@pytest.mark.license_headers
def test_bad_chars(tmp_path: pytest.TempPathFactory):
    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    bad_chars_name = "bad_chars.py"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Make asset directories if using a custom license or template
    # Asset directories are .reuse and LICENSES
    make_asset_dirs(tmp_path, template_path, template_name, license_path, license_name)

    # Set up git repository in tmp_path
    repo = init_repo(tmp_path)

    # Copy LICENSE file to tmp_path repo
    cp_LICENSE_file(tmp_path)

    # Copy file with bad characters to git repository
    shutil.copyfile(
        os.path.join(REPO_PATH, "tests", "test_reuse_files", bad_chars_name), bad_chars_name
    )

    # Assert the hook failed
    assert add_argv_run(repo, bad_chars_name, [bad_chars_name]) == 1

    # Assert the hook added the license header correctly
    check_ansys_header(bad_chars_name)

    os.chdir(REPO_PATH)


@pytest.mark.license_headers
def test_index_exception(tmp_path: pytest.TempPathFactory):
    # Set template and license names
    template_name = "copyright_only.jinja2"
    license_name = "MIT.txt"
    test_filename = "index_error.scss"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Make asset directories if using a custom license or template
    # Asset directories are .reuse and LICENSES
    make_asset_dirs(tmp_path, template_path, template_name, license_path, license_name)

    # Set up git repository in tmp_path
    repo = init_repo(tmp_path)

    # Copy LICENSE file to tmp_path repo
    cp_LICENSE_file(tmp_path)

    # Copy file that will cause an IndexError to git repository
    shutil.copyfile(
        os.path.join(REPO_PATH, "tests", "test_reuse_files", test_filename), test_filename
    )

    custom_args = [
        test_filename,
        "--custom_template=copyright_only",
        "--custom_copyright=ANSYS, Inc. Unauthorized use, distribution, \
            or duplication is prohibited.",
        "--ignore_license_check",
        f"--start_year={START_YEAR}",
    ]

    # Assert the hook failed
    assert add_argv_run(repo, test_filename, custom_args) == 1

    # Assert the single line comment changed to
    # a multiline comment. This causes an IndexError in the hook
    file = open(test_filename, "r")
    count = 0
    for line in file:
        count += 1
        if count == 1:
            assert "/*" in line
        # Ensure header was updated correctly and didn't add
        # an extra SPDX-Identifier line
        if count == 2:
            assert f" * Copyright (C) 2023 - {dt.today().year} ANSYS, Inc. Unauthorized use" in line
        if count == 3:
            assert "*/" in line
        if count > 4:
            break
    file.close()

    os.chdir(REPO_PATH)


def check_license_year(license_file, copyright, start_year, current_year):
    f = open(license_file, "r")

    for line in f:
        if copyright in line:
            if start_year != current_year:
                assert f"{start_year} - {current_year}" in line
            else:
                assert current_year in line
        return


@pytest.mark.license_headers
def test_license_year_update(tmp_path: pytest.TempPathFactory):
    """Tests if the year in the license header is updated."""
    # license_path = os.path.join(REPO_PATH, "LICENSES", license_name)
    license = "LICENSE"
    template_path = os.path.join(REPO_PATH, "tests", "test_reuse_files", "LICENSES", license)
    tmp_license = os.path.join(tmp_path, license)
    custom_args = []

    os.chdir(tmp_path)

    # Copy the LICENSE file to the tmp_path
    shutil.copyfile(template_path, tmp_license)

    # Set up git repository in tmp_path
    repo = init_repo(tmp_path)

    # Add custom args & tmp_file
    add_argv_run(repo, tmp_license, custom_args)

    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    values = {
        "copyright": args.custom_copyright,
        "license": args.custom_license,
        "start_year": START_YEAR,
        "current_year": dt.today().year,
        "git_repo": git_repo,
    }

    # Years to update the LICENSE file
    years = ["2022", dt.today().year, values["start_year"]]

    # Check the copyright line has "2022 - {current_year}", "{current_year}"
    # and "2023 - {current_year}"
    for year in years:
        values["start_year"] = year
        hook.update_license_file(values)
        check_license_year(
            tmp_license, values["copyright"], values["start_year"], values["current_year"]
        )

    os.chdir(REPO_PATH)


def test_no_recursion(tmp_path: pytest.TempPathFactory):
    """Test license headers with function that does not use recursion."""
    # Set template and license names
    # List of files to be git added
    new_files = []
    custom_args = []

    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)
    new_files.append(tmp_file)
    custom_args = [tmp_file, f"--start_year={START_YEAR}"]

    # Git add tmp_file and run hook with custom arguments
    assert add_argv_run(repo, tmp_file, custom_args) == 1

    # Add file with updated header
    repo.index.add([tmp_file])

    for file in range(0, sys.getrecursionlimit() + 1):
        # Create temporary python file
        new_file = create_test_file(tmp_path)
        # Git add new file
        repo.index.add(new_file)
        # Append file to new_files list
        new_files.append(new_file)
        # Add new file without header to custom_args
        custom_args.insert(0, new_file)

    assert add_argv_run(repo, new_files, custom_args) == 1

    # Check headers are correct in all tmp_files
    for file in new_files:
        check_ansys_header(file)

    os.chdir(REPO_PATH)
