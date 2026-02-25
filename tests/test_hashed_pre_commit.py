# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

import sys

import pytest

import ansys.pre_commit_hooks.hashed_pre_commit as hook


def write_config(tmp_path, content):
    """Write a .pre-commit-config.yaml file and return its path."""
    config_file = tmp_path / ".pre-commit-config.yaml"
    config_file.write_text(content)
    return str(config_file)


@pytest.mark.hashed_pre_commit
def test_valid_sha_hash(tmp_path):
    """Test that a repo using a full SHA hash passes validation."""
    content = """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2
    hooks:
      - id: trailing-whitespace
"""
    config_file = write_config(tmp_path, content)
    assert hook.check_pre_commit_config(config_file) is True


@pytest.mark.hashed_pre_commit
def test_invalid_tag_revision(tmp_path, capsys):
    """Test that a repo using a tag name fails validation."""
    content = """\
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
"""
    config_file = write_config(tmp_path, content)
    assert hook.check_pre_commit_config(config_file) is False
    output = capsys.readouterr()
    assert "v4.4.0" in output.out
    assert "https://github.com/pre-commit/pre-commit-hooks" in output.out


@pytest.mark.hashed_pre_commit
def test_mixed_revisions(tmp_path, capsys):
    """Test that a config with both valid and invalid revisions fails."""
    sha = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    content = f"""\
repos:
  - repo: https://github.com/psf/black
    rev: {sha}
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
"""
    config_file = write_config(tmp_path, content)
    assert hook.check_pre_commit_config(config_file) is False
    output = capsys.readouterr()
    assert "v4.4.0" in output.out


@pytest.mark.hashed_pre_commit
def test_all_sha_hashes(tmp_path):
    """Test that a config where all repos use SHA hashes passes."""
    sha1 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    sha2 = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
    content = f"""\
repos:
  - repo: https://github.com/psf/black
    rev: {sha1}
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: {sha2}
    hooks:
      - id: trailing-whitespace
"""
    config_file = write_config(tmp_path, content)
    assert hook.check_pre_commit_config(config_file) is True


@pytest.mark.hashed_pre_commit
def test_empty_config(tmp_path):
    """Test that an empty config file is treated as compliant."""
    config_file = write_config(tmp_path, "")
    assert hook.check_pre_commit_config(config_file) is True


@pytest.mark.hashed_pre_commit
def test_config_without_repos(tmp_path):
    """Test that a config without a repos key is treated as compliant."""
    content = "default_language_version:\n  python: python3\n"
    config_file = write_config(tmp_path, content)
    assert hook.check_pre_commit_config(config_file) is True


@pytest.mark.hashed_pre_commit
def test_is_sha_hash_valid():
    """Test is_sha_hash returns True for a valid 40-char hex string."""
    assert hook.is_sha_hash("a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2") is True


@pytest.mark.hashed_pre_commit
def test_is_sha_hash_invalid_tag():
    """Test is_sha_hash returns False for a tag string."""
    assert hook.is_sha_hash("v4.4.0") is False


@pytest.mark.hashed_pre_commit
def test_is_sha_hash_too_short():
    """Test is_sha_hash returns False for a hash that is too short."""
    assert hook.is_sha_hash("a1b2c3d4") is False


@pytest.mark.hashed_pre_commit
def test_is_sha_hash_non_hex():
    """Test is_sha_hash returns False for a 40-char non-hex string."""
    assert hook.is_sha_hash("z" * 40) is False


@pytest.mark.hashed_pre_commit
def test_main_pass(tmp_path):
    """Test main returns 0 when all revisions are hashes."""
    sha = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    content = f"""\
repos:
  - repo: https://github.com/psf/black
    rev: {sha}
    hooks:
      - id: black
"""
    config_file = write_config(tmp_path, content)
    sys.argv[1:] = [config_file]
    assert hook.main() == 0


@pytest.mark.hashed_pre_commit
def test_main_fail(tmp_path):
    """Test main returns 1 when a revision is not a hash."""
    content = """\
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
"""
    config_file = write_config(tmp_path, content)
    sys.argv[1:] = [config_file]
    assert hook.main() == 1


@pytest.mark.hashed_pre_commit
def test_main_no_files():
    """Test main returns 0 when no files are provided."""
    sys.argv[1:] = []
    assert hook.main() == 0
