import argparse
import os
import shutil
import sys

import git
import pytest

import ansys.pre_commit_hooks.add_license_headers as hook


def create_test_file(tmp_path, file_name):
    """Create temporary file for reuse testing."""
    test_file = os.path.join(tmp_path, file_name)

    # Create test file with a random message
    with open(test_file, "w") as f:
        f.write("# test message")
    f.close()

    return test_file


def init_git_repo(tmp_path, template_path, template_name):
    """Initialize git repository and add the .reuse directory & template."""
    reuse_dir = os.path.join(tmp_path, ".reuse", "templates")

    # Create .reuse directory and copy template file to it
    os.makedirs(reuse_dir)
    shutil.copyfile(f"{template_path}", f"{reuse_dir}/{template_name}")

    # Initialize tmp_path as a git repository
    git.Repo.init(tmp_path)
    repo = git.Repo(tmp_path)
    repo.index.commit("initialized git repo for tmp_path")

    return repo


def test_custom_args(tmp_path: pytest.TempPathFactory):
    """Test custom arguments for loc, copyright, template, and license."""
    # Save current working directory
    current_work_dir = os.getcwd()

    template_name = "test_template.jinja2"
    template_path = os.path.join(os.getcwd(), "tests", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    # Create a test file in tmp_path
    create_test_file(tmp_path, "test.py")

    # Stage test.py file
    repo.index.add(os.path.join(tmp_path, "test.py"))

    # Pass in custom arguments
    sys.argv[1:] = [
        "test.py",
        '--custom_copyright="Super cool copyright"',
        "--custom_template=test_template",
        "--custom_license=ECL-1.0",
    ]
    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(current_work_dir)


def test_multiple_files(tmp_path: pytest.TempPathFactory):
    """Test reuse is run on files without headers, when one file already has header."""
    # Save current working directory
    current_work_dir = os.getcwd()

    template_name = "ansys.jinja2"
    template_path = os.path.join(current_work_dir, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    # Create a test file in tmp_path
    create_test_file(tmp_path, "test.py")

    # Stage test.py file
    repo.index.add(os.path.join(tmp_path, "test.py"))

    # Pass in file arguments
    sys.argv[1:] = ["test.py"]

    hook.main()

    # Add test.py with license header
    repo.index.add(os.path.join(tmp_path, "test.py"))

    # Create two new files to run REUSE on
    new_files = ["test2.py", "test3.py"]
    for file in new_files:
        create_test_file(tmp_path, file)
        repo.index.add(os.path.join(tmp_path, file))

    # Pass in the file arguments
    sys.argv[1:] = ["test.py", "test2.py", "test3.py"]

    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(current_work_dir)


def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    # Save current working directory
    current_work_dir = os.getcwd()

    template_name = "ansys.jinja2"
    template_path = os.path.join(current_work_dir, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    # Create a test file in tmp_path
    create_test_file(tmp_path, "test.py")

    # Stage test.py file
    repo.index.add(os.path.join(tmp_path, "test.py"))

    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(current_work_dir)


def test_main_passes():
    """Test all files are compliant."""
    res = hook.main()

    # Assert main runs successfully
    assert res == 0


def test_license_check():
    """Test license is checked in the header."""
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == False


def test_no_license_check():
    """Test license check is ignored."""
    sys.argv[1:] = ["--ignore_license_check"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == True
