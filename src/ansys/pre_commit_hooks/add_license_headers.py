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

"""
Module for running `REUSE <https://reuse.software/>`_ to add missing license headers to files.

A license header consists of the Ansys copyright statement and licensing information.
"""
import argparse
from datetime import date as dt
import json
import os
from tempfile import NamedTemporaryFile

import git
from reuse import header, lint, project

DEFAULT_SOURCE_CODE_DIRECTORY = "src"
"""Default directory to check files for license headers."""


def set_lint_args(parser):
    """
    Add lint arguments to the parser for `REUSE <https://reuse.software/>`_.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        Parser without any lint arguments.

    Returns
    -------
    argparse.Namespace
        Parser namespace containing lint arguments.
    """
    parser.add_argument(
        "--loc",
        type=str,
        help="Directory to check files for license headers.",
        default=DEFAULT_SOURCE_CODE_DIRECTORY,
    )
    parser.add_argument("--parser")
    parser.add_argument("--no_multiprocessing", action="store_true")
    lint.add_arguments(parser)

    return parser.parse_args()


def list_noncompliant_files(args, proj):
    """
    Get a list of the files that are missing license headers.

    Parameters
    ----------
    args: argparse.Namespace
        Namespace of arguments with their values.
    proj: project.Project
        Project to run `REUSE <https://reuse.software/>`_ on.

    Returns
    -------
    list
        List of the files that are missing license headers.
    """
    # Create a temporary file containing lint.run json output
    filename = None
    with NamedTemporaryFile(mode="w", delete=False) as tmp:
        args.json = True
        lint.run(args, proj, tmp)
        filename = tmp.name

    # Open the temporary file, load the JSON file, and find files that
    # are missing license headers.
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
    Find files that are missing license headers and run `REUSE <https://reuse.software/>`_ on them.

    Returns
    -------
    int
        ``1`` if ``REUSE`` changed all noncompliant files.

        ``2`` if the ``.reuse`` or location directory does not exist in the root path
        of the GitHub repository.
    """
    # Set up argparse for location, parser, and lint
    # Lint contains four arguments: quiet, json, plain, and no_multiprocessing
    parser = argparse.ArgumentParser()
    args = set_lint_args(parser)

    # Check if required directories exist
    dir_exists = check_dir_exists(args.loc)
    if not dir_exists:
        # Previous check_dir_exists() function returned error because
        # --loc's value does not exist... returning 2
        return 2

    proj = project.Project(rf"{args.loc}")

    missing_headers = list_noncompliant_files(args, proj)

    # Get current year for license file
    year = dt.today().year

    # If there are files missing headers, run REUSE and return 1
    if missing_headers:
        # Returns 1 if REUSE changes all noncompliant files
        run_reuse(parser, year, args.loc, missing_headers)
        return 1

    # Hook ran fine.... returning exit code 0
    return 0


def repo_path():
    """
    Get the path to the root of the git repository.

    Returns
    -------
    str
        Path to the root of the git repository.
    """
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    return git_root


def check_dir_exists(folder_name) -> bool:
    """
    Check if the ``.reuse`` or the location directory exist in the root path of the git repo.

    Parameters
    ----------
    folder_name: str
        Folder to check if it exists.

    Returns
    -------
    bool
        Returns ``False`` if  the ``.reuse`` or ``{folder_name}`` directory do
        not exist in the root path of the git repository. Otherwise, ``True``.
    """
    # Get root path of git repository
    git_root = repo_path()

    # If the .reuse or default_dir directory does not exist in the root
    # of the git repository, return 1
    if not os.path.isdir(os.path.join(git_root, ".reuse")):
        print(
            f"The .reuse directory does not exist in {git_root}.",
            "Please copy the .reuse directory from https://github.com/ansys/pre-commit-hooks/.",
            sep=os.linesep,
        )
        return False
    elif not os.path.isdir(os.path.join(git_root, folder_name)):
        print(
            f"The {folder_name} directory does not exist in {git_root}.",
            "Please add the --loc flag to .pre-commit-config.yaml, as follows:\n",
            "- id: add-license-headers",
            "    args:",
            "    - --loc=mydir",
            "",
            "Where mydir is a directory containing files that are checked for license headers.",
            sep=os.linesep,
        )
        return False
    else:
        return True


def run_reuse(parser, year, loc, missing_headers):
    """
    Run `REUSE <https://reuse.software/>`_ on files that are missing license headers.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        Parser containing the previously set arguments.
    year: int
        Current year for the license header.
    loc: str
        Location to search for files that are missing license headers.
    missing_headers: list
        List of files that are missing license headers.

    """
    # Add header arguments to parser. Arguments are: copyright, license, contributor,
    # year, style, copyright-style, template, exclude-year, merge-copyrights, single-line,
    # multi-line, explicit-license, force-dot-license, recursive, no-replace,
    # skip-unrecognized, and skip-existing.
    header.add_arguments(parser)

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
        proj = project.Project(repo_path())
        header.run(args, proj)


def main():
    """Find files missing license headers and run `REUSE <https://reuse.software/>`_ on them."""
    return find_files_missing_header()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
