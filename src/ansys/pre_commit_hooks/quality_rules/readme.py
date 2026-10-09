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

from html import unescape
from pathlib import Path
import re
from typing import Callable
from urllib.parse import unquote, urlsplit

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

from ansys.pre_commit_hooks.quality_rules.common import (
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

# Image declarations are parsed before badge URLs are classified. This keeps a
# badge check from matching ordinary prose or a link target on another line.
_RST_IMAGE_URL = re.compile(
    r"^[ \t]*\.\.[ \t]+(?:\|[^\n|]+\|[ \t]+)?image::[ \t]+(?P<url>\S+)[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
_MARKDOWN_IMAGE_URL = re.compile(
    r"!\[[^\]\n]*\]\([ \t]*(?:<(?P<angle>[^>\n]+)>|(?P<plain>[^\s)\n]+))",
)
_MARKDOWN_REFERENCE_IMAGE = re.compile(r"!\[(?P<alt>[^\]\n]*)\]\[(?P<reference>[^\]\n]*)\]")
_MARKDOWN_REFERENCE_DEFINITION = re.compile(
    r"^[ \t]{0,3}\[(?P<label>[^\]\n]+)\]:[ \t]*" r"(?:<(?P<angle>[^>\n]+)>|(?P<plain>\S+))",
    re.MULTILINE,
)
_HTML_IMAGE_URL = re.compile(
    r"<img\b[^>]*\bsrc[ \t]*=[ \t]*(?P<quote>[\"'])(?P<url>.*?)" r"(?P=quote)",
    re.IGNORECASE | re.DOTALL,
)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_SHIELDS_HOSTS = frozenset({"img.shields.io", "shields.io"})


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
    "Apache-2.0": r"apache[-_ .]*2(?:[._-]*0)?",
    "MIT": r"mit",
    "BSD-2-Clause": r"bsd[-_ .]*2[-_ .]*clause",
    "BSD-3-Clause": r"bsd[-_ .]*3[-_ .]*clause",
}

# Recognizes a normalized license identifier from declared license text.
_LICENSE_IDENTIFIERS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bMIT(?: License)?\b(?![-_])", re.IGNORECASE), "MIT"),
    (re.compile(r"Apache License(?:,| )? Version 2\.0|Apache-2\.0", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"BSD[-_ ]?2[-_ ]?Clause\b(?![-_])", re.IGNORECASE), "BSD-2-Clause"),
    (re.compile(r"BSD[-_ ]?3[-_ ]?Clause\b(?![-_])", re.IGNORECASE), "BSD-3-Clause"),
)


def _normalized_reference_label(label: str) -> str:
    """Return a normalized Markdown reference label."""
    return " ".join(label.split()).casefold()


def _visible_markup(content: str) -> str:
    """Remove HTML comments and Markdown fenced code blocks."""
    lines: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in _HTML_COMMENT.sub("", content).splitlines(keepends=True):
        stripped = line.lstrip()
        indentation = len(line) - len(stripped)
        fence = re.match(r"(`{3,}|~{3,})", stripped) if indentation <= 3 else None
        if not fence_character:
            if fence:
                fence_character = fence.group()[0]
                fence_length = len(fence.group())
            else:
                lines.append(line)
        elif re.fullmatch(
            rf"{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            stripped.rstrip("\r\n"),
        ):
            fence_character = ""
            fence_length = 0
    return "".join(lines)


def _image_urls(content: str) -> tuple[str, ...]:
    """Return image source URLs declared in README markup."""
    content = _visible_markup(content)
    urls = [match.group("url") for match in _RST_IMAGE_URL.finditer(content)]
    urls.extend(
        match.group("angle") or match.group("plain")
        for match in _MARKDOWN_IMAGE_URL.finditer(content)
    )
    urls.extend(match.group("url") for match in _HTML_IMAGE_URL.finditer(content))

    definitions = {
        _normalized_reference_label(match.group("label")): (
            match.group("angle") or match.group("plain")
        )
        for match in _MARKDOWN_REFERENCE_DEFINITION.finditer(content)
    }
    for match in _MARKDOWN_REFERENCE_IMAGE.finditer(content):
        label = match.group("reference") or match.group("alt")
        url = definitions.get(_normalized_reference_label(label))
        if url:
            urls.append(url)

    return tuple(dict.fromkeys(unescape(url.strip()) for url in urls if url.strip()))


def _url_host_and_path(url: str) -> tuple[str, str]:
    """Return a normalized host and decoded path for an image URL."""
    try:
        parsed = urlsplit(url)
        if parsed.hostname is None and not url.startswith(("/", "#")):
            parsed = urlsplit(f"//{url}")
        host = (parsed.hostname or "").rstrip(".").casefold()
    except ValueError:
        return "", ""
    return host, unquote(parsed.path).casefold()


def _is_ansys_badge(url: str) -> bool:
    """Return whether an image URL identifies a PyAnsys or Ansys badge."""
    host, path = _url_host_and_path(url)
    if host in _SHIELDS_HOSTS and path.startswith("/badge/"):
        badge_name = path.removeprefix("/badge/")
        if re.match(r"(?:py[-_ ]?)?ansys(?:[-_./]|$)", badge_name):
            return True
    return bool(re.search(r"(?:^|[/_.-])py[-_ ]?ansys(?:[/_.-]|$)", path))


def _is_pypi_badge(url: str) -> bool:
    """Return whether an image URL identifies a PyPI badge."""
    host, path = _url_host_and_path(url)
    return (
        (host in _SHIELDS_HOSTS and path.startswith(("/pypi/", "/badge/pypi-")))
        or (host == "badge.fury.io" and path.startswith("/py/"))
        or (host == "pypi.org" and path.startswith("/project/"))
    )


def _is_github_actions_badge(url: str) -> bool:
    """Return whether an image URL identifies a GitHub Actions badge."""
    host, path = _url_host_and_path(url)
    return host == "github.com" and bool(
        re.fullmatch(r"/[^/]+/[^/]+/actions/workflows/[^/]+/badge\.svg", path)
    )


def _license_badge_matcher(identifier: str) -> Callable[[str], bool]:
    """Return a predicate for a Shields badge with the declared license."""
    term = _BADGE_IDENTIFIERS.get(identifier)
    if term is None:
        if len(identifier) > 128 or "\n" in identifier:
            return lambda url: False
        words = re.findall(r"[a-z0-9]+", identifier.casefold())
        if not words:
            return lambda url: False
        term = r"[-_ .]*".join(re.escape(word) for word in words)

    pattern = re.compile(
        rf"(?:^|[-_./])(?:license[-_ .]+{term}|{term}[-_ .]+license)(?=[-_./]|$)",
        re.IGNORECASE,
    )

    def matches(url: str) -> bool:
        host, path = _url_host_and_path(url)
        return (
            host in _SHIELDS_HOSTS
            and path.startswith("/badge/")
            and bool(pattern.search(path.removeprefix("/badge/")))
        )

    return matches


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
        return value.strip() or None
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"].strip() or None
        if isinstance(value.get("file"), str):
            content = file_content(root, value["file"])
            if content is None:
                return None
            return content.strip() or None
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

    pyproject = file_content(root, "pyproject.toml")
    if pyproject is None:
        return None
    try:
        metadata = tomllib.loads(pyproject)
    except (TypeError, ValueError):
        return None

    license_text = _declared_license_text(metadata.get("project"), root)
    if license_text is None:
        return None

    if "\n" not in license_text and re.search(r"\b(?:AND|OR|WITH)\b", license_text):
        return license_text
    for pattern, identifier in _LICENSE_IDENTIFIERS:
        if pattern.search(license_text):
            return identifier
    return license_text


def _badge_result(
    root: Path,
    readme_path: str | None,
    matcher: Callable[[str], bool],
    label: str,
    severity: str = "WARNING",
) -> bool | str:
    """Return the result of a README badge-presence check.

    Parameters
    ----------
    root : pathlib.Path
        Repository root directory.
    readme_path : str or None
        Name of the detected README file.
    matcher : Callable[[str], bool]
        Predicate that identifies a badge image URL.
    label : str
        Badge description used in the message.
    severity : str, default: "WARNING"
        Message prefix used when the badge is missing, ``"WARNING"`` or ``"ERROR"``.

    Returns
    -------
    bool or str
        ``True`` if the badge is found, otherwise a ``"<severity>: ..."`` message.
        A missing README file also produces the message.
    """
    if readme_path:
        content = file_content(root, readme_path)
        if content is None:
            return f"ERROR: {readme_path} could not be read as UTF-8."
        if any(matcher(url) for url in _image_urls(content)):
            return True
    location = f"in {readme_path}" if readme_path else "because no README file exists"
    return f"{severity}: {label} not found {location}."


def _section_result(root: Path, readme_path: str | None, pattern: re.Pattern) -> bool | str:
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
    bool or str
        Whether the heading exists. ``False`` if there is no README file, or an
        ``"ERROR: ..."`` message if the README cannot be read as UTF-8.
    """
    if readme_path is None:
        return False
    content = file_content(root, readme_path)
    if content is None:
        return f"ERROR: {readme_path} could not be read as UTF-8."
    return bool(pattern.search(content))


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
    - A missing README produces an error.
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
            ``True`` for ``README.rst``, a ``"WARNING: ..."`` message for
            ``README.md``, and ``False`` if no README exists.
        """
        if readme_path == "README.rst":
            return True
        # NOTE: RST format is preferred over MD because `twine check` doesn't
        # do anything with MD file
        # See https://github.com/pypa/twine/blob/main/twine/commands/check.py#L32
        # for more information
        if readme_path == "README.md":
            return "WARNING: README.md found; the PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    """README has a PyAnsys or Ansys badge.

    Looks for a PyAnsys or Ansys badge image, such as an ``img.shields.io`` badge
    named ``Py-Ansys`` or ``Ansys``, or any badge image URL that contains
    ``pyansys``. The ``ansys`` organization name in a GitHub URL, for example in a
    workflow badge, does not count.

    Notes
    -----
    - A missing badge produces an error, including when there is no README file.
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
            ``True`` if the badge is found, otherwise an ``"ERROR: ..."`` message.
        """
        return _badge_result(
            root,
            readme_path,
            _is_ansys_badge,
            "PyAnsys or Ansys badge image",
            severity="ERROR",
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
            ``True`` if the badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        return _badge_result(root, readme_path, _is_pypi_badge, "PyPI badge image")


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
            ``True`` if a matching badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        identifier = _project_license(root)
        if identifier is None:
            return (
                "WARNING: No project license found in pyproject.toml, so the README "
                "license badge cannot be verified."
            )

        return _badge_result(
            root,
            readme_path,
            _license_badge_matcher(identifier),
            f"{identifier} license badge image matching project metadata",
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
            ``True`` if the badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        return _badge_result(
            root, readme_path, _is_github_actions_badge, "GH-CI workflow badge.svg URL"
        )


class RM005(README):
    """README has an installation section.

    Requires a heading that contains ``install``, such as ``Installation`` or
    ``How to install``. Either a Markdown ``#`` heading or an underlined
    reStructuredText heading is accepted. The word in body text or in a URL does
    not count.

    Notes
    -----
    - A missing heading produces an error, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README has an installation heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(root, readme_path, _INSTALL_SECTION)


class RM006(README):
    """README has a documentation section.

    Requires a heading that contains ``documentation``. Either a Markdown ``#``
    heading or an underlined reStructuredText heading is accepted. The word in body
    text or in a URL does not count.

    Notes
    -----
    - A missing heading produces an error, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README has a documentation heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(root, readme_path, _DOCUMENTATION_SECTION)


class RM007(README):
    """README has a license section.

    Requires a heading that contains ``license`` or ``licence``. Either a Markdown
    ``#`` heading or an underlined reStructuredText heading is accepted. The word in
    body text, or in a badge URL, does not count.

    Notes
    -----
    - A missing heading produces an error, including when there is no README file.
    """

    @staticmethod
    def check(root: Path, readme_path: str | None) -> bool | str:
        """Return whether the README has a license heading.

        Parameters
        ----------
        root : pathlib.Path
            Repository root directory.
        readme_path : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(root, readme_path, _LICENSE_SECTION)
