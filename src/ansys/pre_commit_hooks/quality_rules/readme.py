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

"""README quality checks.

This rule set validates that the repository README follows PyAnsys
documentation standards and includes commonly expected project badges.

The checks cover:

* README availability
    - README.rst (preferred)
    - README.md (supported but not preferred)

* Badges
    - PyAnsys or Ansys badge
    - PyPI badge
    - Project license badge
    - GitHub Actions CI badge

* Content sections
    - Installation
    - Documentation
    - License
"""

from __future__ import annotations

from pathlib import Path
import re

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

from ansys.pre_commit_hooks.quality_rules.common import (
    file_contains,
    file_content,
    file_exists,
)

__all__ = [
    "README",
    "RM000",
    "RM001",
    "RM002",
    "RM003",
    "RM004",
    "RM005",
    "RM006",
    "RM007",
]

# Badge presence patterns, compiled once and reused across checks.
_ANSYS_BADGE = re.compile(
    r"img\.shields\.io/badge/(?:py-?)?ansys|"
    r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys",
    re.IGNORECASE,
)
_PYPI_BADGE = re.compile(
    r"img\.shields\.io[^)\"']*pypi|pypi\.org/project[^)\"']*badge|badge\.fury\.io/py",
    re.IGNORECASE,
)
_GH_CI_BADGE = re.compile(
    r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg", re.IGNORECASE
)


def _heading_pattern(term: str) -> re.Pattern:
    """Return a regular expression matching a section heading.

    Parameters
    ----------
    term : str
        Regular expression that the heading text must contain.

    Returns
    -------
    re.Pattern
        Pattern matching a Markdown ``#`` heading or an underlined
        reStructuredText heading whose text contains ``term``.
    """
    title = rf"[^\n]*{term}[^\n]*"
    return re.compile(
        rf"^(?:#{{1,6}}[ \t]+{title}|{title}\n[=\-^~\"#*+`]{{3,}})[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    )


# Content section patterns.
_INSTALL_SECTION = _heading_pattern(r"install")
_DOCUMENTATION_SECTION = _heading_pattern(r"documentation")
_LICENSE_SECTION = _heading_pattern(r"licen[sc]e")

# Maps a project license to the token expected in its README badge.
_BADGE_IDENTIFIERS = {
    "Apache-2.0": r"apache(?:[-_% ]?2(?:[._-]?0)?)?",
    "MIT": r"mit",
    "BSD-2-Clause": r"bsd[-_ ]?2[-_ ]?clause",
    "BSD-3-Clause": r"bsd[-_ ]?3[-_ ]?clause",
}

# Recognizes a normalized license identifier from declared license text.
_LICENSE_IDENTIFIERS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bMIT(?: License)?\b", re.IGNORECASE), "MIT"),
    (re.compile(r"Apache License(?:,| )? Version 2\.0|Apache-2\.0", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"BSD[-_ ]?2[-_ ]?Clause", re.IGNORECASE), "BSD-2-Clause"),
    (re.compile(r"BSD[-_ ]?3[-_ ]?Clause", re.IGNORECASE), "BSD-3-Clause"),
)


def _declared_license_text(project: object, root: Path) -> str | None:
    """Return the license text declared in the ``[project]`` table.

    Parameters
    ----------
    project : object
        Parsed ``[project]`` table from ``pyproject.toml``.
    root : pathlib.Path
        Repository root directory, used to read a ``license.file`` entry.

    Returns
    -------
    str or None
        The license string, the ``license.text`` value, or the content of the
        ``license.file`` file. ``None`` if no license is declared.
    """
    if not isinstance(project, dict):
        return None

    value = project.get("license")
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"].strip()
        if isinstance(value.get("file"), str):
            return file_content(root, value["file"])
    return None


def _project_license(root: Path) -> str | None:
    """Return the project license identifier declared in ``pyproject.toml``.

    Parameters
    ----------
    root : pathlib.Path
        Repository root directory.

    Returns
    -------
    str or None
        ``MIT``, ``Apache-2.0``, ``BSD-2-Clause`` or ``BSD-3-Clause`` for a
        recognized license, or the declared text for any other license. ``None``
        if ``pyproject.toml`` is missing, is not valid TOML, or declares no license.
    """
    if not file_exists(root, "pyproject.toml"):
        return None

    try:
        metadata = tomllib.loads(file_content(root, "pyproject.toml"))
    except (TypeError, ValueError):
        return None

    license_text = _declared_license_text(metadata.get("project"), root)
    if license_text is None:
        return None

    for pattern, identifier in _LICENSE_IDENTIFIERS:
        if pattern.search(license_text):
            return identifier
    return license_text


def _badge_result(
    root: Path,
    readme_path: str | None,
    pattern: re.Pattern,
    label: str,
    severity: str = "WARN",
) -> bool | str:
    """Return the result of a README badge-presence check.

    Parameters
    ----------
    root : pathlib.Path
        Repository root directory.
    readme_path : str or None
        Name of the detected README file.
    pattern : re.Pattern
        Pattern that identifies the badge.
    label : str
        Badge description used in the message.
    severity : str, default: "WARN"
        Message prefix used when the badge is missing, ``"WARN"`` or ``"FAIL"``.

    Returns
    -------
    bool or str
        ``True`` if the badge is found, otherwise a ``"<severity>: ..."`` message.
        A missing README file also produces the message.
    """
    if readme_path and file_contains(root, readme_path, pattern):
        return True
    location = f"in {readme_path}" if readme_path else "because no README file exists"
    return f"{severity}: {label} not found {location}."


def _section_result(root: Path, readme_path: str | None, pattern: re.Pattern) -> bool:
    """Return whether a README section heading is present.

    Parameters
    ----------
    root : pathlib.Path
        Repository root directory.
    readme_path : str or None
        Name of the detected README file.
    pattern : re.Pattern
        Heading pattern created by ``_heading_pattern``.

    Returns
    -------
    bool
        Whether the heading exists. ``False`` if there is no README file.
    """
    return bool(readme_path) and file_contains(root, readme_path, pattern)


class README:
    """README rule family.

    Base class of the README quality rules. Each rule is a subclass named
    ``RM<nnn>`` with a static ``check`` method that receives the repository root
    and the name of the detected README file.
    """

    family = "readme"


class RM000(README):
    """README file exists.

    Requires a ``README.rst`` or ``README.md`` file in the repository root.

    Notes
    -----
    - ``README.rst`` passes.
    - ``README.md`` is accepted with a warning, because ``README.rst`` is preferred.
    - A missing README fails.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the repository has a supported README file.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` for ``README.rst``, a ``"WARN: ..."`` message for ``README.md``,
            and ``False`` if no README exists.
        """
        if readme_path == "README.rst":
            return True
        # NOTE: RST format is preferred over MD because `twine check` doesn't
        # do anything with MD file
        # See https://github.com/pypa/twine/blob/main/twine/commands/check.py#L32
        # for more information
        if readme_path == "README.md":
            return "WARN: README.md found — PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    """README has a PyAnsys or Ansys badge.

    Looks for a PyAnsys or Ansys badge image, such as an ``img.shields.io`` badge
    named ``Py-Ansys`` or ``Ansys``, or any badge image URL that contains
    ``pyansys``. The ``ansys`` organization name in a GitHub URL, for example in a
    workflow badge, does not count.

    Notes
    -----
    - A missing badge fails, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README contains a PyAnsys or Ansys badge.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise a ``"FAIL: ..."`` message.
        """
        return _badge_result(
            root, readme_path, _ANSYS_BADGE, "PyAnsys or Ansys badge image", severity="FAIL"
        )


class RM002(README):
    """README has a PyPI badge.

    Looks for a PyPI badge image: an ``img.shields.io`` PyPI badge, a
    ``pypi.org/project`` badge link, or a ``badge.fury.io/py`` badge.

    Notes
    -----
    - A missing badge produces a warning, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README contains a PyPI badge.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise a ``"WARN: ..."`` message.
        """
        return _badge_result(root, readme_path, _PYPI_BADGE, "PyPI badge image")


class RM003(README):
    """README has a license badge matching project metadata.

    Reads the license declared in ``[project].license`` of ``pyproject.toml`` and
    looks for a license badge for the same license. The declaration can be a license
    string, a ``license.text`` value, or a ``license.file`` path whose content is
    read. MIT, Apache-2.0, BSD-2-Clause and BSD-3-Clause are recognized. Any other
    license is matched by its declared text.

    Notes
    -----
    - A missing badge, or a badge for a different license, produces a warning,
      including when there is no README file.
    - A warning is also produced when ``pyproject.toml`` is missing or invalid, or
      declares no license, because the badge cannot be verified.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README license badge matches project metadata.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if a matching badge is found, otherwise a ``"WARN: ..."`` message.
        """
        identifier = _project_license(root)
        if identifier is None:
            return (
                "WARN: No project license found in pyproject.toml, so the README "
                "license badge cannot be verified."
            )

        term = _BADGE_IDENTIFIERS.get(identifier, re.escape(identifier))
        pattern = re.compile(
            rf"(?:img\.)?shields\.io[^)\"']*{term}|{term}[^)\"']*license",
            re.IGNORECASE,
        )
        if readme_path and file_contains(root, readme_path, pattern):
            return True
        location = f"in {readme_path}" if readme_path else "because no README file exists"
        return (
            f"WARN: {identifier} license badge image not found or does not "
            f"match project metadata {location}."
        )


class RM004(README):
    """README has a GH-CI badge.

    Looks for a GitHub Actions workflow badge, a ``badge.svg`` URL under
    ``github.com/<owner>/<repository>/actions/workflows/``.

    Notes
    -----
    - A missing badge produces a warning, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README contains a GitHub Actions badge.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise a ``"WARN: ..."`` message.
        """
        return _badge_result(root, readme_path, _GH_CI_BADGE, "GH-CI workflow badge.svg URL")


class RM005(README):
    """README has an installation section.

    Requires a heading that contains ``install``, such as ``Installation`` or
    ``How to install``. Either a Markdown ``#`` heading or an underlined
    reStructuredText heading is accepted. The word in body text or in a URL does
    not count.

    Notes
    -----
    - A missing heading fails, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool:
        """Return whether the README has an installation heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool
            ``True`` if the heading exists, ``False`` otherwise.
        """
        return _section_result(root, readme_path, _INSTALL_SECTION)


class RM006(README):
    """README has a documentation section.

    Requires a heading that contains ``documentation``. Either a Markdown ``#``
    heading or an underlined reStructuredText heading is accepted. The word in body
    text or in a URL does not count.

    Notes
    -----
    - A missing heading fails, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool:
        """Return whether the README has a documentation heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool
            ``True`` if the heading exists, ``False`` otherwise.
        """
        return _section_result(root, readme_path, _DOCUMENTATION_SECTION)


class RM007(README):
    """README has a license section.

    Requires a heading that contains ``license`` or ``licence``. Either a Markdown
    ``#`` heading or an underlined reStructuredText heading is accepted. The word in
    body text, or in a badge URL, does not count.

    Notes
    -----
    - A missing heading fails, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool:
        """Return whether the README has a license heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool
            ``True`` if the heading exists, ``False`` otherwise.
        """
        return _section_result(root, readme_path, _LICENSE_SECTION)
