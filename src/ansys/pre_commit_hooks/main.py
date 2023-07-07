#!/usr/bin/env python
"""Run reuse for files missing license headers."""
import datetime
import os
import os.path
import subprocess

from reuse import lint
from reuse.project import Project
from reuse.report import ProjectReport


def get_files():
    """Generate report containing files without the license header."""
    project = Project("./")
    report = ProjectReport.generate(project)
    return lint.lint_files_without_copyright_and_licensing(report)


def run_reuse(file):
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
    subprocess.check_call(cmd)


def main():
    """Run reuse on files without license headers."""
    # Run reuse lint command to find files without license header
    missing_header = get_files()

    # Run reuse command for files without license header
    for file in missing_header:
        if os.path.isfile(file):
            run_reuse(file)


if __name__ == "__main__":
    main()
