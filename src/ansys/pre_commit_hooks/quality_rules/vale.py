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
``doc/.vale.ini`` and the files it depends on.

The checks cover:

* The ``doc/.vale.ini`` file exists
* The ``Google`` package is listed in ``Packages`` and applied through
  ``BasedOnStyles`` together with the built-in ``Vale`` style
* The ``ANSYS`` vocabulary is enabled through ``Vocab`` and provides
  ``accept.txt`` and ``reject.txt`` files
* The core settings (``StylesPath``, ``MinAlertLevel``, ``IgnoredScopes``,
  ``SkippedScopes``, and ``WordTemplate``) follow the PyAnsys template
* Python, Markdown, and reStructuredText files are linted, Python files are
  parsed as Markdown, and ``Vale.Terms``, ``TokenIgnores``, and
  ``BlockIgnores`` are configured
* The styles ``.gitignore`` ignores everything except the ANSYS vocabulary
* The ``accept.txt`` vocabulary is populated, without duplicate or blank lines
* Legacy codespell word lists are migrated to the ANSYS vocabulary

Paths such as the vocabulary and the styles ``.gitignore`` are resolved under
``StylesPath``, relative to the ``doc`` directory. Vocabulary files are looked
up in the Vale 3 layout (``config/vocabularies/ANSYS``) or the legacy layout
(``Vocab/ANSYS``). Missing, unreadable, or invalid configuration is reported
as an ``ERROR``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import configparser
import fnmatch
from pathlib import Path, PurePosixPath
import re
from typing import ClassVar, Final

from ansys.pre_commit_hooks.quality_rules.common import RuleCheckResult, file_content, file_exists

__all__ = [
    "VL001",
    "VL002",
    "VL003",
    "VL004",
    "VL005",
    "VL006",
    "VL007",
    "VL008",
    "VL009",
    "VL010",
    "VL011",
    "VL012",
    "VL013",
    "VL014",
    "VL015",
    "VL016",
    "VL017",
    "VL018",
    "VL019",
    "Vale",
]

_DOC_DIRECTORY: Final[str] = "doc"
_VALE_CONFIG: Final[str] = f"{_DOC_DIRECTORY}/.vale.ini"
_GLOBAL_SECTION: Final[str] = "__vale_global__"
_FORMATS_SECTION: Final[str] = "formats"
_GOOGLE_PACKAGE: Final[str] = "Google"
_VALE_STYLE: Final[str] = "Vale"
_ANSYS_VOCABULARY: Final[str] = "ANSYS"
_VOCABULARY_DIRECTORIES: Final[tuple[str, ...]] = (
    f"config/vocabularies/{_ANSYS_VOCABULARY}",
    f"Vocab/{_ANSYS_VOCABULARY}",
)
_EXPECTED_STYLES_PATH: Final[str] = "styles"
_ALERT_LEVELS: Final[tuple[str, ...]] = ("suggestion", "warning", "error")
_MINIMUM_ALERT_LEVEL: Final[str] = "warning"
_IGNORED_SCOPES: Final[tuple[str, ...]] = ("code", "tt")
_SKIPPED_SCOPES: Final[tuple[str, ...]] = ("script", "style", "pre", "figure")
_WORD_TEMPLATE: Final[str] = r"\b(?:%s)\b"
_LINTED_EXTENSIONS: Final[tuple[str, ...]] = ("py", "md", "rst")
_STYLES_GITIGNORE_PATTERNS: Final[tuple[str, ...]] = (
    "*",
    f"!**/{_ANSYS_VOCABULARY}/accept.txt",
    f"!**/{_ANSYS_VOCABULARY}/reject.txt",
    "!.gitignore",
)
_CODESPELL_FILES: Final[tuple[str, ...]] = (".codespell.exclude", ".codespell.ignore")
_BRACE_GROUP: Final[re.Pattern[str]] = re.compile(r"\{([^{}]*)\}")


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


def _style_sections(parser: configparser.ConfigParser) -> list[str]:
    """Return the glob sections that apply settings to matching files.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parsed Vale configuration.

    Returns
    -------
    list[str]
        Section names other than the global and ``[formats]`` sections.
    """
    return [
        section
        for section in parser.sections()
        if section not in {_GLOBAL_SECTION, _FORMATS_SECTION}
    ]


def _based_on_styles(parser: configparser.ConfigParser) -> set[str]:
    """Return every style applied through ``BasedOnStyles``.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parsed Vale configuration.

    Returns
    -------
    set[str]
        The union of the ``BasedOnStyles`` lists of all glob sections.
    """
    return {
        style
        for section in _style_sections(parser)
        for style in _list_setting(parser, section, "BasedOnStyles")
    }


def _expand_braces(pattern: str) -> list[str]:
    """Expand ``{a,b}`` alternatives in a Vale section glob.

    Parameters
    ----------
    pattern : str
        Section glob, for example ``"*.{py,md,rst}"``.

    Returns
    -------
    list[str]
        ``fnmatch`` patterns without brace groups.
    """
    match = _BRACE_GROUP.search(pattern)
    if match is None:
        return [pattern]
    prefix, suffix = pattern[: match.start()], pattern[match.end() :]
    return [
        expanded
        for alternative in match.group(1).split(",")
        for expanded in _expand_braces(f"{prefix}{alternative.strip()}{suffix}")
    ]


def _section_matches_extension(section: str, extension: str) -> bool:
    """Return whether a section glob matches files with an extension.

    Parameters
    ----------
    section : str
        Section glob, for example ``"*.{py,md,rst}"``.
    extension : str
        File extension without the leading dot.

    Returns
    -------
    bool
        ``True`` when the glob matches a file named ``file.<extension>``.
    """
    return any(
        fnmatch.fnmatchcase(f"file.{extension}", pattern) for pattern in _expand_braces(section)
    )


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


def _styles_directory(parser: configparser.ConfigParser) -> PurePosixPath | str:
    """Return the styles directory relative to the repository root.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parsed Vale configuration.

    Returns
    -------
    pathlib.PurePosixPath or str
        ``doc/<StylesPath>``, or an ``"ERROR: ..."`` message when
        ``StylesPath`` is not set.
    """
    styles_path = _setting(parser, _GLOBAL_SECTION, "StylesPath")
    if not styles_path:
        return f"ERROR: {_VALE_CONFIG} must set StylesPath to locate the Vale styles."
    return PurePosixPath(_DOC_DIRECTORY, styles_path)


def _find_vocabulary_file(repository_root: Path, file_name: str) -> tuple[str | None, str]:
    """Locate an ANSYS vocabulary file under ``StylesPath``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    file_name : str
        Vocabulary file name, ``"accept.txt"`` or ``"reject.txt"``.

    Returns
    -------
    tuple[str or None, str]
        The repository-relative path of the first existing candidate and an
        empty string, or ``None`` and an ``"ERROR: ..."`` message.
    """
    parser = _load_configuration(repository_root)
    if isinstance(parser, str):
        return None, parser
    styles_directory = _styles_directory(parser)
    if isinstance(styles_directory, str):
        return None, styles_directory
    candidates = [
        (styles_directory / vocabulary_directory / file_name).as_posix()
        for vocabulary_directory in _VOCABULARY_DIRECTORIES
    ]
    for candidate in candidates:
        if file_exists(repository_root, candidate):
            return candidate, ""
    return None, f"ERROR: The ANSYS vocabulary file {candidates[0]} does not exist."


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
    path, error = _find_vocabulary_file(repository_root, file_name)
    return True if path is not None else error


def _accept_vocabulary(repository_root: Path) -> list[str] | str:
    """Read the lines of the ANSYS ``accept.txt`` vocabulary.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    list[str] or str
        The file lines, or an ``"ERROR: ..."`` message when the file is missing
        or cannot be read as UTF-8.
    """
    path, error = _find_vocabulary_file(repository_root, "accept.txt")
    if path is None:
        return error
    content = file_content(repository_root, path)
    if content is None:
        return f"ERROR: Cannot read {path} as UTF-8 within the repository."
    return content.splitlines()


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
            prefixed with ``"ERROR: "``, ``"WARNING: "``, or
            ``"RECOMMENDATION: "``.
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
        if _GOOGLE_PACKAGE not in _based_on_styles(parser):
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


class VL006(Vale):
    """Vale StylesPath is styles."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``StylesPath`` points to ``doc/styles``."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        styles_path = _setting(parser, _GLOBAL_SECTION, "StylesPath")
        if styles_path is not None and PurePosixPath(styles_path) == PurePosixPath(
            _EXPECTED_STYLES_PATH
        ):
            return True
        return f"WARNING: {_VALE_CONFIG} must set StylesPath = {_EXPECTED_STYLES_PATH}."


class VL007(Vale):
    """Vale MinAlertLevel is warning or stricter."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``MinAlertLevel`` hides suggestions only.

        Returns
        -------
        bool or str
            ``True`` for ``warning`` or ``error``, otherwise a
            ``"WARNING: ..."`` message. An unset value counts as Vale's
            ``suggestion`` default.
        """
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        level = (_setting(parser, _GLOBAL_SECTION, "MinAlertLevel") or "suggestion").lower()
        if level in _ALERT_LEVELS and _ALERT_LEVELS.index(level) >= _ALERT_LEVELS.index(
            _MINIMUM_ALERT_LEVEL
        ):
            return True
        return f"WARNING: {_VALE_CONFIG} must set MinAlertLevel to warning or error."


def _check_scopes(repository_root: Path, key: str, expected: tuple[str, ...]) -> RuleCheckResult:
    """Check that a scope list setting contains the expected scopes.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    key : str
        ``IgnoredScopes`` or ``SkippedScopes``.
    expected : tuple[str, ...]
        Scopes that the setting must include.

    Returns
    -------
    bool or str
        ``True`` when every scope is listed, otherwise a
        ``"RECOMMENDATION: ..."`` message naming the missing scopes.
    """
    parser = _load_configuration(repository_root)
    if isinstance(parser, str):
        return parser
    configured = set(_list_setting(parser, _GLOBAL_SECTION, key))
    missing = [scope for scope in expected if scope not in configured]
    if not missing:
        return True
    return f"RECOMMENDATION: Add {', '.join(missing)} to {key} in {_VALE_CONFIG}."


class VL008(Vale):
    """Vale IgnoredScopes includes code and tt."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check the inline scopes that Vale ignores."""
        return _check_scopes(repository_root, "IgnoredScopes", _IGNORED_SCOPES)


class VL009(Vale):
    """Vale SkippedScopes includes script, style, pre, and figure."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check the block scopes that Vale skips."""
        return _check_scopes(repository_root, "SkippedScopes", _SKIPPED_SCOPES)


class VL010(Vale):
    """Vale WordTemplate matches whole words."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``WordTemplate`` uses the PyAnsys word boundaries."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        if _setting(parser, _GLOBAL_SECTION, "WordTemplate") == _WORD_TEMPLATE:
            return True
        return f"RECOMMENDATION: Set WordTemplate = {_WORD_TEMPLATE} in {_VALE_CONFIG}."


class VL011(Vale):
    """Vale lints Python, Markdown, and reStructuredText files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that styles apply to ``py``, ``md``, and ``rst`` files.

        Returns
        -------
        bool or str
            ``True`` when, for every extension, a glob section that sets
            ``BasedOnStyles`` matches it, otherwise a ``"WARNING: ..."``
            message naming the uncovered extensions.
        """
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        styled_sections = [
            section
            for section in _style_sections(parser)
            if _list_setting(parser, section, "BasedOnStyles")
        ]
        missing = [
            extension
            for extension in _LINTED_EXTENSIONS
            if not any(
                _section_matches_extension(section, extension) for section in styled_sections
            )
        ]
        if not missing:
            return True
        return (
            f"WARNING: {_VALE_CONFIG} does not apply BasedOnStyles to "
            f"{', '.join(f'*.{extension}' for extension in missing)} files."
        )


class VL012(Vale):
    """Vale parses Python files as Markdown."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``[formats]`` maps ``py`` to ``md``."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        if (
            parser.has_section(_FORMATS_SECTION)
            and _setting(parser, _FORMATS_SECTION, "py") == "md"
        ):
            return True
        return f"RECOMMENDATION: Add py = md to the [formats] section of {_VALE_CONFIG}."


class VL013(Vale):
    """Vale applies the built-in Vale style."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``BasedOnStyles`` includes the ``Vale`` style."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        if _VALE_STYLE in _based_on_styles(parser):
            return True
        return f"WARNING: {_VALE_CONFIG} must apply {_VALE_STYLE} through BasedOnStyles."


class VL014(Vale):
    """Vale disables the Vale.Terms rule."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that a glob section sets ``Vale.Terms = NO``."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        if any(
            (_setting(parser, section, "Vale.Terms") or "").upper() == "NO"
            for section in _style_sections(parser)
        ):
            return True
        return (
            f"RECOMMENDATION: Set Vale.Terms = NO in {_VALE_CONFIG} so that the ANSYS "
            "vocabulary does not enforce letter case."
        )


class VL015(Vale):
    """Vale configures TokenIgnores and BlockIgnores."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that glob sections set ``TokenIgnores`` and ``BlockIgnores``."""
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        sections = _style_sections(parser)
        missing = [
            key
            for key in ("TokenIgnores", "BlockIgnores")
            if not any(_setting(parser, section, key) for section in sections)
        ]
        if not missing:
            return True
        return f"RECOMMENDATION: Set {' and '.join(missing)} in {_VALE_CONFIG}."


class VL016(Vale):
    """The Vale styles .gitignore keeps only the ANSYS vocabulary."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check the ignore patterns of ``<StylesPath>/.gitignore``.

        Returns
        -------
        bool or str
            ``True`` when the file contains every PyAnsys pattern, otherwise a
            ``"WARNING: ..."`` message naming the file and missing patterns.
        """
        parser = _load_configuration(repository_root)
        if isinstance(parser, str):
            return parser
        styles_directory = _styles_directory(parser)
        if isinstance(styles_directory, str):
            return styles_directory
        gitignore = (styles_directory / ".gitignore").as_posix()
        content = file_content(repository_root, gitignore)
        if content is None:
            return f"WARNING: {gitignore} does not exist or cannot be read."
        patterns = {line.strip() for line in content.splitlines()}
        missing = [pattern for pattern in _STYLES_GITIGNORE_PATTERNS if pattern not in patterns]
        if not missing:
            return True
        return f"WARNING: {gitignore} is missing the patterns: {', '.join(missing)}."


class VL017(Vale):
    """The ANSYS accept.txt vocabulary is not empty."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that ``accept.txt`` has at least one entry."""
        lines = _accept_vocabulary(repository_root)
        if isinstance(lines, str):
            return lines
        if any(line.strip() for line in lines):
            return True
        return "RECOMMENDATION: Add project terms to the ANSYS accept.txt vocabulary."


class VL018(Vale):
    """The ANSYS accept.txt vocabulary has no duplicate or blank lines."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check ``accept.txt`` for duplicate and blank lines."""
        lines = _accept_vocabulary(repository_root)
        if isinstance(lines, str):
            return lines
        seen: set[str] = set()
        duplicates: list[str] = []
        blank_lines = 0
        for line in lines:
            entry = line.strip()
            if not entry:
                blank_lines += 1
            elif entry in seen:
                if entry not in duplicates:
                    duplicates.append(entry)
            else:
                seen.add(entry)
        issues = []
        if duplicates:
            issues.append(f"duplicate entries {', '.join(duplicates)}")
        if blank_lines:
            issues.append(f"{blank_lines} blank line(s)")
        if not issues:
            return True
        return f"RECOMMENDATION: Remove {' and '.join(issues)} from the ANSYS accept.txt."


class VL019(Vale):
    """Legacy codespell word lists are migrated to Vale."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check for ``.codespell.exclude`` and ``.codespell.ignore`` files."""
        legacy = [name for name in _CODESPELL_FILES if file_exists(repository_root, name)]
        if not legacy:
            return True
        return (
            f"RECOMMENDATION: Move the words in {', '.join(legacy)} to the ANSYS "
            "accept.txt vocabulary, then delete the file(s)."
        )
