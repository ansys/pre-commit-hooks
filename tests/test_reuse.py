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


def create_test_file(tmp_path):
    """Create temporary file for reuse testing."""
    with NamedTemporaryFile(mode="w", delete=False, dir=tmp_path) as tmp:
        tmp.write("# test message")
        tmp.close()
        filename = tmp.name

    py_filename = f"{filename}.py"
    os.rename(filename, py_filename)

    return py_filename


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
    os.chdir(REPO_PATH)

    template_name = "test_template.jinja2"
    template_path = os.path.join(REPO_PATH, "tests", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)

    # Stage test.py file
    repo.index.add(tmp_file)

    # Pass in custom arguments
    sys.argv[1:] = [
        tmp_file,
        '--custom_copyright="Super cool copyright"',
        "--custom_template=test_template",
        "--custom_license=ECL-1.0",
    ]
    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(REPO_PATH)


def test_multiple_files(tmp_path: pytest.TempPathFactory):
    """Test reuse is run on files without headers, when one file already has header."""
    os.chdir(REPO_PATH)

    template_name = "ansys.jinja2"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    new_files = []

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)
    new_files.append(tmp_file)

    # Stage test.py file
    repo.index.add(tmp_file)

    # Pass in file arguments
    sys.argv[1:] = new_files

    hook.main()

    # Add test.py with license header
    repo.index.add(tmp_file)

    # Create two new files to run REUSE on
    # new_files = ["test2.py", "test3.py"]
    # for file in new_files:
    for i in range(0, 2):
        tmp_file = create_test_file(tmp_path)
        repo.index.add(tmp_file)
        new_files.append(tmp_file)

    # Pass in the file arguments
    sys.argv[1:] = new_files

    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(REPO_PATH)


def test_main_fails(tmp_path: pytest.TempPathFactory):
    """Test reuse is being run on noncompliant file."""
    os.chdir(REPO_PATH)

    template_name = "ansys.jinja2"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)

    # Stage test.py file
    repo.index.add(tmp_file)

    sys.argv[1:] = [tmp_file]

    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 1

    os.chdir(REPO_PATH)


def test_main_passes():
    """Test all files are compliant."""
    os.chdir(REPO_PATH)

    sys.argv[1:] = []
    res = hook.main()

    # Assert main runs successfully
    assert res == 0

    os.chdir(REPO_PATH)


def test_license_check():
    """Test license is checked in the header."""
    os.chdir(REPO_PATH)

    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == False


def test_no_license_check():
    """Test license check is ignored."""
    os.chdir(REPO_PATH)

    sys.argv[1:] = ["--ignore_license_check"]
    parser = argparse.ArgumentParser()
    args = hook.set_lint_args(parser)

    assert args.ignore_license_check == True


def test_update_header(tmp_path: pytest.TempPathFactory):
    """Test update header."""
    template_name = "ansys.jinja2"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    new_files = []

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)
    new_files.append(tmp_file)

    # Stage test.py file
    repo.index.add(new_files)

    hook.main()

    # Add test.py with license header
    repo.index.add(new_files)

    res = hook.main()

    # Assert main runs successfully with custom arguments
    assert res == 0

    os.chdir(REPO_PATH)


def test_update_changed_header(tmp_path: pytest.TempPathFactory):
    """Test that header is updated when the jinja file changes."""
    template_name = "ansys.jinja2"
    template_path = os.path.join(REPO_PATH, ".reuse", "templates", template_name)

    # Change dir to tmp_path
    os.chdir(tmp_path)

    # Set up git repository in tmp_path
    repo = init_git_repo(tmp_path, template_path, template_name)

    new_files = []

    # Create a test file in tmp_path
    tmp_file = create_test_file(tmp_path)
    new_files.append(tmp_file)

    # Stage test.py file
    repo.index.add(new_files)

    sys.argv[1:] = new_files

    hook.main()

    # Add test.py with license header
    repo.index.add(new_files)

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

    file = open(orig_jinja, "r")
    for line in file:
        print(line, end="")

    # Git add jinja file
    new_files.append(orig_jinja)
    repo.index.add(new_files)

    sys.argv[1:] = new_files

    # Run main
    hook.main()

    # Check that "New Permission" is in the tmp file header
    file = open(tmp_file, "r")
    for line in file:
        if "Permission" in line:
            assert "New Permission" in line

    os.chdir(REPO_PATH)
