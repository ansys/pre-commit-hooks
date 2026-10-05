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

"""Build system checks.

This rule set validates repository build metadata and ensures the project uses
an acceptable Python packaging backend.

The checks cover:

* build-system table presence
* setuptools, Poetry, Hatchling, Flit, or PDM detection
* backend preference validation against the repository standard
"""

from __future__ import annotations

from functools import cache
import re

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10.
    import toml as tomllib

    TOMLDecodeError = tomllib.TomlDecodeError
else:
    TOMLDecodeError = tomllib.TOMLDecodeError

from .common import checked_contains, file_content, file_exists

__all__ = [
    "BS001",
    "BS002",
    "BS003",
    "BS004",
    "BS005",
    "BS006",
    "BS007",
    "BS008",
    "BS009",
    "BS010",
    "BS011",
    "BS012",
    "BS013",
    "BS014",
    "BS015",
    "BS016",
    "BuildSystem",
]


_BACKENDS = {
    "flit_core.buildapi": ("Flit", "flit", "flit_core"),
    "poetry.core.masonry.api": ("Poetry", "poetry", "poetry_core"),
    "hatchling.build": ("Hatch", "hatch", "hatchling"),
    "pdm.backend": ("PDM", "pdm", "pdm"),
    "maturin": ("Maturin", "maturin", "maturin"),
    "setuptools.build_meta": ("Setuptools", "setuptools", "setuptools"),
    "setuptools.build_meta:__legacy__": ("Setuptools", "setuptools", "setuptools"),
}


@cache
def _parse_pyproject(content: str) -> dict | None:
    """Parse pyproject.toml content, caching repeated parses."""
    try:
        return tomllib.loads(content)
    except TOMLDecodeError:
        return None


def _load_pyproject(root) -> dict:
    """Load pyproject.toml or return an empty table when it is invalid."""
    if not file_exists(root, "pyproject.toml"):
        return {}
    return _parse_pyproject(file_content(root, "pyproject.toml")) or {}


def _build_system(root) -> dict:
    """Return the build-system table from pyproject.toml."""
    return _load_pyproject(root).get("build-system", {})


def _project(root) -> dict:
    """Return the project table from pyproject.toml."""
    return _load_pyproject(root).get("project", {})


def _project_field_defined(root, field: str) -> bool:
    """Return whether a project field is defined directly or dynamically."""
    project = _project(root)
    return bool(project.get(field) or field in project.get("dynamic", []))


def _has_valid_pyproject(root) -> bool | None:
    """Return whether pyproject.toml exists and contains valid TOML."""
    if not file_exists(root, "pyproject.toml"):
        return None
    return _parse_pyproject(file_content(root, "pyproject.toml")) is not None


def _dependencies(root) -> list[str]:
    """Return regular and optional project dependencies."""
    project = _project(root)
    dependencies = list(project.get("dependencies", []))
    for optional_dependencies in project.get("optional-dependencies", {}).values():
        dependencies.extend(optional_dependencies)
    return dependencies


def _requirement_name(requirement: str) -> str:
    """Return a normalized package name from a dependency requirement."""
    name = re.split(r"[<>=!~;\s\[]", requirement, maxsplit=1)[0]
    return name.lower().replace("-", "_").replace(".", "_")


def _is_pinned(requirement: str) -> bool:
    """Return whether a dependency requirement includes a version operator."""
    return bool(re.search(r"(?:===|==|~=|!=|>=|<=|>|<)", requirement))


def _detect_backend_from_table(build_system: dict) -> tuple[str, str]:
    """Detect the configured backend from a parsed build-system table."""
    backend = build_system.get("build-backend", "")

    result = _BACKENDS.get(backend)
    if result:
        return result[:2]

    if build_system:
        return "Other", "other"

    return "Unknown", "unknown"


def _detect_backend(content: str) -> tuple[str, str]:
    """Detect the configured build backend from pyproject.toml."""
    build_system = _parse_pyproject(content)
    if build_system is None:
        return "Unknown", "unknown"
    return _detect_backend_from_table(build_system.get("build-system", {}))


class BuildSystem:
    """Build system rule family."""

    family = "build_system"


class BS001(BuildSystem):
    """The [build-system] table is declared."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether a build-system table is present in pyproject.toml."""
        return checked_contains(root, "pyproject.toml", "[build-system]")


class BS002(BuildSystem):
    """Uses a supported modern build backend."""

    requires = frozenset({"BS001"})

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
                f"WARN: Uses {name} — consider migrating to Flit, Hatch, "
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
            f"WARN: Legacy file(s) found: {', '.join(found)}. "
            "Remove in favour of pyproject.toml."
        )


class BS004(BuildSystem):
    """The build backend version is pinned in requires."""

    requires = frozenset({"BS001"})

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether the build backend requirement includes a version pin."""
        if not file_exists(root, "pyproject.toml"):
            return None

        build_system = _load_pyproject(root).get("build-system", {})

        requires = build_system.get("requires")
        if not requires:
            return False

        unpinned = [requirement for requirement in requires if not _is_pinned(requirement)]
        if not unpinned:
            return True

        return f"WARN: Unpinned build requirements: {', '.join(unpinned)}."


class BS005(BuildSystem):
    """The build backend is explicitly defined."""

    requires = frozenset({"BS001"})

    @staticmethod
    def check(root) -> bool | None:
        """Return whether build-backend is explicitly configured."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return bool(_build_system(root).get("build-backend"))


class BS006(BuildSystem):
    """The build-system requires list is not empty."""

    requires = frozenset({"BS001"})

    @staticmethod
    def check(root) -> bool | None:
        """Return whether build-system requires contains at least one item."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return bool(_build_system(root).get("requires"))


class BS007(BuildSystem):
    """The configured backend is represented in build-system requires."""

    requires = frozenset({"BS005", "BS006"})

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the backend package appears in build requirements."""
        if not file_exists(root, "pyproject.toml"):
            return None

        build_system = _build_system(root)
        backend = _BACKENDS.get(build_system.get("build-backend", ""))
        if backend is None:
            return True

        return any(
            _requirement_name(requirement) == backend[2]
            for requirement in build_system.get("requires", [])
        )


class BS008(BuildSystem):
    """The project name is defined."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether project.name is present and non-empty."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return _project_field_defined(root, "name")


class BS009(BuildSystem):
    """The project version is defined."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether version is declared directly or dynamically."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return _project_field_defined(root, "version")


class BS010(BuildSystem):
    """The project description is defined."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether description is declared directly or dynamically."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return _project_field_defined(root, "description")


class BS011(BuildSystem):
    """The supported Python version range is declared."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether project.requires-python is present and non-empty."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return bool(_project(root).get("requires-python"))


class BS012(BuildSystem):
    """The pyproject.toml file contains valid TOML."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether pyproject.toml exists and parses successfully."""
        return _has_valid_pyproject(root)


class BS013(BuildSystem):
    """Project dependencies include version pins."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether all declared project dependencies are pinned."""
        if not file_exists(root, "pyproject.toml"):
            return None

        unpinned = [
            requirement for requirement in _dependencies(root) if not _is_pinned(requirement)
        ]
        if not unpinned:
            return True
        return f"WARN: Unpinned dependencies: {', '.join(unpinned)}."


class BS014(BuildSystem):
    """Project dependencies do not contain duplicates."""

    @staticmethod
    def check(root) -> bool | None | str:
        """Return whether regular and optional dependencies are unique."""
        if not file_exists(root, "pyproject.toml"):
            return None

        seen = set()
        duplicates = []
        for requirement in _dependencies(root):
            name = _requirement_name(requirement)
            if name in seen and name not in duplicates:
                duplicates.append(name)
            seen.add(name)

        if not duplicates:
            return True
        return f"WARN: Duplicate dependencies: {', '.join(duplicates)}."


class BS015(BuildSystem):
    """The project license is defined."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether license metadata is declared directly or dynamically."""
        if not file_exists(root, "pyproject.toml"):
            return None
        project = _project(root)
        return bool(_project_field_defined(root, "license") or project.get("license-files"))


class BS016(BuildSystem):
    """The project readme is defined."""

    @staticmethod
    def check(root) -> bool | None:
        """Return whether readme metadata is declared directly or dynamically."""
        if not file_exists(root, "pyproject.toml"):
            return None
        return _project_field_defined(root, "readme")
