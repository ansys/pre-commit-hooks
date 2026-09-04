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

"""Vale configuration checks.

This rule set validates that Vale is configured according to PyAnsys
documentation standards.

The checks cover:

* Vale configuration
    - doc/.vale.ini exists
    - Google style package is configured
    - ANSYS vocabulary is configured

* Vocabulary files
    - ANSYS accept.txt exists
    - ANSYS reject.txt exists (recommended)
"""

from __future__ import annotations

from ansys.pre_commit_hooks.quality_rules.common import (
    checked_contains,
    file_exists,
)

__all__ = [
    "Vale",
    "VL001",
    "VL002",
    "VL003",
    "VL004",
    "VL005",
]

_VALE_CONFIG = "doc/.vale.ini"
_ACCEPT_VOCAB = "doc/styles/config/vocabularies/ANSYS/accept.txt"
_REJECT_VOCAB = "doc/styles/config/vocabularies/ANSYS/reject.txt"


class Vale:
    """Vale rule family."""

    family = "vale"


class VL001(Vale):
    """The doc/.vale.ini file exists."""

    @staticmethod
    def check(root) -> bool:
        """Return whether the Vale configuration exists."""
        return file_exists(root, _VALE_CONFIG)


class VL002(Vale):
    """Vale uses the Google style package."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Vale configuration uses the Google style package."""
        return checked_contains(root, _VALE_CONFIG, "Google")


class VL003(Vale):
    """Vale uses the ANSYS vocabulary."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the Vale configuration references the ANSYS vocabulary."""
        return checked_contains(root, _VALE_CONFIG, "ANSYS")


class VL004(Vale):
    """The ANSYS accept.txt vocabulary exists."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool:
        """Return whether the accepted vocabulary file exists."""
        return file_exists(root, _ACCEPT_VOCAB)


class VL005(Vale):
    """The ANSYS reject.txt vocabulary exists."""

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | str:
        """Return whether the recommended rejected vocabulary file exists."""
        if file_exists(root, _REJECT_VOCAB):
            return True

        return "⚠️ ANSYS reject.txt vocabulary not found. " "The file is optional but recommended."
