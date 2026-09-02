# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Vale checks."""

from __future__ import annotations

from .common import file_contains, file_exists

__all__ = ["Vale", "VL001", "VL002", "VL003", "VL004", "VL005"]


class Vale:
    family = "vale"


class VL001(Vale):
    "doc/.vale.ini exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "doc/.vale.ini")


class VL002(Vale):
    "Vale uses Google style package"

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/.vale.ini"):
            return None
        return file_contains(root, "doc/.vale.ini", "Google")


class VL003(Vale):
    "Vale uses ANSYS vocabulary"

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, "doc/.vale.ini"):
            return None
        return file_contains(root, "doc/.vale.ini", "ANSYS")


class VL004(Vale):
    "ANSYS accept.txt vocabulary exists"

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/accept.txt")


class VL005(Vale):
    "ANSYS reject.txt vocabulary exists"

    requires = {"VL001"}

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/reject.txt")
