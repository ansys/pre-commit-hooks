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

"""Documentation checks.

This rule set validates the repository documentation structure and Sphinx
configuration.

The checks cover:

* doc/source directory presence
* Sphinx config file presence
* numpydoc configuration
* expected documentation conventions and structure
"""

from __future__ import annotations

import re

from ansys.pre_commit_hooks.quality_rules.common import (
    checked_contains,
    file_content,
    file_exists,
)

__all__ = [
    "DOC001",
    "DOC002",
    "DOC003",
    "DOC004",
    "DOC005",
    "DOC006",
    "DOC007",
    "DOC008",
    "Documentation",
]


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
        """Return whether the Sphinx configuration file exists."""
        return file_exists(root, "doc/source/conf.py")


class DOC003(Documentation):
    """The Sphinx config includes numpydoc."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether numpydoc is enabled in the Sphinx configuration."""
        return checked_contains(root, "doc/source/conf.py", "numpydoc")


class DOC004(Documentation):
    """The Sphinx config includes sphinx_design."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether sphinx_design is enabled in the Sphinx configuration."""
        return checked_contains(root, "doc/source/conf.py", "sphinx_design")


class DOC005(Documentation):
    """The Sphinx config includes intersphinx."""

    requires = {"DOC002"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether intersphinx is enabled in the Sphinx configuration."""
        return checked_contains(root, "doc/source/conf.py", "intersphinx")


class DOC006(Documentation):
    """The index page has a getting started section."""

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the documentation index includes a getting-started section."""
        return checked_contains(
            root,
            "doc/source/index.rst",
            re.compile(r"getting.started", re.IGNORECASE),
        )


class DOC007(Documentation):
    """The index page has an API reference section."""

    requires = {"DOC001"}

    @staticmethod
    def check(root) -> bool | None:
        """Return whether the documentation index includes an API reference section."""
        return checked_contains(
            root,
            "doc/source/index.rst",
            re.compile(
                r"api.reference|api_reference",
                re.IGNORECASE,
            ),
        )


class DOC008(Documentation):
    """Gallery examples are configured when gallery extensions are enabled.

    Configure examples in ``doc/source/conf.py`` via ``sphinx_gallery_conf['examples_dirs']``.
    For ``nbsphinx``, ensure the extension is enabled in ``doc/source/conf.py`` and an
    examples directory exists with at least one file.
    """

    requires = {"DOC001", "DOC002"}
    pass_detail: str | None = None

    @classmethod
    def check(cls, root) -> bool | None:
        """Return whether examples are configured for the detected gallery extension."""
        cls.pass_detail = None
        conf = file_content(root, "doc/source/conf.py")

        if not conf:
            return None

        has_sphinx_gallery = bool(
            re.search(
                r"sphinx_gallery(?:\.gen_gallery)?",
                conf,
                re.IGNORECASE,
            )
        )
        has_nbsphinx = bool(re.search(r"\bnbsphinx\b", conf, re.IGNORECASE))

        if not has_sphinx_gallery and not has_nbsphinx:
            return None

        if has_sphinx_gallery:
            if not (re.search(r"\bexamples_dirs\b", conf) and re.search(r"\bgallery_dirs\b", conf)):
                return False

            examples_dirs = cls._extract_examples_dirs(conf)
            if not examples_dirs:
                return False

            configured_ok = all(
                cls._configured_examples_dir_has_files(root, path) for path in examples_dirs
            )
            if configured_ok:
                cls.pass_detail = (
                    "Examples configured in doc/source/conf.py via examples_dirs="
                    f"{examples_dirs}."
                )
            return configured_ok

        for candidate in ("examples", "doc/examples", "doc/source/examples"):
            if cls._dir_has_files(root, candidate):
                cls.pass_detail = (
                    "nbsphinx enabled in doc/source/conf.py and examples found in " f"{candidate}."
                )
                return True

        return False

    @staticmethod
    def _extract_examples_dirs(conf: str) -> list[str]:
        """Return path strings configured under the ``examples_dirs`` key."""
        match = re.search(
            r"['\"]?examples_dirs['\"]?\s*[:=]\s*(\[[^\]]*\]|\"[^\"]+\"|'[^']+')",
            conf,
            re.DOTALL,
        )
        if not match:
            return []

        raw_value = match.group(1)
        return [path for _, path in re.findall(r"(['\"])(.+?)\1", raw_value)]

    @staticmethod
    def _dir_has_files(root, path: str) -> bool:
        """Return whether the given directory exists and has at least one file."""
        try:
            directory = root.joinpath(path)
            if not directory.is_dir():
                return False

            for entry in directory.iterdir():
                if entry.is_file():
                    return True
                if entry.is_dir() and DOC008._dir_tree_has_files(entry):
                    return True

            return False
        except (AttributeError, OSError, TypeError, ValueError):
            return False

    @staticmethod
    def _dir_tree_has_files(directory) -> bool:
        """Return whether a directory tree contains at least one file."""
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    return True
                if entry.is_dir() and DOC008._dir_tree_has_files(entry):
                    return True
        except (AttributeError, OSError, TypeError, ValueError):
            return False

        return False

    @staticmethod
    def _configured_examples_dir_has_files(root, configured_path: str) -> bool:
        """Return whether a configured examples path exists and is non-empty.

        Paths in ``examples_dirs`` are typically relative to ``doc/source/conf.py``.
        For compatibility, this also checks repository-root-relative paths.
        """
        candidates = [f"doc/source/{configured_path}", configured_path]
        return any(DOC008._dir_has_files(root, candidate) for candidate in candidates)
