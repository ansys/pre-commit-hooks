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
import os
import pathlib
import re
import shutil
import sys
from tempfile import NamedTemporaryFile

import git
from reuse import extract
from reuse.cli import common
from reuse.cli.annotate import add_header_to_file, get_comment_style, get_reuse_info, get_template

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


def set_variables(obj: common.ClickObj, values: dict, args: argparse.Namespace) -> tuple:
    """Set variables to run `REUSE <https://reuse.software/>`_ on the project.

    Parameters
    ----------
    obj: common.ClickObj
        A click object used in `REUSE <https://reuse.software/>`_ to annotate files.
    values: dict
        Dictionary containing the values of files, copyright,
        template, license, changed_headers, year, and git_repo.
    args: argparse.Namespace
        Namespace of arguments with their values.
    Returns
    -------
    tuple
        Tuple containing the project, template, commented, license, files, copyright, and years.
    """
    project = obj.project
    template, commented = get_template(values["template"], project)

    license = [] if args.ignore_license_check else [values["license"]]
    files = values["files"]
    copyright = [values["copyright"]]
    years = (
        f"{values['start_year']} - {values['current_year']}"
        if values["start_year"] != values["current_year"]
        else f"{values['current_year']}"
    )

    return project, template, commented, license, files, copyright, years


def add_file_header(
    copyright: str, license: str, years: str, file: str, template: str, commented: bool
) -> tuple:
    """Add the license header to the file.

    Parameters
    ----------
    copyright: str
        The copyright line for the license header. For example,
        "ANSYS, Inc. and/or its affiliates."
    license: str
        The license for the license header. For example, "MIT".
    years: str
        The year span in the license header. For example, "2024" or "2023 - 2024".
    file: str
        The file path to add the license header to.
    template: str
        The template to use for the license header. For example, "ansys.jinja2".
    commented: bool
        Whether the template is commented or not.
    """
    reuse_info = get_reuse_info(
        copyrights=copyright,
        licenses=license,
        copyright_prefix="string-c",
        year=years,
        contributors="",
    )

    add_header_to_file(
        path=file,
        reuse_info=reuse_info,
        template=template,
        template_is_commented=commented,
        style=f"{get_comment_style(file).SHORTHAND}",
        merge_copyrights=True,
        out=sys.stdout,
    )


def non_recursive_file_check(
    changed_headers: int, obj: common.ClickObj, values: dict, args: argparse.Namespace
) -> int:
    """
    Check if the committed file is missing its header.

    Parameters
    ----------
    changed_headers: int
        ``0`` if no headers were added or updated.
        ``1`` if headers were added or updated.
    obj: common.ClickObj
        A click object used in `REUSE <https://reuse.software/>`_ to annotate files.
    values: dict
        Dictionary containing the values of files, copyright,
        template, license, changed_headers, year, and git_repo.
    args: argparse.Namespace
        Namespace of arguments with their values.

    Returns
    -------
    int
        ``0`` if all files contain headers and are up to date.
        ``1`` if ``REUSE`` changed all noncompliant files.
    """
    project, template, commented, license, pre_commit_files, copyright, years = set_variables(
        obj, values, args
    )

    for file in pre_commit_files:
        # Get the reuse information of the file
        file_reuse_info = project.reuse_info_of(file)

        # If the file is empty or does not contain reuse information
        if (not file_reuse_info) or (os.path.getsize(file) == 0):
            changed_headers = 1
            add_file_header(copyright, license, years, file, template, commented)
        elif file_reuse_info:
            # license = [] if the file header already contains SPDX-License-Identifier
            # This prevents SPDX-License-Identifier from being added twice
            license = []

            # Save current copy of file
            before_hook = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(file, before_hook)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                add_file_header(copyright, license, years, file, template, commented)

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


def recursive_file_check(
    changed_headers: int, obj: common.ClickObj, values: dict, args: argparse.Namespace, count: int
) -> int:
    """Check if the committed file is missing its header.

    Parameters
    ----------
    changed_headers: int
        ``0`` if no headers were added or updated.
        ``1`` if headers were added or updated.
    obj: common.ClickObj
        A click object used in `REUSE <https://reuse.software/>`_ to annotate files.
    values: dict
        Dictionary containing the values of files, copyright,
        template, license, changed_headers, year, and git_repo.
    args: argparse.Namespace
        Namespace of arguments with their values.
    count: int
        Integer of the location in the files array.

    Returns
    -------
    int
        ``0`` if all files contain headers and are up to date.
        ``1`` if ``REUSE`` changed all noncompliant files.
    """
    project, template, commented, license, pre_commit_files, copyright, years = set_variables(
        obj, values, args
    )

    if count < len(pre_commit_files):
        # Get the file name at count from pre_commit_files
        file = pre_commit_files[count]
        # Get the reuse information of the file
        file_reuse_info = project.reuse_info_of(file)

        if (not file_reuse_info) or (os.path.getsize(file) == 0):
            changed_headers = 1
            add_file_header(copyright, license, years, file, template, commented)

            # Check if the next file is in missing_headers
            return recursive_file_check(changed_headers, obj, values, args, count + 1)
        elif file_reuse_info:
            # license = [] if the file header already contains SPDX-License-Identifier
            # This prevents SPDX-License-Identifier from being added twice
            license = []

            # Save current copy of file
            before_hook = NamedTemporaryFile(mode="w", delete=False).name
            shutil.copyfile(file, before_hook)

            # Update the header
            # tmp captures the stdout of the header.run() function
            with NamedTemporaryFile(mode="w", delete=True) as tmp:
                add_file_header(copyright, license, years, file, template, commented)

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

            return recursive_file_check(changed_headers, obj, values, args, count + 1)

    return changed_headers


def check_same_content(before_hook: str, after_hook: str) -> bool:
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
    found_reuse_info = False

    before_hook_file = pathlib.Path(before_hook).open(encoding="utf-8", newline="", mode="r")
    before_hook_lines = before_hook_file.readlines()

    after_hook_file = pathlib.Path(after_hook).open(encoding="utf-8", newline="", mode="r")
    after_hook_lines = after_hook_file.readlines()

    with pathlib.Path(after_hook).open(encoding="utf-8", newline="", mode="w") as file:
        # Copy file content before add-license-header was run into
        # the file after add-license-header was run.
        for line in after_hook_lines:
            # Copy the new reuse lines into the file
            if extract.contains_reuse_info(line):
                count += 1
                found_reuse_info = True
                file.write(line)
            else:
                if found_reuse_info:
                    try:
                        # Check the lines after the reuse info are the same
                        # If not, print the line after the reuse info
                        # This happens when a comment changes from one line to
                        # multiline
                        if line != before_hook_lines[count]:
                            file.write(line)
                    except IndexError:
                        pass

                    # Copy the rest of the file after the reuse information
                    for line_after_reuse_info in before_hook_lines[count:]:
                        file.write(line_after_reuse_info)
                    break
                # Copy the header lines before reuse information is found
                else:
                    count += 1
                    file.write(line)


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


def update_year_range(
    user_start_year: str, match_start_year: str, current_year: str, match_end_year: str
) -> tuple:
    """Update the year or year range in the LICENSE file.

    Parameters
    ----------
    user_start_year: str
       The start year supplied by the user in the pre-commit hook configuration.
    match_start_year: str
        The start year of the year range in the LICENSE file. For example, the LICENSE file
        contains the range "2023 - 2024", so match_start_year is 2023.
    current_year: str
        The current year based on the datetime module.
    match_end_year: str
        The end year of the year range in the LICENSE file. For example, the LICENSE file
        contains the range "2023 - 2024", so match_end_year is 2024.

    Returns
    -------
    tuple
        Tuple containing the updated start and end years.
    """
    # If the user start year from the pre-commit hook is less than the match start year,
    # set the match_start_year as the user_start_year
    if user_start_year < match_start_year:
        match_start_year = user_start_year
    # If the match end year is less than the current year, set the match_end_year to the
    # current year
    if match_end_year < current_year:
        match_end_year = current_year

    return match_start_year, match_end_year


def update_license_file(arg_dict: dict) -> int:
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

    user_start_year = str(arg_dict["start_year"])
    current_year = str(arg_dict["current_year"])
    # Span or single year
    year_regex = r"(\d{4}) - (\d{4})|\d{4}"

    # Check if custom_license is MIT
    if os.path.isfile(repo_license_loc) and (arg_dict["license"] == DEFAULT_LICENSE):
        with pathlib.Path(repo_license_loc).open(encoding="utf-8", newline="", mode="r") as file:
            lines = file.readlines()
            content = "".join(lines)

        # Get the first instance of the year range, either one year or a range of years
        year_range_match = re.search(year_regex, content)
        # Get the group from the year_range_match
        year_range = year_range_match.group()
        updated_year_range = ""

        # Fix the start and end years in the range
        if "-" in year_range:
            match_start_yr, match_end_yr = update_year_range(
                user_start_year, year_range_match.group(1), current_year, year_range_match.group(2)
            )
        else:
            match_start_yr, match_end_yr = update_year_range(
                user_start_year, year_range, current_year, year_range
            )

        # Update the content if the start and end years are different
        if match_start_yr != match_end_yr:
            updated_year_range = f"{match_start_yr} - {match_end_yr}"
            # print(f"Replacing {year_range} with {updated_year_range}")
            content = re.sub(year_regex, updated_year_range, content)

            with pathlib.Path(repo_license_loc).open(
                encoding="utf-8", newline="", mode="w"
            ) as file:
                file.write(content)

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


def run_hook() -> int:
    """
    Add and update file headers with `REUSE <https://reuse.software/>`_.

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

    # Link the default template and/or license from the assets folder to your git repo.
    link_assets(assets, os_git_root, args)

    # Create click object for the project
    obj = common.ClickObj(git_root)

    # Add or update headers of required files.
    # Return 1 if files were added or updated, and return 0 if no files were altered.
    if len(values["files"]) <= (sys.getrecursionlimit() - 2):
        file_return_code = recursive_file_check(changed_headers, obj, values, args, 0)
    else:
        file_return_code = non_recursive_file_check(changed_headers, obj, values, args)

    # Unlink default files & remove .reuse and LICENSES folders if empty
    cleanup(assets, os_git_root)

    # Returns 1 if REUSE changes noncompliant files or the year was updated in LICENSE
    # Returns 0 if all files are compliant
    return 1 if (license_return_code or file_return_code) == 1 else 0


def main():
    """Add and update file headers with `REUSE <https://reuse.software/>`_."""
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
