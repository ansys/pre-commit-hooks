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

The checks cover the documentation source tree and layout, Sphinx configuration,
index card links, authored RST filenames, gallery examples, and API docstring
coverage tooling.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
from typing import ClassVar, Final
from urllib.parse import urlsplit

import yaml

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
    "DOC009",
    "DOC010",
    "DOC011",
    "DOC012",
    "DOC013",
    "DOC014",
    "DOC015",
    "DOC016",
    "DOC017",
    "DOC018",
    "DOC019",
    "DOC020",
    "DOC021",
    "DOC022",
    "DOC023",
    "DOC024",
    "DOC025",
    "DOC026",
    "DOC027",
    "DOC028",
    "DOC029",
    "DOC030",
    "DOCUMENTATION_QUALITY_RULES",
    "Documentation",
]

_DOC_INDEX: Final[str] = "doc/source/index.rst"
_SPHINX_CONFIG: Final[str] = "doc/source/conf.py"
_PRE_COMMIT_CONFIG: Final[str] = ".pre-commit-config.yaml"
_NOT_LITERAL: Final[object] = object()
_INDEX_CARD_TARGETS: Final[tuple[str, ...]] = (
    "getting-started",
    "user-guide",
    "api",
    "examples",
    "contribute",
    "changelog",
)


def _contains(repository_root: Path, relative_path: str, pattern: str | re.Pattern[str]) -> bool:
    """Return whether a readable repository file contains the requested text or pattern."""
    content = file_content(repository_root, relative_path)
    if content is None:
        return False
    if isinstance(pattern, str):
        return pattern in content
    return pattern.search(content) is not None


def _sphinx_assignments(repository_root: Path) -> dict[str, ast.expr] | None:
    """Return top-level Sphinx config assignments without executing the file."""
    content = file_content(repository_root, _SPHINX_CONFIG)
    if content is None:
        return None
    try:
        module = ast.parse(content)
    except SyntaxError:
        return None

    assignments: dict[str, ast.expr] = {}
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                assignments[statement.target.id] = statement.value
    return assignments


def _literal(node: ast.expr | None) -> object:
    """Return a literal AST value or a sentinel when it is dynamic or invalid."""
    if node is None:
        return _NOT_LITERAL
    try:
        return ast.literal_eval(node)
    except (TypeError, ValueError):
        return _NOT_LITERAL


def _dict_value(node: ast.expr | None, key: str) -> ast.expr | None:
    """Return a value from a literal dictionary by its string key."""
    if not isinstance(node, ast.Dict):
        return None
    for candidate, value in zip(node.keys, node.values, strict=True):
        if _literal(candidate) == key:
            return value
    return None


def _has_nonempty_setting(node: ast.expr | None) -> bool:
    """Return whether a setting is non-empty or has a dynamic expression."""
    value = _literal(node)
    if value is not _NOT_LITERAL:
        return isinstance(value, str) and bool(value.strip())
    return node is not None and not (isinstance(node, ast.Constant) and node.value is None)


def _valid_hostname(value: object) -> bool:
    """Return whether a string is a dotted hostname with valid DNS labels."""
    if not isinstance(value, str) or len(value) > 253 or "." not in value:
        return False
    return all(
        re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in value.rstrip(".").split(".")
    )


def _valid_cname(node: ast.expr | None) -> bool:
    """Return whether CNAME is a hostname or getenv call with a hostname fallback."""
    value = _literal(node)
    if value is not _NOT_LITERAL:
        return _valid_hostname(value)
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "getenv"
    ):
        return False
    fallback = (
        node.args[1]
        if len(node.args) > 1
        else next((keyword.value for keyword in node.keywords if keyword.arg == "default"), None)
    )
    return _valid_hostname(_literal(fallback))


def _valid_copyright(node: ast.expr | None) -> bool:
    """Return whether copyright is a non-empty literal or formatted string."""
    value = _literal(node)
    if value is not _NOT_LITERAL:
        return isinstance(value, str) and bool(value.strip())
    return (
        isinstance(node, ast.JoinedStr)
        and any(
            isinstance(value, ast.Constant) and isinstance(value.value, str) and value.value.strip()
            for value in node.values
        )
        and any(isinstance(value, ast.FormattedValue) for value in node.values)
    )


def _valid_switcher_url(node: ast.expr | None) -> bool:
    """Return whether a switcher URL is HTTPS or a matching HTTPS f-string."""
    value = _literal(node)
    if isinstance(value, str):
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.netloc)
            and parsed.path.endswith("/versions.json")
        )
    if isinstance(node, ast.JoinedStr):
        static_parts = "".join(
            part.value
            for part in node.values
            if isinstance(part, ast.Constant) and isinstance(part.value, str)
        )
        return static_parts.startswith("https://") and "/versions.json" in static_parts
    return isinstance(node, (ast.Call, ast.Name, ast.Attribute))


def _index_card_doc_targets(content: str) -> set[str]:
    """Return document targets linked from Sphinx Design card directives."""
    lines = content.splitlines()
    targets: set[str] = set()
    directive = re.compile(r"^(?P<indent>[ \t]*)\.\.\s+(?:grid-item-card|card)::")
    for index, line in enumerate(lines):
        match = directive.match(line)
        if match is None:
            continue
        indent = len(match.group("indent"))
        block: list[str] = []
        for block_line in lines[index + 1 :]:
            if block_line.strip() and len(block_line) - len(block_line.lstrip(" \t")) <= indent:
                break
            block.append(block_line)
        block_text = "\n".join(block)
        link_type = re.search(r"(?m)^\s*:link-type:\s*(\S+)", block_text)
        link = re.search(r"(?m)^\s*:link:\s*(\S+)", block_text)
        if link_type is not None and link_type.group(1).lower() == "doc" and link is not None:
            target = link.group(1).strip().removesuffix(".rst").strip("/")
            if target.endswith("/index"):
                target = target.removesuffix("/index")
            targets.add(target)
    return targets


def _authored_rst_paths(repository_root: Path) -> list[Path] | None:
    """Return authored RST files, excluding generated AutoAPI source pages."""
    source_directory = _repository_file(repository_root, "doc/source")
    if source_directory is None:
        return None
    try:
        return [
            path
            for path in source_directory.rglob("*")
            if path.is_file()
            and path.suffix.lower() == ".rst"
            and path.relative_to(source_directory).parts[:2] != ("api", "src")
        ]
    except OSError:
        return None


def _directory_has_files(repository_root: Path, relative_path: str) -> bool:
    """Return whether a documentation section contains at least one file."""
    directory = _repository_file(repository_root, f"doc/source/{relative_path}")
    if directory is None:
        return False
    try:
        return directory.is_dir() and any(entry.is_file() for entry in directory.rglob("*"))
    except OSError:
        return False


def _has_interrogate_hook(repository_root: Path) -> bool:
    """Return whether the pre-commit configuration declares an interrogate hook."""
    content = file_content(repository_root, _PRE_COMMIT_CONFIG)
    if content is None:
        return False
    try:
        configuration: object = yaml.safe_load(content)
    except yaml.YAMLError:
        return False
    if not isinstance(configuration, dict):
        return False
    repositories = configuration.get("repos")
    if not isinstance(repositories, list):
        return False
    return any(
        isinstance(repository, dict)
        and isinstance(hooks := repository.get("hooks"), list)
        and any(isinstance(hook, dict) and hook.get("id") == "interrogate" for hook in hooks)
        for repository in repositories
    )


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
    """Numpydoc is enabled for NumPy-style API documentation."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend numpydoc for rendering NumPy-style API documentation."""
        if _contains(repository_root, _SPHINX_CONFIG, "numpydoc"):
            return True
        return (
            f"RECOMMENDATION: Enable numpydoc in {_SPHINX_CONFIG} to render NumPy-style "
            "API documentation."
        )


class DOC004(Documentation):
    """Intersphinx is enabled for cross-project documentation references."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend intersphinx for linking to external project documentation."""
        if _contains(repository_root, _SPHINX_CONFIG, "intersphinx"):
            return True
        return (
            f"RECOMMENDATION: Enable intersphinx in {_SPHINX_CONFIG} to link references "
            "to external documentation."
        )


class DOC005(Documentation):
    """The index page has a getting started section."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation index has a getting-started section."""
        return _contains(repository_root, _DOC_INDEX, re.compile(r"getting.started", re.IGNORECASE))


class DOC006(Documentation):
    """The index page has an API reference section."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Return whether the documentation index has an API reference section."""
        return _contains(
            repository_root,
            _DOC_INDEX,
            re.compile(r"api.reference|api_reference", re.IGNORECASE),
        )


class DOC007(Documentation):
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
                return DOC007._examples_recommendation()
            examples_dirs = DOC007._extract_examples_dirs(conf)
            if examples_dirs and all(
                DOC007._configured_examples_dir_has_files(repository_root, path)
                for path in examples_dirs
            ):
                return True
            return DOC007._examples_recommendation()

        if any(
            DOC007._dir_has_files(repository_root, candidate)
            for candidate in ("examples", "doc/examples", "doc/source/examples")
        ):
            return True
        return DOC007._examples_recommendation()

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
            return directory.is_dir() and DOC007._dir_tree_has_files(directory)
        except OSError:
            return False

    @staticmethod
    def _dir_tree_has_files(directory: Path) -> bool:
        """Return whether a directory tree contains a regular file."""
        try:
            for entry in directory.iterdir():
                if entry.is_file():
                    return True
                if entry.is_dir() and not entry.is_symlink() and DOC007._dir_tree_has_files(entry):
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
        return any(DOC007._dir_has_files(repository_root, path) for path in candidates)


class DOC008(Documentation):
    """The Ansys Sphinx theme and PyAnsys branding are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Warn when the Ansys Sphinx theme or branding settings are missing."""
        assignments = _sphinx_assignments(repository_root)
        if assignments is None:
            return f"WARNING: Cannot verify theme and branding settings in {_SPHINX_CONFIG}."
        configured = (
            _literal(assignments.get("html_theme")) == "ansys_sphinx_theme"
            and _literal(_dict_value(assignments.get("html_theme_options"), "logo")) == "pyansys"
            and isinstance(assignments.get("html_favicon"), ast.Name)
            and assignments["html_favicon"].id == "ansys_favicon"
        )
        if not configured:
            return (
                f"WARNING: Configure html_theme='ansys_sphinx_theme', the pyansys logo, and "
                f"ansys_favicon in {_SPHINX_CONFIG}."
            )
        return True


class DOC009(Documentation):
    """Project and page titles are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Check that project and page titles are non-empty."""
        assignments = _sphinx_assignments(repository_root)
        if assignments is None:
            return False
        return all(
            _has_nonempty_setting(assignments.get(name))
            for name in ("project", "html_title", "html_short_title")
        )


class DOC010(Documentation):
    """Site author, copyright, and CNAME metadata are configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend complete author, copyright, and CNAME metadata."""
        assignments = _sphinx_assignments(repository_root)
        if assignments is None:
            return True

        missing = []
        if not _has_nonempty_setting(assignments.get("author")):
            missing.append("author")
        if not _valid_copyright(assignments.get("copyright")):
            missing.append("copyright")
        if not _valid_cname(assignments.get("cname")):
            missing.append("cname")
        if not missing:
            return True
        return (
            "RECOMMENDATION: Review "
            f"{', '.join(missing)} in {_SPHINX_CONFIG}; provide non-empty metadata and a valid "
            "CNAME hostname."
        )


class DOC011(Documentation):
    """The Ansys theme version switcher is configured."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend a complete switcher configuration when it is statically inspectable."""
        assignments = _sphinx_assignments(repository_root)
        if assignments is None:
            return True

        theme_options = assignments.get("html_theme_options")
        if theme_options is None:
            missing = ["json_url", "version_match"]
        elif not isinstance(theme_options, ast.Dict):
            return True
        else:
            switcher = _dict_value(theme_options, "switcher")
            if switcher is None:
                missing = ["json_url", "version_match"]
            elif not isinstance(switcher, ast.Dict):
                return True
            else:
                missing = []
                if not _valid_switcher_url(_dict_value(switcher, "json_url")):
                    missing.append("json_url")
                if not _has_nonempty_setting(_dict_value(switcher, "version_match")):
                    missing.append("version_match")

        if not missing:
            return True
        return (
            "RECOMMENDATION: Configure "
            f"{', '.join(missing)} in html_theme_options['switcher'] in {_SPHINX_CONFIG}."
        )


class DOC012(Documentation):
    """The index links required documentation pages with cards."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Require Sphinx Design cards linking to every top-level docs page."""
        index = file_content(repository_root, _DOC_INDEX)
        if index is None:
            return f"WARNING: Cannot check documentation cards because {_DOC_INDEX} cannot be read."
        linked_targets = _index_card_doc_targets(index)
        missing = [target for target in _INDEX_CARD_TARGETS if target not in linked_targets]
        if missing:
            return (
                f"WARNING: Add documentation cards in {_DOC_INDEX} linking to: "
                f"{', '.join(missing)}."
            )
        return True


class DOC013(Documentation):
    """Authored RST filenames use lowercase letters and hyphens."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Reject authored RST filenames with uppercase letters or underscores."""
        paths = _authored_rst_paths(repository_root)
        if paths is None:
            return "WARNING: Cannot inspect RST files under doc/source."
        invalid = [
            path.relative_to(repository_root).as_posix()
            for path in paths
            if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*\.rst", path.name) is None
        ]
        if invalid:
            return (
                "WARNING: Rename RST files to lowercase words separated by hyphens: "
                f"{', '.join(sorted(invalid))}."
            )
        return True


def _layout_page_result(
    repository_root: Path, page: str, *, alternatives: tuple[str, ...] = ()
) -> RuleCheckResult:
    """Recommend a missing page, accepting any supported repository-relative path."""
    paths = (page, *alternatives)
    if any(file_exists(repository_root, f"doc/source/{path}") for path in paths):
        return True
    locations = " or ".join(f"doc/source/{path}" for path in paths)
    return f"RECOMMENDATION: Add a documentation page at {locations}."


def _layout_section_result(repository_root: Path, section: str) -> RuleCheckResult:
    """Recommend content when a documentation section has no files."""
    if _directory_has_files(repository_root, section):
        return True
    return f"RECOMMENDATION: Add content under doc/source/{section}/."


class DOC014(Documentation):
    """The getting-started page is provided as a root page or section index."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend either supported getting-started page path."""
        return _layout_page_result(
            repository_root,
            "getting-started.rst",
            alternatives=("getting-started/index.rst",),
        )


class DOC015(Documentation):
    """The user-guide page is provided as a root page or section index."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend either supported user-guide page path."""
        return _layout_page_result(
            repository_root, "user-guide.rst", alternatives=("user-guide/index.rst",)
        )


class DOC016(Documentation):
    """The API page is provided as a root page or section index."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend either supported API page path."""
        return _layout_page_result(repository_root, "api.rst", alternatives=("api/index.rst",))


class DOC017(Documentation):
    """The examples page is provided as a root page or section index."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend either supported examples page path."""
        return _layout_page_result(
            repository_root, "examples.rst", alternatives=("examples/index.rst",)
        )


class DOC018(Documentation):
    """The contribute page is provided as a root page or section index."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend either supported contribute page path."""
        return _layout_page_result(
            repository_root, "contribute.rst", alternatives=("contribute/index.rst",)
        )


class DOC019(Documentation):
    """The changelog root page exists."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the changelog root page when it is missing."""
        return _layout_page_result(repository_root, "changelog.rst")


class DOC020(Documentation):
    """The getting-started section contains documentation files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend content when the getting-started section is empty or absent."""
        return _layout_section_result(repository_root, "getting-started")


class DOC021(Documentation):
    """The user-guide section contains documentation files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend content when the user-guide section is empty or absent."""
        return _layout_section_result(repository_root, "user-guide")


class DOC022(Documentation):
    """The API section contains documentation files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend content when the API section is empty or absent."""
        return _layout_section_result(repository_root, "api")


class DOC023(Documentation):
    """The examples section contains files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend content when the examples section is empty or absent."""
        return _layout_section_result(repository_root, "examples")


class DOC024(Documentation):
    """The contribute section contains documentation files."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend content when the contribute section is empty or absent."""
        return _layout_section_result(repository_root, "contribute")


class DOC025(Documentation):
    """The user contributor guide is recommended."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend adding the user contributor guide when it is missing."""
        return _layout_page_result(repository_root, "contribute/user.rst")


class DOC026(Documentation):
    """The documentarian contributor guide is recommended."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend adding the documentarian contributor guide when it is missing."""
        return _layout_page_result(repository_root, "contribute/documentarian.rst")


class DOC027(Documentation):
    """The developer contributor guide is recommended."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend adding the developer contributor guide when it is missing."""
        return _layout_page_result(repository_root, "contribute/developer.rst")


class DOC028(Documentation):
    """The interrogate hook checks docstring coverage."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend the interrogate pre-commit hook when it is not configured."""
        if _has_interrogate_hook(repository_root):
            return True
        return (
            "RECOMMENDATION: Add the interrogate pre-commit hook to monitor docstring coverage; "
            "coverage gaps are advisory."
        )


class DOC029(Documentation):
    """Sphinx AutoAPI or an API reference page is available."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Find AutoAPI references in the config or accept a manually maintained API page."""
        if file_exists(repository_root, "doc/source/api.rst") or file_exists(
            repository_root, "doc/source/api/index.rst"
        ):
            return True

        config = file_content(repository_root, _SPHINX_CONFIG)
        if config is None:
            return f"WARNING: Cannot inspect {_SPHINX_CONFIG}; enable AutoAPI or add an API page."
        autoapi_markers = (
            "ansys_sphinx_theme.extension.autoapi",
            "autoapi.extension",
        )
        if any(marker in config for marker in autoapi_markers):
            return True
        return (
            f"WARNING: Sphinx AutoAPI was not found in {_SPHINX_CONFIG}; enable AutoAPI "
            "or add an API page."
        )


class DOC030(Documentation):
    """A cheatsheet is added to the documentation."""

    @staticmethod
    def check(repository_root: Path, readme_file: str | None) -> RuleCheckResult:
        """Recommend adding a cheatsheet to the documentation."""
        assignments = _sphinx_assignments(repository_root)
        if assignments is None:
            return True
        theme_options = assignments.get("html_theme_options")
        if theme_options is None:
            missing = ["cheatsheet"]
        elif not isinstance(theme_options, ast.Dict):
            return True
        else:
            cheatsheet = _dict_value(theme_options, "cheatsheet")
            if cheatsheet is None:
                missing = ["cheatsheet"]
            elif not isinstance(cheatsheet, ast.Dict):
                missing = ["file", "title", "version", "pages"]
            else:
                missing = []
                for key in ("file", "title", "version"):
                    if not _has_nonempty_setting(_dict_value(cheatsheet, key)):
                        missing.append(key)
                pages = _literal(_dict_value(cheatsheet, "pages"))
                if (
                    not isinstance(pages, (list, tuple))
                    or not pages
                    or not all(isinstance(page, str) and page.strip() for page in pages)
                ):
                    missing.append("pages")

        if not missing:
            return True
        return "RECOMMENDATION: Add a cheatsheet to the documentation."


DOCUMENTATION_QUALITY_RULES: tuple[type[Documentation], ...] = tuple(
    sorted(Documentation.__subclasses__(), key=lambda rule_class: rule_class.__name__)
)
