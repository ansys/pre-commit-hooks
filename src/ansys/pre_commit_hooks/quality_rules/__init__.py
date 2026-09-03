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

"""Rule definitions for the PyAnsys repository quality report.

This package contains the repository quality checks used to review PyAnsys
projects for consistent metadata, automation, documentation, and security
standards.

The checks are grouped into rule families such as:

* build system validation
* CI/CD workflow validation
* Dependabot configuration
* documentation requirements
* project metadata
* README quality
* security checks
* Vale linting configuration
"""

from __future__ import annotations

from ansys.pre_commit_hooks.quality_rules.build_system import (
    BS001,
    BS002,
    BS003,
    BS004,
    BuildSystem,
)
from ansys.pre_commit_hooks.quality_rules.cicd import (
    CI004,
    CI005,
    CI006,
    CI007,
    CI008,
    CI009,
    CI010,
    CI011,
    CI012,
    CI013,
    CI014,
    CI015,
    CI016,
    CICD,
)
from ansys.pre_commit_hooks.quality_rules.cicd_files import CI001, CI002, CI003, CICDFiles
from ansys.pre_commit_hooks.quality_rules.common import (
    CANONICAL_WF,
    _first_doc_line,
    all_workflows_content,
    file_contains,
    file_content,
    file_exists,
    is_mcp,
    normalize_check_result,
    readme_path,
    wf_content,
    wf_label,
    workflow_map,
)
from ansys.pre_commit_hooks.quality_rules.dependabot import (
    DB001,
    DB002,
    DB003,
    DB004,
    DB005,
    DB006,
    DB007,
    DB008,
    Dependabot,
)
from ansys.pre_commit_hooks.quality_rules.documentation import (
    DOC001,
    DOC002,
    DOC003,
    DOC004,
    DOC005,
    DOC006,
    DOC007,
    Documentation,
)
from ansys.pre_commit_hooks.quality_rules.labeler import LB001, LB002, LB003, LB004, LB005, Labeler
from ansys.pre_commit_hooks.quality_rules.mcp import (
    MCP,
    MCP001,
    MCP002,
    MCP003,
    MCP004,
    MCP005,
    MCP006,
    MCP007,
)
from ansys.pre_commit_hooks.quality_rules.pre_commit import (
    PC001,
    PC002,
    PC003,
    PC004,
    PC005,
    PC006,
    PC007,
    PC008,
    PC009,
    PC010,
    PreCommit,
)
from ansys.pre_commit_hooks.quality_rules.project_metadata import (
    PM001,
    PM002,
    PM003,
    PM004,
    PM005,
    PM006,
    PM007,
    PM008,
    PM009,
    PM010,
    PM011,
    PM012,
    PM013,
    PM014,
    PM015,
    ProjectMetadata,
)
from ansys.pre_commit_hooks.quality_rules.readme import (
    README,
    RM000,
    RM001,
    RM002,
    RM003,
    RM004,
    RM005,
    RM006,
    RM007,
    RM008,
)
from ansys.pre_commit_hooks.quality_rules.security import (
    SEC001,
    SEC002,
    SEC003,
    SEC004,
    SEC005,
    Security,
)
from ansys.pre_commit_hooks.quality_rules.vale import VL001, VL002, VL003, VL004, VL005, Vale

__all__ = [
    "file_exists",
    "file_content",
    "file_contains",
    "CANONICAL_WF",
    "all_workflows_content",
    "wf_content",
    "wf_label",
    "workflow_map",
    "readme_path",
    "is_mcp",
    "normalize_check_result",
    "repo_review_families",
    "repo_review_checks",
    "_first_doc_line",
    "ProjectMetadata",
    "PM001",
    "PM002",
    "PM003",
    "PM004",
    "PM005",
    "PM006",
    "PM007",
    "PM008",
    "PM009",
    "PM010",
    "PM011",
    "PM012",
    "PM013",
    "PM014",
    "PM015",
    "CICDFiles",
    "CI001",
    "CI002",
    "CI003",
    "CICD",
    "CI004",
    "CI005",
    "CI006",
    "CI007",
    "CI008",
    "CI009",
    "CI010",
    "CI011",
    "CI012",
    "CI013",
    "CI014",
    "CI015",
    "CI016",
    "Dependabot",
    "DB001",
    "DB002",
    "DB003",
    "DB004",
    "DB005",
    "DB006",
    "DB007",
    "DB008",
    "Documentation",
    "DOC001",
    "DOC002",
    "DOC003",
    "DOC004",
    "DOC005",
    "DOC006",
    "DOC007",
    "README",
    "RM000",
    "RM001",
    "RM002",
    "RM003",
    "RM004",
    "RM005",
    "RM006",
    "RM007",
    "RM008",
    "BuildSystem",
    "BS001",
    "BS002",
    "BS003",
    "BS004",
    "Security",
    "SEC001",
    "SEC002",
    "SEC003",
    "SEC004",
    "SEC005",
    "Labeler",
    "LB001",
    "LB002",
    "LB003",
    "LB004",
    "LB005",
    "Vale",
    "VL001",
    "VL002",
    "VL003",
    "VL004",
    "VL005",
    "MCP",
    "MCP001",
    "MCP002",
    "MCP003",
    "MCP004",
    "MCP005",
    "MCP006",
    "MCP007",
    "PreCommit",
    "PC001",
    "PC002",
    "PC003",
    "PC004",
    "PC005",
    "PC006",
    "PC007",
    "PC008",
    "PC009",
    "PC010",
]


QUALITY_RULE_FAMILIES = (
    ProjectMetadata,
    CICDFiles,
    CICD,
    Dependabot,
    PreCommit,
    Documentation,
    README,
    BuildSystem,
    Security,
    Labeler,
    Vale,
    MCP,
)

QUALITY_RULE_METADATA = {
    "project_metadata": {"name": "Project Metadata", "order": 10},
    "cicd_files": {"name": "CI/CD — Workflow File Names", "order": 20},
    "cicd": {"name": "CI/CD — Content Checks", "order": 25},
    "dependabot": {"name": "Dependabot", "order": 30},
    "pre_commit": {"name": "Pre-commit", "order": 40},
    "documentation": {"name": "Documentation", "order": 50},
    "readme": {"name": "README", "order": 60},
    "build_system": {"name": "Build System", "order": 70},
    "security": {"name": "Security", "order": 80},
    "labeler": {"name": "Labeler", "order": 90},
    "vale": {"name": "Vale", "order": 100},
    "mcp": {"name": "MCP Release Readiness", "order": 110},
}


def repo_review_families() -> dict[str, dict]:
    """Return the family metadata used by the quality report."""
    return dict(QUALITY_RULE_METADATA)


def repo_review_checks() -> dict[str, object]:
    """Return all discovered rule objects keyed by their rule class name."""
    result: dict[str, object] = {}
    for family in QUALITY_RULE_FAMILIES:
        for cls in family.__subclasses__():
            result[cls.__name__] = cls()
    return result
