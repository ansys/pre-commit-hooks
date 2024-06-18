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
from enum import Enum
from itertools import product
import json
import os
import pathlib
import re
from tempfile import NamedTemporaryFile

import git
from jinja2 import Environment, FileSystemLoader
import requests
import semver
import toml

from ansys.pre_commit_hooks.add_license_headers import check_same_content

# Get current git repository
git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = pathlib.Path(git_repo.git.rev_parse("--show-toplevel"))
"""Default repository path."""
DOC_REPO_NAME = REPO_PATH.name
"""Name of the repository."""
HOOK_PATH = pathlib.Path(__file__).parent.resolve()
"""Location of the pre-commit hook on your system."""
LICENSES_JSON = HOOK_PATH / "assets" / "licenses.json"
"""JSON file containing licenses information."""
DEFAULT_AUTHOR_MAINT_NAME = "ANSYS, Inc."
"""Default name of project authors and maintainers."""
DEFAULT_AUTHOR_MAINT_EMAIL = "pyansys.core@ansys.com"
"""Default email of project authors and maintainers."""
DEFAULT_START_YEAR = dt.today().year
"""Default start year of the repository."""
DEFAULT_LICENSE = "MIT"
"""Default license of the repository"""


class Filenames(Enum):
    """Enum of files to check."""

    AUTHORS = "AUTHORS.md"
    CONTRIBUTING = "CONTRIBUTING.md"
    CONTRIBUTORS = "CONTRIBUTORS.md"
    LICENSE = "LICENSE"
    README = "README.rst" | "README.md"


def check_config_file(author_maint_name, author_maint_email, is_compliant, non_compliant_name):
    """Check naming convention, version, author, and maintainer information."""
    # Is zero when the configuration file is compliant and one when it is not compliant
    has_pyproject = (REPO_PATH / "pyproject.toml").exists()
    has_setup = (REPO_PATH / "setup.py").exists()
    if has_pyproject:
        is_compliant, project_name = check_pyproject_toml(
            author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    elif has_setup:
        is_compliant, project_name = check_setup_py(
            author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    else:
        print("pyproject.toml and setup.py files do not exist")
        project_name = None

    # Returns 0 if file is complaint or 1 if it is not compliant
    return is_compliant, project_name


def check_pyproject_toml(
    author_maint_name, author_maint_email, is_compliant, non_compliant_name
) -> int:
    """Check pyproject.toml file for correct naming convention, version, author, and maintainer."""
    # Load pyproject.toml
    with open(REPO_PATH / "pyproject.toml", "r") as project_file:
        config = toml.load(project_file)
        project = config.get("project")

        # Check the project name follows naming conventions: ansys-{product}-{library}
        # Ignore this check if non_compliant_name argument is True
        if not non_compliant_name:
            name = project.get("name", "DNE")
            if (name == "DNE") or (
                (name != "DNE") and not bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name))
            ):
                is_compliant = False
                print("Project name does not follow naming conventions")

        # Check the project version follows Semantic versioning
        project_version = project.get("version", "DNE")
        if project_version != "DNE":
            try:
                version = semver.Version.parse(project_version)
            except ValueError:
                is_compliant = False
                print("Project version does not follow semantic versioning")

        # Check the project author and maintainer names and emails match argument input
        category, metadata = ["authors", "maintainers"], ["name", "email"]
        # [('authors', 'name'), ('authors', 'email'), ('maintainers', 'name'),
        # ('maintainers', 'email')]
        output = list(product(category, metadata))

        for combo in output:
            # project.get("authors", "DNE")[0].get("name", "DNE")
            # "DNE" is printed when the key does not exist
            project_value = project.get(combo[0], "DNE")[0].get(combo[1], "DNE")
            if project_value == "DNE":
                print(f"Project {combo[0]} {combo[1]} does not exist in the pyproject.toml file")
            else:
                if combo[1] == "email":
                    is_compliant = check_auth_maint(
                        project_value, author_maint_email, f"{combo[0]} {combo[1]}"
                    )
                elif combo[1] == "name":
                    is_compliant = check_auth_maint(
                        project_value, author_maint_name, f"{combo[0]} {combo[1]}"
                    )

    return is_compliant, name


def check_auth_maint(project_value, arg_value, err_string):
    """Check if the author and maintainer names and emails are the same."""
    if project_value not in arg_value:
        print(f"Project {err_string} is not {arg_value}")
        return False


def check_setup_py(author_maint_name: str, author_maint_email: str, non_compliant: int):
    """Check setup.py file for correct naming convention, version, author, and maintainer."""
    print("Not implemented")


def download_license_json(url: str):
    """Download the licenses.json file and update it if release dates are different."""
    if not os.path.exists(LICENSES_JSON):
        r = requests.get(url)
        status_code = r.status_code
        if status_code == 200:
            with open(LICENSES_JSON, "w") as f:
                f.write(r.text)

            restructure_json(LICENSES_JSON)


def restructure_json(file):
    """Remove extra information from licenses.json file."""
    licenseId_name_dict = {}

    with open(file, "r", encoding="utf-8") as json_file:
        existing_json = json.load(json_file)

        for license in existing_json["licenses"]:
            if not license["isDeprecatedLicenseId"]:
                licenseId_name_dict[license["licenseId"]] = license["name"]

    with open(file, "w") as json_file:
        json_file.write(json.dumps(licenseId_name_dict, indent=4))


def check_file_exists(
    files: list, project_name: str, start_year: str, is_compliant: bool, license: str
) -> int:
    """Check files exist. If they do not exist, create them using jinja templates."""
    # check if there is a readme (markdown or rst)
    year_str = (
        start_year if start_year == DEFAULT_START_YEAR else f"{start_year} - {DEFAULT_START_YEAR}"
    )

    for file in files:
        repo_file_path = REPO_PATH / file
        file_content = generate_file_from_jinja(file, project_name, year_str)

        if not os.path.exists(repo_file_path):
            is_compliant = False
            print(f"{file} does not exist. Creating file from template...")

            # Create the missing file using jinja templates
            with open(repo_file_path, "w") as f:
                f.write(file_content)
        else:
            # Check content
            if file in (Filenames.CONTRIBUTORS, Filenames.LICENSE):
                is_compliant = check_file_content(
                    repo_file_path, file_content, is_compliant, license
                )

    return is_compliant


def generate_file_from_jinja(file, project_name, year_str):
    """Generate file using jinja templates."""
    loader = FileSystemLoader(searchpath=os.path.join(HOOK_PATH, "templates"))
    env = Environment(loader=loader)
    template = env.get_template(file)
    file_content = template.render(
        doc_repo_name=DOC_REPO_NAME, project_name=project_name, year_span=year_str
    )

    return file_content


def check_file_content(file, generated_content, is_compliant, license):
    """Check file content."""
    generated_file = NamedTemporaryFile(mode="w", delete=False).name
    with open(generated_file, "w") as f:
        f.write(generated_content)

    # Check if CONTRIBUTORS.md content has been changed from template
    if file in Filenames.CONTRIBUTORS and check_same_content(file, generated_file):
        is_compliant = False
        print("Please update your CONTRIBUTORS.md file.")
    # Check if the license phrase is in LICENSE (by default, MIT)
    elif file in Filenames.LICENSE:
        license_line_found = False
        with open(LICENSES_JSON, "r") as f:
            license_json = json.load(f)
            license_full_name = license_json[license]

        with open(file, "r") as license:
            for line in license:
                if license_full_name in line:
                    license_line_found = True
                    break

        # If the license line wasn't found in LICENSE, it is not compliant
        if not license_line_found:
            is_compliant = False
            print(f"The {Filenames.LICENSE} file content is missing {license_full_name}")

    return is_compliant


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
    # Whether or not the project name is intentionally non-compliant
    # non_compliant_name is by default False when action="store_true"
    parser.add_argument("--non_compliant_name", action="store_true")

    args = parser.parse_args()
    author_maint_name = args.author_maint_name
    author_maint_email = args.author_maint_email
    start_year = args.start_year
    non_compliant_name = args.non_compliant_name
    license = args.license

    # ["AUTHORS.md", "CONTRIBUTING.md", "CONTRIBUTORS.md", "LICENSE", "README"]
    check_exists_list = [file.value for file in Filenames]
    json_url = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"

    is_compliant = True
    is_compliant, project_name = check_config_file(
        author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )
    download_license_json(json_url)
    is_compliant = check_file_exists(check_exists_list, project_name, start_year, license)

    # Return 1 if there were one or more non-compliant files.
    return 0 if is_compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
