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

"""Quality-check registry subpackage."""

from collections.abc import Iterable

from ansys.pre_commit_hooks.quality_rules.cicd import CICD
from ansys.pre_commit_hooks.quality_rules.common import _QualityRule
from ansys.pre_commit_hooks.quality_rules.project_metadata import ProjectMetadata
from ansys.pre_commit_hooks.quality_rules.readme import README

README_QUALITY_RULES: tuple[type[README], ...] = tuple(
    sorted(README.__subclasses__(), key=lambda rule_class: rule_class.__name__)
)
PROJECT_METADATA_QUALITY_RULES: tuple[type[ProjectMetadata], ...] = tuple(
    sorted(ProjectMetadata.__subclasses__(), key=lambda rule_class: rule_class.__name__)
)
CICD_QUALITY_RULES: tuple[type[CICD], ...] = tuple(
    sorted(CICD.__subclasses__(), key=lambda rule_class: rule_class.__name__)
)

# Maps each rule family name to its rule classes.
RULE_FAMILIES: dict[str, tuple[type[_QualityRule], ...]] = {
    README.family: README_QUALITY_RULES,
    ProjectMetadata.family: PROJECT_METADATA_QUALITY_RULES,
    CICD.family: CICD_QUALITY_RULES,
}
# Families evaluated when no ``--family`` is requested.
DEFAULT_RULE_FAMILIES: tuple[str, ...] = tuple(RULE_FAMILIES)

# Re-export each rule class so the names in ``__all__`` resolve.
globals().update(
    {
        rule_class.__name__: rule_class
        for rule_classes in RULE_FAMILIES.values()
        for rule_class in rule_classes
    }
)

__all__ = [
    "CICD",
    "CICD_QUALITY_RULES",
    "DEFAULT_RULE_FAMILIES",
    "PROJECT_METADATA_QUALITY_RULES",
    "README",
    "README_QUALITY_RULES",
    "RULE_FAMILIES",
    "ProjectMetadata",
    "repo_review_checks",
]
__all__.extend(
    rule_class.__name__ for rule_classes in RULE_FAMILIES.values() for rule_class in rule_classes
)


def repo_review_checks(families: Iterable[str] = DEFAULT_RULE_FAMILIES) -> dict[str, _QualityRule]:
    """Return the registered rule instances for the requested families.

    Parameters
    ----------
    families : collections.abc.Iterable[str], default: every family
        Rule family names to include.

    Returns
    -------
    dict[str, _QualityRule]
        Rule instances keyed by their rule IDs.
    """
    return {
        rule_class.__name__: rule_class()
        for family in families
        for rule_class in RULE_FAMILIES[family]
    }
