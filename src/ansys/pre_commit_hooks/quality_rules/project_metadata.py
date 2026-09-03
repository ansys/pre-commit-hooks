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
    - LICENSE file contains recognized MIT or Apache 2.0 wording
"""

from __future__ import annotations

import re

from ansys.pre_commit_hooks.quality_rules.common import (
    file_content,
    file_exists,
)

__all__ = [
    "ProjectMetadata",
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
]

_PYPROJECT = "pyproject.toml"
_LICENSE = "LICENSE"

_DEFAULT_AUTHOR = "Synopsys, Inc. and ANSYS, Inc."
_DEFAULT_EMAIL = "pyansys-core@synopsys.com"


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
            return "⚠️ README.md found — README.rst is the preferred format."

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
            match = re.search(
                r"\[^\"']+[\"']",
                content,
                re.MULTILINE,
            )

            if match:
                return True

            return False

        readme = readme_path or "README.rst"

        if readme in content:
            return True

        if "README" in content:
            return "⚠️ readme key found but exact README filename " "not confirmed."

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
            return "⚠️ project name not found in pyproject.toml."

        name = match.group(1)

        if re.fullmatch(r"ansys-[a-z0-9-]+-[a-z0-9-]+", name):
            return True

        return f"⚠️ project name '{name}' does not match ansys-*-*."


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
            return "⚠️ project version not found in pyproject.toml."

        version = match.group(1)

        semver_pattern = r"\d+\.\d+\.\d+" r"(?:-(?:a|b|beta|rc|dev)\.?\d+)?"

        pep440_dev_pattern = r"\d+\.\d+(?:\.\d+)?\.dev\d+"

        if re.fullmatch(semver_pattern, version) or re.fullmatch(pep440_dev_pattern, version):
            return True

        return (
            f"⚠️ project version '{version}' does not follow "
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

        name_ok = bool(
            re.search(
                rf'authors\s*=\s*\[[\s\S]*?name\s*=\s*["\']{re.escape(_DEFAULT_AUTHOR)}["\']',
                content,
            )
        )

        email_ok = bool(
            re.search(
                rf'authors\s*=\s*\[[\s\S]*?email\s*=\s*["\']{re.escape(_DEFAULT_EMAIL)}["\']',
                content,
            )
        )

        maintainer_name_ok = bool(
            re.search(
                rf'maintainers\s*=\s*\[[\s\S]*?name\s*=\s*["\']{re.escape(_DEFAULT_AUTHOR)}["\']',
                content,
            )
        )

        maintainer_email_ok = bool(
            re.search(
                rf'maintainers\s*=\s*\[[\s\S]*?email\s*=\s*["\']{re.escape(_DEFAULT_EMAIL)}["\']',
                content,
            )
        )

        if name_ok and email_ok and maintainer_name_ok and maintainer_email_ok:
            return True

        return (
            "⚠️ author/maintainer metadata does not match "
            "Synopsys, Inc. and ANSYS, Inc. / "
            "pyansys-core@synopsys.com."
        )


class PM015(ProjectMetadata):
    """The LICENSE file includes recognized project license wording."""

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the LICENSE file contains expected MIT or Apache 2.0 text."""
        if not file_exists(root, _LICENSE):
            return None

        content = file_content(root, _LICENSE)

        if (
            "MIT License" in content
            or re.search(
                r"Apache License.*Version 2\.0",
                content,
                re.IGNORECASE | re.DOTALL,
            )
            or "Apache License" in content
        ):
            return True

        return (
            "⚠️ LICENSE file content is missing a recognized "
            "license statement (MIT or Apache 2.0)."
        )


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

        return "⚠️ .github/CODEOWNERS exists but has no owner entries."


def _validate_python_version_spec(spec: str) -> bool | str:
    """Validate that a Python version spec defines supported lower and upper bounds."""
    if not re.search(r">=\d+\.\d+", spec) or not re.search(r"[<,]=?\d+", spec):
        return (
            f"⚠️ requires-python '{spec}' does not declare a supported PyAnsys version range. "
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
