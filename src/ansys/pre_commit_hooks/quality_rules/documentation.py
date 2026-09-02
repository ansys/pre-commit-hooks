# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Documentation checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists

__all__ = ["Documentation", "DOC001", "DOC002", "DOC003", "DOC004", "DOC005", "DOC006", "DOC007"]


class Documentation:
    family = "documentation"


class DOC001(Documentation):
    "doc/source/ structure exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "doc/source/index.rst")


class DOC002(Documentation):
    "conf.py exists"

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "doc/source/conf.py")


class DOC003(Documentation):
    "conf.py includes numpydoc"

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "numpydoc")


class DOC004(Documentation):
    "conf.py includes sphinx_design"

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "sphinx_design")


class DOC005(Documentation):
    "conf.py includes intersphinx"

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "intersphinx")


class DOC006(Documentation):
    "index.rst has Getting started section"

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(root, "doc/source/index.rst", re.compile(r"getting.started", re.I))


class DOC007(Documentation):
    "index.rst has API reference section"

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(
            root, "doc/source/index.rst", re.compile(r"api.reference|api_reference", re.I)
        )
