import argparse
import os
import shutil
import sys

import git
import pytest
from reuse import project

import ansys.pre_commit_hooks.add_license_headers as hook

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_argparse_passes():
    """Test argparse passes given loc."""
    sys.argv[1:] = [f"--loc=./"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    # Assert loc argument is same as set above
    assert args.loc == "./"


def test_argparse_default():
    """Test argparse returns default if loc argument is not provided."""
    sys.argv[1:] = []
    parser = argparse.ArgumentParser()

    args = hook.set_lint_args(parser)

    # Assert error is thrown for empty loc argument
    assert args.loc == "src"


def test_all_files_compliant(tmp_path: pytest.TempPathFactory):
    """Test no noncompliant files are found."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)
    proj = project.Project(rf"{args.loc}")

    missing_headers = hook.list_noncompliant_files(args, proj)

    # Assert all files are compliant
    assert len(missing_headers) == 0


def create_test_file(tmp_path):
    """Create temporary file for reuse testing."""
    test_file = os.path.join(tmp_path, "test.py")

    # Create test file with a random message
    with open(test_file, "w") as f:
        f.write("# test message")
    f.close()

    return test_file


def test_noncompliant_files_found(tmp_path: pytest.TempPathFactory):
    """Test noncompliant file is found."""
    test_file = create_test_file(tmp_path)
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)
    proj = project.Project(rf"{args.loc}")

    missing_headers = hook.list_noncompliant_files(args, proj)

    # Assert noncompliant file is found
    assert missing_headers != []

    # Remove test file from git repo
    os.remove(test_file)


def test_find_files_missing_header_passes(tmp_path: pytest.TempPathFactory):
    """Test no noncompliant files are found."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    result = hook.find_files_missing_header()

    # Assert all files are compliant
    assert result == 0


def test_find_files_missing_header_fails(tmp_path: pytest.TempPathFactory):
    """Test noncompliant file is found."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    # Create noncompliant file in tmp_path
    test_file = create_test_file(tmp_path)
    result = hook.find_files_missing_header()

    # Assert noncompliant file is found
    assert result == 1

    # Remove test file from git repo
    os.remove(test_file)


def test_reuse_dir_dne(tmp_path: pytest.TempPathFactory):
    """Test reuse directory does not exist."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    # Create noncompliant file in tmp_path
    test_file = create_test_file(tmp_path)

    # Rename .reuse to invalid name
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    os.rename(os.path.join(git_root, ".reuse"), os.path.join(git_root, "invalid_reuse"))

    store_err = None
    try:
        result = hook.find_files_missing_header()

        # Assert .reuse directory does not exist
        assert result == 2

    except Exception as err:
        store_err = err
        pass

    # Restore original environment
    os.rename(os.path.join(git_root, "invalid_reuse"), os.path.join(git_root, ".reuse"))
    os.remove(test_file)

    if store_err:
        raise store_err


def test_default_dir_dne(tmp_path: pytest.TempPathFactory):
    """Test default directory does not exist."""
    test_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Initialize tmp_path as a git repository
        git.Repo.init(tmp_path)

        # Create ".reuse" directory
        os.mkdir(os.path.join(tmp_path, ".reuse"))

        # Check if src directory exists
        default_dir = "src"
        sys.argv[1:] = [rf"--loc={default_dir}"]
        result = hook.find_files_missing_header()

        # Assert src directory was not found in the tmp_path directory
        assert result == 2
    finally:
        os.chdir(test_dir)


def test_custom_args(tmp_path: pytest.TempPathFactory):
    """Test custom arguments for loc, copyright, template, and license."""
    # Initialize tmp_path as a git repository
    git.Repo.init(tmp_path)

    dirs = ["dir1", "dir2"]
    template_name = "test_template.jinja2"
    template_path = os.path.join(os.getcwd(), "tests", template_name)
    reuse_dir = os.path.join(tmp_path, ".reuse", "templates")

    # Create .reuse directory and copy template file to it
    os.makedirs(reuse_dir)
    shutil.copyfile(f"{template_path}", f"{reuse_dir}/{template_name}")

    # Create directories & files to test
    for dir in dirs:
        dir_path = os.path.join(tmp_path, dir)
        # Create src code directory
        os.mkdir(dir_path)
        os.chdir(dir_path)
        # Add temporary file to directory
        create_test_file(dir_path)
        os.chdir(tmp_path)

    # Pass in custom arguments
    sys.argv[1:] = [
        f"--loc={dirs[0]},{dirs[1]}",
        '--custom_copyright="Super cool copyright"',
        "--custom_template=test_template",
        "--custom_license=ECL-1.0",
    ]
    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1


def test_main_passes():
    """Test all files are compliant."""
    # Ensure you are always running from root path to repo
    current_work_dir = os.getcwd()
    os.chdir(ROOT_DIR)

    try:
        sys.argv[1:] = ["--loc=src"]

        res = hook.main()
        assert res == 0
    finally:
        os.chdir(current_work_dir)


def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    # Ensure you are always running from root path to repo
    current_work_dir = os.getcwd()
    os.chdir(ROOT_DIR)

    try:
        sys.argv[1:] = [rf"--loc={tmp_path}"]
        test_file = create_test_file(tmp_path)

        # Run main given non_compliant file
        res = hook.main()
        assert res == 1

    finally:
        # Remove test file from git repo
        os.remove(test_file)
        os.chdir(current_work_dir)
