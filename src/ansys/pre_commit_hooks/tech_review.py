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
"""Module for checking if a repository is compliant with required files in the technical review."""
import argparse
from datetime import date as dt
import os
import pathlib
import re

# import shutil
from tempfile import NamedTemporaryFile

import git
from jinja2 import Environment, FileSystemLoader

# from reuse._licenses import _load_license_list
import toml

from ansys.pre_commit_hooks.add_license_headers import check_same_content

# Get current git repository
git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = git_repo.git.rev_parse("--show-toplevel")
"""Default repository path."""
DOC_REPO_NAME = os.path.basename(REPO_PATH)
"""Name of the repository."""
HOOK_PATH = pathlib.Path(__file__).parent.resolve()
"""Location of the pre-commit hook on your system."""
LICENSES_JSON = os.path.join(HOOK_PATH, "..", "reuse", "resources", "licenses.json")
"""JSON file containing licenses information."""
DEFAULT_AUTHOR_MAINT_NAME = "ANSYS, Inc."
"""Default name of project authors and maintainers."""
DEFAULT_AUTHOR_MAINT_EMAIL = "pyansys.core@ansys.com"
"""Default email of project authors and maintainers."""
DEFAULT_START_YEAR = dt.today().year
"""Default start year of the repository."""
DEFAULT_LICENSE = "MIT"
"""Default license of the repository"""


def check_config_file(author_maint_name, author_maint_email):
    """Check naming convention, version, author, and maintainer information."""
    # Is zero when the configuration file is compliant and one when it is not compliant
    non_compliant = 0

    if os.path.exists(os.path.join(REPO_PATH, "pyproject.toml")):
        non_compliant, project_name = check_pyproject_toml(
            author_maint_name, author_maint_email, non_compliant
        )
    elif os.path.exists(os.path.join(REPO_PATH, "setup.py")):
        non_compliant, project_name = check_setup_py(
            author_maint_name, author_maint_email, non_compliant
        )
    else:
        print("pyproject.toml and setup.py files do not exist")
        print("Project name does not follow naming conventions")
        print("Project version does not contain Semantic versioning")
        print("Author and maintainer is not ANSYS, Inc.")
        print("Author and maintainer email is not pyansys.core@ansys.com")
        non_compliant = 1
        project_name = None

    # Returns 0 if file is complaint or 1 if it is not compliant
    return non_compliant, project_name


# also add check for KeyError (try/except)
def check_pyproject_toml(author_maint_name, author_maint_email, non_compliant) -> int:
    """Check pyproject.toml file for correct naming convention, version, author, and maintainer."""
    # Load pyproject.toml
    with open(os.path.join(REPO_PATH, "pyproject.toml"), "r") as f:
        config = toml.load(f)

        # Check the project name follows naming conventions
        # ansys-{product}-{library}
        # ignore this check if name not compliant arg activated
        name = config["project"]["name"]
        if not bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name)):
            print("Project name does not follow naming conventions")
            non_compliant = 1

        # Check the project version follows Semantic versioning
        # accept letters in regex in minor & patch versions
        # look at semver docs for regex
        version = config["project"]["version"]
        if not bool(re.match(r"^[0-9]+.[0-9]+.[0-9]+$", version)):
            print("Project version does not follow Semantic versioning")
            non_compliant = 1

        # Check the project author and maintainer name is ANSYS, Inc.
        authors_name = config["project"]["authors"][0]["name"]
        maintainers_name = config["project"]["maintainers"][0]["name"]
        if author_maint_name not in authors_name:
            print(f"Project author name is not {author_maint_name}")
            non_compliant = 1
        elif author_maint_name not in maintainers_name:
            print(f"Project maintainer name is not {author_maint_name}")
            non_compliant = 1

        # Check the project author and maintainer email is pyansys.core@ansys.com
        authors_email = config["project"]["authors"][0]["email"]
        maintainers_email = config["project"]["maintainers"][0]["email"]
        if author_maint_email not in authors_email:
            print(f"Project author email is not {author_maint_email}")
            non_compliant = 1
        elif author_maint_email not in maintainers_email:
            print(f"Project maintainer email is not {author_maint_email}")
            non_compliant = 1

    return non_compliant, name


def check_setup_py(author_maint_name: str, author_maint_email: str, non_compliant: int):
    """Check setup.py file for correct naming convention, version, author, and maintainer."""
    print("Not implemented")


def check_file_exists(files: list, project_name: str, start_year: str) -> int:
    """Check files exist. If they do not exist, create them using jinja templates."""
    # check if there is a readme (markdown or rst)
    non_compliant = 0
    year_str = (
        start_year if start_year == DEFAULT_START_YEAR else f"{start_year} - {DEFAULT_START_YEAR}"
    )

    for file in files:
        repo_file_path = os.path.join(REPO_PATH, file)
        file_content = generate_file_from_jinja(file, project_name, year_str)

        if not os.path.exists(repo_file_path):
            non_compliant = 1
            print(f"{file} does not exist. Creating file from template...")

            # Create the missing file using jinja templates
            with open(repo_file_path, "w") as f:
                f.write(file_content)
        else:
            # Check content
            if file == ("CONTRIBUTORS.md" or "LICENSE"):
                check_file_content(repo_file_path, file_content)

    return non_compliant


def generate_file_from_jinja(file, project_name, year_str):
    """Generate file using jinja templates."""
    loader = FileSystemLoader(searchpath=os.path.join(HOOK_PATH, "templates"))
    env = Environment(loader=loader)
    template = env.get_template(file)
    file_content = template.render(
        doc_repo_name=DOC_REPO_NAME, project_name=project_name, year_span=year_str
    )

    return file_content


def check_file_content(file, generated_content):
    """Check file content."""
    non_compliant = 0

    generated_file = NamedTemporaryFile(mode="w", delete=False).name
    with open(generated_file, "w") as f:
        f.write(generated_content)

    # Check if CONTRIBUTORS.md content has been changed from template
    if file == "CONTRIBUTORS.md" and check_same_content(file, generated_file):
        print("Please update your CONTRIBUTORS.md file.")
        non_compliant = 1
    # Check if the license phrase is in LICENSE (by default, MIT)
    elif file == "LICENSE":
        with open(file, "r") as f:
            if "MIT" not in f.readline():
                print(f"MIT is not in {file}")

    return non_compliant


# check there are src/ tests/ doc/ folders in root of git repo
# verify there are no dockerfiles at the root level - should be in doc folder
# check there's a dependabot.yml file

# eventually - check the ci_cd yml file actions doc-style, code-style, etc
# run pytest, parse coverage files


def main():
    """Check files for technical review."""
    parser = argparse.ArgumentParser()
    # Get list of committed files
    parser.add_argument("files", nargs="*")
    # Get the name of the authors and maintainers of the project
    parser.add_argument(
        "--author_maint_name",
        type=str,
        help="Name of the authors and maintainers of the project.",
        default=DEFAULT_AUTHOR_MAINT_NAME,
    )
    # Get the email of the authors and maintainers of the project
    parser.add_argument(
        "--author_maint_email",
        type=str,
        help="Email of the authors and maintainers of the project.",
        default=DEFAULT_AUTHOR_MAINT_EMAIL,
    )
    # Get the start year of the repository
    parser.add_argument(
        "--start_year", type=str, help="Start year of the repository.", default=DEFAULT_START_YEAR
    )
    # Get the license the repository uses
    parser.add_argument(
        "--license", type=str, help="License that the repository uses.", default=DEFAULT_LICENSE
    )

    count = 0
    args = parser.parse_args()
    author_maint_name = args.author_maint_name
    author_maint_email = args.author_maint_email
    start_year = args.start_year

    check_exists_list = ["AUTHORS.md", "CONTRIBUTING.md", "CONTRIBUTORS.md", "LICENSE"]
    check_content_list = check_exists_list.pop(2)
    check_content_list = check_content_list.append("README.rst")

    non_compliant, project_name = check_config_file(author_maint_name, author_maint_email)
    count += non_compliant
    count += check_file_exists(check_exists_list, project_name, start_year)
    count += check_file_content(check_content_list)

    # Return 1 if there were one or more non-compliant files.
    return 1 if count >= 1 else 0


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
