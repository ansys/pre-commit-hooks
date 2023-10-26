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
import filecmp
import json
import os
import pathlib
import shutil
import sys
from tempfile import NamedTemporaryFile

import git
from reuse import header, lint, project

DEFAULT_TEMPLATE = "ansys"
"""Default template to use for license headers."""
DEFAULT_COPYRIGHT = "ANSYS, Inc. and/or its affiliates."
"""Default copyright line for license headers."""
DEFAULT_LICENSE = "MIT"
"""Default license for headers."""


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
    # Get list of committed files
    parser.add_argument("files", nargs="*")
    # Get custom copyright statement
    parser.add_argument(
        "--custom_copyright",
        type=str,
        help="Default copyright line for license headers.",
        default=DEFAULT_COPYRIGHT,
    )
    # Get custom template
    parser.add_argument(
        "--custom_template",
        type=str,
        help="Default template to use for license headers.",
        default=DEFAULT_TEMPLATE,
    )
    # Get custom license
    parser.add_argument(
        "--custom_license",
        type=str,
        help="Default license for headers.",
        default=DEFAULT_LICENSE,
    )
    # Ignore license check by default is False when action='store_true'
    parser.add_argument("--ignore_license_check", action="store_true")
    parser.add_argument("--parser")
    parser.add_argument("--no_multiprocessing", action="store_true")
    lint.add_arguments(parser)

    return parser.parse_args()


def copy_assets(proj_root, args):
    """Copy .reuse and LICENSES folders from assets directory."""
    hook_loc = pathlib.Path(__file__).parent.resolve()
    directories = [".reuse"]

    # If ignore_license_check is False, copy LICENSES folder to
    # the root of the repository
    if not args.ignore_license_check:
        directories.append("LICENSES")

    for dir in directories:
        src = os.path.join(hook_loc, "assets", dir)
        dest = os.path.join(proj_root, dir)

        # If .reuse or LICENSES exists in the root of the repository,
        # only replace .reuse/templates/ansys.jinja2 and LICENSES/MIT.txt
        if os.path.isdir(dest):
            if ".reuse" in dest:
                src_file = os.path.join(src, "templates", "ansys.jinja2")
                dest_file = os.path.join(dest, "templates", "ansys.jinja2")
            elif "LICENSES" in dest:
                src_file = os.path.join(src, "MIT.txt")
                dest_file = os.path.join(dest, "MIT.txt")

            if os.path.isfile(dest_file):
                # Remove destination file & replace with
                # a new copy from source
                os.remove(dest_file)
                shutil.copyfile(src_file, dest_file)
        else:
            # If destination directory does not exist, copy the entire
            # folder from src to dest
            shutil.copytree(src, dest)


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

    # Get files missing copyright information
    missing_headers = set(lint_json["non_compliant"]["missing_copyright_info"])

    # If ignore_license_check is False, check files for missing licensing information
    if not args.ignore_license_check:
        missing_licensing_info = set(lint_json["non_compliant"]["missing_licensing_info"])
        missing_headers = missing_headers.union(missing_licensing_info)

        if lint_json["non_compliant"]["missing_licenses"]:
            missing_licenses = set(
                lint_json["non_compliant"]["missing_licenses"][args.custom_license]
            )
            missing_headers = missing_headers.union(missing_licenses)

    # Remove temporary file
    os.remove(filename)

    return missing_headers


def set_header_args(parser, year, file_path, copyright, template):
    """
    Set arguments for `REUSE <https://reuse.software/>`_.

    Parameters
    ----------
    parser: argparse.ArgumentParser
        Parser containing default license header arguments.
    year: int
        Current year retrieved by datetime.
    file_path: str
        Specific file path to create license headers.
    copyright: str
        Copyright line for license headers.
    template: str
        Name of the template for license headers (name.jinja2).

    Returns
    -------
    argparse.Namespace
        Namespace of arguments with their values.
    """
    # Provide values for license header arguments
    args = parser.parse_args([file_path])
    args.year = [str(year)]
    args.copyright_style = "string-c"
    args.copyright = [copyright]
    args.merge_copyrights = True
    args.template = template
    args.skip_unrecognised = True
    args.parser = parser

    return args


def check_exists(changed_headers, parser, values, proj, missing_headers, i):
    """
    Check if the committed file is missing its header.

    Parameters
    ----------
    changed_headers: int
        ``0`` if no headers were added or updated.
        ``1`` if headers were added or updated.
    parser: argparse.ArgumentParser
        Parser containing default license header arguments.
    values: dictionary
        Dictionary containing the values of files, copyright,
        template, license, changed_headers, year, and git_repo.
    proj: project.Project
        Project to run `REUSE <https://reuse.software/>`_ on.
    missing_headers: list
        Committed files that are missing copyright and/or
        license information in their headers.

    Returns
    -------
    int
        ``0`` if all files contain headers and are up to date.
        ``1`` if ``REUSE`` changed all noncompliant files.
    """
    files = values["files"]
    year = values["year"]
    copyright = values["copyright"]
    template = values["template"]

    if i < len(files):
        # If the committed file is in missing_headers
        if files[i] in missing_headers:
            changed_headers = 1
            # Run REUSE on the file
            args = set_header_args(parser, year, files[i], copyright, template)
            if not args.ignore_license_check:
                args.license = [values["license"]]
            header.run(args, proj)

            # Check if the next file is in missing_headers
            return check_exists(changed_headers, parser, values, proj, missing_headers, i + 1)
        else:
            # Save current copy of files[i]
            tempfile = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(files[i], tempfile)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                args = set_header_args(parser, year, files[i], copyright, template)
                header.run(args, proj, tmp)

            # Compare the tempfile with the updated file
            same_content = filecmp.cmp(tempfile, files[i], shallow=False)
            # Diff the updated file with the version of the file that was git added
            diff = values["git_repo"].git.diff(files[i], name_only=True)
            # Print header was successfully changed if it was modified
            if diff or (same_content == False):
                changed_headers = 1
                print(f"Successfully changed header of {files[i]}")

            return check_exists(changed_headers, parser, values, proj, missing_headers, i + 1)

    return changed_headers


def get_full_paths(file_list):
    """
    Update file paths to be absolute paths with system separators.

    Parameters
    ----------
    file_list: list
        List containing committed files.

    Returns
    -------
    list
        List containing the full paths of committed files.
    """
    full_path_files = []
    for file in file_list:
        if "win" in sys.platform:
            split_str = file.split("/")
            full_path_files.append(os.path.abspath(os.path.join(*split_str)))
        else:
            full_path_files.append(os.path.abspath(file))

    return full_path_files


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

    # Get root directory of the git repository.
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)

    # Set changed_headers to zero by default
    changed_headers = 0

    # Create dictionary containing the committed files, custom copyright,
    # template, license, changed_headers, year, and git_repo
    values = {
        "files": get_full_paths(args.files),
        "copyright": args.custom_copyright,
        "template": args.custom_template,
        "license": args.custom_license,
        "year": dt.today().year,
        "git_repo": git_repo,
    }

    # Add header arguments to parser. Arguments are: copyright, license, contributor,
    # year, style, copyright-style, template, exclude-year, merge-copyrights, single-line,
    # multi-line, explicit-license, force-dot-license, recursive, no-replace,
    # skip-unrecognized, and skip-existing
    header.add_arguments(parser)

    # Run REUSE on root of the repository
    git_root = values["git_repo"].git.rev_parse("--show-toplevel")

    # Copy .reuse folder and LICENSES folder (if licenses are being checked)
    copy_assets(git_root, args)

    proj = project.Project(git_root)

    # Get files missing headers (copyright and/or license information)
    missing_headers = list(list_noncompliant_files(args, proj))

    # Returns 1 if REUSE changes noncompliant files
    # Returns 0 if all files are compliant
    return check_exists(changed_headers, parser, values, proj, missing_headers, 0)


def main():
    """Find files missing license headers and run `REUSE <https://reuse.software/>`_ on them."""
    return find_files_missing_header()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
