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

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    _repository_file,
    file_content,
    file_exists,
)

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
    if not file_exists(repository_root, relative_path):
        return None
    return file_content(repository_root, relative_path)


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


def _has_url_entry(content: str, key: str) -> bool:
    """Return whether a top-level ``key = "http(s)://..."`` entry exists."""
    return bool(re.search(rf"^{re.escape(key)}\s*=\s*[\"']https?://", content, re.MULTILINE))


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
    """The CHANGELOG.md or doc/source/changelog.rst file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the changelog file is present."""
        return _has_any_file(repository_root, (_CHANGELOG, _DOC_CHANGELOG))


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
    """Pyproject.toml references the README file."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether pyproject.toml references the expected README file."""
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        if (readme_file or "README.rst") in content:
            return True
        if "README" in content:
            return "WARNING: readme key found but exact README filename not confirmed."
        return False


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
        if not re.search(r">=\d+\.\d+", spec) or not re.search(r"[<,]=?\d+", spec):
            return (
                f"WARNING: requires-python '{spec}' does not declare a supported PyAnsys "
                "version range. Use >=3.10,<4 or a more recent support window."
            )
        return True

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether Python support is declared with both lower and upper bounds."""
        sources = ((_PYPROJECT, "requires-python"), ("setup.py", "python_requires"))
        for relative_path, key in sources:
            content = _read(repository_root, relative_path)
            match = re.search(rf'{key}\s*=\s*["\']([^"\']+)["\']', content) if content else None
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
        content = _read(repository_root, _PYPROJECT)
        if content is None:
            return _missing(_PYPROJECT)

        missing = [key for key in _REQUIRED_PROJECT_URLS if not _has_url_entry(content, key)]
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
