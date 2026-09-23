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
    - CHANGELOG.md
    - CODE_OF_CONDUCT.md
    - CONTRIBUTING.md
    - CONTRIBUTORS.md
    - LICENSE
    - SECURITY.md
    - .github/CODEOWNERS

* README requirements
    - README exists
    - README.rst preferred over README.md
    - pyproject.toml references the README

* Packaging metadata
    - LICENSE metadata is declared
    - Project name follows ansys-*-* convention
    - Project version follows accepted versioning schemes
    - Author and maintainer metadata is configured

* Licensing
    - LICENSE file contains recognized Apache 2.0 wording
"""

from __future__ import annotations

from pathlib import Path
import re

from ansys.pre_commit_hooks.quality_rules.common import (
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
    "PM021",
    "PM022",
    "PM024",
    "PM025",
    "PM026",
    "PM027",
    "PM028",
    "PM029",
    "PM030",
    "PM031",
    "PM032",
    "PM033",
    "ProjectMetadata",
]

_PYPROJECT = "pyproject.toml"
_LICENSE = "LICENSE"
_TEMPLATE_DIR = Path(__file__).resolve().parent / "metadata_templates"

_DEFAULT_AUTHOR = "Synopsys, Inc. and ANSYS, Inc."
_DEFAULT_EMAIL = "pyansys-core@synopsys.com"


def _normalize_license_identifier(license_name: str) -> str:
    """Normalize common license aliases for metadata checks."""
    normalized = license_name.strip()
    key = normalized.lower().replace("_", "-").replace(" ", "")
    aliases = {
        "apache": "Apache-2.0",
        "apache2": "Apache-2.0",
        "apache-2": "Apache-2.0",
        "apache2.0": "Apache-2.0",
        "apache-2.0": "Apache-2.0",
    }
    return aliases.get(key, normalized)


def _has_any_file(root, *paths: str) -> bool:
    """Return whether any of the provided file paths exist under the repo root."""
    return any(file_exists(root, path) for path in paths)


def _has_any_directory(root, *paths: str) -> bool:
    """Return whether any of the provided directory paths exist under the repo root."""
    for path in paths:
        try:
            if root.joinpath(path).is_dir():
                return True
        except (AttributeError, TypeError, ValueError):
            continue
    return False


class ProjectMetadata:
    """Project metadata rule family."""

    family = "project_metadata"


class PM001(ProjectMetadata):
    """The AUTHORS file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the AUTHORS file is present."""
        return file_exists(root, "AUTHORS")


class PM002(ProjectMetadata):
    """The CHANGELOG.md file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the changelog file is present."""
        return file_exists(root, "CHANGELOG.md")


class PM003(ProjectMetadata):
    """The CODE_OF_CONDUCT.md file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the code-of-conduct file is present."""
        return file_exists(root, "CODE_OF_CONDUCT.md")


class PM004(ProjectMetadata):
    """The CONTRIBUTING.md file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the contributing guide is present."""
        return file_exists(root, "CONTRIBUTING.md")


class PM005(ProjectMetadata):
    """The CONTRIBUTORS.md file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the contributors file is present."""
        return file_exists(root, "CONTRIBUTORS.md")


class PM006(ProjectMetadata):
    """The LICENSE file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the license file is present."""
        return file_exists(root, _LICENSE)


class PM007(ProjectMetadata):
    """README exists, with README.rst preferred."""

    @staticmethod
    def check(root, readme_path: str | None) -> bool | str:
        """Return whether the README is present and in the preferred format."""
        if readme_path is None:
            return False

        if readme_path == "README.md":
            return "WARN: README.md found — README.rst is the preferred format."

        return True


class PM008(ProjectMetadata):
    """The SECURITY.md file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the security policy file is present."""
        return file_exists(root, "SECURITY.md")


class PM009(ProjectMetadata):
    """The .github/CODEOWNERS file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the CODEOWNERS file is present."""
        return file_exists(root, ".github/CODEOWNERS")


class PM010(ProjectMetadata):
    """Pyproject.toml references the README file."""

    requires = {"PM007"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether pyproject.toml references the expected README file."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)

        if re.search(r"poetry\.core|poetry-core", content):
            readme = readme_path or "README.rst"
            if readme in content:
                return True

            if "README" in content:
                return "WARN: readme key found but exact README filename not confirmed."

            return False

        readme = readme_path or "README.rst"

        if readme in content:
            return True

        if "README" in content:
            return "WARN: readme key found but exact README filename " "not confirmed."

        return False


class PM011(ProjectMetadata):
    """Pyproject.toml references the LICENSE file."""

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether pyproject.toml references the license file."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)

        if re.search(r"poetry\.core|poetry-core", content):
            return bool(
                re.search(
                    r"\[tool\.poetry\][\s\S]*?license\s*=",
                    content,
                    re.MULTILINE,
                )
            )

        return bool(
            re.search(r"license-files\s*=", content)
            or re.search(r"license\s*=\s*\{[^}]*file", content)
            or re.search(
                r'license\s*=\s*["\']LICENSE["\']',
                content,
            )
        )


class PM012(ProjectMetadata):
    """Project name follows the ansys-*-* convention."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the project name matches the PyAnsys naming convention."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)

        match = re.search(
            r'^name\s*=\s*["\']([^"\']+)["\']',
            content,
            re.MULTILINE,
        )

        if not match:
            return "WARN: project name not found in pyproject.toml."

        name = match.group(1)

        if re.fullmatch(r"ansys-[a-z0-9-]+-[a-z0-9-]+", name):
            return True

        return f"WARN: project name '{name}' does not match ansys-*-*."


class PM013(ProjectMetadata):
    """Project version follows semantic versioning or accepted dev versions."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the project version uses a valid release or dev version."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)

        match = re.search(
            r'^version\s*=\s*["\']([^"\']+)["\']',
            content,
            re.MULTILINE,
        )

        if not match:
            return "WARN: project version not found in pyproject.toml."

        version = match.group(1)

        semver_pattern = r"\d+\.\d+\.\d+" r"(?:-(?:a|b|beta|rc|dev)\.?\d+)?"

        pep440_dev_pattern = r"\d+\.\d+(?:\.\d+)?\.dev\d+"

        if re.fullmatch(semver_pattern, version) or re.fullmatch(pep440_dev_pattern, version):
            return True

        return (
            f"WARN: project version '{version}' does not follow "
            "semantic versioning or the accepted Python "
            "dev-version form."
        )


class PM014(ProjectMetadata):
    """Project author and maintainer metadata matches PyAnsys defaults."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether author and maintainer metadata are configured as expected."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)

        authors_match = re.search(r"authors\s*=\s*\[([\s\S]*?)\]", content)
        maintainers_match = re.search(r"maintainers\s*=\s*\[([\s\S]*?)\]", content)

        author_block = authors_match.group(1) if authors_match else ""
        maintainer_block = maintainers_match.group(1) if maintainers_match else ""

        name_ok = bool(
            re.search(
                rf'name\s*=\s*["\']{re.escape(_DEFAULT_AUTHOR)}["\']',
                author_block,
            )
        )

        email_ok = bool(
            re.search(
                rf'email\s*=\s*["\']{re.escape(_DEFAULT_EMAIL)}["\']',
                author_block,
            )
        )

        maintainer_name_ok = bool(
            re.search(
                rf'name\s*=\s*["\']{re.escape(_DEFAULT_AUTHOR)}["\']',
                maintainer_block,
            )
        )

        maintainer_email_ok = bool(
            re.search(
                rf'email\s*=\s*["\']{re.escape(_DEFAULT_EMAIL)}["\']',
                maintainer_block,
            )
        )

        if name_ok and email_ok and maintainer_name_ok and maintainer_email_ok:
            return True

        return (
            "WARN: author/maintainer metadata does not match "
            "Synopsys, Inc. and ANSYS, Inc. / "
            "pyansys-core@synopsys.com."
        )


class PM015(ProjectMetadata):
    """The LICENSE file includes recognized Apache 2.0 project license wording."""

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the LICENSE file contains expected Apache 2.0 text."""
        if not file_exists(root, _LICENSE):
            return None

        content = file_content(root, _LICENSE)

        if (
            re.search(
                r"Apache License.*Version 2\.0",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            or "Apache License" in content
        ):
            return True

        return "WARN: LICENSE file content is missing a recognized Apache 2.0 statement."


class PM016(ProjectMetadata):
    """The .github/CODEOWNERS file contains at least one valid owner entry."""

    requires = {"PM009"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the CODEOWNERS file contains at least one valid ownership entry."""
        if not file_exists(root, ".github/CODEOWNERS"):
            return None

        content = file_content(root, ".github/CODEOWNERS")

        if re.search(r"^\s*[^#\n]+\s+@\S+", content, re.MULTILINE):
            return True

        return "WARN: .github/CODEOWNERS exists but has no owner entries."


def _validate_python_version_spec(spec: str) -> bool | str:
    """Validate that a Python version spec defines supported lower and upper bounds."""
    if not re.search(r">=\d+\.\d+", spec) or not re.search(r"[<,]=?\d+", spec):
        return (
            f"WARN: requires-python '{spec}' does not declare a supported PyAnsys version range. "
            "Use >=3.10,<4 or a more recent support window."
        )

    return True


class PM017(ProjectMetadata):
    """Project declares supported Python versions with explicit bounds."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether Python support is declared with both lower and upper bounds."""
        if file_exists(root, _PYPROJECT):
            content = file_content(root, _PYPROJECT)
            match = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return _validate_python_version_spec(match.group(1))

        if file_exists(root, "setup.py"):
            content = file_content(root, "setup.py")
            match = re.search(r'python_requires\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return _validate_python_version_spec(match.group(1))

        return None


class PM021(ProjectMetadata):
    """The project includes a docs directory."""

    @staticmethod
    def check(root) -> bool:
        """Return whether a documentation directory is present."""
        return _has_any_directory(root, "docs", "doc")


class PM022(ProjectMetadata):
    """The project includes a tests directory."""

    @staticmethod
    def check(root) -> bool:
        """Return whether a test directory is present."""
        return _has_any_directory(root, "tests", "test")


class PM024(ProjectMetadata):
    """The project supports a task runner such as nox, tox, or pixi."""

    @staticmethod
    def check(root) -> bool:
        """Return whether an easy task runner is configured for the project."""
        return _has_any_file(
            root,
            "tox.ini",
            "noxfile.py",
            "noxfile.toml",
            "pixi.toml",
            "justfile",
            "Makefile",
        )


class PM025(ProjectMetadata):
    """Project contact and support links are provided in pyproject metadata."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether key support URLs are declared under project.urls."""
        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)
        missing = []

        if not re.search(r"^Issues\s*=\s*[\"']https?://", content, re.MULTILINE):
            missing.append("Issues")

        if not re.search(r"^Discussions\s*=\s*[\"']https?://", content, re.MULTILINE):
            missing.append("Discussions")

        if not re.search(r"^Documentation\s*=\s*[\"']https?://", content, re.MULTILINE):
            missing.append("Documentation")

        if not missing:
            return True

        return "WARN: missing support/contact project URLs in pyproject.toml: " + ", ".join(missing)


class PM026(ProjectMetadata):
    """The AUTHORS file contains compliant contributor ownership information."""

    requires = {"PM001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether AUTHORS includes at least one ownership entry and the corporate owner."""
        if not file_exists(root, "AUTHORS"):
            return None

        content = file_content(root, "AUTHORS")
        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip() and not line.startswith("#")
        ]

        if not lines:
            return "WARN: AUTHORS exists but has no contributor ownership entries."

        if not any(_DEFAULT_AUTHOR in line for line in lines):
            return "WARN: AUTHORS is missing the expected corporate owner entry."

        return True


class PM027(ProjectMetadata):
    """The CONTRIBUTORS.md file includes lead and main contributors sections."""

    requires = {"PM005"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether CONTRIBUTORS.md includes lead and contributor details."""
        if not file_exists(root, "CONTRIBUTORS.md"):
            return None

        content = file_content(root, "CONTRIBUTORS.md")

        has_lead_heading = bool(re.search(r"^##\s+Project\s+Lead\b", content, re.MULTILINE))
        has_individual_heading = bool(
            re.search(r"^##\s+Individual\s+Contributors\b", content, re.MULTILINE)
        )
        has_bullets = bool(re.search(r"^\*\s+\[[^\]]+\]\([^\)]+\)", content, re.MULTILINE))

        if has_lead_heading and has_individual_heading and has_bullets:
            return True

        return (
            "WARN: CONTRIBUTORS.md should include 'Project Lead' and 'Individual Contributors' "
            "sections with at least one contributor entry."
        )


class PM028(ProjectMetadata):
    """Pyproject license matches the selected --license value."""

    @staticmethod
    def check(root, expected_license: str | None = None) -> bool | None | str:
        """Return whether pyproject license metadata matches the selected expected license."""
        if expected_license is None:
            return None

        if not file_exists(root, _PYPROJECT):
            return None

        content = file_content(root, _PYPROJECT)
        expected = _normalize_license_identifier(expected_license)

        str_match = re.search(r'^license\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if str_match:
            actual = _normalize_license_identifier(str_match.group(1))
            if actual == expected:
                return True
            return f"FAIL: Project license in pyproject.toml ('{str_match.group(1)}') does not match --license={expected}"  # noqa: E501

        if expected == "Apache-2.0" and re.search(
            r"license\s*=\s*\{[^\}]*Apache", content, re.IGNORECASE
        ):
            return True

        return "FAIL: Project license does not exist in pyproject.toml or does not match --license"


class PM029(ProjectMetadata):
    """LICENSE file content matches the selected --license value."""

    requires = {"PM006"}

    @staticmethod
    def check(root, expected_license: str | None = None) -> bool | None | str:
        """Return whether LICENSE content matches the selected expected license."""
        if expected_license is None:
            return None

        if not file_exists(root, _LICENSE):
            return None

        content = file_content(root, _LICENSE)
        expected = _normalize_license_identifier(expected_license)

        if expected == "Apache-2.0":
            apache_ok = (
                "Apache License, Version 2.0" in content
                or "Apache License 2.0" in content
                or re.search(r"Apache License.*Version 2\.0", content, re.IGNORECASE | re.DOTALL)
            )
            return (
                True
                if apache_ok
                else 'FAIL: "The LICENSE file content is missing "Apache License 2.0"'
            )

        return "FAIL: Unsupported expected license for LICENSE content check"


def _normalize_text_for_template_compare(text: str) -> str:
    """Normalize text for stable template comparisons across line endings."""
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()


def _file_matches_template(root, repo_file: str, template_file: str) -> bool | None:
    """Return whether a repository file matches the corresponding metadata template file."""
    if not file_exists(root, repo_file):
        return None

    template_path = _TEMPLATE_DIR / template_file
    if not template_path.exists():
        return None

    actual = file_content(root, repo_file)
    expected = template_path.read_text(encoding="utf-8")
    return _normalize_text_for_template_compare(actual) == _normalize_text_for_template_compare(
        expected
    )


class PM030(ProjectMetadata):
    """The AUTHORS file follows the expected PyAnsys template structure."""

    requires = {"PM001", "PM026"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether AUTHORS matches the expected metadata template file."""
        matches = _file_matches_template(root, "AUTHORS", "AUTHORS")
        if matches is None:
            return None

        if matches:
            return True

        return "WARN: AUTHORS content does not match metadata template AUTHORS."


class PM031(ProjectMetadata):
    """The CODE_OF_CONDUCT.md file follows the expected template content."""

    requires = {"PM003"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether CODE_OF_CONDUCT.md matches the expected metadata template file."""
        matches = _file_matches_template(root, "CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.md")
        if matches is None:
            return None

        if matches:
            return True

        return (
            "WARN: CODE_OF_CONDUCT.md content does not match metadata template CODE_OF_CONDUCT.md."
        )


class PM032(ProjectMetadata):
    """The CONTRIBUTING.md file follows the expected template content."""

    requires = {"PM004"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether CONTRIBUTING.md matches the expected metadata template file."""
        matches = _file_matches_template(root, "CONTRIBUTING.md", "CONTRIBUTING.md")
        if matches is None:
            return None

        if matches:
            return True

        return "WARN: CONTRIBUTING.md content does not match metadata template CONTRIBUTING.md."


class PM033(ProjectMetadata):
    """The CONTRIBUTORS.md file follows the expected template content."""

    requires = {"PM005", "PM027"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether CONTRIBUTORS.md matches the expected metadata template file."""
        matches = _file_matches_template(root, "CONTRIBUTORS.md", "CONTRIBUTORS.md")
        if matches is None:
            return None

        if matches:
            return True

        return "WARN: CONTRIBUTORS.md content does not match metadata template CONTRIBUTORS.md."
