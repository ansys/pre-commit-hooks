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

"""Documentation structure and Sphinx configuration checks.

The checks cover the documentation source tree, Sphinx extensions and index
sections, and example configuration for supported gallery extensions.
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import ClassVar, Final

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
    _repository_file,
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
    "DOCUMENTATION_QUALITY_RULES",
    "Documentation",
]

_DOC_INDEX: Final[str] = "doc/source/index.rst"
_SPHINX_CONFIG: Final[str] = "doc/source/conf.py"


def _contains(repository_root: Path, relative_path: str, pattern: str | re.Pattern[str]) -> bool:
    """Return whether a readable repository file contains the requested text or pattern."""
    content = file_content(repository_root, relative_path)
    if content is None:
        return False
    if isinstance(pattern, str):
        return pattern in content
    return pattern.search(content) is not None


class Documentation:
    """Documentation rule family."""

    family: ClassVar[str] = "documentation"


class DOC001(Documentation):
    """The doc/source structure exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation index exists."""
        return file_exists(repository_root, _DOC_INDEX)


class DOC002(Documentation):
    """The Sphinx config exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the Sphinx configuration exists."""
        return file_exists(repository_root, _SPHINX_CONFIG)


class DOC003(Documentation):
    """The Sphinx config includes numpydoc."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether numpydoc is enabled in the Sphinx configuration."""
        return _contains(repository_root, _SPHINX_CONFIG, "numpydoc")


class DOC004(Documentation):
    """Sphinx Design is configured when its components are used."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend sphinx_design when it is not configured."""
        if _contains(repository_root, _SPHINX_CONFIG, "sphinx_design"):
            return True
        return (
            "RECOMMENDATION: Enable sphinx_design in doc/source/conf.py when using "
            "Sphinx Design components."
        )


class DOC005(Documentation):
    """The Sphinx config includes intersphinx."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether intersphinx is enabled in the Sphinx configuration."""
        return _contains(repository_root, _SPHINX_CONFIG, "intersphinx")


class DOC006(Documentation):
    """The index page has a getting started section."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation index has a getting-started section."""
        return _contains(repository_root, _DOC_INDEX, re.compile(r"getting.started", re.IGNORECASE))


class DOC007(Documentation):
    """The index page has an API reference section."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation index has an API reference section."""
        return _contains(
            repository_root,
            _DOC_INDEX,
            re.compile(r"api.reference|api_reference", re.IGNORECASE),
        )


class DOC008(Documentation):
    """Gallery examples are recommended when a gallery extension is enabled."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that enabled gallery extensions have example files configured."""
        conf = file_content(repository_root, _SPHINX_CONFIG)
        if conf is None:
            return True

        has_sphinx_gallery = bool(
            re.search(r"sphinx_gallery(?:\.gen_gallery)?", conf, re.IGNORECASE)
        )
        has_nbsphinx = bool(re.search(r"\bnbsphinx\b", conf, re.IGNORECASE))

        if not has_sphinx_gallery and not has_nbsphinx:
            return True

        if has_sphinx_gallery:
            if not (re.search(r"\bexamples_dirs\b", conf) and re.search(r"\bgallery_dirs\b", conf)):
                return DOC008._examples_recommendation()
            examples_dirs = DOC008._extract_examples_dirs(conf)
            if examples_dirs and all(
                DOC008._configured_examples_dir_has_files(repository_root, path)
                for path in examples_dirs
            ):
                return True
            return DOC008._examples_recommendation()

        if any(
            DOC008._dir_has_files(repository_root, candidate)
            for candidate in ("examples", "doc/examples", "doc/source/examples")
        ):
            return True
        return DOC008._examples_recommendation()

    @staticmethod
    def _examples_recommendation() -> str:
        """Return guidance for adding examples to an enabled gallery extension."""
        return (
            "RECOMMENDATION: Configure an examples directory with example files for the enabled "
            "gallery extension."
        )

    @staticmethod
    def _extract_examples_dirs(conf: str) -> list[str]:
        """Return paths configured under the ``examples_dirs`` key."""
        match = re.search(
            r"['\"]?examples_dirs['\"]?\s*[:=]\s*(\[[^\]]*\]|\"[^\"]+\"|'[^']+')",
            conf,
            re.DOTALL,
        )
        if not match:
            return []
        return [path for _, path in re.findall(r"(['\"])(.+?)\1", match.group(1))]

    @staticmethod
    def _dir_has_files(repository_root: Path, relative_path: str) -> bool:
        """Return whether a repository directory tree contains a file."""
        directory = _repository_file(repository_root, relative_path)
        if directory is None:
            return False
        try:
            return directory.is_dir() and DOC008._dir_tree_has_files(directory)
        except OSError:
            return False

    @staticmethod
    def _dir_tree_has_files(directory: Path) -> bool:
        """Return whether a directory tree contains a regular file."""
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    return True
                if entry.is_dir() and not entry.is_symlink() and DOC008._dir_tree_has_files(entry):
                    return True
        except OSError:
            return False
        return False

    @staticmethod
    def _configured_examples_dir_has_files(repository_root: Path, configured_path: str) -> bool:
        """Return whether a configured examples path exists and contains a file.

        Paths in ``examples_dirs`` are usually relative to ``doc/source/conf.py``;
        repository-root-relative paths are also supported.
        """
        candidates = (f"doc/source/{configured_path}", configured_path)
        return any(DOC008._dir_has_files(repository_root, path) for path in candidates)


DOCUMENTATION_QUALITY_RULES: tuple[type[Documentation], ...] = tuple(
    sorted(Documentation.__subclasses__(), key=lambda rule_class: rule_class.__name__)
)
