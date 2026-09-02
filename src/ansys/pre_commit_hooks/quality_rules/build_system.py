# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

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
    m = re.search(r'build-backend\s*=\s*["\']([^"\']+)["\']', content)
    backend = m.group(1) if m else ""
    for pattern, name in _BACKENDS.items():
        if pattern in backend:
            return name, pattern.split(".")[0].replace("_core", "")
    if "[build-system]" in content:
        return "Other", "other"
    return "Unknown", "unknown"


class BuildSystem:
    family = "build_system"


class BS001(BuildSystem):
    "[build-system] table declared"

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "pyproject.toml"):
            return None
        return file_contains(root, "pyproject.toml", "[build-system]")


class BS002(BuildSystem):
    "Uses a supported modern build backend"

    requires = {"BS001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        name, key = _detect_backend(file_content(root, "pyproject.toml"))
        if key == "unknown":
            return False
        if key == "setuptools":
            return (
                f"⚠️ Uses {name} — consider migrating to Flit, Hatch, or Poetry for simpler config."
            )
        return True


class BS003(BuildSystem):
    "No legacy setup.py or setup.cfg"

    @staticmethod
    def check(root) -> bool | str:
        has_py = file_exists(root, "setup.py")
        has_cfg = file_exists(root, "setup.cfg")
        if not has_py and not has_cfg:
            return True
        found = [f for f, present in [("setup.py", has_py), ("setup.cfg", has_cfg)] if present]
        return f"⚠️ Legacy file(s) found: {', '.join(found)}. Remove in favour of pyproject.toml."


class BS004(BuildSystem):
    "Build backend version pinned in requires"

    requires = {"BS001"}

    @staticmethod
    def check(root) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        m = re.search(r"requires\s*=\s*\[([^\]]+)\]", content)
        if not m:
            return False
        if re.search(r"[><=!~]", m.group(1)):
            return True
        return "⚠️ Build backend in requires has no version pin (e.g. >=x.y)."
