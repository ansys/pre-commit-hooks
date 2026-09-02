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

"""Documentation checks."""

from __future__ import annotations

import re

from .common import file_contains, file_exists

__all__ = ["Documentation", "DOC001", "DOC002", "DOC003", "DOC004", "DOC005", "DOC006", "DOC007"]


class Documentation:
    """Documentation rule family."""

    family = "documentation"


class DOC001(Documentation):
    """The doc/source structure exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the documentation index file exists."""
        return file_exists(root, "doc/source/index.rst")


class DOC002(Documentation):
    """The Sphinx config exists."""

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool:
        """Return whether the Sphinx conf.py file exists."""
        return file_exists(root, "doc/source/conf.py")


class DOC003(Documentation):
    """The Sphinx config includes numpydoc."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether numpydoc is enabled in the Sphinx config."""
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "numpydoc")


class DOC004(Documentation):
    """The Sphinx config includes sphinx_design."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether sphinx_design is enabled in the Sphinx config."""
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "sphinx_design")


class DOC005(Documentation):
    """The Sphinx config includes intersphinx."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether intersphinx is enabled in the Sphinx config."""
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "intersphinx")


class DOC006(Documentation):
    """The index page has a getting started section."""

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the docs index includes a getting-started section."""
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(root, "doc/source/index.rst", re.compile(r"getting.started", re.I))


class DOC007(Documentation):
    """The index page has an API reference section."""

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the docs index includes an API reference section."""
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(
            root, "doc/source/index.rst", re.compile(r"api.reference|api_reference", re.I)
        )
