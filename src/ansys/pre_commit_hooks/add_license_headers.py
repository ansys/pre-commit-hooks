# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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
import fileinput
import json
import os
import pathlib
from platform import python_version
import shutil
import sys
from tempfile import NamedTemporaryFile

import git
from reuse import _annotate, _util, lint, project

DEFAULT_TEMPLATE = "ansys"
"""Default template to use for license headers."""
DEFAULT_COPYRIGHT = "ANSYS, Inc. and/or its affiliates."
"""Default copyright line for license headers."""
DEFAULT_LICENSE = "MIT"
"""Default license for headers."""
DEFAULT_START_YEAR = dt.today().year


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
    # Get the start year
    parser.add_argument(
        "--start_year",
        type=str,
        help="Start year for copyright line in headers.",
        default=DEFAULT_START_YEAR,
    )
    # Ignore license check by default is False when action='store_true'
    parser.add_argument("--ignore_license_check", action="store_true")
    parser.add_argument("--parser")
    parser.add_argument("--no_multiprocessing", action="store_true")

    # Option for printing lint output
    mutex_group = parser.add_mutually_exclusive_group()
    mutex_group.add_argument("-q", "--quiet", action="store_true")

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

    # Remove temporary file
    os.remove(filename)

    return missing_headers


def set_header_args(
    parser: argparse.ArgumentParser,
    start_year: str,
    current_year: int,
    file_path: str,
    copyright: str,
    template: str,
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
    if start_year == current_year:
        args.year = [current_year]
    else:
        args.year = [int(start_year), current_year]
    args.copyright_prefix = "string-c"
    args.copyright = [copyright]
    args.merge_copyrights = True
    args.template = template
    args.skip_unrecognised = True
    args.parser = parser

    return args


def non_recursive_file_check(changed_headers, parser, values, proj, missing_headers):
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
    start_year = values["start_year"]
    current_year = values["current_year"]
    copyright = values["copyright"]
    template = values["template"]

    for file in files:
        args = set_header_args(parser, start_year, current_year, file, copyright, template)
        # If the committed file is in missing_headers
        if (file in missing_headers) or (os.path.getsize(file) == 0):
            changed_headers = 1
            # Run REUSE on the file
            if not args.ignore_license_check:
                args.license = [values["license"]]

            _annotate.run(args, proj)
        else:
            # Save current copy of file
            before_hook = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(file, before_hook)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                _annotate.run(args, proj, tmp)

            # Check if the file before add-license-headers was run is the same as the one
            # after add-license-headers was run. If not, apply the syntax changes
            # from other hooks before add-license-headers was run to the file
            if check_same_content(before_hook, file) == False:
                add_hook_changes(before_hook, file)

            # Check if the file content before add-license-headers was run has been changed
            # Assuming the syntax was fixed in the above if statement, this check is
            # solely for the file's content
            if check_same_content(before_hook, file) == False:
                changed_headers = 1
                print(f"Successfully changed header of {file}")

            os.remove(before_hook)

    return changed_headers


def recursive_file_check(changed_headers, parser, values, proj, missing_headers, count):
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
    count: int
        Integer of the location in the files array.

    Returns
    -------
    int
        ``0`` if all files contain headers and are up to date.
        ``1`` if ``REUSE`` changed all noncompliant files.
    """
    files = values["files"]
    start_year = values["start_year"]
    current_year = values["current_year"]
    copyright = values["copyright"]
    template = values["template"]

    if count < len(files):
        # If the committed file is in missing_headers
        file = files[count]

        if (file in missing_headers) or (os.path.getsize(file) == 0):
            changed_headers = 1
            # Run REUSE on the file
            args = set_header_args(parser, start_year, current_year, file, copyright, template)
            if not args.ignore_license_check:
                args.license = [values["license"]]
            _annotate.run(args, proj)

            # Check if the next file is in missing_headers
            return recursive_file_check(
                changed_headers, parser, values, proj, missing_headers, count + 1
            )
        else:
            # Save current copy of file
            before_hook = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(file, before_hook)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                args = set_header_args(parser, start_year, current_year, file, copyright, template)
                _annotate.run(args, proj, tmp)

            # Check if the file before add-license-headers was run is the same as the one
            # after add-license-headers was run. If not, apply the syntax changes
            # from other hooks before add-license-headers was run to the file
            if check_same_content(before_hook, file) == False:
                add_hook_changes(before_hook, file)

            # Check if the file content before add-license-headers was run has been changed
            # Assuming the syntax was fixed in the above if statement, this check is
            # solely for the file's content
            if check_same_content(before_hook, file) == False:
                changed_headers = 1
                print(f"Successfully changed header of {file}")

            os.remove(before_hook)

            return recursive_file_check(
                changed_headers, parser, values, proj, missing_headers, count + 1
            )

    return changed_headers


def check_same_content(before_hook, after_hook):
    """
    Check if file before the hook ran is the same as after the hook ran.

    Parameters
    ----------
    before_hook: str
        Path to file before add-license-headers was run.
    after_hook: str
        Path to file after add-license-headers was run.

    Returns
    -------
    bool
        ``True`` if the files have the same content.
        ``False`` if the files have different content.
    """
    # Check if the files have the same content
    same_files = filecmp.cmp(before_hook, after_hook, shallow=False)
    # If the files are different, return False. Otherwise, return True
    if same_files == False:
        return False
    else:
        return True


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
    count = 0
    before_hook_file = open(before_hook, "r", encoding="utf8")
    before_hook_lines = before_hook_file.readlines()
    found_reuse_info = False

    # Check if python version is 3.9 since fileinput.input()
    # does not support the "encoding" keyword
    if "3.9" in python_version():
        file = fileinput.input(after_hook, inplace=True)
    else:
        file = fileinput.input(after_hook, inplace=True, encoding="utf8")

    # Copy file content before add-license-header was run into
    # the file after add-license-header was run.
    # stdout is redirected into the file if inplace is True
    for line in file:
        # Copy the new reuse lines into the file
        if _util.contains_reuse_info(line):
            count += 1
            found_reuse_info = True
            print(line.rstrip())
        else:
            if found_reuse_info:
                try:
                    # Check the lines after the reuse info are the same
                    # If not, print the line after the reuse info
                    # This happens when a comment changes from one line to
                    # multiline
                    if line != before_hook_lines[count]:
                        print(line.rstrip())
                except IndexError:
                    pass

                # Copy the rest of the file after the reuse information
                for line_after_reuse_info in before_hook_lines[count:]:
                    print(line_after_reuse_info.rstrip())
                break
            # Copy the header lines before reuse information is found
            else:
                count += 1
                print(line.rstrip())
    fileinput.close()


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


def update_license_file(arg_dict):
    """
    Update the LICENSE file to match MIT.txt, adjusting the year span to each repository.

    Parameters
    ----------
    arg_dict: dict
        Dictionary containing the committed files, custom copyright, template, license,
        changed_headers, start & end year, and git_repo
    """
    # Get location of LICENSE file in the repository the hook runs on
    git_root = arg_dict["git_repo"].git.rev_parse("--show-toplevel")
    repo_license_loc = os.path.join(git_root, "LICENSE").replace(os.sep, "/")
    save_repo_license = shutil.copyfile(repo_license_loc, f"{repo_license_loc}_save")

    # Get the location of MIT.txt in the hook's assets folder
    hook_loc = pathlib.Path(__file__).parent.resolve()
    hook_license_file = os.path.join(hook_loc, "assets", "LICENSES", f"{DEFAULT_LICENSE}.txt")

    # Copy MIT.txt from the assets folder to the LICENSE file in the repository
    if os.path.isfile(repo_license_loc) and (arg_dict["license"] == DEFAULT_LICENSE):
        shutil.copyfile(hook_license_file, repo_license_loc)

    # Whether or not the year in LICENSE was updated
    # 0 is unchanged, 1 is changed
    changed = 0

    # Check if custom_license is MIT
    if os.path.isfile(repo_license_loc) and (arg_dict["license"] == DEFAULT_LICENSE):
        if "3.9" in python_version():
            file = fileinput.input(repo_license_loc, inplace=True)
        else:
            file = fileinput.input(repo_license_loc, inplace=True, encoding="utf8")

        copyright = arg_dict["copyright"]
        start_year = str(arg_dict["start_year"])
        current_year = str(arg_dict["current_year"])

        for line in file:
            if copyright in line:
                # Copyright line: "Copyright (c) 2023 - 2024 ANSYS, Inc. and/or its affiliates."
                # Get the index of the closing parenthesis of the copyright line
                paren_index = line.index(")") + 2
                # Get the index of the start of the copyright statement
                cpright_index = line.index(copyright) - 1
                # Create the year string to be replaced in the copyright line
                # For example, "2024", or "2023 - 2024"
                year_range = (
                    f"{start_year} - {current_year}"
                    if (start_year != current_year)
                    else current_year
                )

                # If the start and end year are different
                if start_year != current_year:
                    if "-" in line:
                        # Get the index of the dash in the year range of the LICENSE file
                        dash_index = line.index("-") - 1
                        # Get the start year of the existing copyright line in the LICENSE file
                        existing_start_year = line[paren_index:dash_index]
                        # If the start year argument and the existing start year are different,
                        # replace the existing start year with the new one.
                        # For example, the existing start year is 2023, but the start_year
                        # argument is 2022.
                        if start_year != existing_start_year:
                            line = line.replace(existing_start_year, start_year)
                    else:
                        # Replace the existing copyright years with the new year_range
                        line = line.replace(line[paren_index:cpright_index], year_range)
                    print(line.rstrip())
                else:
                    if "-" in line:
                        # If there is a year range in the existing LICENSE file, but the
                        # start_year and current_year are the same, remove the year range
                        # and replace it with the current year
                        line = line.replace(line[paren_index:cpright_index], current_year)
                    print(line.rstrip())
            else:
                print(line.rstrip())

    fileinput.close()

    # If the year changed, print a message that the LICENSE file was changed
    if not check_same_content(save_repo_license, repo_license_loc):
        changed = 1
        print(f"Successfully updated year in {repo_license_loc}")

    # Remove the temporary file
    os.remove(save_repo_license)

    return changed


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

    # Check start_year is valid
    try:
        # Check the start year is not later than the current year
        if int(args.start_year) > dt.today().year:
            print("Please provide a start year less than or equal to the current year.")
            exit(1)
        # Check the start year isn't earlier than when computers were created :)
        if int(args.start_year) < 1942:
            print("Please provide a start year greater than or equal to 1942.")
            exit(1)
    except ValueError:
        print("Please ensure the start year is a number.")

    # Create dictionary containing the committed files, custom copyright,
    # template, license, changed_headers, year, and git_repo
    values = {
        "files": get_full_paths(args.files),
        "copyright": args.custom_copyright,
        "template": args.custom_template,
        "license": args.custom_license,
        "start_year": args.start_year,
        "current_year": dt.today().year,
        "git_repo": git_repo,
    }

    # Update the year in the copyright line of the LICENSE file
    license_return_code = update_license_file(values)

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
    _annotate.add_arguments(parser)

    # Link the default template and/or license from the assets folder to your git repo.
    link_assets(assets, os_git_root, args)

    # Project to run `REUSE <https://reuse.software/>`_ on
    proj = project.Project(git_root)

    # Get files missing headers (copyright and/or license information)
    missing_headers = list(list_noncompliant_files(args, proj))

    # Add or update headers of required files.
    # Return 1 if files were added or updated, and return 0 if no files were altered.
    if len(values["files"]) <= (sys.getrecursionlimit() - 2):
        file_return_code = recursive_file_check(
            changed_headers, parser, values, proj, missing_headers, 0
        )
    else:
        file_return_code = non_recursive_file_check(
            changed_headers, parser, values, proj, missing_headers
        )

    # Unlink default files & remove .reuse and LICENSES folders if empty
    cleanup(assets, os_git_root)

    # Returns 1 if REUSE changes noncompliant files or the year was updated in LICENSE
    # Returns 0 if all files are compliant
    return 1 if (license_return_code or file_return_code) == 1 else 0


def main():
    """Find files missing license headers and run `REUSE <https://reuse.software/>`_ on them."""
    return find_files_missing_header()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
