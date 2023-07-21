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
import datetime
import os
import subprocess
import sys
from tempfile import NamedTemporaryFile

from reuse import lint
from reuse.project import Project
from reuse.report import ProjectReport


def get_args(args):
    """Retrieve value of --loc argument."""
    parser = argparse.ArgumentParser(description="Get repository location.")
    parser.add_argument(
        "--loc", type=str, required=True, help="Path to repository location", default="src"
    )
    return parser.parse_args(args).loc


def get_files(loc):
    """
    Generate report containing files without the license header.

    Parameters
    ----------
    loc : str
        Path to repository location.
    """
    project = Project(loc)
    report = ProjectReport.generate(project)

    with NamedTemporaryFile(mode="w") as tmp:
        output = lint.lint_files_without_copyright_and_licensing(report, tmp)

    return output


def get_files_missing_header(loc):
    """Retrieve files without license header."""
    try:
        # Run reuse lint command to find files without license header
        missing_header = get_files(loc)
        return missing_header
    except NotADirectoryError as e:  # When loc is an invalid path
        return str(e) + " for a repository"


def run_reuse_cmd(file):
    """Run the reuse command for files missing the license header."""
    year = datetime.date.today().year
    cmd = [
        "reuse",
        "annotate",
        "--year",
        rf"{year}",
        "--copyright-style",
        "string-c",
        "--merge-copyright",
        "--template=ansys",
        "-l",
        "MIT",
        "-c",
        "ANSYS, Inc. and/or its affiliates.",
        "--skip-unrecognised",
        rf"{file}",
    ]
    subprocess.check_call(cmd, stdout=subprocess.PIPE)


def run_reuse_on_files(loc):
    """Run the reuse annotate command on all files without license header."""
    missing_header = get_files_missing_header(loc)
    if missing_header:
        # Run reuse command for files without license header
        for file in missing_header:
            print(f"License header added to {file}")
            if os.path.isfile(file):
                run_reuse_cmd(file)
        return 1

    # Return zero if all files have license header
    return 0


def main():
    """Run reuse on files without license headers."""
    try:
        # Get repository location argument
        loc = get_args([sys.argv[1]])
        return run_reuse_on_files(loc)
    except IndexError as e:
        print("Please provide the --loc argument. IndexError: " + str(e))


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
