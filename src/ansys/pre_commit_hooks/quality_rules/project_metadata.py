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

"""Project metadata checks."""

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
]


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
        """Return whether the code of conduct file is present."""
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
        return file_exists(root, "LICENSE")


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
        """Return whether the code owners file is present."""
        return file_exists(root, ".github/CODEOWNERS")


class PM010(ProjectMetadata):
    """Pyproject.toml references the README file."""

    requires = {"PM007"}

    @staticmethod
    def check(root, readme_path: str | None) -> bool | None | str:
        """Return whether pyproject.toml references the expected README file."""
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", content):
            m = re.search(
                r"\[tool\.poetry\][\s\S]*?readme\s*=\s*[\"']([^\"']+)[\"']",
                content,
                re.M,
            )
            if m:
                return True
            return False
        rm = readme_path or "README.rst"
        if rm in content:
            return True
        if "README" in content:
            return "⚠️ readme key found but exact README filename not confirmed."
        return False


class PM011(ProjectMetadata):
    """Pyproject.toml references the LICENSE file."""

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether pyproject.toml references the license file."""
        if not file_exists(root, "pyproject.toml"):
            return None
        c = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", c):
            return bool(re.search(r"\[tool\.poetry\][\s\S]*?license\s*=", c, re.M))
        return bool(
            re.search(r"license-files\s*=", c)
            or re.search(r"license\s*=\s*\{[^}]*file", c)
            or re.search(r'license\s*=\s*["\']LICENSE["\']', c)
        )


class PM012(ProjectMetadata):
    """Project name follows the ansys-*-* convention."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the project name matches the PyAnsys naming convention."""
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        match = re.search(r'^name\s*=\s*["\']([^"\']+)["\']', content, re.M)
        if not match:
            return "⚠️ project name not found in pyproject.toml."
        name = match.group(1)
        if re.fullmatch(r"ansys-[a-z0-9-]+-[a-z0-9-]+", name):
            return True
        return f"⚠️ project name '{name}' does not match ansys-*-*."


class PM013(ProjectMetadata):
    """Project version follows semantic versioning."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the project version uses semantic versioning."""
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.M)
        if not match:
            return "⚠️ project version not found in pyproject.toml."
        version = match.group(1)
        if re.fullmatch(r"\d+\.\d+\.\d+(?:[.-]?(?:a|b|rc|dev)\d+)?", version):
            return True
        return f"⚠️ project version '{version}' does not follow semantic versioning."


class PM014(ProjectMetadata):
    """Project author and maintainer metadata matches the PyAnsys defaults."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether author and maintainer metadata are configured as expected."""
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        name_ok = bool(
            re.search(
                r'authors\s*=\s*\[[\s\S]*?name\s*=\s*["\']Synopsys, Inc\. and ANSYS, Inc\.["\']',
                content,
            )
        )
        email_ok = bool(
            re.search(
                r'authors\s*=\s*\[[\s\S]*?email\s*=\s*["\']pyansys-core@synopsys.com["\']', content
            )
        )
        maintainer_name_ok = bool(
            re.search(
                r'maintainers\s*=\s*\[[\s\S]*?name\s*=\s*["\']Synopsys, Inc\. and ANSYS, Inc\.["\']',  # noqa: E501
                content,
            )
        )
        maintainer_email_ok = bool(
            re.search(
                r'maintainers\s*=\s*\[[\s\S]*?email\s*=\s*["\']pyansys-core@synopsys.com["\']',
                content,
            )
        )
        if name_ok and email_ok and maintainer_name_ok and maintainer_email_ok:
            return True
        return (
            "⚠️ author/maintainer metadata does not match "
            "Synopsys, Inc. and ANSYS, Inc. / pyansys-core@synopsys.com."
        )


class PM015(ProjectMetadata):
    """The LICENSE file includes the MIT License wording."""

    requires = {"PM006"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the LICENSE file contains the expected MIT License text."""
        if not file_exists(root, "LICENSE"):
            return None
        content = file_content(root, "LICENSE")
        if "MIT License" in content:
            return True
        return '⚠️ LICENSE file content is missing "MIT License".'
