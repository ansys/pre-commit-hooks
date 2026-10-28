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

"""Run the initial README checks for a repository."""

from __future__ import annotations

import builtins
from collections.abc import Mapping
import json
import os
from pathlib import Path
import sys
from typing import Any, Final, Literal, TextIO, TypeAlias, TypedDict

import click

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 relies on ``toml``.
    import toml as tomllib

from ansys.pre_commit_hooks.quality_rules import (
    DEFAULT_RULE_FAMILIES,
    RULE_FAMILIES,
    repo_review_checks,
)
from ansys.pre_commit_hooks.quality_rules.common import (
    ERROR,
    PASSED,
    WARNING,
    RuleStatus,
    _first_doc_line,
    _QualityRule,
    file_content,
    normalize_check_result,
    readme_path,
)

ColorMode: TypeAlias = Literal["auto", "always", "never"]

_ANSI_RESET: Final = "\033[0m"
_ANSI_BOLD: Final = "\033[1m"
_STATUS_COLORS: Final[dict[RuleStatus, str]] = {
    PASSED: "\033[32m",
    WARNING: "\033[33m",
    ERROR: "\033[31m",
}


def autoflush_print(*args: object, **kwargs: Any) -> None:
    """Call :func:`print` and always flush so output appears immediately."""
    kwargs["flush"] = True
    builtins.print(*args, **kwargs)


class _RuleResult(TypedDict):
    """Serialized result for one quality-report rule."""

    id: str
    family: str
    label: str
    description: str
    status: RuleStatus
    detail: str


class _StatusTally(TypedDict):
    """Counts for each public quality-report status."""

    PASSED: int
    WARNING: int
    ERROR: int


class _QualityReport(TypedDict):
    """Complete quality-report payload."""

    results: list[_RuleResult]
    tally: _StatusTally
    score: int


class _RuleMetadata(TypedDict):
    """Metadata that describes an available quality-report rule."""

    id: str
    family: str
    name: str
    description: str


def _colors_enabled(
    color_mode: ColorMode,
    output_stream: TextIO,
    environment: Mapping[str, str],
) -> bool:
    """Return whether ANSI colors should be emitted.

    Parameters
    ----------
    color_mode : {"auto", "always", "never"}
        Requested color behavior.
    output_stream : typing.TextIO
        Stream that receives the report.
    environment : collections.abc.Mapping[str, str]
        Process environment used to inspect ``NO_COLOR`` and ``FORCE_COLOR``.

    Returns
    -------
    bool
        Whether ANSI color sequences should be included.
    """
    if color_mode == "always":
        return True
    if color_mode == "never" or "NO_COLOR" in environment:
        return False
    if environment.get("FORCE_COLOR", "") not in {"", "0"}:
        return True
    return output_stream.isatty()


def _styled(text: str, ansi_style: str, *, colors_enabled: bool) -> str:
    """Apply an ANSI style when colors are enabled.

    Parameters
    ----------
    text : str
        Text to style.
    ansi_style : str
        ANSI escape sequence applied before the text.
    colors_enabled : bool
        Whether to include ANSI escape sequences.

    Returns
    -------
    str
        Styled text, or the original text when colors are disabled.
    """
    if not colors_enabled:
        return text
    return f"{ansi_style}{text}{_ANSI_RESET}"


def _status_text(status: RuleStatus, *, colors_enabled: bool) -> str:
    """Format a status using its assigned color.

    Parameters
    ----------
    status : RuleStatus
        Status to format.
    colors_enabled : bool
        Whether to include ANSI escape sequences.

    Returns
    -------
    str
        Left-aligned status text with optional color.
    """
    padded_status = f"{status:<7}"
    return _styled(
        padded_status,
        _STATUS_COLORS[status],
        colors_enabled=colors_enabled,
    )


def _overall_status(quality_report: _QualityReport) -> RuleStatus:
    """Return the highest status present in a quality report.

    Parameters
    ----------
    quality_report : _QualityReport
        Report returned by ``_run_checks``.

    Returns
    -------
    RuleStatus
        ``ERROR`` when errors are present, otherwise ``WARNING`` when warnings
        are present, and ``PASSED`` otherwise.
    """
    status_tally = quality_report["tally"]
    if status_tally[ERROR]:
        return ERROR
    if status_tally[WARNING]:
        return WARNING
    return PASSED


def _normalize_rule_ids(argument_values: list[str]) -> set[str]:
    """Normalize repeated and comma-separated rule IDs.

    Parameters
    ----------
    argument_values : list[str]
        Values supplied to a repeatable rule-ID command-line option.

    Returns
    -------
    set[str]
        Uppercase rule IDs with surrounding whitespace and empty values
        removed.
    """
    return {
        rule_id.strip().upper()
        for argument_value in argument_values
        for rule_id in argument_value.split(",")
        if rule_id.strip()
    }


def _families_to_run(selected_families: set[str] | None) -> tuple[str, ...]:
    """Return the rule families to evaluate.

    Parameters
    ----------
    selected_families : set[str] or None
        Explicitly requested families.

    Returns
    -------
    tuple[str, ...]
        The requested families, or every family when none is requested.
    """
    if selected_families:
        return tuple(sorted(selected_families))
    return DEFAULT_RULE_FAMILIES


def _execute_check(
    rule: _QualityRule,
    rule_id: str,
    repository_root: Path,
    detected_readme_file: str | None,
) -> _RuleResult:
    """Execute and serialize one rule.

    Parameters
    ----------
    rule : _QualityRule
        Rule instance to execute.
    rule_id : str
        Stable identifier for the rule.
    repository_root : pathlib.Path
        Repository root directory.
    detected_readme_file : str or None
        Detected README path, or ``None`` when no supported README exists.

    Returns
    -------
    _RuleResult
        Normalized rule result ready for text or JSON output.
    """
    try:
        raw_result = rule.check(repository_root, detected_readme_file)
    except (OSError, TypeError, ValueError) as error:
        raw_result = f"ERROR: Check error: {error}"

    rule_status, result_detail = normalize_check_result(raw_result, rule)
    return {
        "id": rule_id,
        "family": rule.family,
        "label": (type(rule).__doc__ or rule_id).strip().splitlines()[0],
        "description": _first_doc_line(rule),
        "status": rule_status,
        "detail": result_detail,
    }


def _run_checks(
    repository_root: Path,
    *,
    selected_rule_ids: set[str] | None = None,
    ignored_rule_ids: set[str] | None = None,
    selected_families: set[str] | None = None,
) -> _QualityReport:
    """Evaluate registered rules for a repository.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.
    selected_rule_ids : set[str] or None, optional
        Rule IDs to evaluate. All rules of the evaluated families are used when
        omitted or empty.
    ignored_rule_ids : set[str] or None, optional
        Rule IDs to omit from the report.
    selected_families : set[str] or None, optional
        Rule families to evaluate. Defaults to every family.

    Returns
    -------
    _QualityReport
        Rule results, status counts, and the resulting score.
    """
    registered_rules = repo_review_checks(_families_to_run(selected_families))
    normalized_selected_ids = {rule_id.upper() for rule_id in selected_rule_ids or set()}
    normalized_ignored_ids = {rule_id.upper() for rule_id in ignored_rule_ids or set()}
    if normalized_selected_ids:
        registered_rules = {
            rule_id: rule
            for rule_id, rule in registered_rules.items()
            if rule_id.upper() in normalized_selected_ids
        }
    detected_readme_file = readme_path(repository_root)
    rule_results = [
        _execute_check(rule, rule_id, repository_root, detected_readme_file)
        for rule_id, rule in registered_rules.items()
        if rule_id.upper() not in normalized_ignored_ids
    ]

    passed_count = sum(rule_result["status"] == PASSED for rule_result in rule_results)
    warning_count = sum(rule_result["status"] == WARNING for rule_result in rule_results)
    error_count = sum(rule_result["status"] == ERROR for rule_result in rule_results)
    scored_rule_count = passed_count + error_count
    return {
        "results": rule_results,
        "tally": {
            PASSED: passed_count,
            WARNING: warning_count,
            ERROR: error_count,
        },
        "score": (round(passed_count / scored_rule_count * 100) if scored_rule_count else 0),
    }


def _metadata_report(
    selected_rule_ids: set[str] | None = None,
    selected_families: set[str] | None = None,
) -> list[_RuleMetadata]:
    """Return metadata for available rules.

    Parameters
    ----------
    selected_rule_ids : set[str] or None, optional
        Rule IDs to include. All rules are included when omitted or empty.
    selected_families : set[str] or None, optional
        Rule families to include. Every family is listed when omitted or empty.

    Returns
    -------
    list[_RuleMetadata]
        Metadata records ordered by rule ID.
    """
    registered_rules = repo_review_checks(selected_families or tuple(RULE_FAMILIES))
    normalized_selected_ids = {rule_id.upper() for rule_id in selected_rule_ids or set()}
    return [
        {
            "id": rule_id,
            "family": rule.family,
            "name": _first_doc_line(rule),
            "description": (type(rule).__doc__ or "").strip().splitlines()[0],
        }
        for rule_id, rule in sorted(registered_rules.items())
        if not normalized_selected_ids or rule_id.upper() in normalized_selected_ids
    ]


def _print_report(
    quality_report: _QualityReport,
    *,
    show_all: bool = False,
    colors_enabled: bool = False,
) -> None:
    """Print a human-readable quality report.

    Parameters
    ----------
    quality_report : _QualityReport
        Report returned by ``_run_checks``.
    show_all : bool, default: False
        Whether to include rules with a ``PASSED`` status.
    colors_enabled : bool, default: False
        Whether to color status text with ANSI escape sequences.
    """
    title = "PyAnsys quality report"
    autoflush_print(_styled(title, _ANSI_BOLD, colors_enabled=colors_enabled))
    autoflush_print("=" * len(title))

    overall_status = _overall_status(quality_report)
    formatted_score = _styled(
        f"{quality_report['score']}%",
        _STATUS_COLORS[overall_status],
        colors_enabled=colors_enabled,
    )
    autoflush_print(f"Score: {formatted_score}")

    status_tally = quality_report["tally"]
    autoflush_print()
    autoflush_print(_styled("Status summary", _ANSI_BOLD, colors_enabled=colors_enabled))
    for status in (PASSED, WARNING, ERROR):
        autoflush_print(
            f"  {_status_text(status, colors_enabled=colors_enabled)} " f"{status_tally[status]:>3}"
        )

    visible_results = [
        rule_result
        for rule_result in quality_report["results"]
        if show_all or rule_result["status"] != PASSED
    ]
    autoflush_print()
    autoflush_print(_styled("Checks", _ANSI_BOLD, colors_enabled=colors_enabled))
    if not visible_results:
        autoflush_print("  No warnings or errors.")
        return

    for rule_result in visible_results:
        result_detail = rule_result["detail"]
        display_headline = (
            result_detail
            if rule_result["status"] in {WARNING, ERROR} and result_detail
            else rule_result["label"]
        )
        autoflush_print(
            f"  {_status_text(rule_result['status'], colors_enabled=colors_enabled)} "
            f"{rule_result['id']}  {display_headline}"
        )
        if (
            result_detail
            and rule_result["status"] not in {WARNING, ERROR}
            and result_detail != display_headline
        ):
            autoflush_print(f"  {result_detail}")


def _find_project_root(start_directory: Path) -> Path:
    """Return the project root for a starting directory.

    Parameters
    ----------
    start_directory : pathlib.Path
        Directory where the search begins, usually the current directory.

    Returns
    -------
    pathlib.Path
        Nearest directory that contains ``pyproject.toml``, searching
        ``start_directory`` and then its parents. ``start_directory`` is
        returned if none contains one.
    """
    for directory in (start_directory, *start_directory.parents):
        if (directory / "pyproject.toml").is_file():
            return directory
    return start_directory


def _validate_rule_ids(
    option_name: str,
    rule_ids: set[str],
) -> None:
    """Validate rule IDs supplied to a command-line option.

    Parameters
    ----------
    option_name : str
        Command-line option associated with ``rule_ids``.
    rule_ids : set[str]
        Normalized rule IDs to validate.
    """
    available_rule_ids = sorted(repo_review_checks(tuple(RULE_FAMILIES)))
    unknown_rule_ids = sorted(rule_ids.difference(available_rule_ids))
    if unknown_rule_ids:
        raise click.UsageError(
            f"unknown rule ID(s) for {option_name}: {', '.join(unknown_rule_ids)}. "
            f"Available rules: {', '.join(available_rule_ids)}"
        )


def _pyproject_ignored_rule_ids(repository_root: Path) -> set[str]:
    """Read ignored rule IDs from ``[tool.pyansys-quality-report]``.

    Parameters
    ----------
    repository_root : pathlib.Path
        Repository root directory.

    Returns
    -------
    set[str]
        Normalized rule IDs listed under the ``ignore`` key. The set is empty when
        ``pyproject.toml`` is missing or has no such key.

    Raises
    ------
    click.UsageError
        If ``pyproject.toml`` is invalid TOML or ``ignore`` is not a list of strings.
    """
    pyproject_content = file_content(repository_root, "pyproject.toml")
    if pyproject_content is None:
        return set()
    try:
        pyproject_data = tomllib.loads(pyproject_content)
    except (TypeError, ValueError) as error:
        raise click.UsageError(f"pyproject.toml is not valid TOML: {error}") from error

    tool_settings = pyproject_data.get("tool", {}).get("pyansys-quality-report", {})
    ignored_values = tool_settings.get("ignore", []) if isinstance(tool_settings, dict) else []
    if not isinstance(ignored_values, list) or not all(
        isinstance(value, str) for value in ignored_values
    ):
        raise click.UsageError(
            "[tool.pyansys-quality-report] ignore in pyproject.toml must be a list of strings"
        )
    return _normalize_rule_ids(ignored_values)


@click.command(help="Run PyAnsys README quality checks.")
@click.option("--json", "json_output", is_flag=True, help="Emit a JSON report.")
@click.option("--metadata", is_flag=True, help="List available rule metadata.")
@click.option("--check", "check", multiple=True, help="Select rule IDs.")
@click.option("--family", multiple=True, help="Select rule family (readme, project_metadata).")
@click.option("--ignore", multiple=True, help="Ignore rule IDs (also read from pyproject.toml).")
@click.option("--show-all", is_flag=True, help="Include passing checks.")
@click.option(
    "--fails-only",
    is_flag=True,
    help="Show warnings and errors only (the default).",
)
@click.option(
    "--color",
    type=click.Choice(["auto", "always", "never"]),
    default="always",
    help="Control ANSI colors (default: always).",
)
def _cli(
    json_output: bool,
    metadata: bool,
    check: tuple[str, ...],
    family: tuple[str, ...],
    ignore: tuple[str, ...],
    show_all: bool,
    fails_only: bool,
    color: ColorMode,
) -> int:
    """Run README quality checks and return the process exit code."""
    if show_all and fails_only:
        raise click.UsageError("Use only one of --show-all or --fails-only")

    selected_rule_ids = _normalize_rule_ids(list(check))
    ignored_rule_ids = _normalize_rule_ids(list(ignore))
    _validate_rule_ids("--check", selected_rule_ids)
    _validate_rule_ids("--ignore", ignored_rule_ids)
    selected_rule_families = {
        rule_family.strip().lower()
        for argument_value in family
        for rule_family in argument_value.split(",")
        if rule_family.strip()
    }
    unknown_families = selected_rule_families - set(RULE_FAMILIES)
    if unknown_families:
        raise click.UsageError(
            f"unknown rule family(ies): {', '.join(sorted(unknown_families))}. "
            f"Available families: {', '.join(RULE_FAMILIES)}"
        )

    if metadata:
        autoflush_print(
            json.dumps(_metadata_report(selected_rule_ids, selected_rule_families), indent=2)
        )
        return 0

    repository_root = _find_project_root(Path.cwd())
    configured_ignored_rule_ids = _pyproject_ignored_rule_ids(repository_root)
    _validate_rule_ids("[tool.pyansys-quality-report] ignore", configured_ignored_rule_ids)
    quality_report = _run_checks(
        repository_root,
        selected_rule_ids=selected_rule_ids,
        ignored_rule_ids=ignored_rule_ids | configured_ignored_rule_ids,
        selected_families=selected_rule_families,
    )
    if json_output:
        autoflush_print(json.dumps(quality_report, indent=2))
        return 1 if quality_report["tally"][ERROR] else 0

    colors_enabled = _colors_enabled(
        color,
        sys.stdout,
        os.environ,
    )
    _print_report(
        quality_report,
        show_all=show_all,
        colors_enabled=colors_enabled,
    )
    return 1 if quality_report["tally"][ERROR] else 0


def main(argv: list[str] | None = None) -> int:
    """Run README quality checks for a repository.

    Parameters
    ----------
    argv : list[str] or None, optional
        Command-line arguments without the executable name. ``sys.argv`` is
        used when omitted.

    Returns
    -------
    int
        ``1`` when any rule reports ``ERROR``, otherwise ``0``.
    """
    try:
        # standalone_mode=False returns the callback's value instead of exiting.
        return _cli.main(args=argv, standalone_mode=False)
    except click.exceptions.Exit as exit_request:
        return exit_request.exit_code
    except click.ClickException as click_error:
        click_error.show()
        raise SystemExit(click_error.exit_code) from click_error
    except click.Abort as abort_request:
        click.echo("Aborted!", err=True)
        raise SystemExit(1) from abort_request


if __name__ == "__main__":
    raise SystemExit(main())
