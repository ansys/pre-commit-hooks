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
"""Module for enforcing hash-based versions in ``.pre-commit-config.yaml`` files."""

import argparse
import re

import yaml

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
"""Regular expression pattern to match a full 40-character SHA-1 commit hash."""


def is_sha_hash(rev: str) -> bool:
    """
    Check if a revision string is a full SHA-1 commit hash.

    Parameters
    ----------
    rev : str
        The revision string to check.

    Returns
    -------
    bool
        ``True`` if ``rev`` is a 40-character hexadecimal SHA-1 hash.
        ``False`` otherwise.
    """
    return bool(SHA_PATTERN.match(rev))


def check_pre_commit_config(config_file: str) -> bool:
    """
    Check that all repos in a ``.pre-commit-config.yaml`` file use hash-based revisions.

    Parameters
    ----------
    config_file : str
        Path to the ``.pre-commit-config.yaml`` file to validate.

    Returns
    -------
    bool
        ``True`` if all repo revisions are SHA hashes.
        ``False`` if one or more repos use non-hash revisions (e.g. tag names).
    """
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    if not config or "repos" not in config:
        return True

    is_compliant = True
    for repo in config["repos"]:
        url = repo.get("repo", "")
        rev = repo.get("rev", "")
        if rev and not is_sha_hash(str(rev)):
            print(
                f"Repo '{url}' uses non-hash revision '{rev}'. "
                "Use a full SHA-1 commit hash instead."
            )
            is_compliant = False

    return is_compliant


def main():
    """Enforce hash-based versions in ``.pre-commit-config.yaml`` files."""
    parser = argparse.ArgumentParser(
        description="Enforce hash-based revisions in .pre-commit-config.yaml files."
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Paths to .pre-commit-config.yaml files to check.",
    )
    args = parser.parse_args()

    is_compliant = True
    for filename in args.filenames:
        if not check_pre_commit_config(filename):
            is_compliant = False

    if not is_compliant:
        print(
            "\nOne or more .pre-commit-config.yaml files use non-hash revisions."
            "Run `pre-commit autoupdated --freeze` to use full SHA-1 commit hashes."
        )
    return 0 if is_compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
