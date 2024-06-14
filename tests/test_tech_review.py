# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import os

import git

# import pytest

# import ansys.pre_commit_hooks.tech_review as hook

git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
REPO_PATH = git_repo.git.rev_parse("--show-toplevel")

# Tests for
# name = "ansys-pre-commit-hooks"
# name2 = "ansys-precommit-hooks"
# name3 = "mechanical-precommit-hook"
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name)) # False
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name2)) # True
# bool(re.match(r"^ansys-[a-z]+-[a-z]+$", name3)) # False
