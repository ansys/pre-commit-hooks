#!/usr/bin/env python
# Copyright (C) 2023 ANSYS, Inc. and/or its affiliates.
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

"""Run reuse for files missing license headers."""
import argparse
from datetime import date as dt
import json
import os
from tempfile import NamedTemporaryFile

import git
from reuse import header, lint, project


def set_lint_args(parser):
    """
    Add arguments to parser for reuse lint.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        Parser without any arguments.

    Returns
    -------
    argparse.Namespace
        Parser Namespace containing lint arguments.
    """
    parser.add_argument("--loc", type=str, help="Path to repository location", default="src")
    parser.add_argument("--parser")
    parser.add_argument("--no_multiprocessing", action="store_true")
    lint.add_arguments(parser)

    return parser.parse_args()


def list_noncompliant_files(args, proj):
    """
    Retrieve list of noncompliant files.

    Parameters
    ----------
    args: argparse.Namespace
        Namespace of arguments with their values.
    proj: project.Project
        Project reuse runs on.

    Returns
    -------
    list
        List of files without license headers.
    """
    # Create a temporary file containing lint.run json output
    filename = None
    with NamedTemporaryFile(mode="w", delete=False) as tmp:
        args.json = True
        lint.run(args, proj, tmp)
        filename = tmp.name

    # Open the temporary file, load the json, and find files missing copyright & licensing info.
    lint_json = None
    with open(filename, "rb") as file:
        lint_json = json.load(file)

    missing_headers = set(
        lint_json["non_compliant"]["missing_copyright_info"]
        + lint_json["non_compliant"]["missing_licensing_info"]
    )

    # Remove temporary file
    os.remove(filename)

    return missing_headers


def find_files_missing_header():
    """
    Retrieve files without license header.

    Returns
    -------
    int
        Returns non-zero int if one or more files are noncompliant,
        or if the .reuse directory is missing.
    """
    # Set up argparse for location, parser, and lint
    # Lint contains 4 args: quiet, json, plain, and no_multiprocessing
    parser = argparse.ArgumentParser()
    args = set_lint_args(parser)
    proj = project.Project(rf"{args.loc}")

    missing_headers = list_noncompliant_files(args, proj)

    # Get current year for license file
    year = dt.today().year

    # If there are files missing headers, run reuse and return 1
    if missing_headers:
        # Returns 1 if reuse changes all noncompliant files
        # Returns 2 if .reuse directory does not exist
        return run_reuse(parser, year, args.loc, missing_headers)

    return 0


def check_reuse_dir():
    """
    Check .reuse directory exists in root of git repository.

    Returns
    -------
    str
        Root path of git repository.
    int
        If .reuse directory does not exist at root path of git repository.
    """
    # Get root directory of current git repository
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    # If .reuse folder does not exist in git repository root, return 1
    if not os.path.isdir(os.path.join(git_root, ".reuse")):
        print(f"Please ensure the .reuse directory is in {git_root}")
        return 1

    return git_root


def run_reuse(parser, year, loc, missing_headers):
    """
    Run reuse command on files without license headers.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        Parser containing previously set arguments.
    year: int
        Current year for license header.
    loc: str
        Location to search for files missing headers.
    missing_headers: list
        List of files that are missing headers.

    Returns
    -------
    int
        Fails pre-commit hook on return 1
    """
    # Add header arguments to parser which include: copyright, license, contributor, year,
    # style, copyright-style, template, exclude-year, merge-copyrights, single-line,
    # multi-line, explicit-license, force-dot-license, recursive, no-replace,
    # skip-unrecognized, skip-existing
    header.add_arguments(parser)

    git_root = check_reuse_dir()
    if git_root == 1:
        # Previous check_reuse_dir() function returned error because .reuse
        # directory does not exist... returning 2
        return 2

    # Add missing license header to each file in the list
    for file in missing_headers:
        args = parser.parse_args([rf"--loc={loc}", file])
        args.year = [str(year)]
        args.copyright_style = "string-c"
        args.copyright = ["ANSYS, Inc. and/or its affiliates."]
        args.merge_copyrights = True
        args.template = "ansys"
        args.license = ["MIT"]
        args.skip_unrecognised = True
        args.parser = parser

        # Requires .reuse directory to be in git_root directory
        proj = project.Project(git_root)
        header.run(args, proj)

    return 1


def main():
    """Find files missing license header & run reuse on them."""
    return find_files_missing_header()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
