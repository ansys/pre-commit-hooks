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

"""Vale checks."""

from __future__ import annotations

from ansys.pre_commit_hooks.quality_rules.common import file_contains, file_exists

__all__ = ["Vale", "VL001", "VL002", "VL003", "VL004", "VL005"]


class Vale:
    """Vale rule family."""

    family = "vale"


class VL001(Vale):
    """The doc/.vale.ini file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the Vale config exists."""
        return file_exists(root, "doc/.vale.ini")


class VL002(Vale):
    """Vale uses the Google style package."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Vale config targets the Google style package."""
        if not file_exists(root, "doc/.vale.ini"):
            return None
        return file_contains(root, "doc/.vale.ini", "Google")


class VL003(Vale):
    """Vale uses the ANSYS vocabulary."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Vale config references the ANSYS vocabulary."""
        if not file_exists(root, "doc/.vale.ini"):
            return None
        return file_contains(root, "doc/.vale.ini", "ANSYS")


class VL004(Vale):
    """The ANSYS accept.txt vocabulary exists."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool:
        """Return whether the accepted vocabulary file exists."""
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/accept.txt")


class VL005(Vale):
    """The ANSYS reject.txt vocabulary exists."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool:
        """Return whether the rejected vocabulary file exists."""
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/reject.txt")
