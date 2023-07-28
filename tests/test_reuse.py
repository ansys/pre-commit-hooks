import argparse
import os
import sys

import git
import pytest
from reuse import project

import ansys.pre_commit_hooks.add_license_headers as hook


def test_argparse_passes():
    """Test argparse passes given loc."""
    sys.argv[1:] = ["--loc=./"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    # Assert loc argument is same as set above
    assert args.loc == "./"


def test_argparse_fails():
    """Test argparse throws error if loc argument is empty."""
    sys.argv[1:] = [""]
    parser = argparse.ArgumentParser()
    try:
        hook.set_lint_args(parser)
        passes = True
    except:
        passes = False

    # Assert error is thrown for empty loc argument
    assert not passes


def test_all_files_compliant(tmp_path: pytest.TempPathFactory):
    """Test no noncompliant files are found."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)
    proj = project.Project(rf"{args.loc}")

    missing_headers = hook.list_noncompliant_files(args, proj)

    # Assert all files are compliant
    assert missing_headers == []


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

    result = hook.find_files_missing_header()

    # Assert .reuse directory does not exist
    assert result == 2

    # Restore original environment
    os.rename(os.path.join(git_root, "invalid_reuse"), os.path.join(git_root, ".reuse"))
    os.remove(test_file)


def test_main_passes():
    """Test all files are compliant."""
    sys.argv[1:] = ["--loc=src"]

    res = hook.main()
    assert res == 0


def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    sys.argv[1:] = [rf"--loc={tmp_path}"]
    test_file = create_test_file(tmp_path)

    # Run main given non_compliant file
    res = hook.main()
    assert res == 1

    # Remove test file from git repo
    os.remove(test_file)
