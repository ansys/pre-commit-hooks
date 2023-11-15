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
import difflib
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


def set_lint_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
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


def link_assets(assets: dict, git_root: str, args: argparse.Namespace) -> None:
    """
    Link the default template and/or license from the assets folder to your git repo.

    Parameters
    ----------
    assets: dict
        Dictionary containing the asset folder information.
    git_root: str
        Full path of the repository's root directory.
    args: argparse.Namespace
        Namespace of arguments with their values.
    """
    # Unlink default files & remove .reuse and LICENSES folders if empty
    cleanup(assets, git_root)

    hook_loc = pathlib.Path(__file__).parent.resolve()

    for key, value in assets.items():
        hook_asset_dir = os.path.join(hook_loc, "assets", value["path"])
        repo_asset_dir = os.path.join(git_root, value["path"])

        # If key is .reuse and the custom template is being used
        if key == ".reuse" and args.custom_template == DEFAULT_TEMPLATE:
            mkdirs_and_link(value["path"], hook_asset_dir, repo_asset_dir, value["default_file"])

        # If key is LICENSES, the default license is being used, and ignore_license_check is False
        if (
            key == "LICENSES"
            and args.custom_license == DEFAULT_LICENSE
            and not args.ignore_license_check
        ):
            mkdirs_and_link(value["path"], hook_asset_dir, repo_asset_dir, value["default_file"])


def mkdirs_and_link(
    asset_dir: str, hook_asset_dir: str, repo_asset_dir: str, filename: str
) -> None:
    """
    Make .reuse or LICENSES directory and create symbolic link to file.

    Parameters
    ----------
    asset_dir: str
        Path of the asset directory required for REUSE (.reuse/templates or LICENSES).
    hook_asset_dir: str
        Full path of the hook's asset directory.
    repo_asset_dir: str
        Full path of the git repository's asset directory.
    filename: str
        Name of the file to be linked from the hook_asset_dir to the repo_asset_dir.
    """
    src = os.path.join(hook_asset_dir, filename)
    dest = os.path.join(repo_asset_dir, filename)
    # If .reuse/templates or LICENSES directories do not exist, create them
    if not os.path.isdir(asset_dir):
        os.makedirs(asset_dir)
    # Make symbolic links to files within the assets folder
    os.symlink(src, dest)


def list_noncompliant_files(args: argparse.Namespace, proj: project.Project) -> list:
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


def set_header_args(
    parser: argparse.ArgumentParser, year: int, file_path: str, copyright: str, template: str
) -> argparse.Namespace:
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


def check_exists(
    changed_headers: int,
    parser: argparse.ArgumentParser,
    values: dict,
    proj: project.Project,
    missing_headers: list,
    i: int,
) -> int:
    """
    Check if the committed file is missing its header.

    Parameters
    ----------
    changed_headers: int
        ``0`` if no headers were added or updated.
        ``1`` if headers were added or updated.
    parser: argparse.ArgumentParser
        Parser containing default license header arguments.
    values: dict
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
            before_hook = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(files[i], before_hook)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                args = set_header_args(parser, year, files[i], copyright, template)
                header.run(args, proj, tmp)

            # check diffs between files and do modifications afterwards
            add_hook_changes(before_hook, files[i])

            # Compare the tempfile with the updated file
            # same_content is True if the two files that are being compared are the same
            same_content = filecmp.cmp(before_hook, files[i], shallow=False)

            # Print header was successfully changed if it was modified
            if same_content == False:
                changed_headers = 1
                print(f"Successfully changed header of {files[i]}")

            return check_exists(changed_headers, parser, values, proj, missing_headers, i + 1)

    return changed_headers


def add_hook_changes(before_hook: str, after_hook: str) -> None:
    """
    Add earlier hook changes to updated file with header.

    Parameters
    ----------
    before_hook: str
        Path to file before add-license-headers was run.
    after_hook: str
        Path to file after add-license-headers was run.
    """
    # Open files
    before_file = open(before_hook, "r")
    after_file = open(after_hook, "r")

    # Compare the files before and after the hook ran
    diff = difflib.ndiff(after_file.readlines(), before_file.readlines())

    before_file.close()
    after_file.close()

    # Combine the changes from before the hook with the changes after the hook
    with NamedTemporaryFile(mode="w", delete=False) as tmp:
        while True:
            try:
                line = str(next(diff))
                if "+" in line[0] and line[2:] == "\n":
                    tmp.write(line[2:])
                elif "-" in line[0]:
                    tmp.write(line[2:])
                elif "?" in line[0]:
                    continue
                elif " " in line[0]:
                    tmp.write(line[2:])
            except StopIteration:
                break

        tmp.close()

        # Copy the file with combined changes to the file that was
        # edited by the add-license-headers hook
        shutil.copyfile(tmp.name, after_hook)

        # Delete temporary file
        os.remove(tmp.name)


def get_full_paths(file_list: list) -> list:
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


def cleanup(assets: dict, os_git_root: str) -> None:
    """
    Unlink the default asset files, and remove directories if empty.

    Parameters
    ----------
    assets: dict
        Dictionary containing assets information
    os_git_root: str
        Full path of the repository's root directory.
    """
    # Remove default assets (.reuse/templates/ansys.jinja2 and LICENSES/MIT.txt)
    for key, value in assets.items():
        dest = os.path.join(os_git_root, value["path"], value["default_file"])
        # If the default asset files exist, unlink and remove directory
        if os.path.exists(dest):
            os.remove(dest)
            if not os.listdir(value["path"]):
                shutil.rmtree(key)


def find_files_missing_header() -> int:
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

    # Run REUSE on root of the repository
    git_root = values["git_repo"].git.rev_parse("--show-toplevel")

    # git_root with correct line separators for operating system
    os_git_root = git_root.replace("/", os.sep)

    # Dictionary containing the asset folder information
    assets = {
        ".reuse": {
            "path": os.path.join(".reuse", "templates"),
            "default_file": f"{DEFAULT_TEMPLATE}.jinja2",
        },
        "LICENSES": {
            "path": "LICENSES",
            "default_file": f"{DEFAULT_LICENSE}.txt",
        },
    }

    # Add header arguments to parser. Arguments are: copyright, license, contributor,
    # year, style, copyright-style, template, exclude-year, merge-copyrights, single-line,
    # multi-line, explicit-license, force-dot-license, recursive, no-replace,
    # skip-unrecognized, and skip-existing
    header.add_arguments(parser)

    # Link the default template and/or license from the assets folder to your git repo.
    link_assets(assets, os_git_root, args)

    # Project to run `REUSE <https://reuse.software/>`_ on
    proj = project.Project(git_root)

    # Get files missing headers (copyright and/or license information)
    missing_headers = list(list_noncompliant_files(args, proj))

    # Add or update headers of required files.
    # Return 1 if files were added or updated, and return 0 if no files were altered.
    return_code = check_exists(changed_headers, parser, values, proj, missing_headers, 0)

    # Unlink default files & remove .reuse and LICENSES folders if empty
    cleanup(assets, os_git_root)

    # Returns 1 if REUSE changes noncompliant files
    # Returns 0 if all files are compliant
    return return_code


def main():
    """Find files missing license headers and run `REUSE <https://reuse.software/>`_ on them."""
    return find_files_missing_header()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
