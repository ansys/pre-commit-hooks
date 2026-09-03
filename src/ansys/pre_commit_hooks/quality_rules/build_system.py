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

"""Build system checks."""

from __future__ import annotations

import re

from .common import file_contains, file_content, file_exists

__all__ = ["BuildSystem", "BS001", "BS002", "BS003", "BS004"]


_BACKENDS = {
    "flit_core": "Flit",
    "poetry.core": "Poetry",
    "hatchling": "Hatch",
    "pdm": "PDM",
    "maturin": "Maturin",
    "setuptools": "Setuptools",
}


def _detect_backend(content: str) -> tuple[str, str]:
    """Detect the configured build backend from pyproject.toml."""
    match = re.search(
        r'build-backend\s*=\s*["\']([^"\']+)["\']',
        content,
    )

    backend = match.group(1) if match else ""

    for pattern, name in _BACKENDS.items():
        if pattern in backend:
            return name, pattern.split(".")[0].replace("_core", "")

    if "[build-system]" in content:
        return "Other", "other"

    return "Unknown", "unknown"


class BuildSystem:
    """Build system rule family."""

    family = "build_system"


class BS001(BuildSystem):
    """The [build-system] table is declared."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether a build-system table is present in pyproject.toml."""
        if not file_exists(root, "pyproject.toml"):
            return None

        return file_contains(root, "pyproject.toml", "[build-system]")


class BS002(BuildSystem):
    """Uses a supported modern build backend."""

    requires = {"BS001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the project uses a supported modern build backend."""
        if not file_exists(root, "pyproject.toml"):
            return None

        name, key = _detect_backend(file_content(root, "pyproject.toml"))

        if key == "unknown":
            return False

        if key == "setuptools":
            return (
                f"⚠️ Uses {name} — consider migrating to Flit, Hatch, "
                "or Poetry for simpler config."
            )

        return True


class BS003(BuildSystem):
    """No legacy setup.py or setup.cfg files are present."""

    @staticmethod
    def check(root) -> bool | str:
        """Return whether the project uses only pyproject.toml for packaging metadata."""
        has_setup_py = file_exists(root, "setup.py")
        has_setup_cfg = file_exists(root, "setup.cfg")

        if not has_setup_py and not has_setup_cfg:
            return True

        found = [
            filename
            for filename, exists in (
                ("setup.py", has_setup_py),
                ("setup.cfg", has_setup_cfg),
            )
            if exists
        ]

        return (
            f"⚠️ Legacy file(s) found: {', '.join(found)}. " "Remove in favour of pyproject.toml."
        )


class BS004(BuildSystem):
    """The build backend version is pinned in requires."""

    requires = {"BS001"}

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the build backend requirement includes a version pin."""
        if not file_exists(root, "pyproject.toml"):
            return None

        content = file_content(root, "pyproject.toml")

        match = re.search(
            r"requires\s*=\s*\[([^\]]+)\]",
            content,
        )

        if not match:
            return False

        if re.search(r"[><=!~]", match.group(1)):
            return True

        return "⚠️ Build backend in requires has no version pin " "(e.g. >=x.y)."
