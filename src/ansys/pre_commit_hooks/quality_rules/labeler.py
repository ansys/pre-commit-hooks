# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Labeler checks."""

from __future__ import annotations

from .common import file_contains, file_exists

__all__ = ["Labeler", "LB001", "LB002", "LB003", "LB004", "LB005"]


class Labeler:
    family = "labeler"


class LB001(Labeler):
    ".github/labeler.yml exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, ".github/labeler.yml")


class LB002(Labeler):
    ".github/labels.yml exists"

    @staticmethod
    def check(root) -> bool:
        return file_exists(root, ".github/labels.yml")


class LB003(Labeler):
    "labels.yml has 'bug' label"

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "bug")


class LB004(Labeler):
    "labels.yml has 'enhancement' label"

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "enhancement")


class LB005(Labeler):
    "labels.yml has 'documentation' label"

    requires = {"LB002"}

    @staticmethod
    def check(root) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "documentation")
