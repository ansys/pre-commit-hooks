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
import filecmp
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

    AUTHORS = "AUTHORS"
    CODE_OF_CONDUCT = "CODE_OF_CONDUCT.md"
    CONTRIBUTING = "CONTRIBUTING.md"
    CONTRIBUTORS = "CONTRIBUTORS.md"
    LICENSE = "LICENSE"
    README = "README"
    DEPENDABOT = "dependabot.yml"


class Directories(Enum):
    """Enum of directories to check."""

    GITHUB = ".github"
    DOC = "doc"
    SRC = "src"
    TESTS = "tests"


def check_dirs_exist(repo_path: str, is_compliant: bool, directories: list) -> bool:
    """
    Check folders exist in the root of the git repository.

    Parameters
    ----------
    repo_path: str
        Path of the repository being checked.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    directories: list
        List of directories to check if they exist in the repository.

    Returns
    -------
    bool
        ``True`` if all directories exist.
        ``False`` if a directory did not exist and was created.
    """
    # For each folder, check if it exists in the repository
    for dirs in directories:
        full_path = repo_path / dirs
        # If the directory does not exist, create it
        if not pathlib.Path.exists(full_path):
            is_compliant = False
            print(f'The "{dirs}" directory does not exist. Creating the "{dirs}" directory...')
            pathlib.Path.mkdir(full_path)

    # Print space after last failure message to break up sections
    if not is_compliant:
        print("")

    return is_compliant


def check_config_file(
    repo_path: str,
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
    non_compliant_name: bool,
) -> bool:
    """
    Check naming convention, version, author, and maintainer information.

    Parameters
    ----------
    repo_path: str
        Path of the repository being checked.
    author_maint_name: str
        Project author and maintainer's name.
    author_maint_email: str
        Project author and maintainer's email.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    non_compliant_name: bool
        ``True`` if the repository's name is not in the form ansys-*-* and it is permitted.
        ``False`` if the repository's name is in the form ansys-*-*.

    Returns
    -------
    bool
        ``True`` if all files exist and contain the correct content.
        ``False`` if a file was created or did not contain the correct content.
    """
    has_pyproject = (repo_path / "pyproject.toml").exists()
    has_setup = (repo_path / "setup.py").exists()

    # If pyproject.toml and setup.py exist or only setup.py exists, check setup.py
    if (has_pyproject and has_setup) or (has_setup and not has_pyproject):
        config_file = "setuptools"
        # Check setup.py information
        is_compliant, project_name = check_setup_py(
            author_maint_name, author_maint_email, is_compliant
        )
    # If pyproject.toml exists and not setup.py
    elif has_pyproject and not has_setup:
        config_file = "pyproject"
        # Check pyproject.toml information
        is_compliant, project_name = check_pyproject_toml(
            repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    else:
        # Ignore config file check
        config_file = ""
        project_name = ""
        print("The pyproject.toml and setup.py files do not exist")
        print("Cannot get the author and maintainer name and email, project name, and version\n")

    # Returns True if file is complaint or False if it is not compliant,
    # the name of the project from the configuration file, and the type
    # of configuration file found in the repository
    return is_compliant, project_name, config_file


def check_pyproject_toml(
    repo_path: str,
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
    non_compliant_name: bool,
) -> tuple:
    """
    Check pyproject.toml file for correct naming convention, version, author, and maintainer.

    Parameters
    ----------
    repo_path: str
        Path of the repository being checked.
    author_maint_name: str
        Project author and maintainer's name.
    author_maint_email: str
        Project author and maintainer's email.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    non_compliant_name: bool
        ``True`` if the repository's name is not in the form ansys-*-* and it is permitted.
        ``False`` if the repository's name is in the form ansys-*-*.

    Returns
    -------
    bool
        ``True`` if the pyproject.toml file's information was correct.
        ``False`` if the pyproject.toml file had missing or incorrect information.
    str
        Name of the project from the pyproject.toml file.
    """
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
                if not bool(re.match(r"^[0-9]+.[0-9]+.dev[0-9]+$", project_version)):
                    is_compliant = False
                    print("Project version does not follow semantic versioning")

        # Check the project author and maintainer names and emails match argument input
        category, metadata = ["authors", "maintainers"], ["name", "email"]
        output = list(product(category, metadata))

        for key, value in output:
            # "DNE" is printed when the key does not exist
            project_value = project.get(key, "DNE")[0].get(value, "DNE")
            if project_value == "DNE":
                is_compliant = False
                # For example: "Project author name does not exist ..."
                print(f"Project {key} {value} does not exist in the pyproject.toml file")
            else:
                if value == "email":
                    is_compliant = check_auth_maint(
                        project_value, author_maint_email, f"{key} {value}", is_compliant
                    )
                elif value == "name":
                    is_compliant = check_auth_maint(
                        project_value, author_maint_name, f"{key} {value}", is_compliant
                    )

    return is_compliant, name


def check_auth_maint(project_value: str, arg_value: str, err_string: str, is_compliant: bool):
    """
    Check if the author and maintainer names and emails are the same.

    Parameters
    ----------
    project_value: str
        The author or maintainer's name or email retrieved from the pyproject.toml file.
    arg_value: str
        The author or maintainer's name or email retrieved from the argument passed into the hook.
    err_str: str
        The message that is printed when an author or maintainer's name or email is incorrect.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.

    Returns
    -------
    bool
        ``True`` if the author and maintainer's name and email are correct.
        ``False`` if the author or maintainer's name or email is incorrect.
    """
    # If the author or maintainer name or email does not match the
    # --author_maint_name or --author_maint_email arguments, it is not compliant
    if project_value != arg_value:
        print(f"Project {err_string} is not {arg_value}")
        is_compliant = False

    return is_compliant


def check_setup_py(
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
) -> tuple:
    """
    Check setup.py file for correct naming convention, version, author, and maintainer.

    Parameters
    ----------
    author_maint_name: str
        Project author and maintainer's name.
    author_maint_email: str
        Project author and maintainer's email.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.

    Returns
    -------
    bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    str
        An empty string since the setup.py check is not implemented.
    """
    # Print message about the setup.py check not being implemented
    print("The setup.py check is not implemented. Please manually check the following:")
    print("- The project name is ansys-*-*")
    print("- The project uses semantic versioning (see https://semver.org/)")
    print(f"- The author and maintainer name is {author_maint_name}")
    print(f"- The author and maintainer email is {author_maint_email}\n")

    return is_compliant, ""


def download_license_json(url: str, json_file: str) -> bool:
    """
    Download the licenses.json file and restructure it to only include the license ID and name.

    Parameters
    ----------
    url: str
        The URL to the licenses.json file that is downloaded.
    json_file: str
        The path of the json_file to be written to and updated.

    Returns
    -------
    bool
        ``True`` if the license file was downloaded and updated.
        ``False`` if there was an issue downloading the license file.
    """
    # If the licenses.json file does not exist in the hook's folder
    if not pathlib.Path.exists(json_file):
        # Download licenses.json
        r = requests.get(url, timeout=60)
        status_code = r.status_code
        if status_code == 200:
            # If it was successfully downloaded, write content to file
            with open(json_file, "w", encoding="utf-8") as f:
                f.write(r.text)

            # Restructure json file to use "licenseID: name"
            restructure_json(json_file)
        else:
            print("There was a problem downloading license.json. Skipping LICENSE content check")
            return False

    return True


def restructure_json(file: str):
    """
    Remove extra information from licenses.json file.

    Parameters
    ----------
    file: str
        The path of the json_file to be updated.
    """
    licenseid_name_dict = {}

    # Open the licenses.json file
    with open(file, "r", encoding="utf-8") as json_file:
        existing_json = json.load(json_file)

        for license in existing_json["licenses"]:
            # If the license is not deprecated, add it to the dictionary
            if not license["isDeprecatedLicenseId"]:
                # { "MIT": "MIT License", ... }
                licenseid_name_dict[license["licenseId"]] = license["name"]

    # Overwrite json file with the dictionary
    with open(file, "w") as json_file:
        json_file.write(json.dumps(licenseid_name_dict, indent=4))


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
) -> bool:
    """
    Check files exist. If they do not exist, create them using jinja templates.

    Parameters
    ----------
    repo_path: str
        Path of the repository being checked.
    files: list
        List of files to check if they exist and their content.
    project_name: str
        The name of the project.
    start_year: str
        The start year of the repository.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    license: str
        The license the repository uses.
    repository_url: str
        The URL of the repository.
    product: str
        The Ansys product the repository is based on.
    config_file: str
        If the project's config file is "setuptools" or "pyproject".
    doc_repo_name: str
        The name of the repository to use in documentation.

    Returns
    -------
    bool
        ``True`` if the files exist and content was correct.
        ``False`` if a file was created and/or its content was incorrect.
    """
    # The range of years for the LICENSE file
    year_str = (
        start_year if start_year == DEFAULT_START_YEAR else f"{start_year} - {DEFAULT_START_YEAR}"
    )
    # Dictionary of internal page references for the technical review
    ref_dict = {
        "AUTHORS": "the-authors-file",
        "CODE_OF_CONDUCT.md": "the-code-of-conduct-md-file",
        "CONTRIBUTING.md": "the-contributing-md-file",
        "CONTRIBUTORS.md": "the-contributors-md-file",
        "LICENSE": "the-license-file",
        "README.rst": "the-readme-file",
        "README.md": "the-readme-file",
    }

    # Check if each file exists. If not, generate the file from the template.
    # Check the content of the LICENSE and CONTRIBUTORS.md files as well
    for file in files:
        if "dependabot" in file:
            repo_file_path = repo_path / ".github" / file
        else:
            if "README" in file:
                if pathlib.Path.exists(repo_path / f"{file}.md"):
                    file = f"{file}.md"
                else:
                    file = f"{file}.rst"

            # Get the full path of the file in the repository
            repo_file_path = repo_path / file

        # Generate file content from corresponding template file
        file_content = generate_file_from_jinja(
            file, project_name, year_str, repository_url, product, config_file, doc_repo_name
        )

        if "AUTHORS" in file:
            if pathlib.Path.exists(repo_path / f"{file}.md"):
                repo_file_path = repo_path / f"{file}.md"

        # If the path does not exist
        if not pathlib.Path.exists(repo_file_path):
            is_compliant = False
            dne_message = f"{file} does not exist. Creating file from template..."
            if "setuptools" in config_file:
                # Dependabot template only requires config_file, so we can make
                # the template
                if "dependabot" in file:
                    write_content(dne_message, repo_file_path, file_content)
                else:
                    # Print directions to manually review configuration file information
                    tech_review_docs = (
                        f"https://dev.docs.pyansys.com/packaging/structure.html#{ref_dict[file]}"
                    )
                    print(f"{file} does not exist. Please see {tech_review_docs}")
            else:
                if "README" in file and product is None:
                    print("The --product argument is required to generate the README file.")
                elif "README" in file and project_name == "":
                    print("The project_name is required to generate the README file.")
                elif "dependabot" in file and config_file == "":
                    print("The config_file type is required to generate the dependabot.yml file.")
                elif "AUTHORS" in file and project_name == "":
                    print("The project_name is required to generate the AUTHORS file.")
                else:
                    # Create the file and write template content to it
                    write_content(dne_message, repo_file_path, file_content)
        else:
            # Check the content of CONTRIBUTORS.md and LICENSE files
            if file in (Filenames.CONTRIBUTORS.value, Filenames.LICENSE.value):
                is_compliant = check_file_content(
                    repo_file_path, file_content, is_compliant, license
                )

    return is_compliant


def generate_file_from_jinja(
    file: str,
    project_name: str,
    year_str: str,
    repo_url: str,
    product: str,
    config_file: str,
    doc_repo_name: str,
) -> str:
    """
    Generate file using jinja templates.

    Parameters
    ----------
    file: str
        The file that the template is being created for.
    project_name: str
        The name of the project.
    year_str: str
        The start year of the repository.
    repo_url: str
        The URL of the repository.
    product: str
        The Ansys product the repository is based on.
    config_file: str
        If the project's config file is "setuptools" or "pyproject".
    doc_repo_name: str
        The name of the repository to use in documentation.

    Returns
    -------
    str
        Content of the template that was generated.
    """
    # Load the templates from the hook path
    loader = FileSystemLoader(searchpath=pathlib.PurePath.joinpath(HOOK_PATH, "templates"))
    env = Environment(loader=loader)  # nosec
    # Get the template for the specified file
    template = env.get_template(file)
    # Generate the file content from the template
    file_content = template.render(
        doc_repo_name=doc_repo_name,  # pymechanical
        project_name=project_name,  # ansys-mechanical-core
        year_span=year_str,  # 2022 - 2024
        repository_url=repo_url,  # https://github.com/ansys/pymechanical
        product=product,  # mechanical
        config_file=config_file,  # pyproject
    )

    return file_content


def write_content(message: str, file_path: str, file_content: str):
    """
    Write generated content from jinja template to a file.

    Parameters
    ----------
    message: str
        The message that details which file is being created.
    file_path: str
        The path of the file to write the content to.
    file_content: str
        The file content that was generated from the jinja templates.
    """
    # Print the message saying the file is not compliant, so the file is being generated
    print(message)

    # Create the missing file using jinja templates
    with open(file_path, "w") as f:
        f.write(file_content)


def check_file_content(file: str, generated_content: str, is_compliant: bool, license: str) -> bool:
    """
    Check the file content of the LICENSE and CONTRIBUTORS.md files.

    Parameters
    ----------
    file: str
        The file that the template is being created for.
    generated_content: str
        Content of the template that was generated.
    is_compliant: bool
        ``True`` if the repository is compliant.
        ``False`` if the repository is not compliant.
    license: str
        The license the repository uses.

    Returns
    -------
    bool
        ``True`` if LICENSE and CONTRIBUTORS.md files had the correct content.
        ``False`` if LICENSE and CONTRIBUTORS.md files had the incorrect content.
    """
    # Save generated file content for comparing the current CONTRIBUTORS.md file with the template
    generated_file = NamedTemporaryFile(mode="w", delete=False).name
    with open(generated_file, "w") as f:
        f.write(generated_content)

    same_files = True if filecmp.cmp(file, generated_file, shallow=False) == True else False

    # Check if CONTRIBUTORS.md content has been changed from template
    if file.name in Filenames.CONTRIBUTORS.value and same_files:
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
                # license_json["MIT"] = "MIT License"
                license_full_name = license_json[license]

            with open(file, "r") as license:
                for line in license:
                    # Check if "MIT License" is in the LICENSE file
                    if license_full_name in line:
                        license_line_found = True
                        break

            # If the license line wasn't found in LICENSE, it is not compliant
            if not license_line_found:
                is_compliant = False
                print(
                    f'"The {Filenames.LICENSE.value} file content is missing "{license_full_name}"'
                )

    return is_compliant


def main():
    """Check files for technical review."""
    parser = argparse.ArgumentParser()
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
    # Get the license the repository uses
    parser.add_argument(
        "--license", type=str, help="License that the repository uses.", default=DEFAULT_LICENSE
    )
    # Get the Ansys product that the repository is related to
    parser.add_argument(
        "--product", type=str, help="Ansys product that the repository is related to."
    )
    # Get the repository URL
    parser.add_argument(
        "--url",
        type=str,
        help="The repository URL. For example, https://github.com/ansys/pymechanical",
    )
    # Whether or not the project name is intentionally non-compliant
    # non_compliant_name is by default False when action="store_true"
    parser.add_argument("--non_compliant_name", action="store_true")

    # Parse arguments
    args = parser.parse_args()
    author_maint_name = args.author_maint_name
    author_maint_email = args.author_maint_email
    non_compliant_name = args.non_compliant_name
    license = args.license
    product = args.product
    repository_url = args.url

    # is_complaint is `True` when all files are compliant and
    # `False` when a file is missing or its content is incorrect
    is_compliant = True

    # Get current git repository
    git_repo = git.Repo(pathlib.Path.cwd(), search_parent_directories=True)
    repo_path = pathlib.Path(git_repo.git.rev_parse("--show-toplevel"))

    # Get dates of commits from earliest to most recent
    g = git.Git(pathlib.Path.cwd())
    all_dates = g.log("--reverse", r"--format=%ci")
    # Get year of first commit
    start_year = int(all_dates[0:4])

    # Get a list of directories to check
    directories = [directory.value for directory in Directories]
    # Check directories exist
    is_compliant = check_dirs_exist(repo_path, is_compliant, directories)

    # Check configuration file information is correct
    is_compliant, project_name, config_file = check_config_file(
        repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )

    # Get a list of files to check
    check_exists_list = [file.value for file in Filenames]
    # Name of the repository
    doc_repo_name = repo_path.name
    if not repository_url:
        repository_url = f"https://github.com/ansys/{doc_repo_name}"

    # Check files exist and if not, create them using jinja templates
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

    # Returns 1 if there were one or more non-compliant files.
    # Returns 0 if the repository is compliant.
    return 0 if is_compliant else 1


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
