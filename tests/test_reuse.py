import argparse
import os
import shutil
import sys
from tempfile import NamedTemporaryFile

import git
import pytest

import ansys.pre_commit_hooks.add_license_headers as hook

git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = git_repo.git.rev_parse("--show-toplevel")


def set_up_repo(tmp_path, template_path, template_name, license_path, license_name):
    """Move to temporary directory, set up git repo, & create test file."""
    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name, license_path, license_name)

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)

    return repo, tmp_file


def init_git_repo(tmp_path, template_path, template_name, license_path, license_name):
    """Initialize git repository and add the .reuse directory & template."""
    reuse_dir = os.path.join(tmp_path, ".reuse", "templates")
    license_dir = os.path.join(tmp_path, "LICENSES")

    # Create .reuse directory and copy template file to it
    os.makedirs(reuse_dir)
    shutil.copyfile(template_path, f"{reuse_dir}/{template_name}")

    os.makedirs(license_dir)
    shutil.copyfile(license_path, f"{license_dir}/{license_name}")

    # Initialize tmp_path as a git repository
    git.Repo.init(tmp_path)
    repo = git.Repo(tmp_path)
    repo.index.commit("initialized git repo for tmp_path")

    return repo


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
    file = open(file_name, "r")
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


def test_custom_args(tmp_path: pytest.TempPathFactory):
    """Test custom arguments for loc, copyright, template, and license."""
    # Set template and license names
    template_name = "test_template.jinja2"
    license_name = "ECL-1.0.txt"
    template_path = os.path.join(REPO_PATH, "tests", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "tests", "LICENSES", license_name)

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


def test_multiple_files(tmp_path: pytest.TempPathFactory, capfd):
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
    file_names = []
    for i in range(0, 2):
        # Create temporary python file
        tmp_file = create_test_file(tmp_path)
        # Save temporary python file name
        file_names.append(tmp_file)
        # Git add new file
        repo.index.add(tmp_file)
        # Append file to new_files list
        new_files.append(tmp_file)

    assert add_argv_run(repo, new_files, new_files) == 1

    for file in new_files:
        check_ansys_header(file)

    os.chdir(REPO_PATH)


def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    # Set template and license names
    template_name = "ansys.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)
    license_path = os.path.join(REPO_PATH, "LICENSES", license_name)

    # Set up git repository in tmp_path with temporary file
    repo, tmp_file = set_up_repo(tmp_path, template_path, template_name, license_path, license_name)

    assert add_argv_run(repo, tmp_file, [tmp_file]) == 1

    check_ansys_header(tmp_file)

    os.chdir(REPO_PATH)


def test_main_passes():
    """Test all files are compliant."""
    sys.argv[1:] = []

    # Assert main runs successfully
    assert hook.main() == 0

    os.chdir(REPO_PATH)


def test_license_check():
    """Test license is checked in the header."""
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == False


def test_no_license_check(tmp_path: pytest.TempPathFactory):
    """Test license check is ignored."""
    # Set template and license names
    template_name = "copyright_only.jinja2"
    license_name = "MIT.txt"
    template_path = os.path.join(REPO_PATH, "tests", "templates", template_name)
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


def test_update_no_change_header(tmp_path: pytest.TempPathFactory):
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


def test_update_changed_header(tmp_path: pytest.TempPathFactory):
    """Test that header is updated when the jinja file changes."""
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

    add_argv_run(repo, new_files, new_files)

    # Change jinja file
    orig_jinja = os.path.join(tmp_path, ".reuse", "templates", template_name)
    tmp_jinja = open("tmp_jinja", "w")

    with open(orig_jinja, "r+") as f:
        for line in f:
            if line.startswith("Permission"):
                line = line.replace("Permission", "New Permission")
            tmp_jinja.write(line)
        tmp_jinja.close()
        f.close()

    shutil.copyfile("tmp_jinja", orig_jinja)
    os.remove("tmp_jinja")

    # Add jinja file to list of files that have been changed
    new_files.append(orig_jinja)

    add_argv_run(repo, new_files, new_files)

    # Check that "New Permission" is in the tmp file header
    file = open(tmp_file, "r")
    for line in file:
        if "Permission" in line:
            assert "New Permission" in line

    os.chdir(REPO_PATH)


def test_missing_licenses(tmp_path: pytest.TempPathFactory):
    """Test that LICENSES folder is required."""
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

    # Remove LICENSES folder from tmp_path
    shutil.rmtree(os.path.join(tmp_path, "LICENSES"))

    # Add header to tmp_file
    add_argv_run(repo, new_files, new_files)

    # If LICENSES folder is missing, then it will fail and
    # add another SPDX line. This shows you need LICENSES folder
    # or else it will not work correctly.
    assert add_argv_run(repo, new_files, new_files) == 1

    os.chdir(REPO_PATH)
