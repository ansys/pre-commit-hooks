# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Project metadata checks.

This rule set validates repository metadata against PyAnsys standards.

The checks cover:

* Governance and repository files
    - AUTHORS
    - CHANGELOG.md or doc/source/changelog.rst
    - CODE_OF_CONDUCT.md
    - CONTRIBUTING.md
    - CONTRIBUTORS.md
    - LICENSE
    - SECURITY.md
    - .github/CODEOWNERS

* Packaging metadata
    - pyproject.toml references the README and LICENSE files
    - Project name follows the ``ansys-*-*`` convention
    - Project version follows the accepted versioning schemes
    - Author and maintainer metadata is configured
    - Supported Python versions have explicit bounds
    - Python version classifiers agree with requires-python
    - Support URLs are declared

* Licensing
    - LICENSE file contains recognized MIT or Apache 2.0 wording

* Repository layout
    - Documentation and tests directories
    - Task runner configuration
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
import re
from typing import ClassVar, Final

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    _repository_file,
    file_content,
    file_exists,
)

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

__all__ = [
    "PM001",
    "PM002",
    "PM003",
    "PM004",
    "PM005",
    "PM006",
    "PM007",
    "PM008",
    "PM009",
    "PM010",
    "PM011",
    "PM012",
    "PM013",
    "PM014",
    "PM015",
    "PM016",
    "PM017",
    "PM018",
    "PM019",
    "PM020",
    "PM021",
    "PM022",
    "PM023",
    "ProjectMetadata",
]

_PYPROJECT: Final = "pyproject.toml"
_LICENSE: Final = "LICENSE"
_CODEOWNERS: Final = ".github/CODEOWNERS"
_AUTHORS: Final = "AUTHORS"
_CHANGELOG: Final = "CHANGELOG.md"
_DOC_CHANGELOG: Final = "doc/source/changelog.rst"
_CODE_OF_CONDUCT: Final = "CODE_OF_CONDUCT.md"
_CONTRIBUTING: Final = "CONTRIBUTING.md"
_CONTRIBUTORS: Final = "CONTRIBUTORS.md"
_LICENSE_TEMPLATES: Final = Path(__file__).resolve().parents[1] / "assets" / "LICENSES"
_SECURITY: Final = "SECURITY.md"

_DEFAULT_AUTHOR: Final = "Synopsys, Inc. and ANSYS, Inc."
_DEFAULT_EMAIL: Final = "pyansys-core@synopsys.com"

_DOCS_DIRECTORIES: Final = ("docs", "doc")
_TESTS_DIRECTORIES: Final = ("tests", "test")
_TASK_RUNNER_FILES: Final = (
    "tox.ini",
    "noxfile.py",
    "noxfile.toml",
    "pixi.toml",
    "justfile",
    "Makefile",
)
_REQUIRED_PROJECT_URLS: Final = ("Issues", "Discussions", "Documentation")

_POETRY_BACKEND: Final = re.compile(r"poetry[._-]core")
_POETRY_LICENSE: Final = re.compile(r"\[tool\.poetry\][\s\S]*?license\s*=")
_PROJECT_NAME: Final = re.compile(r"""^name\s*=\s*["']([^"']+)["']""", re.MULTILINE)
_PROJECT_VERSION: Final = re.compile(r"""^version\s*=\s*["']([^"']+)["']""", re.MULTILINE)
_CODEOWNER_ENTRY: Final = re.compile(r"^\s*[^#\n]+\s+@\S+", re.MULTILINE)
_LEAD_HEADING: Final = re.compile(r"^##\s+Project\s+Lead\b", re.MULTILINE)
_INDIVIDUAL_HEADING: Final = re.compile(r"^##\s+Individual\s+Contributors\b", re.MULTILINE)
_CONTRIBUTOR_BULLET: Final = re.compile(r"^\*\s+\[[^\]]+\]\([^)]+\)", re.MULTILINE)


def _has_any_file(repository_root: Path, relative_paths: Sequence[str]) -> bool:
    """Return whether any of the given files exists in the repository."""
    return any(file_exists(repository_root, path) for path in relative_paths)


def _has_any_directory(repository_root: Path, relative_paths: Sequence[str]) -> bool:
    """Return whether any of the given directories exists inside the repository."""
    for path in relative_paths:
        resolved_directory = _repository_file(repository_root, path)
        try:
            if resolved_directory is not None and resolved_directory.is_dir():
                return True
        except OSError:
            continue
    return False


def _read(repository_root: Path, relative_path: str) -> str | None:
    """Return file content, or ``None`` if the file is missing or unreadable."""
    return (
        None
        if not file_exists(repository_root, relative_path)
        else file_content(repository_root, relative_path)
    )


def _missing(relative_path: str) -> str:
    """Return the warning used when a file needed for a check is unavailable."""
    return f"WARNING: {relative_path} not found or not readable, so this check was skipped."


def _collapse_whitespace(text: str) -> str:
    """Return text with every run of whitespace replaced by a single space."""
    return " ".join(text.split())


def _license_body_matches(content: str, template_name: str, start: str, end: str) -> bool:
    """Return whether ``content`` contains the standard license body from a template.

    Whitespace is collapsed on both sides so that line wrapping differences are ignored.
    """
    template = (_LICENSE_TEMPLATES / template_name).read_text(encoding="utf-8")
    body = template[template.index(start) : template.index(end) + len(end)]
    return _collapse_whitespace(body) in _collapse_whitespace(content)


def _pyproject_data(repository_root: Path) -> dict[str, object] | str:
    """Parse project metadata or return an explicit warning."""
    content = _read(repository_root, _PYPROJECT)
    if content is None:
        return _missing(_PYPROJECT)
    try:
        return tomllib.loads(content)
    except ValueError as error:
        return f"WARNING: {_PYPROJECT} is not valid TOML: {error}"


def _project_table(data: dict[str, object]) -> dict[str, object] | str:
    """Return the project table or an explicit warning."""
    project = data.get("project")
    if not isinstance(project, dict):
        return "WARNING: pyproject.toml must contain a [project] table."
    dynamic = project.get("dynamic", [])
    if not isinstance(dynamic, list) or not all(isinstance(key, str) for key in dynamic):
        return "WARNING: project.dynamic must be a list of strings."
    return project


def _python_specifiers(spec: object) -> SpecifierSet | str:
    """Parse an explicit Python support range with lower and upper comparators."""
    if not isinstance(spec, str) or not spec.strip():
        return "WARNING: requires-python must be a non-empty version specifier string."
    try:
        specifiers = SpecifierSet(spec)
    except InvalidSpecifier:
        return f"WARNING: requires-python '{spec}' is not a valid version specifier."
    operators = {specifier.operator for specifier in specifiers}
    if not operators.intersection({">", ">="}) or not operators.intersection({"<", "<="}):
        return (
            f"WARNING: requires-python '{spec}' must declare explicit lower and upper "
            "bounds, for example >=3.10,<4."
        )
    return specifiers


def _supports_python_minor(specifiers: SpecifierSet, version: str) -> bool:
    """Return whether a Python minor series has an allowed stable patch release."""
    minor = Version(version).release
    candidates = {Version(f"{version}.0")}
    # Membership can change at a specifier boundary or immediately after it.
    for specifier in specifiers:
        try:
            boundary = Version(specifier.version.removesuffix(".*"))
        except InvalidVersion:
            # Arbitrary equality (===) can name a non-version, not a Python release.
            return False
        if boundary.release[:2] == minor:
            patch = boundary.release[2] if len(boundary.release) > 2 else 0
            candidates.update({Version(f"{version}.{patch}"), Version(f"{version}.{patch + 1}")})
    return any(specifiers.contains(candidate) for candidate in candidates)


def _has_rst_changelog_content(content: str) -> bool:
    """Require an RST title followed by non-placeholder content."""
    lines = content.splitlines()
    placeholders = {"todo", "tbd", "placeholder", "coming soon", "no releases yet"}
    for index in range(len(lines) - 1):
        title, underline = lines[index].strip(), lines[index + 1].strip()
        if (
            not title
            or title.startswith("..")
            or not any(character.isalnum() for character in title)
            or len(underline) < len(title)
            or len(set(underline)) != 1
            or underline[0] not in '=-~^"#*+'
        ):
            continue
        for body_index in range(index + 2, len(lines)):
            line = lines[body_index].strip()
            if (
                not line
                or line.startswith("..")
                or not any(character.isalnum() for character in line)
                or line.lower().rstrip(".:") in placeholders
            ):
                continue
            if body_index + 1 < len(lines):
                next_line = lines[body_index + 1].strip()
                if (
                    len(next_line) >= len(line)
                    and len(set(next_line)) == 1
                    and next_line[0] in '=-~^"#*+'
                ):
                    continue
            return True
        return False
    return False


def _has_default_contact(content: str, key: str) -> bool:
    """Return whether the ``key = [...]`` block lists the default author name and email."""
    block_match = re.search(rf"{re.escape(key)}\s*=\s*\[([\s\S]*?)\]", content)
    block = block_match.group(1) if block_match else ""
    return bool(
        re.search(rf'name\s*=\s*["\']{re.escape(_DEFAULT_AUTHOR)}["\']', block)
        and re.search(rf'email\s*=\s*["\']{re.escape(_DEFAULT_EMAIL)}["\']', block)
    )


class ProjectMetadata(ABC):
    """Project metadata rule family.

    Base class of the project metadata quality rules. Each rule is a subclass
    named ``PM<nnn>`` with a static ``check`` method that receives the repository
    root and the name of the detected README file.
    """

    family: ClassVar[str] = "project_metadata"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a project metadata rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, or ``None`` when no supported README exists.

        Returns
        -------
        bool or str
            Raw rule result consumed by the quality-report runner.
        """
        raise NotImplementedError


class PM001(ProjectMetadata):
    """The AUTHORS file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the AUTHORS file is present."""
        return file_exists(repository_root, _AUTHORS)


class PM002(ProjectMetadata):
    """CHANGELOG.md exists or doc/source/changelog.rst has a title and content."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check the Markdown changelog or validate the RST fallback."""
        if file_exists(repository_root, _CHANGELOG):
            return True
        if not file_exists(repository_root, _DOC_CHANGELOG):
            return False
        content = _read(repository_root, _DOC_CHANGELOG)
        if content is None:
            return _missing(_DOC_CHANGELOG)
        if _has_rst_changelog_content(content):
            return True
        return (
            f"WARNING: {_DOC_CHANGELOG} must contain a valid RST title and "
            "non-placeholder content."
        )


class PM003(ProjectMetadata):
    """The CODE_OF_CONDUCT.md file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the code-of-conduct file is present."""
        return file_exists(repository_root, _CODE_OF_CONDUCT)


class PM004(ProjectMetadata):
    """The CONTRIBUTING.md file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the contributing guide is present."""
        return file_exists(repository_root, _CONTRIBUTING)


class PM005(ProjectMetadata):
    """The CONTRIBUTORS.md file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the contributors file is present."""
        return file_exists(repository_root, _CONTRIBUTORS)


class PM006(ProjectMetadata):
    """The LICENSE file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the license file is present."""
        return file_exists(repository_root, _LICENSE)


class PM007(ProjectMetadata):
    """The SECURITY.md file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the security policy file is present."""
        return file_exists(repository_root, _SECURITY)


class PM008(ProjectMetadata):
    """The .github/CODEOWNERS file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the CODEOWNERS file is present."""
        return file_exists(repository_root, _CODEOWNERS)


class PM009(ProjectMetadata):
    """Pyproject.toml declares README content and referenced files exist."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Validate static README declarations and setuptools dynamic file references."""
        data = _pyproject_data(repository_root)
        if isinstance(data, str):
            return data
        project = _project_table(data)
        if isinstance(project, str):
            return project
        readme = project.get("readme")
        dynamic = project.get("dynamic", [])
        is_dynamic = isinstance(dynamic, list) and "readme" in dynamic
        if readme is None and is_dynamic:
            tool = data.get("tool")
            setuptools = tool.get("setuptools") if isinstance(tool, dict) else None
            dynamic = setuptools.get("dynamic") if isinstance(setuptools, dict) else None
            readme = dynamic.get("readme") if isinstance(dynamic, dict) else None
            if readme is None:
                return "WARNING: Dynamic README content cannot be verified statically."
        if readme is None:
            return False
        if isinstance(readme, dict):
            if "file" in readme and "text" in readme:
                return "WARNING: README metadata must not declare both file and text."
            if "text" in readme and "file" not in readme:
                text = readme["text"]
                if isinstance(text, str) and text.strip():
                    return True
                return "WARNING: project.readme.text must be a non-empty string."
            readme = readme.get("file")
        if not is_dynamic and not isinstance(readme, str):
            return "WARNING: project.readme must declare a single file path or inline text."
        paths = [readme] if isinstance(readme, str) else readme
        if (
            not isinstance(paths, list)
            or not paths
            or not all(isinstance(path, str) and path.strip() for path in paths)
        ):
            return "WARNING: README metadata must declare a file path or inline text."
        missing = [
            path
            for path in paths
            if isinstance(path, str) and not file_exists(repository_root, path)
        ]
        if missing:
            return "WARNING: Referenced README files not found in repository: " + ", ".join(missing)
        return True


class PM010(ProjectMetadata):
    """Pyproject.toml references the LICENSE file."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether pyproject.toml references the license file."""
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        if _POETRY_BACKEND.search(content):
            return bool(_POETRY_LICENSE.search(content))

        return bool(
            re.search(r"license-files\s*=", content)
            or re.search(r"license\s*=\s*\{[^}]*file", content)
            or re.search(r'license\s*=\s*["\']LICENSE["\']', content)
        )


class PM011(ProjectMetadata):
    """Project name follows the ansys-*-* convention."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the project name matches the PyAnsys naming convention."""
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        match = _PROJECT_NAME.search(content)
        if not match:
            return "WARNING: project name not found in pyproject.toml."

        name = match.group(1)
        if re.fullmatch(r"ansys-[a-z0-9-]+-[a-z0-9-]+", name):
            return True
        return f"WARNING: project name '{name}' does not match ansys-*-*."


class PM012(ProjectMetadata):
    """Project version follows an accepted versioning scheme."""

    # Only the subset supported by the PyAnsys tooling: N.N.N[{a|b|rc}N] or PEP 440 dev.
    _RELEASE: ClassVar[re.Pattern[str]] = re.compile(r"\d+\.\d+\.\d+(?:(?:a|b|rc)\d+)?")
    _DEV: ClassVar[re.Pattern[str]] = re.compile(r"\d+\.\d+(?:\.\d+)?\.dev\d+")
    _DYNAMIC_VERSION: ClassVar[re.Pattern[str]] = re.compile(
        r"^dynamic\s*=\s*\[[^\]]*[\"']version[\"']", re.MULTILINE
    )

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the project version uses a valid release or dev version."""
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        match = _PROJECT_VERSION.search(content)
        if not match:
            # The build backend resolves a dynamic version (for example from __init__.py).
            if PM012._DYNAMIC_VERSION.search(content):
                return True
            return "WARNING: project version not found in pyproject.toml."

        version = match.group(1)
        if PM012._RELEASE.fullmatch(version) or PM012._DEV.fullmatch(version):
            return True
        return (
            f"WARNING: project version '{version}' does not follow N.N.N[{{a|b|rc}}N] "
            "or the accepted Python dev-version form."
        )


class PM013(ProjectMetadata):
    """Project author and maintainer metadata matches PyAnsys defaults."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether author and maintainer metadata are configured as expected."""
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        if _has_default_contact(content, "authors") and _has_default_contact(
            content, "maintainers"
        ):
            return True
        return (
            "WARNING: author/maintainer metadata does not match "
            f"{_DEFAULT_AUTHOR} / {_DEFAULT_EMAIL}."
        )


class PM014(ProjectMetadata):
    """The LICENSE file contains the standard MIT or Apache 2.0 license text."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the LICENSE file contains the standard MIT or Apache 2.0 text."""
        content = _read(repository_root, _LICENSE)
        if content is None:
            return _missing(_LICENSE)

        if _collapse_whitespace(content).startswith("MIT License") and _license_body_matches(
            content, "MIT.txt", "Permission is hereby granted", "SOFTWARE."
        ):
            return True
        if _license_body_matches(
            content, "Apache-2.0.txt", "Apache License", "END OF TERMS AND CONDITIONS"
        ):
            return True
        return "WARNING: LICENSE file text does not match the standard MIT or Apache 2.0 license."


class PM015(ProjectMetadata):
    """The .github/CODEOWNERS file contains at least one valid owner entry."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the CODEOWNERS file contains at least one valid ownership entry."""
        content = _read(repository_root, _CODEOWNERS)
        if content is None:
            return _missing(_CODEOWNERS)

        if _CODEOWNER_ENTRY.search(content):
            return True
        return f"WARNING: {_CODEOWNERS} exists but has no owner entries."


class PM016(ProjectMetadata):
    """Project declares supported Python versions with explicit bounds."""

    @staticmethod
    def _validate_python_version_spec(spec: str) -> RuleCheckResult:
        """Validate that a Python version spec defines lower and upper bounds."""
        result = _python_specifiers(spec)
        return result if isinstance(result, str) else True

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether Python support is declared with both lower and upper bounds."""
        if file_exists(repository_root, _PYPROJECT):
            data = _pyproject_data(repository_root)
            if isinstance(data, str):
                return data
            project = _project_table(data)
            if isinstance(project, str):
                return project
            if "requires-python" in project:
                result = _python_specifiers(project["requires-python"])
                return result if isinstance(result, str) else True
        content = _read(repository_root, "setup.py")
        match = (
            re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content) if content else None
        )
        if match:
            return PM016._validate_python_version_spec(match.group(1))
        return "WARNING: requires-python is not declared in pyproject.toml or setup.py."


class PM017(ProjectMetadata):
    """The project includes a docs directory."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a documentation directory is present."""
        return _has_any_directory(repository_root, _DOCS_DIRECTORIES)


class PM018(ProjectMetadata):
    """The project includes a tests directory."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a test directory is present."""
        return _has_any_directory(repository_root, _TESTS_DIRECTORIES)


class PM019(ProjectMetadata):
    """The project supports a task runner such as nox, tox, or pixi."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether a task runner is configured for the project."""
        return _has_any_file(repository_root, _TASK_RUNNER_FILES)


class PM020(ProjectMetadata):
    """Project contact and support links are provided in pyproject metadata."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether key support URLs are declared under project.urls."""
        data = _pyproject_data(repository_root)
        if isinstance(data, str):
            return data
        project = _project_table(data)
        if isinstance(project, str):
            return project
        urls = project.get("urls")
        if not isinstance(urls, dict):
            return "WARNING: Support URLs must be declared in [project.urls]."
        missing = []
        for key in _REQUIRED_PROJECT_URLS:
            url = urls.get(key)
            if not isinstance(url, str) or not re.fullmatch(r"https?://\S+", url):
                missing.append(key)
        if not missing:
            return True
        return "WARNING: missing support/contact project URLs in pyproject.toml: " + ", ".join(
            missing
        )


class PM021(ProjectMetadata):
    """The AUTHORS file contains compliant contributor ownership information."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether AUTHORS includes at least one entry and the corporate owner."""
        content = _read(repository_root, _AUTHORS)
        if content is None:
            return _missing(_AUTHORS)

        stripped_lines = (line.strip() for line in content.splitlines())
        lines = [line for line in stripped_lines if line and not line.startswith("#")]
        if not lines:
            return "WARNING: AUTHORS exists but has no contributor ownership entries."
        if not any(_DEFAULT_AUTHOR in line for line in lines):
            return "WARNING: AUTHORS is missing the expected corporate owner entry."
        return True


class PM022(ProjectMetadata):
    """The CONTRIBUTORS.md file includes lead and main contributors sections."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether CONTRIBUTORS.md includes lead and contributor details."""
        content = _read(repository_root, _CONTRIBUTORS)
        if content is None:
            return _missing(_CONTRIBUTORS)

        if (
            _LEAD_HEADING.search(content)
            and _INDIVIDUAL_HEADING.search(content)
            and _CONTRIBUTOR_BULLET.search(content)
        ):
            return True
        return (
            "WARNING: CONTRIBUTORS.md should include 'Project Lead' and 'Individual "
            "Contributors' sections with at least one contributor entry."
        )


class PM023(ProjectMetadata):
    """Python version classifiers are present and compatible with requires-python."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that every declared Python minor series has a supported patch release."""
        data = _pyproject_data(repository_root)
        if isinstance(data, str):
            return data
        project = _project_table(data)
        if isinstance(project, str):
            return project
        specifiers = _python_specifiers(project.get("requires-python"))
        if isinstance(specifiers, str):
            return specifiers
        classifiers = project.get("classifiers")
        dynamic = project.get("dynamic", [])
        if classifiers is None and isinstance(dynamic, list) and "classifiers" in dynamic:
            return "WARNING: Dynamic Python classifiers cannot be verified statically."
        if not isinstance(classifiers, list) or not all(
            isinstance(classifier, str) for classifier in classifiers
        ):
            return "WARNING: project.classifiers must list supported Python minor versions."
        versions = [
            match.group(1)
            for classifier in classifiers
            if isinstance(classifier, str)
            and (match := re.fullmatch(r"Programming Language :: Python :: (\d+\.\d+)", classifier))
        ]
        if not versions:
            return "WARNING: No Python minor-version classifiers declared in project.classifiers."
        incompatible = [
            version for version in versions if not _supports_python_minor(specifiers, version)
        ]
        if incompatible:
            return "WARNING: Python classifiers incompatible with requires-python: " + ", ".join(
                incompatible
            )
        return True
