# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Tests for the ghaction-pin pre-commit hook."""

import pathlib
import shutil
import sys
from unittest.mock import MagicMock, patch

import pytest

import ansys.pre_commit_hooks.ghaction_pin as hook

TEST_FILES_DIR = pathlib.Path(__file__).parent / "test_ghaction_pin_files"

# A fake 40-char SHA returned by the mocked GitHub API.
FAKE_SHA = "aaaaaaaabbbbbbbbccccccccddddddddeeeeeeee"


def _mock_session(sha: str = FAKE_SHA) -> MagicMock:
    """Return a requests.Session mock that always resolves refs to *sha*."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"sha": sha}

    session = MagicMock()
    session.get.return_value = resp
    return session


def run_main(custom_args):
    """Inject sys.argv and call hook.main()."""
    sys.argv[1:] = custom_args
    return hook.main()


# ---------------------------------------------------------------------------
# Unit tests – resolve_ref_to_sha
# ---------------------------------------------------------------------------


@pytest.mark.ghaction_pin
def test_resolve_ref_lightweight_tag():
    """A lightweight tag resolved via the commits API is returned directly."""
    session = _mock_session(FAKE_SHA)
    cache = {}
    sha = hook.resolve_ref_to_sha("actions", "checkout", "v4", session, cache)
    assert sha == FAKE_SHA
    # Second call must use cache, not session.
    session.get.reset_mock()
    sha2 = hook.resolve_ref_to_sha("actions", "checkout", "v4", session, cache)
    assert sha2 == FAKE_SHA
    session.get.assert_not_called()


@pytest.mark.ghaction_pin
def test_resolve_ref_commits_api_no_token():
    """The commits API is tried first and works without a token."""
    commits_resp = MagicMock()
    commits_resp.status_code = 200
    commits_resp.json.return_value = {"sha": FAKE_SHA}

    session = MagicMock()
    session.get.return_value = commits_resp

    cache = {}
    sha = hook.resolve_ref_to_sha("ansys", "actions", "v10.3.2", session, cache)
    assert sha == FAKE_SHA
    # Should have only called the commits endpoint, not the git/ref endpoint.
    called_urls = [call.args[0] for call in session.get.call_args_list]
    assert any("commits" in u for u in called_urls)
    assert not any("git/ref" in u for u in called_urls)


@pytest.mark.ghaction_pin
def test_resolve_ref_not_found():
    """Returns None when the commits API returns a non-200 status."""
    not_found = MagicMock()
    not_found.status_code = 404

    session = MagicMock()
    session.get.return_value = not_found

    cache = {}
    sha = hook.resolve_ref_to_sha("fake", "repo", "v99", session, cache)
    assert sha is None


# ---------------------------------------------------------------------------
# Unit tests – pin_file
# ---------------------------------------------------------------------------


@pytest.mark.ghaction_pin
def test_pin_file_modifies_unpinned(tmp_path):
    """Unpinned action refs are replaced with SHA-pinned refs."""
    src = TEST_FILES_DIR / "unpinned.yml"
    dest = tmp_path / "unpinned.yml"
    shutil.copy(src, dest)

    session = _mock_session()
    cache = {}
    modified = hook.pin_file(dest, session, cache)

    assert modified is True
    content = dest.read_text(encoding="utf-8")
    # Local action must be untouched.
    assert "uses: ./.github/actions/my-action" in content
    # Unpinned refs must now contain the SHA.
    assert f"@{FAKE_SHA}" in content
    # Original tag preserved as comment.
    assert "# v4" in content
    assert "# v10.3.2" in content
    assert "# v10" in content


@pytest.mark.ghaction_pin
def test_pin_file_skips_already_pinned(tmp_path):
    """Files where all refs are already pinned are not modified."""
    src = TEST_FILES_DIR / "already_pinned.yml"
    dest = tmp_path / "already_pinned.yml"
    shutil.copy(src, dest)
    original = dest.read_text(encoding="utf-8")

    session = _mock_session()
    cache = {}
    modified = hook.pin_file(dest, session, cache)

    assert modified is False
    assert dest.read_text(encoding="utf-8") == original


@pytest.mark.ghaction_pin
def test_pin_file_crlf_line_endings(tmp_path):
    """CRLF line endings (Windows) are handled and preserved correctly."""
    # Build the workflow content with CRLF endings explicitly.
    lines = [
        "name: CI\r\n",
        "jobs:\r\n",
        "  build:\r\n",
        "    steps:\r\n",
        "      - uses: actions/checkout@v4\r\n",
    ]
    dest = tmp_path / "crlf.yml"
    dest.write_bytes("".join(lines).encode("utf-8"))

    session = _mock_session()
    cache = {}
    modified = hook.pin_file(dest, session, cache)

    assert modified is True
    content = dest.read_bytes().decode("utf-8")
    # SHA must appear in the output.
    assert f"@{FAKE_SHA}" in content
    # CRLF endings must be preserved.
    assert "\r\n" in content
    # No bare LF-only lines should have been introduced.
    assert "\r\n" in content


@pytest.mark.ghaction_pin
def test_pin_file_skips_unresolvable(tmp_path):
    """Lines whose ref cannot be resolved are left unchanged."""
    workflow = "name: CI\njobs:\n  build:\n    steps:\n      - uses: bad/repo@v1\n"
    dest = tmp_path / "workflow.yml"
    dest.write_text(workflow, encoding="utf-8")

    not_found = MagicMock()
    not_found.status_code = 404
    session = MagicMock()
    session.get.return_value = not_found

    cache = {}
    modified = hook.pin_file(dest, session, cache)

    assert modified is False
    assert dest.read_text(encoding="utf-8") == workflow


# ---------------------------------------------------------------------------
# Unit tests – collect_workflow_files
# ---------------------------------------------------------------------------


@pytest.mark.ghaction_pin
def test_collect_workflow_files_from_dir(tmp_path):
    """YAML files inside a directory are collected recursively."""
    (tmp_path / "a.yml").write_text("", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.yaml").write_text("", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("", encoding="utf-8")

    files = hook.collect_workflow_files([str(tmp_path)])
    names = {f.name for f in files}
    assert names == {"a.yml", "b.yaml"}


@pytest.mark.ghaction_pin
def test_collect_workflow_files_from_file(tmp_path):
    """An explicit file path is included directly."""
    target = tmp_path / "ci.yml"
    target.write_text("", encoding="utf-8")
    files = hook.collect_workflow_files([str(target)])
    assert len(files) == 1
    assert files[0].name == "ci.yml"


@pytest.mark.ghaction_pin
def test_collect_workflow_files_deduplicates(tmp_path):
    """Passing the same file and its parent directory does not duplicate it."""
    target = tmp_path / "ci.yml"
    target.write_text("", encoding="utf-8")
    files = hook.collect_workflow_files([str(target), str(tmp_path)])
    assert len(files) == 1


# ---------------------------------------------------------------------------
# Integration tests – main()
# ---------------------------------------------------------------------------


@pytest.mark.ghaction_pin
def test_main_returns_1_when_files_modified(tmp_path):
    """main() returns 1 when at least one file is modified."""
    src = TEST_FILES_DIR / "unpinned.yml"
    dest = tmp_path / "unpinned.yml"
    shutil.copy(src, dest)

    with patch("ansys.pre_commit_hooks.ghaction_pin._make_session", return_value=_mock_session()):
        result = run_main([str(dest)])

    assert result == 1


@pytest.mark.ghaction_pin
def test_main_returns_0_when_no_changes(tmp_path):
    """main() returns 0 when all files are already pinned."""
    src = TEST_FILES_DIR / "already_pinned.yml"
    dest = tmp_path / "already_pinned.yml"
    shutil.copy(src, dest)

    with patch("ansys.pre_commit_hooks.ghaction_pin._make_session", return_value=_mock_session()):
        result = run_main([str(dest)])

    assert result == 0


@pytest.mark.ghaction_pin
def test_main_no_args_returns_0():
    """main() with no arguments prints help and returns 0."""
    result = run_main([])
    assert result == 0
