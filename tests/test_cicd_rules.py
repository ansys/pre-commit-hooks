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

"""Tests for the CI/CD quality rule family."""

import pytest

from ansys.pre_commit_hooks import pyansys_quality_report as report
from ansys.pre_commit_hooks.quality_rules import repo_review_checks
from ansys.pre_commit_hooks.quality_rules.common import all_workflows_content

_SHA = "a" * 40

# Action used by each rule that checks for a reusable action.
_RULE_ACTIONS = {
    "CI002": "actions/labeler",
    "CI003": "ansys/actions/check-vulnerabilities",
    "CI004": "ansys/actions/code-style",
    "CI005": "ansys/actions/changelog-fragment",
    "CI006": "ansys/actions/doc-style",
    "CI007": "ansys/actions/doc-build",
    "CI008": "ansys/actions/build-wheelhouse",
    "CI009": "ansys/actions/tests",
    "CI010": "ansys/actions/release-github",
    "CI011": "ansys/actions/check-actions-security",
    "CI012": "ansys/actions/build-library",
    "CI013": "ansys/actions/doc-deploy-dev",
    "CI014": "ansys/actions/doc-deploy-stable",
    "CI015": "ansys/actions/doc-deploy-changelog",
}


def _write_workflow(root, text, name="ci.yml"):
    """Write a workflow file under ``.github/workflows``."""
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True, exist_ok=True)
    (workflows / name).write_text(text, encoding="utf-8")


def _uses_line(action, ref="v1"):
    """Return a workflow step that uses an action."""
    return f"    steps:\n      - uses: {action}@{ref}\n"


def _rule(rule_id):
    """Return the registered CI/CD rule instance for a rule ID."""
    return repo_review_checks(["cicd"])[rule_id]


def test_registry_contains_cicd_rules():
    """The CI/CD family exposes CI001 through CI016 without the abstract helper."""
    rules = repo_review_checks(["cicd"])

    assert list(rules) == [f"CI{number:03d}" for number in range(1, 17)]
    assert all(rule.family == "cicd" for rule in rules.values())


def test_cicd_family_runs_by_default_in_report(tmp_path):
    """The quality report evaluates the CI/CD family when families are not selected."""
    _write_workflow(tmp_path, _uses_line("actions/checkout", _SHA))

    results = {item["id"]: item for item in report._run_checks(tmp_path)["results"]}

    assert results["CI001"]["family"] == "cicd"
    assert results["CI001"]["status"] == "PASSED"
    assert results["CI002"]["status"] == "WARNING"


def test_ci001_requires_workflow_files(tmp_path):
    """CI001 fails when no workflow file exists."""
    assert _rule("CI001").check(tmp_path, None) is False

    _write_workflow(tmp_path, _uses_line("actions/checkout", _SHA))

    assert _rule("CI001").check(tmp_path, None) is True


@pytest.mark.parametrize("rule_id", [*_RULE_ACTIONS, "CI016"])
def test_rules_warn_when_no_workflows_exist(tmp_path, rule_id):
    """Action and SHA rules warn when there are no workflow files to inspect."""
    result = _rule(rule_id).check(tmp_path, None)

    assert isinstance(result, str)
    assert result.startswith("WARNING:")


@pytest.mark.parametrize(("rule_id", "action"), _RULE_ACTIONS.items())
def test_action_rules_pass_when_action_is_used(tmp_path, rule_id, action):
    """Each action rule passes when its reusable action is referenced."""
    _write_workflow(tmp_path, _uses_line(action))

    assert _rule(rule_id).check(tmp_path, None) is True


@pytest.mark.parametrize("rule_id", list(_RULE_ACTIONS))
def test_action_rules_warn_when_action_is_missing(tmp_path, rule_id):
    """Each action rule warns when the workflows do not reference its action."""
    _write_workflow(tmp_path, _uses_line("actions/checkout"))

    result = _rule(rule_id).check(tmp_path, None)

    assert isinstance(result, str)
    assert result.startswith("WARNING:")


def test_tests_rule_ignores_mentions_of_pytest_or_tox(tmp_path):
    """CI009 requires the tests action, not a pytest or tox command in a run step."""
    _write_workflow(
        tmp_path,
        "    steps:\n      - run: pytest tests\n      - run: tox -e py\n",
    )

    assert _rule("CI009").check(tmp_path, None).startswith("WARNING:")

    _write_workflow(tmp_path, _uses_line("ansys/actions/tests-pytest"))

    assert _rule("CI009").check(tmp_path, None) is True


def test_workflow_files_are_merged_from_yml_and_yaml_only(tmp_path):
    """Workflow content combines .yml and .yaml files and ignores other files."""
    _write_workflow(tmp_path, _uses_line("actions/labeler"), name="labels.yml")
    _write_workflow(tmp_path, _uses_line("ansys/actions/tests"), name="tests.yaml")
    _write_workflow(tmp_path, _uses_line("ansys/actions/doc-build"), name="notes.txt")

    content = all_workflows_content(tmp_path)

    assert content is not None
    assert "actions/labeler" in content
    assert "ansys/actions/tests" in content
    assert "doc-build" not in content
    assert _rule("CI002").check(tmp_path, None) is True
    assert _rule("CI009").check(tmp_path, None) is True
    assert _rule("CI007").check(tmp_path, None).startswith("WARNING:")


def test_all_workflows_content_is_none_for_empty_workflow_directory(tmp_path):
    """An empty workflow directory has no content to inspect."""
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    assert all_workflows_content(tmp_path) is None


def test_ci016_accepts_sha_pinned_and_local_actions(tmp_path):
    """CI016 passes when remote actions are SHA-pinned and local actions are used."""
    _write_workflow(
        tmp_path,
        _uses_line("actions/checkout", _SHA) + "      - uses: ./.github/actions/local\n",
    )

    assert _rule("CI016").check(tmp_path, None) is True


def test_ci016_reports_unpinned_actions(tmp_path):
    """CI016 lists each unpinned remote action once."""
    _write_workflow(
        tmp_path,
        _uses_line("actions/checkout", "v4")
        + _uses_line("actions/checkout", "v4")
        + _uses_line("ansys/actions/tests", _SHA),
    )

    result = _rule("CI016").check(tmp_path, None)

    assert result == "WARNING: Actions are not SHA-pinned: actions/checkout@v4."


def test_ci016_rejects_references_with_multiple_at_signs(tmp_path):
    """A 40-character suffix is not enough when the reference syntax is malformed."""
    _write_workflow(tmp_path, _uses_line("actions/checkout", f"v4@{_SHA}"))

    assert _rule("CI016").check(tmp_path, None) == (
        f"WARNING: Actions are not SHA-pinned: actions/checkout@v4@{_SHA}."
    )


def test_all_cicd_rules_pass_with_full_workflow_policy(tmp_path):
    """A workflow that uses every required action with SHA pins passes every CI/CD rule."""
    steps = "".join(_uses_line(action, _SHA) for action in _RULE_ACTIONS.values())
    _write_workflow(tmp_path, steps)

    results = {
        rule_id: _rule(rule_id).check(tmp_path, None) for rule_id in repo_review_checks(["cicd"])
    }

    assert all(result is True for result in results.values()), results
