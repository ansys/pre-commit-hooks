# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Generate a PyAnsys repository quality report for the current project.

This implementation keeps the quality logic bundled in the hook repo itself so it
works in a standalone pre-commit environment without the separate
``pyansys-repo-review`` package being installed.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from datetime import date as dt
from enum import Enum
import filecmp
from io import BytesIO, StringIO
from itertools import product
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from typing import Any

try:
    from importlib.resources.abc import Traversable
except ImportError:  # pragma: no cover
    from importlib.abc import Traversable

from ansys.pre_commit_hooks.quality_rules import (
    _first_doc_line,
    _interpret,
    is_mcp,
    readme_path,
    repo_review_checks,
    repo_review_families,
    workflow_map,
)

_PATHS_TO_FETCH = [
    "AUTHORS",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "LICENSE",
    "README.rst",
    "README.md",
    "SECURITY.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/labeler.yml",
    ".github/labels.yml",
    ".github/zizmor.yml",
    ".github/workflows/ci_cd_main.yml",
    ".github/workflows/ci_cd_pr.yml",
    ".github/workflows/ci_cd_release.yml",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "doc/.vale.ini",
    "doc/source/index.rst",
    "doc/source/conf.py",
    "doc/styles/config/vocabularies/ANSYS/accept.txt",
    "doc/styles/config/vocabularies/ANSYS/reject.txt",
]


HOOK_PATH = Path(__file__).parent.resolve()
"""Location of the pre-commit hook on your system."""

LICENSES_JSON = HOOK_PATH / "assets" / "licenses.json"
"""JSON file containing licenses information."""

DEFAULT_AUTHOR_MAINT_NAME = "Synopsys, Inc. and ANSYS, Inc."
"""Default name of project authors and maintainers."""

DEFAULT_AUTHOR_MAINT_EMAIL = "pyansys-core@synopsys.com"
"""Default email of project authors and maintainers."""

DEFAULT_START_YEAR = dt.today().year
"""Default start year of the repository."""

DEFAULT_LICENSE = "MIT"
"""Default license of the repository."""

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


class MemoryTraversable(Traversable):
    """In-memory Traversable backed by a flat dict mapping path -> content."""

    def __init__(self, files: dict[str, str | None], path: str = "") -> None:
        """Initialize a virtual Traversable with a dict of file contents."""
        self._files = files
        self._path = path.strip("/")

    @property
    def name(self) -> str:
        """Return the final path component for this virtual file or directory."""
        return self._path.split("/")[-1] if self._path else ""

    def is_file(self) -> bool:
        """Return whether this virtual path resolves to a file."""
        return self._path in self._files and self._files[self._path] is not None

    def is_dir(self) -> bool:
        """Return whether this virtual path resolves to a directory."""
        if not self._path:
            return True
        prefix = self._path + "/"
        return any(key.startswith(prefix) for key in self._files)

    def iterdir(self) -> Iterator[MemoryTraversable]:
        """Yield child paths for this virtual directory."""
        prefix = (self._path + "/") if self._path else ""
        seen: set[str] = set()
        for key in self._files:
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix) :]
            child_name = rest.split("/")[0]
            if child_name and child_name not in seen:
                seen.add(child_name)
                yield MemoryTraversable(self._files, f"{prefix}{child_name}")

    def joinpath(self, *parts: str) -> MemoryTraversable:
        """Join path components under this virtual root."""
        combined = "/".join(filter(None, [self._path, *parts]))
        return MemoryTraversable(self._files, combined)

    __truediv__ = joinpath

    def open(self, mode: str = "r", encoding: str = "utf-8", **_) -> StringIO | BytesIO:
        """Open the virtual file as a text or binary stream."""
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        if "b" in mode:
            return BytesIO(content.encode(encoding))
        return StringIO(content)

    def read_bytes(self) -> bytes:
        """Read the virtual file as raw bytes."""
        return self.open("rb").read()

    def read_text(self, encoding: str = "utf-8") -> str:
        """Read the virtual file as UTF-8 text."""
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        return content

    def __repr__(self) -> str:
        """Return a string representation of the virtual path."""
        return f"MemoryTraversable({self._path!r})"

    def __str__(self) -> str:
        """Return a string representation of the virtual path."""
        return self._path


def check_dirs_exist(repo_path: Path | str, is_compliant: bool, directories: list[str]) -> bool:
    """Check folders exist in the root of the git repository."""
    repo_path = Path(repo_path)
    for directory in directories:
        full_path = repo_path / directory
        if not full_path.exists():
            is_compliant = False
            print(
                f'The "{directory}" directory does not exist. Creating the "{directory}" directory...'  # noqa: E501
            )
            full_path.mkdir(parents=True, exist_ok=True)

    if not is_compliant:
        print("")

    return is_compliant


def check_config_file(
    repo_path: Path | str,
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
    non_compliant_name: bool,
) -> tuple[bool, str, str]:
    """Check naming convention, version, author, and maintainer information."""
    repo_path = Path(repo_path)
    has_pyproject = (repo_path / "pyproject.toml").exists()
    has_setup = (repo_path / "setup.py").exists()

    if (has_pyproject and has_setup) or (has_setup and not has_pyproject):
        config_file = "setuptools"
        is_compliant, project_name = check_setup_py(
            author_maint_name, author_maint_email, is_compliant
        )
    elif has_pyproject and not has_setup:
        config_file = "pyproject"
        is_compliant, project_name = check_pyproject_toml(
            repo_path, author_maint_name, author_maint_email, is_compliant, non_compliant_name
        )
    else:
        config_file = ""
        project_name = ""
        print("The pyproject.toml and setup.py files do not exist")
        print("Cannot get the author and maintainer name and email, project name, and version\n")

    return is_compliant, project_name, config_file


def check_pyproject_toml(
    repo_path: Path | str,
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
    non_compliant_name: bool,
) -> tuple[bool, str]:
    """Check pyproject.toml file for correct naming convention, version, author, and maintainer."""
    repo_path = Path(repo_path)
    name = ""
    import toml

    with open(repo_path / "pyproject.toml", "r", encoding="utf-8") as project_file:
        config = toml.load(project_file)
        project = config.get("project", {})

        if not non_compliant_name:
            name = project.get("name", "DNE")
            if (name == "DNE") or (
                (name != "DNE") and not bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name))
            ):
                is_compliant = False
                print("Project name does not follow naming conventions")

        project_version = project.get("version", "DNE")
        if project_version != "DNE":
            try:
                import semver

                semver.Version.parse(project_version)
            except ValueError:
                if not bool(re.match(r"^[0-9]+.[0-9]+.dev[0-9]+$", project_version)):
                    is_compliant = False
                    print("Project version does not follow semantic versioning")

        for key, value in list(product(["authors", "maintainers"], ["name", "email"])):
            project_value = project.get(key, "DNE")[0].get(value, "DNE")
            if project_value == "DNE":
                is_compliant = False
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


def check_auth_maint(
    project_value: str, arg_value: str, err_string: str, is_compliant: bool
) -> bool:
    """Check if the author and maintainer names and emails are the same."""
    if project_value != arg_value:
        print(f"Project {err_string} is not {arg_value}")
        is_compliant = False
    return is_compliant


def check_setup_py(
    author_maint_name: str,
    author_maint_email: str,
    is_compliant: bool,
) -> tuple[bool, str]:
    """Check setup.py file for correct naming convention, version, author, and maintainer."""
    print("The setup.py check is not implemented. Please manually check the following:")
    print("- The project name is ansys-*-*")
    print("- The project uses semantic versioning (see https://semver.org/)")
    print(f"- The author and maintainer name is {author_maint_name}")
    print(f"- The author and maintainer email is {author_maint_email}\n")
    return is_compliant, ""


def download_license_json(url: str, json_file: Path | str) -> bool:
    """Download the licenses.json file and restructure to include the license ID and name."""
    json_file = Path(json_file)
    if not json_file.exists():
        import requests

        response = requests.get(url, timeout=60)
        status_code = response.status_code
        if status_code == 200:
            json_file.write_text(response.text, encoding="utf-8")
            restructure_json(json_file)
        else:
            print("There was a problem downloading license.json. Skipping LICENSE content check")
            return False
    return True


def restructure_json(file: Path | str):
    """Remove extra information from licenses.json file."""
    file = Path(file)
    licenseid_name_dict = {}
    with open(file, "r", encoding="utf-8") as json_file:
        existing_json = json.load(json_file)
        for license in existing_json["licenses"]:
            if not license["isDeprecatedLicenseId"]:
                licenseid_name_dict[license["licenseId"]] = license["name"]
    with open(file, "w", encoding="utf-8") as json_file:
        json_file.write(json.dumps(licenseid_name_dict, indent=4))


def generate_file_from_jinja(
    file: str,
    project_name: str,
    year_str: str,
    repo_url: str,
    product: str | None,
    config_file: str,
    doc_repo_name: str,
) -> str:
    """Generate file using jinja templates."""
    from jinja2 import Environment, FileSystemLoader

    loader = FileSystemLoader(searchpath=Path.joinpath(HOOK_PATH, "templates"))
    env = Environment(loader=loader)  # nosec
    template = env.get_template(file)
    return template.render(
        doc_repo_name=doc_repo_name,
        project_name=project_name,
        year_span=year_str,
        repository_url=repo_url,
        product=product,
        config_file=config_file,
    )


def write_content(message: str, file_path: Path | str, file_content: str):
    """Write generated content from jinja template to a file."""
    print(message)
    Path(file_path).write_text(file_content, encoding="utf-8")


def check_file_exists(
    repo_path: Path | str,
    files: list[str],
    project_name: str,
    start_year: int,
    is_compliant: bool,
    license: str,
    repository_url: str,
    product: str | None,
    config_file: str,
    doc_repo_name: str,
) -> bool:
    """Check files exist; if missing, generate them from the template."""
    repo_path = Path(repo_path)
    year_str = (
        start_year if start_year == DEFAULT_START_YEAR else f"{start_year} - {DEFAULT_START_YEAR}"
    )
    ref_dict = {
        "AUTHORS": "the-authors-file",
        "CODE_OF_CONDUCT.md": "the-code-of-conduct-md-file",
        "CONTRIBUTING.md": "the-contributing-md-file",
        "CONTRIBUTORS.md": "the-contributors-md-file",
        "LICENSE": "the-license-file",
        "README.rst": "the-readme-file",
        "README.md": "the-readme-file",
    }

    for file_name in files:
        if "dependabot" in file_name:
            repo_file_path = repo_path / ".github" / file_name
        else:
            if "README" in file_name:
                if (repo_path / f"{file_name}.md").exists():
                    file_name = f"{file_name}.md"
                else:
                    file_name = f"{file_name}.rst"
            repo_file_path = repo_path / file_name

        file_content = generate_file_from_jinja(
            file_name, project_name, year_str, repository_url, product, config_file, doc_repo_name
        )

        if "AUTHORS" in file_name and (repo_path / f"{file_name}.md").exists():
            repo_file_path = repo_path / f"{file_name}.md"

        if not repo_file_path.exists():
            is_compliant = False
            dne_message = f"{file_name} does not exist. Creating file from template..."
            if "setuptools" in config_file:
                if "dependabot" in file_name:
                    write_content(dne_message, repo_file_path, file_content)
                else:
                    tech_review_docs = f"https://dev.docs.pyansys.com/packaging/structure.html#{ref_dict[file_name]}."  # noqa: E501
                    print(f"{file_name} does not exist. Please see {tech_review_docs}")
            else:
                if "README" in file_name and product is None:
                    print("The --product argument is required to generate the README file.")
                elif "README" in file_name and project_name == "":
                    print("The project_name is required to generate the README file.")
                elif "dependabot" in file_name and config_file == "":
                    print("The config_file type is required to generate the dependabot.yml file.")
                elif "AUTHORS" in file_name and project_name == "":
                    print("The project_name is required to generate the AUTHORS file.")
                else:
                    write_content(dne_message, repo_file_path, file_content)
        else:
            if file_name in (Filenames.CONTRIBUTORS.value, Filenames.LICENSE.value):
                is_compliant = check_file_content(
                    repo_file_path, file_content, is_compliant, license
                )

    return is_compliant


def check_file_content(
    file: Path | str, generated_content: str, is_compliant: bool, license: str
) -> bool:
    """Check the file content of the LICENSE and CONTRIBUTORS.md files."""
    file = Path(file)
    generated_file = NamedTemporaryFile(mode="w", delete=False)
    with open(generated_file.name, "w", encoding="utf-8") as f:
        f.write(generated_content)

    same_files = filecmp.cmp(file, generated_file.name, shallow=False)

    if file.name == Filenames.CONTRIBUTORS.value and same_files:
        is_compliant = False
        print("Please update your CONTRIBUTORS.md file.")
    elif file.name == Filenames.LICENSE.value:
        downloaded = download_license_json(JSON_URL, LICENSES_JSON)
        if downloaded:
            license_line_found = False
            with open(LICENSES_JSON, "r", encoding="utf-8") as f:
                license_json = json.load(f)
                license_full_name = license_json[license]

            with open(file, "r", encoding="utf-8") as license_file:
                for line in license_file:
                    if license_full_name in line:
                        license_line_found = True
                        break

            if not license_line_found:
                is_compliant = False
                print(
                    f'"The {Filenames.LICENSE.value} file content is missing "{license_full_name}"'
                )

    return is_compliant


def _bootstrap_legacy_files(
    repo_root: Path | str,
    *,
    author_maint_name: str,
    author_maint_email: str,
    license: str,
    product: str | None,
    repository_url: str | None,
    non_compliant_name: bool,
) -> int:
    """Apply the legacy tech-review bootstrap logic and file-content checks."""
    repo_root = Path(repo_root)
    is_compliant = True
    import git

    try:
        git_repo = git.Repo(repo_root, search_parent_directories=True)
        root = Path(git_repo.git.rev_parse("--show-toplevel"))
    except (git.InvalidGitRepositoryError, git.GitCommandError):
        root = repo_root

    try:
        g = git.Git(root)
        all_dates = g.log("--reverse", "--format=%ci")
        start_year = int(all_dates[0:4]) if all_dates else DEFAULT_START_YEAR
    except Exception:
        start_year = DEFAULT_START_YEAR

    is_compliant = check_dirs_exist(
        root, is_compliant, [directory.value for directory in Directories]
    )
    is_compliant, project_name, config_file = check_config_file(
        root, author_maint_name, author_maint_email, is_compliant, non_compliant_name
    )

    check_exists_list = [file.value for file in Filenames]
    doc_repo_name = root.name
    repo_url = repository_url or f"https://github.com/ansys/{doc_repo_name}"
    is_compliant = check_file_exists(
        root,
        check_exists_list,
        project_name,
        start_year,
        is_compliant,
        license,
        repo_url,
        product,
        config_file,
        doc_repo_name,
    )
    return 0 if is_compliant else 1


def _run_checks(files: dict[str, str | None], is_mcp_flag: bool) -> dict[str, Any]:
    """Run the package-based repo review checks against an in-memory file set."""
    root = MemoryTraversable(files)
    fixture_values = {
        "root": root,
        "package": root,
        "workflow_map": workflow_map(root),
        "readme_path": readme_path(root),
        "is_mcp": is_mcp_flag or is_mcp(root),
    }

    checks = repo_review_checks()
    families = repo_review_families()
    results = []

    for code, check_obj in checks.items():
        try:
            import inspect

            signature = inspect.signature(check_obj.check)
            kwargs = {
                key: fixture_values[key] for key in signature.parameters if key in fixture_values
            }
            raw = check_obj.check(**kwargs)
        except (AttributeError, TypeError, ValueError) as exc:  # pragma: no cover
            raw = f"⚠️ Check error: {exc}"

        status, detail = _interpret(raw, check_obj)
        results.append(
            {
                "id": code,
                "family": check_obj.family,
                "family_name": families.get(check_obj.family, {}).get("name", check_obj.family),
                "label": type(check_obj).__doc__ or code,
                "description": _first_doc_line(check_obj),
                "status": status,
                "detail": detail,
            }
        )

    tally = {"passed": 0, "failed": 0, "warned": 0, "not_applicable": 0}
    for result in results:
        if result["status"] == "pass":
            tally["passed"] += 1
        elif result["status"] == "fail":
            tally["failed"] += 1
        elif result["status"] == "warn":
            tally["warned"] += 1
        else:
            tally["not_applicable"] += 1

    scored = tally["passed"] + tally["failed"]
    score = round(tally["passed"] / scored * 100) if scored else 0
    return {
        "results": results,
        "tally": {
            "pass": tally["passed"],
            "fail": tally["failed"],
            "warn": tally["warned"],
            "na": tally["not_applicable"],
        },
        "score": score,
        "workflow_map": fixture_values["workflow_map"],
        "project_metadata": {
            "build_system": {"name": "Unknown", "key": "unknown"},
            "license": None,
            "python_requires": None,
        },
    }


def _load_files(repo_root: Path) -> dict[str, str | None]:
    """Load the repository files needed by the quality report from disk."""
    files: dict[str, str | None] = {}
    for relative_path in _PATHS_TO_FETCH:
        candidate = repo_root / relative_path
        if candidate.is_file():
            files[relative_path] = candidate.read_text(encoding="utf-8", errors="replace")
        else:
            files[relative_path] = None

    workflows = repo_root / ".github" / "workflows"
    if workflows.is_dir():
        for workflow in workflows.glob("*.y*ml"):
            files[workflow.relative_to(repo_root).as_posix()] = workflow.read_text(
                encoding="utf-8", errors="replace"
            )

    return files


def _style_status(status: str, text: str) -> str:
    """Style a status label for console output."""
    if status == "pass":
        color = "\033[32m"
    elif status == "warn":
        color = "\033[33m"
    elif status == "fail":
        color = "\033[31m"
    elif status == "na":
        color = "\033[36m"
    else:
        color = ""
    reset = "\033[0m"
    return f"{color}{text}{reset}" if color else text


def _print_report(review: dict[str, Any], *, show_passes: bool = False) -> None:
    """Print the repo quality summary to stdout."""
    results = review["results"]
    tally = review["tally"]
    score = review["score"]

    print("PyAnsys quality report")
    print("=" * 24)
    print(f"Score: {score}%")
    summary = (
        f"Summary: pass={_style_status('pass', str(tally['pass']))} "
        f"fail={_style_status('fail', str(tally['fail']))} "
        f"warn={_style_status('warn', str(tally['warn']))} "
        f"na={_style_status('na', str(tally['na']))}"
    )
    print(summary)

    for item in results:
        if item["status"] == "pass" and not show_passes:
            continue
        detail = item["detail"] or ""
        label = _style_status(item["status"], item["status"].upper())
        print(f"- [{label}] {item['id']} - {item['label']}")
        if detail:
            print(f"  {detail}")


def main(argv: list[str] | None = None) -> int:
    """Run the repository bootstrap and the PyAnsys quality report."""
    parser = argparse.ArgumentParser(description="Run the PyAnsys repository quality report.")
    parser.add_argument("--repo-root", default=".", help="Repository root to review.")
    parser.add_argument(
        "--json", action="store_true", help="Emit a JSON report instead of a text summary."
    )
    parser.add_argument(
        "--all", action="store_true", help="Show all checks, including passing ones."
    )
    parser.add_argument(
        "--fix-missing",
        action="store_true",
        help="Generate missing repository scaffolding before running the quality report.",
    )
    parser.add_argument(
        "--author_maint_name",
        type=str,
        help="Name of the authors and maintainers of the project.",
        default=DEFAULT_AUTHOR_MAINT_NAME,
    )
    parser.add_argument(
        "--author_maint_email",
        type=str,
        help="Email of the authors and maintainers of the project.",
        default=DEFAULT_AUTHOR_MAINT_EMAIL,
    )
    parser.add_argument(
        "--license",
        type=str,
        help="License that the repository uses.",
        default=DEFAULT_LICENSE,
    )
    parser.add_argument(
        "--product",
        type=str,
        help="Ansys product that the repository is related to.",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="The repository URL. For example, https://github.com/ansys/pymechanical",
    )
    parser.add_argument("--non_compliant_name", action="store_true")
    args, unknown = parser.parse_known_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    legacy_exit = 0
    if args.fix_missing:
        current_dir = Path.cwd()
        os.chdir(repo_root)
        try:
            legacy_exit = _bootstrap_legacy_files(
                repo_root,
                author_maint_name=args.author_maint_name,
                author_maint_email=args.author_maint_email,
                license=args.license,
                product=args.product,
                repository_url=args.url,
                non_compliant_name=args.non_compliant_name,
            )
        finally:
            os.chdir(current_dir)

        if legacy_exit == 0:
            print("\nLegacy tech-review bootstrap complete.")
        else:
            print(f"\nLegacy tech-review bootstrap reported exit code {legacy_exit}.")

    files = _load_files(repo_root)
    review = _run_checks(files, is_mcp_flag=is_mcp(MemoryTraversable(files)))

    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] or legacy_exit else 0

    _print_report(review, show_passes=args.all)
    return 1 if review["tally"]["fail"] or legacy_exit else 0


if __name__ == "__main__":
    raise SystemExit(main())
