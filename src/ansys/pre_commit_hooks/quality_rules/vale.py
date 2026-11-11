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

This rule set validates the documentation Vale configuration in
``doc/.vale.ini``.

The checks cover:

* The ``doc/.vale.ini`` file exists
* The ``Google`` package is listed in ``Packages`` and applied through
  ``BasedOnStyles``
* The ``ANSYS`` vocabulary is enabled through ``Vocab``
* The ``ANSYS`` vocabulary provides ``accept.txt`` and ``reject.txt`` files

Vocabulary files are looked up under ``StylesPath``, relative to the ``doc``
directory, in the Vale 3 layout (``config/vocabularies/ANSYS``) or the legacy
layout (``Vocab/ANSYS``). Missing, unreadable, or invalid configuration is
reported as an ``ERROR``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import configparser
from pathlib import Path, PurePosixPath
from typing import ClassVar, Final

from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult, file_content, file_exists

__all__ = [
    "VL001",
    "VL002",
    "VL003",
    "VL004",
    "VL005",
    "Vale",
]

_DOC_DIRECTORY: Final[str] = "doc"
_VALE_CONFIG: Final[str] = f"{_DOC_DIRECTORY}/.vale.ini"
_GLOBAL_SECTION: Final[str] = "__vale_global__"
_GOOGLE_PACKAGE: Final[str] = "Google"
_ANSYS_VOCABULARY: Final[str] = "ANSYS"
_VOCABULARY_DIRECTORIES: Final[tuple[str, ...]] = (
    f"config/vocabularies/{_ANSYS_VOCABULARY}",
    f"Vocab/{_ANSYS_VOCABULARY}",
)


def _load_configuration(repository_root: Path) -> configparser.ConfigParser | str:
    """Load and parse the Vale configuration.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    configparser.ConfigParser or str
        The parsed configuration, with top-level keys stored in a synthetic
        global section, or an ``"ERROR: ..."`` message when the file cannot be
        read or parsed.
    """
    content = file_content(repository_root, _VALE_CONFIG)
    if content is None:
        return f"ERROR: Cannot read {_VALE_CONFIG} as UTF-8 within the repository."
    # Interpolation is disabled because Vale values such as
    # ``WordTemplate = \b(?:%s)\b`` contain literal percent signs.
    parser = configparser.ConfigParser(
        interpolation=None,
        strict=False,
        delimiters=("=",),
        comment_prefixes=("#", ";"),
        inline_comment_prefixes=("#", ";"),
    )
    try:
        parser.read_string(f"[{_GLOBAL_SECTION}]\n{content}", source=_VALE_CONFIG)
    except configparser.Error:
        return f"ERROR: Invalid INI syntax in {_VALE_CONFIG}."
    return parser


def _setting(parser: configparser.ConfigParser, section: str, key: str) -> str | None:
    """Return a setting value without surrounding whitespace or quotes.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parsed Vale configuration.
    section : str
        Section that holds the setting.
    key : str
        Setting name, matched case-insensitively.

    Returns
    -------
    str or None
        The unquoted value, or ``None`` when the setting is absent.
    """
    value = parser.get(section, key, fallback=None)
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1].strip()
    return value


def _list_setting(parser: configparser.ConfigParser, section: str, key: str) -> list[str]:
    """Split a comma-separated setting into its non-empty items.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parsed Vale configuration.
    section : str
        Section that holds the setting.
    key : str
        Setting name, matched case-insensitively.

    Returns
    -------
    list[str]
        The stripped items, or an empty list when the setting is absent.
    """
    value = _setting(parser, section, key)
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _package_name(package: str) -> str:
    """Return the package name from a Vale package name or download URL.

    Parameters
    ----------
    package : str
        A ``Packages`` entry, for example ``"Google"`` or
        ``"https://example.com/Google.zip"``.

    Returns
    -------
    str
        The package name without any URL path or ``.zip`` suffix.
    """
    return package.rstrip("/").rsplit("/", 1)[-1].removesuffix(".zip")


def _check_vocabulary_file(repository_root: Path, file_name: str) -> RuleCheckResult:
    """Check whether an ANSYS vocabulary file exists under ``StylesPath``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    file_name : str
        Vocabulary file name, ``"accept.txt"`` or ``"reject.txt"``.

    Returns
    -------
    bool or str
        ``True`` when the file exists in a supported vocabulary directory, or
        an ``"ERROR: ..."`` message that names the expected location.
    """
    parser = _load_configuration(repository_root)
    if isinstance(parser, str):
        return parser
    styles_path = _setting(parser, _GLOBAL_SECTION, "StylesPath")
    if not styles_path:
        return f"ERROR: {_VALE_CONFIG} must set StylesPath to locate the ANSYS vocabulary."
    styles_directory = PurePosixPath(_DOC_DIRECTORY, styles_path)
    candidates = [
        (styles_directory / vocabulary_directory / file_name).as_posix()
        for vocabulary_directory in _VOCABULARY_DIRECTORIES
    ]
    if any(file_exists(repository_root, candidate) for candidate in candidates):
        return True
    return f"ERROR: The ANSYS vocabulary file {candidates[0]} does not exist."


class Vale(ABC):
    """Vale rule family.

    Base class of the Vale quality rules. Each rule is a subclass named
    ``VL<nnn>`` with a static ``check`` method that evaluates the documentation
    Vale configuration independently. Missing or unreadable configuration is
    reported as an error rather than skipped.
    """

    family: ClassVar[str] = "vale"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a Vale rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, unused by this rule family.

        Returns
        -------
        bool or str
            ``True`` when the rule passes, ``False`` for an error, or a string
            prefixed with ``"ERROR: "``.
        """
        raise NotImplementedError


class VL001(Vale):
    """The doc/.vale.ini file exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the Vale configuration exists."""
        return file_exists(repository_root, _VALE_CONFIG)


class VL002(Vale):
    """Vale uses the Google style package."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that Google is both installed and applied.

        Returns
        -------
        bool or str
            ``True`` when ``Packages`` lists Google and a ``BasedOnStyles``
            setting applies it, otherwise an ``"ERROR: ..."`` message.
        """
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        packages = _list_setting(parser, _GLOBAL_SECTION, "Packages")
        if _GOOGLE_PACKAGE not in {_package_name(package) for package in packages}:
            return f"ERROR: {_VALE_CONFIG} must list {_GOOGLE_PACKAGE} in Packages."
        if not any(
            _GOOGLE_PACKAGE in _list_setting(parser, section, "BasedOnStyles")
            for section in parser.sections()
        ):
            return f"ERROR: {_VALE_CONFIG} must apply {_GOOGLE_PACKAGE} through BasedOnStyles."
        return True


class VL003(Vale):
    """Vale uses the ANSYS vocabulary."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``Vocab`` enables the ANSYS vocabulary."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        if _ANSYS_VOCABULARY in _list_setting(parser, _GLOBAL_SECTION, "Vocab"):
            return True
        return f"ERROR: {_VALE_CONFIG} must set Vocab to include {_ANSYS_VOCABULARY}."


class VL004(Vale):
    """The ANSYS accept.txt vocabulary exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the ANSYS accept.txt vocabulary file exists."""
        return _check_vocabulary_file(repository_root, "accept.txt")


class VL005(Vale):
    """The ANSYS reject.txt vocabulary exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the ANSYS reject.txt vocabulary file exists."""
        return _check_vocabulary_file(repository_root, "reject.txt")
