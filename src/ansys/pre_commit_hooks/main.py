#!/usr/bin/env python
"""Run reuse for files missing license headers."""
import argparse
import datetime
import os
import subprocess
import sys

from reuse import lint
from reuse.project import Project
from reuse.report import ProjectReport


def get_args(args):
    """Retrieve all arguments passed in by the user."""
    parser = argparse.ArgumentParser(description="Get repository location.")
    parser.add_argument("--loc", type=str, required=True, help="Path to repository location")
    return parser.parse_args(args)


def get_loc(args):
    """Retrieve value of --loc argument."""
    loc = get_args(args).loc
    return loc


def get_files(loc):
    """Generate report containing files without the license header."""
    project = Project(loc)
    report = ProjectReport.generate(project)
    f = open(os.path.join(loc, "tmp"), "w")
    output = lint.lint_files_without_copyright_and_licensing(report, f)
    f.close()
    os.remove(os.path.join(loc, "tmp"))
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

    if missing_header != set():
        # Run reuse command for files without license header
        for file in missing_header:
            print(file)
            if os.path.isfile(file):
                run_reuse_cmd(file)
        return 1

    # Return zero if all files have license header
    return 0


def main():
    """Run reuse on files without license headers."""
    # Get repository location argument
    loc = get_loc([sys.argv[1]])
    return run_reuse_on_files(loc)


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
