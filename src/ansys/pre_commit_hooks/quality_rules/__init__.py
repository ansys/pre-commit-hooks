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

"""Initial README-only quality-check registry."""

from ansys.pre_commit_hooks.quality_rules.readme import README

README_QUALITY_RULES = tuple(sorted(README.__subclasses__(), key=lambda rule: rule.__name__))

# Re-export each rule class so the names in ``__all__`` resolve.
globals().update({rule.__name__: rule for rule in README_QUALITY_RULES})

__all__ = ["README", "README_QUALITY_RULES", "repo_review_checks"]
__all__.extend(rule.__name__ for rule in README_QUALITY_RULES)


def repo_review_checks() -> dict[str, object]:
    """Return the supported README checks keyed by rule ID."""
    return {rule.__name__: rule() for rule in README_QUALITY_RULES}
