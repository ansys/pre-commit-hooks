# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Generate a PyAnsys repository quality report for the current project.

This implementation keeps the quality logic bundled in the hook repo itself so it
works in a standalone pre-commit environment without the separate
``pyansys-repo-review`` package being installed.
"""

from __future__ import annotations

import argparse
import json
import re
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Iterator

try:
    from importlib.resources.abc import Traversable
except ImportError:  # pragma: no cover
    from importlib.abc import Traversable

_PATHS_TO_FETCH = [
    "AUTHORS",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "CONTRIBUTORS.md",
    "LICENSE",
    "README.rst",
    "README.md",
    "SECURITY.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/labeler.yml",
    ".github/labels.yml",
    ".github/zizmor.yml",
    ".github/workflows/ci_cd_main.yml",
    ".github/workflows/ci_cd_pr.yml",
    ".github/workflows/ci_cd_release.yml",
    ".pre-commit-config.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "doc/.vale.ini",
    "doc/source/index.rst",
    "doc/source/conf.py",
    "doc/styles/config/vocabularies/ANSYS/accept.txt",
    "doc/styles/config/vocabularies/ANSYS/reject.txt",
]


class MemoryTraversable(Traversable):
    """In-memory Traversable backed by a flat dict mapping path -> content."""

    def __init__(self, files: dict[str, str | None], path: str = "") -> None:
        self._files = files
        self._path = path.strip("/")

    @property
    def name(self) -> str:
        return self._path.split("/")[-1] if self._path else ""

    def is_file(self) -> bool:
        return self._path in self._files and self._files[self._path] is not None

    def is_dir(self) -> bool:
        if not self._path:
            return True
        prefix = self._path + "/"
        return any(key.startswith(prefix) for key in self._files)

    def iterdir(self) -> Iterator["MemoryTraversable"]:
        prefix = (self._path + "/") if self._path else ""
        seen: set[str] = set()
        for key in self._files:
            if not key.startswith(prefix):
                continue
            rest = key[len(prefix) :]
            child_name = rest.split("/")[0]
            if child_name and child_name not in seen:
                seen.add(child_name)
                yield MemoryTraversable(self._files, f"{prefix}{child_name}")

    def joinpath(self, *parts: str) -> "MemoryTraversable":
        combined = "/".join(filter(None, [self._path, *parts]))
        return MemoryTraversable(self._files, combined)

    __truediv__ = joinpath

    def open(self, mode: str = "r", encoding: str = "utf-8", **_) -> StringIO | BytesIO:
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        if "b" in mode:
            return BytesIO(content.encode(encoding))
        return StringIO(content)

    def read_bytes(self) -> bytes:
        return self.open("rb").read()

    def read_text(self, encoding: str = "utf-8") -> str:
        content = self._files.get(self._path)
        if content is None:
            raise FileNotFoundError(self._path)
        return content

    def __repr__(self) -> str:
        return f"MemoryTraversable({self._path!r})"

    def __str__(self) -> str:
        return self._path


def file_exists(root: Traversable, path: str) -> bool:
    try:
        return root.joinpath(path).is_file()
    except Exception:
        return False


def file_content(root: Traversable, path: str) -> str:
    try:
        f = root.joinpath(path)
        if f.is_file():
            return f.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def file_contains(root: Traversable, path: str, pattern: str | re.Pattern) -> bool:
    content = file_content(root, path)
    if not content:
        return False
    if isinstance(pattern, str):
        return pattern in content
    return bool(pattern.search(content))


CANONICAL_WF = {
    "main": ".github/workflows/ci_cd_main.yml",
    "pr": ".github/workflows/ci_cd_pr.yml",
    "release": ".github/workflows/ci_cd_release.yml",
}


def all_workflows_content(root: Traversable) -> str:
    return _merge_all_workflows(root)


def wf_content(root: Traversable, role: str, workflow_map: dict) -> tuple[bool, str]:
    canonical = CANONICAL_WF[role]
    if file_exists(root, canonical):
        return True, file_content(root, canonical)

    entry = workflow_map.get(role)
    if entry and not entry.get("is_fallback"):
        path = entry.get("path", "")
        return False, file_content(root, path) if path else ""
    return False, _merge_all_workflows(root)


def _merge_all_workflows(root: Traversable) -> str:
    try:
        entries = [
            e for e in root.joinpath(".github/workflows").iterdir() if e.name.endswith((".yml", ".yaml"))
        ]
    except Exception:
        return ""
    parts = []
    for entry in entries:
        try:
            c = entry.read_text(encoding="utf-8")
            if c:
                parts.append(c)
        except Exception:
            pass
    return "\n\n".join(parts)


def wf_label(role: str, workflow_map: dict) -> str:
    entry = workflow_map.get(role)
    if not entry:
        return CANONICAL_WF.get(role, role)
    if entry.get("is_fallback"):
        sources = entry.get("sources", [])
        return f"{len(sources)} workflow file(s) ({', '.join(sources)})"
    return entry.get("name", role)


def workflow_map(root: Traversable) -> dict[str, dict]:
    wf_dir = root.joinpath(".github/workflows")
    try:
        entries = [e for e in wf_dir.iterdir() if e.name.endswith((".yml", ".yaml"))]
    except Exception:
        entries = []

    result: dict[str, dict] = {}
    for entry in entries:
        role = _classify_workflow(entry.name)
        if role != "unknown" and role not in result:
            result[role] = {
                "name": entry.name,
                "path": f".github/workflows/{entry.name}",
                "is_fallback": False,
                "sources": [entry.name],
            }

    for role in ("main", "pr", "release"):
        if role not in result and entries:
            result[role] = {
                "name": f"{len(entries)} workflow(s)",
                "path": None,
                "is_fallback": True,
                "sources": [e.name for e in entries],
            }

    return result


def _classify_workflow(name: str) -> str:
    n = name.lower()
    if re.search(r"release|publish|deploy", n):
        return "release"
    if re.search(r"\bpr\b|pull.?request|pull_request", n):
        return "pr"
    if re.search(r"main|push|branch|nightly|schedule|ci_cd_main|ci.main", n):
        return "main"
    if re.search(r"\bci\b|build|test", n):
        return "pr"
    return "unknown"


def readme_path(root: Traversable) -> str | None:
    if file_exists(root, "README.rst"):
        return "README.rst"
    if file_exists(root, "README.md"):
        return "README.md"
    return None


def is_mcp(root: Traversable) -> bool:
    try:
        pyproject_text = root.joinpath("pyproject.toml").read_text()
        return bool(re.search(r"\b(fastmcp|mcp)\b", pyproject_text, re.IGNORECASE))
    except Exception:
        pass
    try:
        return file_exists(root, "src/server.py") or file_exists(root, "server.py")
    except Exception:
        return False


class ProjectMetadata:
    family = "project_metadata"


class PM001(ProjectMetadata):
    "AUTHORS exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "AUTHORS")


class PM002(ProjectMetadata):
    "CHANGELOG.md exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "CHANGELOG.md")


class PM003(ProjectMetadata):
    "CODE_OF_CONDUCT.md exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "CODE_OF_CONDUCT.md")


class PM004(ProjectMetadata):
    "CONTRIBUTING.md exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "CONTRIBUTING.md")


class PM005(ProjectMetadata):
    "CONTRIBUTORS.md exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "CONTRIBUTORS.md")


class PM006(ProjectMetadata):
    "LICENSE exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "LICENSE")


class PM007(ProjectMetadata):
    "README exists (.rst preferred)"

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | str:
        if readme_path is None:
            return False
        if readme_path == "README.md":
            return "⚠️ README.md found — README.rst is the preferred format."
        return True


class PM008(ProjectMetadata):
    "SECURITY.md exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "SECURITY.md")


class PM009(ProjectMetadata):
    ".github/CODEOWNERS exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, ".github/CODEOWNERS")


class PM010(ProjectMetadata):
    "pyproject.toml references README file"

    requires = {"PM007"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", content):
            m = re.search(r"\[tool\.poetry\][\s\S]*?readme\s*=\s*[\"']([^\"']+)[\"']", content, re.M)
            if m:
                return True
            return False
        rm = readme_path or "README.rst"
        if rm in content:
            return True
        if "README" in content:
            return "⚠️ readme key found but exact README filename not confirmed."
        return False


class PM011(ProjectMetadata):
    "pyproject.toml references LICENSE file"

    requires = {"PM006"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "pyproject.toml"):
            return None
        c = file_content(root, "pyproject.toml")
        if re.search(r"poetry\.core|poetry-core", c):
            return bool(re.search(r"\[tool\.poetry\][\s\S]*?license\s*=", c, re.M))
        return bool(
            re.search(r"license-files\s*=", c)
            or re.search(r'license\s*=\s*\{[^}]*file', c)
            or re.search(r'license\s*=\s*["\']LICENSE["\']', c)
        )


class CICDFiles:
    family = "cicd_files"


class CI001(CICDFiles):
    "ci_cd_main.yml exists"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["main"]):
            return True
        lbl = wf_label("main", workflow_map)
        return f"⚠️ Canonical ci_cd_main.yml not found — detected: {lbl}"


class CI002(CICDFiles):
    "ci_cd_pr.yml exists"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["pr"]):
            return True
        lbl = wf_label("pr", workflow_map)
        return f"⚠️ Canonical ci_cd_pr.yml not found — detected: {lbl}"


class CI003(CICDFiles):
    "ci_cd_release.yml exists"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | str:
        if file_exists(root, CANONICAL_WF["release"]):
            return True
        lbl = wf_label("release", workflow_map)
        return f"⚠️ Canonical ci_cd_release.yml not found — detected: {lbl}"


class CICD:
    family = "cicd"


class CI004(CICD):
    "Workflows use concurrency blocks"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("main", "ci_cd_main.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [lbl for role, lbl in present if "concurrency:" not in wf_content(root, role, workflow_map)[1]]
        if not missing:
            return True
        return f"⚠️ concurrency: block missing in: {', '.join(missing)}"


class CI005(CICD):
    "Workflows set root `permissions: {}`"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("release", "ci_cd_release.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [lbl for role, lbl in present if not re.search(r"^permissions:\s*\{\}", wf_content(root, role, workflow_map)[1], re.M)]
        return True if not missing else f"Missing root permissions: {{}} in: {', '.join(missing)}"


class CI006(CICD):
    "checkout uses persist-credentials: false"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | None | str:
        roles = [("pr", "ci_cd_pr.yml"), ("release", "ci_cd_release.yml")]
        present = [(role, lbl) for role, lbl in roles if wf_content(root, role, workflow_map)[1]]
        if not present:
            return None
        missing = [lbl for role, lbl in present if "persist-credentials: false" not in wf_content(root, role, workflow_map)[1]]
        if not missing:
            return True
        return f"⚠️ persist-credentials: false missing in: {', '.join(missing)}"


class CI007(CICD):
    "Labeler job present across workflows"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/[^\s]*label|\blabeler\b", content, re.IGNORECASE))


class CI008(CICD):
    "ansys/actions/check-vulnerabilities used"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return "ansys/actions/check-vulnerabilities" in content


class CI009(CICD):
    "ansys/actions/code-style used"

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        content = all_workflows_content(root)
        if not content:
            return None
        if "ansys/actions/code-style" in content:
            return True
        return "⚠️ ansys/actions/code-style not found in any workflow file."


class CI010(CICD):
    "check-pr-title step present across workflows"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/check-pr-title|check-pr-title", content, re.IGNORECASE))


class CI011(CICD):
    "changelog-fragment step present across workflows"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/[^\s]*changelog|changelog-fragment", content, re.IGNORECASE))


class CI012(CICD):
    "ansys/actions/check-doc-style used"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/check-doc-style|doc-style", content, re.IGNORECASE))


class CI013(CICD):
    "ansys/actions/doc-build used"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/doc-build|\bdoc-build\b", content, re.IGNORECASE))


class CI014(CICD):
    "ansys/actions/build-wheelhouse used"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/build-wheelhouse|build-wheelhouse", content, re.IGNORECASE))


class CI015(CICD):
    "ansys/actions/tests-pytest (or pytest) used"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/tests-pytest|ansys/actions/tests|\btests\b|pytest", content, re.IGNORECASE))


class CI016(CICD):
    "update-changelog step present across workflows"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        content = all_workflows_content(root)
        if not content:
            return None
        return bool(re.search(r"ansys/actions/release-github|update-changelog", content, re.IGNORECASE))


class Dependabot:
    family = "dependabot"


_PATH_DEPENDABOT = ".github/dependabot.yml"


class DB001(Dependabot):
    ".github/dependabot.yml exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, _PATH_DEPENDABOT)


class DB002(Dependabot):
    "dependabot.yml sets version: 2"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(root, _PATH_DEPENDABOT, re.compile(r"^version:\s*2\s*$", re.M))


class DB003(Dependabot):
    "pip or uv ecosystem configured"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        has_pip = file_contains(root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?"))
        has_uv = file_contains(root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?"))
        if has_pip:
            return True
        if has_uv:
            return "⚠️ uv ecosystem configured (pip preferred for PyAnsys standard)."
        return False


class DB004(Dependabot):
    "github-actions ecosystem configured"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        return file_contains(root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?github-actions[\"']?"))


class DB005(Dependabot):
    "Weekly update interval set"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        content = file_content(root, _PATH_DEPENDABOT)
        count = len(re.findall(r"interval:\s*[\"']?weekly[\"']?", content))
        if count >= 2:
            return True
        return f"⚠️ Only {count} ecosystem(s) use weekly interval (expected ≥2)."


class DB006(Dependabot):
    "Cooldown default-days: 7 configured"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r"default-days:\s*7")):
            return True
        return "⚠️ Cooldown default-days: 7 not found in dependabot.yml."


class DB007(Dependabot):
    "pip uses versioning-strategy: lockfile-only"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        has_uv = file_contains(root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?"))
        has_pip = file_contains(root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?"))
        if has_uv and not has_pip:
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r"versioning-strategy:\s*[\"']?lockfile-only[\"']?")):
            return True
        return "⚠️ versioning-strategy: lockfile-only not found for pip ecosystem."


class DB008(Dependabot):
    "pip groups all dependencies together"

    requires = {"DB001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, _PATH_DEPENDABOT):
            return None
        if file_contains(root, _PATH_DEPENDABOT, re.compile(r'patterns:\s*\n\s+- ["\']?\*["\']?')):
            return True
        return '⚠️ pip groups wildcard pattern "- \"*\"" not found in dependabot.yml.'


class Documentation:
    family = "documentation"


class DOC001(Documentation):
    "doc/source/ structure exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "doc/source/index.rst")


class DOC002(Documentation):
    "conf.py exists"

    requires = {"DOC001"}

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "doc/source/conf.py")


class DOC003(Documentation):
    "conf.py includes numpydoc"

    requires = {"DOC002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "numpydoc")


class DOC004(Documentation):
    "conf.py includes sphinx_design"

    requires = {"DOC002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "sphinx_design")


class DOC005(Documentation):
    "conf.py includes intersphinx"

    requires = {"DOC002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "doc/source/conf.py"):
            return None
        return file_contains(root, "doc/source/conf.py", "intersphinx")


class DOC006(Documentation):
    "index.rst has Getting started section"

    requires = {"DOC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(root, "doc/source/index.rst", re.compile(r"getting.started", re.I))


class DOC007(Documentation):
    "index.rst has API reference section"

    requires = {"DOC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return file_contains(root, "doc/source/index.rst", re.compile(r"api.reference|api_reference", re.I))


class README:
    family = "readme"


class RM000(README):
    "README file exists"

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | str:
        if readme_path == "README.rst":
            return True
        if readme_path == "README.md":
            return "⚠️ README.md found — PyAnsys preferred format is README.rst."
        return False


class RM001(README):
    "README has PyAnsys badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(root, readme_path, re.compile(r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys", re.I)):
            return True
        return f"⚠️ PyAnsys badge image not found in {readme_path}."


class RM002(README):
    "README has PyPI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(root, readme_path, re.compile(r"img\.shields\.io[^)\"']*pypi|pypi\.org/project[^)\"']*badge|badge\.fury\.io/py", re.I)):
            return True
        return f"⚠️ PyPI badge image not found in {readme_path}."


class RM003(README):
    "README has Codecov badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(root, readme_path, re.compile(r"codecov\.io[^)\"']*badge|badge\.svg[^)\"']*codecov", re.I)):
            return True
        return f"⚠️ Codecov badge image not found in {readme_path}."


class RM004(README):
    "README has MIT license badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(root, readme_path, re.compile(r"shields\.io[^)\"']*mit|img\.shields\.io[^)\"']*license", re.I)):
            return True
        return f"⚠️ MIT license badge image not found in {readme_path}."


class RM005(README):
    "README has GH-CI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(root, readme_path, re.compile(r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg", re.I)):
            return True
        return f"⚠️ GH-CI workflow badge.svg URL not found in {readme_path}."


class RM006(README):
    "README has Installation section"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"install", re.I))


class RM007(README):
    "README has Documentation section"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"documentation", re.I))


class RM008(README):
    "README has License section"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None:
        if not readme_path:
            return None
        return file_contains(root, readme_path, re.compile(r"license", re.I))


class BuildSystem:
    family = "build_system"


_BACKENDS = {
    "flit_core": "Flit",
    "poetry.core": "Poetry",
    "hatchling": "Hatch",
    "pdm": "PDM",
    "maturin": "Maturin",
    "setuptools": "Setuptools",
}


def _detect_backend(content: str) -> tuple[str, str]:
    m = re.search(r'build-backend\s*=\s*["\']([^"\']+)["\']', content)
    backend = m.group(1) if m else ""
    for pattern, name in _BACKENDS.items():
        if pattern in backend:
            return name, pattern.split(".")[0].replace("_core", "")
    if "[build-system]" in content:
        return "Other", "other"
    return "Unknown", "unknown"


class BS001(BuildSystem):
    "[build-system] table declared"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, "pyproject.toml"):
            return None
        return file_contains(root, "pyproject.toml", "[build-system]")


class BS002(BuildSystem):
    "Uses a supported modern build backend"

    requires = {"BS001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        name, key = _detect_backend(file_content(root, "pyproject.toml"))
        if key == "unknown":
            return False
        if key == "setuptools":
            return f"⚠️ Uses {name} — consider migrating to Flit, Hatch, or Poetry for simpler config."
        return True


class BS003(BuildSystem):
    "No legacy setup.py or setup.cfg"

    @staticmethod
    def check(root: Traversable) -> bool | str:
        has_py = file_exists(root, "setup.py")
        has_cfg = file_exists(root, "setup.cfg")
        if not has_py and not has_cfg:
            return True
        found = [f for f, present in [("setup.py", has_py), ("setup.cfg", has_cfg)] if present]
        return f"⚠️ Legacy file(s) found: {', '.join(found)}. Remove in favour of pyproject.toml."


class BS004(BuildSystem):
    "Build backend version pinned in requires"

    requires = {"BS001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, "pyproject.toml"):
            return None
        content = file_content(root, "pyproject.toml")
        m = re.search(r"requires\s*=\s*\[([^\]]+)\]", content)
        if not m:
            return False
        if re.search(r"[><=!~]", m.group(1)):
            return True
        return "⚠️ Build backend in requires has no version pin (e.g. >=x.y)."


class Security:
    family = "security"


class SEC001(Security):
    ".github/zizmor.yml exists"

    @staticmethod
    def check(root: Traversable) -> bool | str:
        if file_exists(root, ".github/zizmor.yml"):
            return True
        return "⚠️ .github/zizmor.yml not found — optional but recommended."


class SEC002(Security):
    "zizmor.yml has secrets-outside-env rule"

    requires = {"SEC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".github/zizmor.yml"):
            return None
        return file_contains(root, ".github/zizmor.yml", "secrets-outside-env")


class SEC003(Security):
    "gitleaks hook configured"

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "gitleaks")


class SEC004(Security):
    "Workflows pin action SHAs"

    @staticmethod
    def check(root: Traversable, workflow_map: dict) -> bool | None | str:
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        if re.search(r"uses:\s*\S+@[0-9a-f]{40}", content, re.I):
            return True
        return "⚠️ No SHA-pinned actions detected in PR workflow. Use full commit SHAs."


class SEC005(Security):
    "SECURITY.md discourages public issue reporting"

    requires = {"PM008"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, "SECURITY.md"):
            return None
        if file_contains(root, "SECURITY.md", re.compile(r"do not|don't|please don", re.I)):
            return True
        return "⚠️ SECURITY.md may not clearly discourage public issue reporting."


class Labeler:
    family = "labeler"


class LB001(Labeler):
    ".github/labeler.yml exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, ".github/labeler.yml")


class LB002(Labeler):
    ".github/labels.yml exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, ".github/labels.yml")


class LB003(Labeler):
    "labels.yml has 'bug' label"

    requires = {"LB002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "bug")


class LB004(Labeler):
    "labels.yml has 'enhancement' label"

    requires = {"LB002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "enhancement")


class LB005(Labeler):
    "labels.yml has 'documentation' label"

    requires = {"LB002"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".github/labels.yml"):
            return None
        return file_contains(root, ".github/labels.yml", "documentation")


class Vale:
    family = "vale"


_INI = "doc/.vale.ini"


class VL001(Vale):
    "doc/.vale.ini exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, _INI)


class VL002(Vale):
    "Vale uses Google style package"

    requires = {"VL001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, _INI):
            return None
        return file_contains(root, _INI, "Google")


class VL003(Vale):
    "Vale uses ANSYS vocabulary"

    requires = {"VL001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, _INI):
            return None
        return file_contains(root, _INI, "ANSYS")


class VL004(Vale):
    "ANSYS accept.txt vocabulary exists"

    requires = {"VL001"}

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/accept.txt")


class VL005(Vale):
    "ANSYS reject.txt vocabulary exists"

    requires = {"VL001"}

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, "doc/styles/config/vocabularies/ANSYS/reject.txt")


class MCP:
    family = "mcp"


class MCP001(MCP):
    "Core governance files all present"

    @staticmethod
    def check(root: Traversable, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        required = ["LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md", ".github/CODEOWNERS"]
        missing = [p for p in required if not file_exists(root, p)]
        return True if not missing else f"Missing: {', '.join(missing)}"


class MCP002(MCP):
    "CI/CD workflows all present"

    @staticmethod
    def check(root: Traversable, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        workflows = [
            ".github/workflows/ci_cd_main.yml",
            ".github/workflows/ci_cd_pr.yml",
            ".github/workflows/ci_cd_release.yml",
        ]
        missing = [p for p in workflows if not file_exists(root, p)]
        return True if not missing else f"Missing: {', '.join(missing)}"


class MCP003(MCP):
    "tests job wired in PR workflow"

    @staticmethod
    def check(root: Traversable, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return bool(re.search(r"tests|pytest", content, re.I))


class MCP004(MCP):
    "doc-build job present in PR workflow"

    @staticmethod
    def check(root: Traversable, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, content = wf_content(root, "pr", workflow_map)
        if not content:
            return None
        return "doc-build" in content


class MCP005(MCP):
    "README and docs metadata aligned"

    @staticmethod
    def check(root: Traversable, is_mcp: bool, readme_path: str | None) -> bool | None | str:
        if not is_mcp:
            return None
        if not file_exists(root, "pyproject.toml"):
            return None
        if not readme_path:
            return False
        filename = readme_path.split("/")[-1]
        if not file_contains(root, "pyproject.toml", filename):
            return f"pyproject.toml does not reference {filename} as readme."
        if readme_path == "README.md":
            return "⚠️ README.md found — PyAnsys preferred format is README.rst."
        return True


class MCP006(MCP):
    "No TODO/FIXME in doc/source/index.rst"

    @staticmethod
    def check(root: Traversable, is_mcp: bool) -> bool | None:
        if not is_mcp:
            return None
        if not file_exists(root, "doc/source/index.rst"):
            return None
        return not file_contains(root, "doc/source/index.rst", re.compile(r"TODO|FIXME"))


class MCP007(MCP):
    "Security checks not bypassed"

    @staticmethod
    def check(root: Traversable, is_mcp: bool, workflow_map: dict) -> bool | None:
        if not is_mcp:
            return None
        _, pr_content = wf_content(root, "pr", workflow_map)
        _, rel_content = wf_content(root, "release", workflow_map)
        combined = pr_content + rel_content
        if not combined.strip():
            return None
        return not bool(re.search(r"--no-verify|skip.*security|disable.*scan", combined, re.I))


class PreCommit:
    family = "pre_commit"


class PC001(PreCommit):
    ".pre-commit-config.yaml exists"

    @staticmethod
    def check(root: Traversable) -> bool:
        return file_exists(root, ".pre-commit-config.yaml")


class PC002(PreCommit):
    "ruff-pre-commit configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "ruff-pre-commit")


class PC003(PreCommit):
    "zizmor configured with --pedantic"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        has_zizmor = file_contains(root, ".pre-commit-config.yaml", "zizmor")
        has_pedantic = file_contains(root, ".pre-commit-config.yaml", "--pedantic")
        if not has_zizmor:
            return False
        if not has_pedantic:
            return "⚠️ zizmor found but --pedantic flag not set."
        return True


class PC004(PreCommit):
    "blacken-docs configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "blacken-docs")


class PC005(PreCommit):
    "codespell configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "codespell")


class PC006(PreCommit):
    "ansys/pre-commit-hooks configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "ansys/pre-commit-hooks")


class PC007(PreCommit):
    "google/yamlfmt configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "yamlfmt")


class PC008(PreCommit):
    "pyright configured"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        return file_contains(root, ".pre-commit-config.yaml", "pyright")


class PC009(PreCommit):
    "autofix_prs: true enabled"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        if file_contains(root, ".pre-commit-config.yaml", "autofix_prs: true"):
            return True
        return "⚠️ autofix_prs: true not set in ci: block."


class PC010(PreCommit):
    "autoupdate_schedule: weekly"

    requires = {"PC001"}

    @staticmethod
    def check(root: Traversable) -> bool | None | str:
        if not file_exists(root, ".pre-commit-config.yaml"):
            return None
        if file_contains(root, ".pre-commit-config.yaml", re.compile(r"autoupdate_schedule:\s*weekly")):
            return True
        return "⚠️ autoupdate_schedule: weekly not found."


def repo_review_families() -> dict[str, dict]:
    return {
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


def repo_review_checks() -> dict:
    families = [
        ProjectMetadata, CICDFiles, CICD, Dependabot, PreCommit, Documentation, README, BuildSystem,
        Security, Labeler, Vale, MCP,
    ]
    result = {}
    for family in families:
        for cls in family.__subclasses__():
            result[cls.__name__] = cls()
    return result


def _first_doc_line(obj: Any) -> str:
    doc = (obj.check.__doc__ or "").strip()
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    return lines[0] if lines else ""


def _interpret(raw: bool | str | None, check_obj: Any) -> tuple[str, str]:
    if raw is True:
        return "pass", ""
    if raw is None:
        return "na", ""
    if isinstance(raw, str) and raw.startswith("⚠️ "):
        return "warn", raw.removeprefix("⚠️ ")
    if raw is False:
        doc = (check_obj.check.__doc__ or "").strip()
        lines = [line.strip() for line in doc.splitlines() if line.strip()]
        detail = lines[-1] if len(lines) > 1 else (lines[0] if lines else "")
        return "fail", detail
    return "fail", str(raw)


def _run_checks(files: dict[str, str | None], is_mcp_flag: bool) -> dict[str, Any]:
    root = MemoryTraversable(files)
    fixture_values = {
        "root": root,
        "package": root,
        "workflow_map": workflow_map(root),
        "readme_path": readme_path(root),
        "is_mcp": is_mcp_flag or is_mcp(root),
    }

    checks = repo_review_checks()
    families = repo_review_families()
    results = []

    for code, check_obj in checks.items():
        try:
            import inspect

            signature = inspect.signature(check_obj.check)
            kwargs = {key: fixture_values[key] for key in signature.parameters if key in fixture_values}
            raw = check_obj.check(**kwargs)
        except Exception as exc:  # pragma: no cover
            raw = f"⚠️ Check error: {exc}"

        status, detail = _interpret(raw, check_obj)
        results.append(
            {
                "id": code,
                "family": check_obj.family,
                "family_name": families.get(check_obj.family, {}).get("name", check_obj.family),
                "label": type(check_obj).__doc__ or code,
                "description": _first_doc_line(check_obj),
                "status": status,
                "detail": detail,
            }
        )

    tally = {"pass": 0, "fail": 0, "warn": 0, "na": 0}
    for result in results:
        tally[result["status"]] += 1

    scored = tally["pass"] + tally["fail"]
    score = round(tally["pass"] / scored * 100) if scored else 0
    return {
        "results": results,
        "tally": tally,
        "score": score,
        "workflow_map": fixture_values["workflow_map"],
        "project_metadata": {"build_system": {"name": "Unknown", "key": "unknown"}, "license": None, "python_requires": None},
    }


def _load_files(repo_root: Path) -> dict[str, str | None]:
    files: dict[str, str | None] = {}
    for relative_path in _PATHS_TO_FETCH:
        candidate = repo_root / relative_path
        if candidate.is_file():
            files[relative_path] = candidate.read_text(encoding="utf-8", errors="replace")
        else:
            files[relative_path] = None

    workflows = repo_root / ".github" / "workflows"
    if workflows.is_dir():
        for workflow in workflows.glob("*.y*ml"):
            files[workflow.relative_to(repo_root).as_posix()] = workflow.read_text(encoding="utf-8", errors="replace")

    return files


def _style_status(status: str, text: str) -> str:
    colors = {
        "pass": "\033[32m",
        "warn": "\033[33m",
        "fail": "\033[31m",
        "na": "\033[36m",
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    return f"{color}{text}{reset}" if color else text


def _print_report(review: dict[str, Any], *, show_passes: bool = False) -> None:
    results = review["results"]
    tally = review["tally"]
    score = review["score"]

    print("PyAnsys quality report")
    print("=" * 24)
    print(f"Score: {score}%")
    summary = (
        f"Summary: pass={_style_status('pass', str(tally['pass']))} "
        f"fail={_style_status('fail', str(tally['fail']))} "
        f"warn={_style_status('warn', str(tally['warn']))} "
        f"na={_style_status('na', str(tally['na']))}"
    )
    print(summary)

    for item in results:
        if item["status"] == "pass" and not show_passes:
            continue
        detail = item["detail"] or ""
        label = _style_status(item["status"], item["status"].upper())
        print(f"- [{label}] {item['id']} - {item['label']}")
        if detail:
            print(f"  {detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the PyAnsys repository quality report.")
    parser.add_argument("--repo-root", default=".", help="Repository root to review.")
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of a text summary.")
    parser.add_argument("--all", action="store_true", help="Show all checks, including passing ones.")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        raise FileNotFoundError(f"Repo root not found: {repo_root}")

    files = _load_files(repo_root)
    review = _run_checks(files, is_mcp_flag=is_mcp(MemoryTraversable(files)))

    if args.json:
        print(json.dumps(review, indent=2))
        return 1 if review["tally"]["fail"] else 0

    _print_report(review, show_passes=args.all)
    return 1 if review["tally"]["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
