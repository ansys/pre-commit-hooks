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
import pathlib
import re
from tempfile import NamedTemporaryFile

import git
from jinja2 import Environment, FileSystemLoader
import requests
import semver
import toml

from ansys.pre_commit_hooks.add_license_headers import check_same_content

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
JSON_URL = "https://raw.githubusercontent.com/spdx/license-list-data/main/json/licenses.json"
"""URL to retrieve list of license IDs and names."""


class Filenames(Enum):
    """Enum of files to check."""

    AUTHORS = "AUTHORS.md"
    CONTRIBUTING = "CONTRIBUTING.md"
    CONTRIBUTORS = "CONTRIBUTORS.md"
    LICENSE = "LICENSE"
    README = "README.rst" or "README.md"
    DEPENDABOT = "dependabot.yml"


def check_config_file(
    repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
):
    """Check naming convention, version, author, and maintainer information."""
    # Is zero when the configuration file is compliant and one when it is not compliant
    has_pyproject = (repo_path / "pyproject.toml").exists()
    has_setup = (repo_path / "setup.py").exists()
    if has_pyproject:
        config_file = "pyproject"
        is_compliant, project_name = check_pyproject_toml(
            repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    elif has_setup:
        config_file = "setuptools"
        is_compliant, project_name = check_setup_py(
            repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    else:
        config_file = ""
        print("pyproject.toml and setup.py files do not exist")
        project_name = None

    # Returns 0 if file is complaint or 1 if it is not compliant
    return is_compliant, project_name, config_file


def check_pyproject_toml(
    repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
) -> int:
    """Check pyproject.toml file for correct naming convention, version, author, and maintainer."""
    name = ""
    # Load pyproject.toml
    with open(repo_path / "pyproject.toml", "r") as project_file:
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
                        project_value, author_maint_email, f"{combo[0]} {combo[1]}", is_compliant
                    )
                elif combo[1] == "name":
                    is_compliant = check_auth_maint(
                        project_value, author_maint_name, f"{combo[0]} {combo[1]}", is_compliant
                    )

    return is_compliant, name


def check_auth_maint(project_value, arg_value, err_string, is_compliant):
    """Check if the author and maintainer names and emails are the same."""
    if project_value not in arg_value:
        print(f"Project {err_string} is not {arg_value}")
        is_compliant = False

    return is_compliant


def check_setup_py(
    repo_path: str, author_maint_name: str, author_maint_email: str, is_compliant: bool
):
    """Check setup.py file for correct naming convention, version, author, and maintainer."""
    print("Not implemented")
    return is_compliant


def download_license_json(url: str, json_file: str):
    """Download the licenses.json file and update it if release dates are different."""
    if not pathlib.Path.exists(json_file):
        r = requests.get(url)
        status_code = r.status_code
        if status_code == 200:
            with open(json_file, "w", encoding="utf-8") as f:
                f.write(r.text)

            restructure_json(json_file)
        else:
            print("There was a problem downloading license.json. Skipping LICENSE content check")
            return False

    return True


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
    repo_path: str,
    files: list,
    project_name: str,
    start_year: str,
    is_compliant: bool,
    license: str,
    repository_url: str,
    product: str,
    config_file: str,
    doc_repo_name: str,
) -> int:
    """Check files exist. If they do not exist, create them using jinja templates."""
    year_str = (
        start_year if start_year == DEFAULT_START_YEAR else f"{start_year} - {DEFAULT_START_YEAR}"
    )

    for file in files:
        if "dependabot" in file:
            repo_file_path = repo_path / ".github" / file
        else:
            repo_file_path = repo_path / file
        file_content = generate_file_from_jinja(
            file, project_name, year_str, repository_url, product, config_file, doc_repo_name
        )

        if not pathlib.Path.exists(repo_file_path):
            is_compliant = False
            print(f"{file} does not exist. Creating file from template...")

            # Create the missing file using jinja templates
            with open(repo_file_path, "w") as f:
                f.write(file_content)
        else:
            # Check content
            if file in (Filenames.CONTRIBUTORS.value, Filenames.LICENSE.value):
                print("checking file content")
                is_compliant = check_file_content(
                    repo_file_path, file_content, is_compliant, license
                )

    return is_compliant


def generate_file_from_jinja(
    file, project_name, year_str, repo_url, product, config_file, doc_repo_name
):
    """Generate file using jinja templates."""
    loader = FileSystemLoader(searchpath=pathlib.PurePath.joinpath(HOOK_PATH, "templates"))
    env = Environment(loader=loader)
    template = env.get_template(file)
    file_content = template.render(
        doc_repo_name=doc_repo_name,  # pymechanical
        project_name=project_name,  # ansys-mechanical-core
        year_span=year_str,  # 2022 - 2024
        repository_url=repo_url,  # https://github.com/ansys/pymechanical
        product=product,  # mechanical
        config_file=config_file,  # pyproject
    )

    return file_content


def check_file_content(file, generated_content, is_compliant, license):
    """Check file content."""
    generated_file = NamedTemporaryFile(mode="w", delete=False).name
    with open(generated_file, "w") as f:
        f.write(generated_content)

    # Check if CONTRIBUTORS.md content has been changed from template
    if file.name in Filenames.CONTRIBUTORS.value and check_same_content(file, generated_file):
        is_compliant = False
        print("Please update your CONTRIBUTORS.md file.")
    # Check if the license phrase is in LICENSE (by default, MIT)
    elif file.name in Filenames.LICENSE.value:
        # Download and adjust json containing license information
        downloaded = download_license_json(JSON_URL, LICENSES_JSON)

        if downloaded:
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
                print(f"The {Filenames.LICENSE.value} file content is missing {license_full_name}")

    return is_compliant


def check_dirs_exist(repo_path, is_compliant, directories):
    """Check src, tests, and doc folders exist in the root of the git repository."""
    for dirs in directories:
        full_path = repo_path / dirs
        if not pathlib.Path.exists(full_path):
            is_compliant = False
            print(f"{dirs} does not exist")

    return is_compliant


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
    # Get the Ansys product that the repository is related to
    parser.add_argument(
        "--product", type=str, help="Ansys product that the repository is related to."
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
    product = args.product

    # Get current git repository
    git_repo = git.Repo(pathlib.Path.cwd(), search_parent_directories=True)
    repo_path = pathlib.Path(git_repo.git.rev_parse("--show-toplevel"))
    # Name of the repository
    doc_repo_name = repo_path.name

    if not product:
        print("Product argument is required to run the hook")
        return 1

    check_exists_list = [file.value for file in Filenames]
    repository_url = f"https://github.com/ansys/{doc_repo_name}"

    is_compliant = True
    # Check pyproject.toml information is correct
    is_compliant, project_name, config_file = check_config_file(
        repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )

    # Check files exist
    is_compliant = check_file_exists(
        repo_path,
        check_exists_list,
        project_name,
        start_year,
        is_compliant,
        license,
        repository_url,
        product,
        config_file,
        doc_repo_name,
    )

    # Check directories exist
    directories = [".github", "doc", "src", "tests"]
    is_compliant = check_dirs_exist(repo_path, is_compliant, directories)

    # Return 1 if there were one or more non-compliant files.
    return 0 if is_compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
