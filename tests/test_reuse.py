import os
import sys

import pytest

import ansys.pre_commit_hooks.add_license_headers as hook


def test_argparse_passes():
    """Test argparse parses loc argument correctly."""
    sys.argv[1:] = ["--loc=./"]
    result = hook.get_args(sys.argv[1:])
    assert result == "./"


def test_argparse_fails():
    """Test argparse throws error if loc argument is empty."""
    sys.argv[1:] = [""]
    try:
        hook.get_args(sys.argv[1:])
        passes = True
    except SystemExit as e:
        passes = False

    assert not passes


def create_test_file(tmp_path):
    """Create temporary file for reuse testing."""
    test_file = os.path.join(tmp_path, "test.py")

    # Create test file with a random message
    with open(test_file, "w") as f:
        f.write("# test message")
    f.close()

    return test_file


def test_reuse_runs(tmp_path: pytest.TempPathFactory):
    """Test reuse annotate command is successful."""
    test_file = create_test_file(tmp_path)
    loc = hook.get_args([rf"--loc={tmp_path}"])

    # Run reuse on temporary file without header
    hook.run_reuse_on_files(loc)

    # Assert reuse added headers to all files
    assert hook.get_files(tmp_path) == set()

    # Remove test file from git repo
    os.remove(test_file)


def test_files_without_headers(tmp_path: pytest.TempPathFactory):
    """Test reuse detects files without license headers."""
    test_file = create_test_file(tmp_path)

    # Assert reuse detects file without header
    assert hook.get_files(tmp_path) != set()

    # Remove test file from git repo
    os.remove(test_file)


def test_invalid_project_loc():
    """Test reuse is being used on invalid repository."""
    out = hook.get_files_missing_header("./bad_repo")
    assert out == "bad_repo is no valid path for a repository"


def test_main():
    """Test reuse is being used on valid repository."""
    sys.argv[1:] = ["--loc=./"]
    res = hook.main()
    assert res == 0
