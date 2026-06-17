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

"""Module for pinning GitHub Actions workflow references to specific commit SHAs.

Each ``uses:`` line that references an action by a mutable ref (tag or branch)
is rewritten to pin the full 40-character commit SHA, with the original ref
preserved as an inline comment for human readability.

Input::

    uses: ansys/actions/code-style@v10.3.2

Output::

    uses: ansys/actions/code-style@d946b24b9a765f4169bcc94afdb27bd1a0533741 # v10.3.2

No authentication is required.  The GitHub commits API works anonymously for
all public repositories (60 requests/hour per IP; cached within each run).
"""

import argparse
import pathlib
import re
import sys
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GITHUB_API = "https://api.github.com"

# Matches a `uses:` step/job referencing an external GitHub action or reusable
# workflow.  Groups:
#   prefix   – leading whitespace plus optional "- " list item marker
#   owner    – GitHub org or user
#   repo     – repository name
#   subpath  – optional subdirectory (e.g. "/code-style" or "/.github/workflows/reuse.yml")
#   ref      – tag, branch, or SHA after "@"
#   comment  – optional existing inline comment (stripped and replaced)
_USES_RE = re.compile(
    r"^(?P<prefix>\s*(?:-\s+)?)uses:\s+"
    r"(?P<owner>[a-zA-Z0-9_.-]+)/(?P<repo>[a-zA-Z0-9_.-]+)"
    r"(?P<subpath>/[^\s@#]*)?"
    r"@(?P<ref>[^\s#]+)"
    r"(?:\s*#\s*(?P<comment>.+))?$"
)

# A full 40-character hexadecimal commit SHA.
_SHA40_RE = re.compile(r"^[0-9a-f]{40}$")

# Matches a uses: line with no @ref at all (missing version entirely).
_USES_NO_REF_RE = re.compile(
    r"^(?P<prefix>\s*(?:-\s+)?)uses:\s+"
    r"(?P<owner>[a-zA-Z0-9_.-]+)/(?P<repo>[a-zA-Z0-9_.-]+)"
    r"(?P<subpath>/[^\s@#]*)?$"
)


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------


def _make_session() -> requests.Session:
    """Create a ``requests.Session`` for the GitHub API."""
    session = requests.Session()
    session.headers["Accept"] = "application/vnd.github+json"
    session.headers["X-GitHub-Api-Version"] = "2022-11-28"
    return session


def resolve_ref_to_sha(
    owner: str,
    repo: str,
    ref: str,
    session: requests.Session,
    cache: dict,
) -> Optional[str]:
    """Return the 40-char commit SHA for *owner*/*repo*@*ref*.

    Parameters
    ----------
    owner : str
        GitHub organisation or user name.
    repo : str
        Repository name.
    ref : str
        Tag name, branch name, or short SHA to resolve.
    session : requests.Session
        Authenticated (or anonymous) HTTP session.
    cache : dict
        Mapping of ``(owner, repo, ref)`` to previously resolved SHAs.

    Returns
    -------
    str or None
        The full 40-character commit SHA, or ``None`` if resolution failed.
    """
    key = (owner, repo, ref)
    if key in cache:
        return cache[key]

    sha = _resolve_via_commits_api(owner, repo, ref, session)
    cache[key] = sha
    return sha


def _resolve_via_commits_api(
    owner: str, repo: str, ref: str, session: requests.Session
) -> Optional[str]:
    """Resolve *ref* to a full commit SHA using the GitHub commits API.

    Works without authentication for all public repositories.
    Returns the full 40-character commit SHA, or ``None`` if the ref
    could not be resolved.
    """
    url = f"{_GITHUB_API}/repos/{owner}/{repo}/commits/{ref}"
    resp = session.get(url, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


# ---------------------------------------------------------------------------
# Core file processing
# ---------------------------------------------------------------------------


def pin_file(filepath: pathlib.Path, session: requests.Session, cache: dict) -> bool:
    """Pin all unpinned GitHub Action refs in *filepath*.

    Parameters
    ----------
    filepath : pathlib.Path
        Path to a GitHub Actions workflow YAML file.
    session : requests.Session
        HTTP session used for GitHub API requests.
    cache : dict
        Shared resolution cache across files (avoids duplicate API calls).

    Returns
    -------
    bool
        ``True`` if the file was modified, ``False`` otherwise.
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    new_lines = []
    modified = False

    for line in lines:
        bare = line.rstrip("\r\n")
        eol = line[len(bare) :]  # preserves original line ending (LF or CRLF)
        m = _USES_RE.match(bare)
        if m is None:
            # Warn about uses: lines that have no @ref at all – they are
            # invalid GitHub Actions syntax and cannot be pinned automatically.
            if _USES_NO_REF_RE.match(bare):
                action_bare = bare.strip().removeprefix("- ").removeprefix("uses:").strip()
                print(
                    f"WARNING: {filepath}: '{action_bare}' has no @ref – "
                    "add a version tag or SHA manually before pinning.",
                    file=sys.stderr,
                )
            new_lines.append(line)
            continue

        indent = m.group("prefix")
        owner = m.group("owner")
        repo = m.group("repo")
        subpath = m.group("subpath") or ""
        ref = m.group("ref")

        # Already pinned to a full commit SHA → leave untouched.
        if _SHA40_RE.match(ref):
            new_lines.append(line)
            continue

        sha = resolve_ref_to_sha(owner, repo, ref, session, cache)
        if sha is None:
            print(
                f"WARNING: could not resolve {owner}/{repo}@{ref} – skipping",
                file=sys.stderr,
            )
            new_lines.append(line)
            continue

        action = f"{owner}/{repo}{subpath}"
        new_line = f"{indent}uses: {action}@{sha} # {ref}{eol}"

        if new_line != line:
            modified = True
            print(f"  pinned {action}@{ref} → @{sha[:7]}…  ({filepath})")

        new_lines.append(new_line)

    if modified:
        filepath.write_text("".join(new_lines), encoding="utf-8")

    return modified


def collect_workflow_files(paths: list) -> list:
    """Collect ``.yml`` / ``.yaml`` files from the given file or directory paths.

    Parameters
    ----------
    paths : list of str or pathlib.Path
        Files or directories to search.

    Returns
    -------
    list of pathlib.Path
        Deduplicated list of YAML files found.
    """
    seen: set = set()
    result = []
    for p in paths:
        path = pathlib.Path(p)
        if path.is_dir():
            candidates = list(path.rglob("*.yml")) + list(path.rglob("*.yaml"))
        elif path.is_file():
            candidates = [path]
        else:
            print(f"WARNING: path does not exist – {p}", file=sys.stderr)
            continue
        for c in candidates:
            resolved = c.resolve()
            if resolved not in seen:
                seen.add(resolved)
                result.append(c)
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Pin GitHub Action refs in workflow files and return an exit code.

    Returns
    -------
    int
        ``0`` if no files were modified, ``1`` if at least one file was
        updated (pre-commit will then re-stage the changes).
    """
    parser = argparse.ArgumentParser(
        description=(
            "Pin GitHub Action refs in workflow YAML files to full commit SHAs. "
            "Pass one or more workflow files or directories as arguments."
        )
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Workflow YAML files or directories containing workflow YAML files.",
    )
    args = parser.parse_args()

    if not args.files:
        parser.print_help(sys.stderr)
        return 0

    workflow_files = collect_workflow_files(args.files)
    if not workflow_files:
        print("No YAML files found in the specified paths.", file=sys.stderr)
        return 0

    session = _make_session()
    cache: dict = {}
    any_modified = False

    for wf_file in workflow_files:
        if pin_file(wf_file, session, cache):
            any_modified = True

    return 1 if any_modified else 0


if __name__ == "__main__":
    sys.exit(main())
