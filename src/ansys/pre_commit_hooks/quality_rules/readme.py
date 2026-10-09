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

from abc import ABC, abstractmethod
from collections.abc import Callable
from html import unescape
from pathlib import Path
import re
from typing import ClassVar, Literal
from urllib.parse import unquote, urlsplit

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

from ansys.pre_commit_hooks.quality_rules.common import (
    RuleCheckResult,
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
_SHIELDS_HOSTS: frozenset[str] = frozenset({"img.shields.io", "shields.io"})


def _heading_pattern(heading_term: str) -> re.Pattern[str]:
    """Return a regular expression matching a section heading.

    Parameters
    ----------
    heading_term : str
        Regular expression that the heading text must contain.

    Returns
    -------
    re.Pattern[str]
        Pattern matching a Markdown ``#`` heading or an underlined
        reStructuredText heading whose text contains ``heading_term``.
    """
    heading_text = rf"[^\n]*{heading_term}[^\n]*"
    return re.compile(
        rf"^(?:#{{1,6}}[ \t]+{heading_text}|" rf"{heading_text}\n[=\-^~\"#*+`]{{3,}})[ \t]*$",
        re.IGNORECASE | re.MULTILINE,
    )


# Content section patterns.
_INSTALL_SECTION = _heading_pattern(r"install")
_DOCUMENTATION_SECTION = _heading_pattern(r"documentation")
_LICENSE_SECTION = _heading_pattern(r"licen[sc]e")

# Maps a project license to the token expected in its README badge.
_BADGE_IDENTIFIERS: dict[str, str] = {
    "Apache-2.0": r"apache[-_ .]*2(?:[._-]*0)?",
    "MIT": r"mit",
    "BSD-2-Clause": r"bsd[-_ .]*2[-_ .]*clause",
    "BSD-3-Clause": r"bsd[-_ .]*3[-_ .]*clause",
}

# Recognizes a normalized license identifier from declared license text.
_LICENSE_IDENTIFIERS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bMIT(?: License)?\b(?![-_])", re.IGNORECASE), "MIT"),
    (re.compile(r"Apache License(?:,| )? Version 2\.0|Apache-2\.0", re.IGNORECASE), "Apache-2.0"),
    (re.compile(r"BSD[-_ ]?2[-_ ]?Clause\b(?![-_])", re.IGNORECASE), "BSD-2-Clause"),
    (re.compile(r"BSD[-_ ]?3[-_ ]?Clause\b(?![-_])", re.IGNORECASE), "BSD-3-Clause"),
)


def _normalized_reference_label(reference_label: str) -> str:
    """Normalize a Markdown reference label.

    Parameters
    ----------
    reference_label : str
        Label from a Markdown reference image or definition.

    Returns
    -------
    str
        Case-folded label with consecutive whitespace collapsed.
    """
    return " ".join(reference_label.split()).casefold()


def _visible_markup(readme_content: str) -> str:
    """Remove non-rendered blocks from README markup.

    Parameters
    ----------
    readme_content : str
        Raw README content.

    Returns
    -------
    str
        Markup with HTML comments and Markdown fenced code blocks removed.
    """
    visible_lines: list[str] = []
    fence_character = ""
    fence_length = 0
    visible_content = _HTML_COMMENT.sub("", readme_content)
    for line in visible_content.splitlines(keepends=True):
        stripped_line = line.lstrip()
        indentation = len(line) - len(stripped_line)
        fence_match = re.match(r"(`{3,}|~{3,})", stripped_line) if indentation <= 3 else None
        if not fence_character:
            if fence_match:
                fence_character = fence_match.group()[0]
                fence_length = len(fence_match.group())
            else:
                visible_lines.append(line)
        elif re.fullmatch(
            rf"{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            stripped_line.rstrip("\r\n"),
        ):
            fence_character = ""
            fence_length = 0
    return "".join(visible_lines)


def _image_urls(readme_content: str) -> tuple[str, ...]:
    """Extract image source URLs from rendered README markup.

    Parameters
    ----------
    readme_content : str
        Raw README content.

    Returns
    -------
    tuple[str, ...]
        Unique image source URLs in their declaration order.
    """
    visible_content = _visible_markup(readme_content)
    image_urls = [match.group("url") for match in _RST_IMAGE_URL.finditer(visible_content)]
    image_urls.extend(
        match.group("angle") or match.group("plain")
        for match in _MARKDOWN_IMAGE_URL.finditer(visible_content)
    )
    image_urls.extend(match.group("url") for match in _HTML_IMAGE_URL.finditer(visible_content))

    reference_definitions = {
        _normalized_reference_label(match.group("label")): (
            match.group("angle") or match.group("plain")
        )
        for match in _MARKDOWN_REFERENCE_DEFINITION.finditer(visible_content)
    }
    for match in _MARKDOWN_REFERENCE_IMAGE.finditer(visible_content):
        reference_label = match.group("reference") or match.group("alt")
        image_url = reference_definitions.get(_normalized_reference_label(reference_label))
        if image_url:
            image_urls.append(image_url)

    return tuple(
        dict.fromkeys(unescape(image_url.strip()) for image_url in image_urls if image_url.strip())
    )


def _url_host_and_path(image_url: str) -> tuple[str, str]:
    """Normalize the host and path of an image URL.

    Parameters
    ----------
    image_url : str
        Absolute, protocol-relative, or host-relative image URL.

    Returns
    -------
    tuple[str, str]
        Case-folded host and decoded path. Two empty strings are returned for
        malformed URLs.
    """
    try:
        parsed_url = urlsplit(image_url)
        if parsed_url.hostname is None and not image_url.startswith(("/", "#")):
            parsed_url = urlsplit(f"//{image_url}")
        url_host = (parsed_url.hostname or "").rstrip(".").casefold()
    except ValueError:
        return "", ""
    return url_host, unquote(parsed_url.path).casefold()


def _is_ansys_badge(image_url: str) -> bool:
    """Return whether an image URL identifies a PyAnsys or Ansys badge.

    Parameters
    ----------
    image_url : str
        README image source URL.

    Returns
    -------
    bool
        Whether the URL identifies a PyAnsys or Ansys badge.
    """
    url_host, url_path = _url_host_and_path(image_url)
    if url_host in _SHIELDS_HOSTS and url_path.startswith("/badge/"):
        badge_name = url_path.removeprefix("/badge/")
        if re.match(r"(?:py[-_ ]?)?ansys(?:[-_./]|$)", badge_name):
            return True
    return bool(re.search(r"(?:^|[/_.-])py[-_ ]?ansys(?:[/_.-]|$)", url_path))


def _is_pypi_badge(image_url: str) -> bool:
    """Return whether an image URL identifies a PyPI badge.

    Parameters
    ----------
    image_url : str
        README image source URL.

    Returns
    -------
    bool
        Whether the URL identifies a PyPI badge.
    """
    url_host, url_path = _url_host_and_path(image_url)
    return (
        (url_host in _SHIELDS_HOSTS and url_path.startswith(("/pypi/", "/badge/pypi-")))
        or (url_host == "badge.fury.io" and url_path.startswith("/py/"))
        or (url_host == "pypi.org" and url_path.startswith("/project/"))
    )


def _is_github_actions_badge(image_url: str) -> bool:
    """Return whether an image URL identifies a GitHub Actions badge.

    Parameters
    ----------
    image_url : str
        README image source URL.

    Returns
    -------
    bool
        Whether the URL identifies a GitHub Actions workflow badge.
    """
    url_host, url_path = _url_host_and_path(image_url)
    return url_host == "github.com" and bool(
        re.fullmatch(r"/[^/]+/[^/]+/actions/workflows/[^/]+/badge\.svg", url_path)
    )


def _never_matches_badge(image_url: str) -> bool:
    """Reject an image URL for an unsupported license declaration.

    Parameters
    ----------
    image_url : str
        README image source URL.

    Returns
    -------
    bool
        Always ``False``.
    """
    return False


def _license_badge_matcher(
    license_identifier: str,
) -> Callable[[str], bool]:
    """Build a predicate for a Shields badge with the declared license.

    Parameters
    ----------
    license_identifier : str
        Normalized license identifier or declared license text.

    Returns
    -------
    collections.abc.Callable[[str], bool]
        Predicate that accepts matching Shields badge image URLs.
    """
    license_pattern = _BADGE_IDENTIFIERS.get(license_identifier)
    if license_pattern is None:
        if len(license_identifier) > 128 or "\n" in license_identifier:
            return _never_matches_badge
        identifier_words = re.findall(r"[a-z0-9]+", license_identifier.casefold())
        if not identifier_words:
            return _never_matches_badge
        license_pattern = r"[-_ .]*".join(re.escape(word) for word in identifier_words)

    badge_pattern = re.compile(
        rf"(?:^|[-_./])(?:license[-_ .]+{license_pattern}|"
        rf"{license_pattern}[-_ .]+license)(?=[-_./]|$)",
        re.IGNORECASE,
    )

    def matches_license_badge(image_url: str) -> bool:
        """Return whether an image URL matches the declared license.

        Parameters
        ----------
        image_url : str
            README image source URL.

        Returns
        -------
        bool
            Whether the URL is a matching Shields license badge.
        """
        url_host, url_path = _url_host_and_path(image_url)
        return (
            url_host in _SHIELDS_HOSTS
            and url_path.startswith("/badge/")
            and bool(badge_pattern.search(url_path.removeprefix("/badge/")))
        )

    return matches_license_badge


def _declared_license_text(project_metadata: object, repository_root: Path) -> str | None:
    """Return the license text declared in the ``[project]`` table.

    Parameters
    ----------
    project_metadata : object
        Parsed ``[project]`` table from ``pyproject.toml``.
    repository_root : pathlib.Path
        Repository root directory, used to read a ``license.file`` entry.

    Returns
    -------
    str or None
        The license string, the ``license.text`` value, or the content of the
        ``license.file`` file. ``None`` if no license is declared.
    """
    if not isinstance(project_metadata, dict):
        return None

    license_declaration = project_metadata.get("license")
    if isinstance(license_declaration, str):
        return license_declaration.strip() or None
    if isinstance(license_declaration, dict):
        declared_text = license_declaration.get("text")
        if isinstance(declared_text, str):
            return declared_text.strip() or None
        declared_file = license_declaration.get("file")
        if isinstance(declared_file, str):
            license_file_content = file_content(repository_root, declared_file)
            if license_file_content is None:
                return None
            return license_file_content.strip() or None
    return None


def _project_license(repository_root: Path) -> str | None:
    """Return the project license identifier declared in ``pyproject.toml``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    str or None
        ``MIT``, ``Apache-2.0``, ``BSD-2-Clause`` or ``BSD-3-Clause`` for a
        recognized license, or the declared text for any other license. ``None``
        if ``pyproject.toml`` is missing, is not valid TOML, or declares no license.
    """
    if not file_exists(repository_root, "pyproject.toml"):
        return None

    pyproject_content = file_content(repository_root, "pyproject.toml")
    if pyproject_content is None:
        return None
    try:
        pyproject_data = tomllib.loads(pyproject_content)
    except (TypeError, ValueError):
        return None

    license_text = _declared_license_text(pyproject_data.get("project"), repository_root)
    if license_text is None:
        return None

    if "\n" not in license_text and re.search(r"\b(?:AND|OR|WITH)\b", license_text):
        return license_text
    for identifier_pattern, license_identifier in _LICENSE_IDENTIFIERS:
        if identifier_pattern.search(license_text):
            return license_identifier
    return license_text


def _badge_result(
    repository_root: Path,
    readme_file: str | None,
    badge_url_matches: Callable[[str], bool],
    badge_label: str,
    missing_status: Literal["WARNING", "ERROR"] = "WARNING",
) -> RuleCheckResult:
    """Return the result of a README badge-presence check.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    readme_file : str or None
        Name of the detected README file.
    badge_url_matches : collections.abc.Callable[[str], bool]
        Predicate that identifies a badge image URL.
    badge_label : str
        Badge description used in the message.
    missing_status : {"WARNING", "ERROR"}, default: "WARNING"
        Message prefix used when the badge is missing, ``"WARNING"`` or ``"ERROR"``.

    Returns
    -------
    bool or str
        ``True`` if the badge is found, otherwise a
        ``"<missing_status>: ..."`` message. A missing README file also
        produces the message.
    """
    if readme_file:
        readme_content = file_content(repository_root, readme_file)
        if readme_content is None:
            return f"ERROR: {readme_file} could not be read as UTF-8."
        if any(badge_url_matches(image_url) for image_url in _image_urls(readme_content)):
            return True
    location = f"in {readme_file}" if readme_file else "because no README file exists"
    return f"{missing_status}: {badge_label} not found {location}."


def _section_result(
    repository_root: Path,
    readme_file: str | None,
    heading_pattern: re.Pattern[str],
) -> RuleCheckResult:
    """Return whether a README section heading is present.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    readme_file : str or None
        Name of the detected README file.
    heading_pattern : re.Pattern[str]
        Heading pattern created by ``_heading_pattern``.

    Returns
    -------
    bool or str
        Whether the heading exists. ``False`` if there is no README file, or an
        ``"ERROR: ..."`` message if the README cannot be read as UTF-8.
    """
    if readme_file is None:
        return False
    readme_content = file_content(repository_root, readme_file)
    if readme_content is None:
        return f"ERROR: {readme_file} could not be read as UTF-8."
    return bool(heading_pattern.search(readme_content))


class README(ABC):
    """README rule family.

    Base class of the README quality rules. Each rule is a subclass named
    ``RM<nnn>`` with a static ``check`` method that receives the repository root
    and the name of the detected README file.
    """

    family: ClassVar[str] = "readme"

    @staticmethod
    @abstractmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Evaluate a README rule.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Detected README path, or ``None`` when no supported README exists.

        Returns
        -------
        bool or str
            Raw rule result consumed by the quality-report runner.
        """
        raise NotImplementedError


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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the repository has a supported README file.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` for ``README.rst``, a ``"WARNING: ..."`` message for
            ``README.md``, and ``False`` if no README exists.
        """
        if readme_file == "README.rst":
            return True
        # NOTE: RST format is preferred over MD because `twine check` doesn't
        # do anything with MD file
        # See https://github.com/pypa/twine/blob/main/twine/commands/check.py#L32
        # for more information
        if readme_file == "README.md":
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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README contains a PyAnsys or Ansys badge.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise an ``"ERROR: ..."`` message.
        """
        return _badge_result(
            repository_root,
            readme_file,
            _is_ansys_badge,
            "PyAnsys or Ansys badge image",
            missing_status="ERROR",
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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README contains a PyPI badge.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        return _badge_result(repository_root, readme_file, _is_pypi_badge, "PyPI badge image")


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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README license badge matches project metadata.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if a matching badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        license_identifier = _project_license(repository_root)
        if license_identifier is None:
            return (
                "WARNING: No project license found in pyproject.toml, so the README "
                "license badge cannot be verified."
            )

        return _badge_result(
            repository_root,
            readme_file,
            _license_badge_matcher(license_identifier),
            f"{license_identifier} license badge image matching project metadata",
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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README contains a GitHub Actions badge.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the badge is found, otherwise a ``"WARNING: ..."`` message.
        """
        return _badge_result(
            repository_root,
            readme_file,
            _is_github_actions_badge,
            "GH-CI workflow badge.svg URL",
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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README has an installation heading.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(repository_root, readme_file, _INSTALL_SECTION)


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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README has a documentation heading.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(repository_root, readme_file, _DOCUMENTATION_SECTION)


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
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the README has a license heading.

        Parameters
        ----------
        repository_root : pathlib.Path
            Repository root directory.
        readme_file : str or None
            Name of the detected README file, or ``None`` if there is none.

        Returns
        -------
        bool or str
            ``True`` if the heading exists, ``False`` otherwise, or an
            ``"ERROR: ..."`` message if the README cannot be read.
        """
        return _section_result(repository_root, readme_file, _LICENSE_SECTION)
