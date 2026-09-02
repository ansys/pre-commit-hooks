# Copyright (C) 2023 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

"""Rule definitions for the PyAnsys repository quality report."""

from __future__ import annotations

from .build_system import BS001, BS002, BS003, BS004, BuildSystem
from .cicd import CI004, CI005, CI006, CI007, CI008, CI009, CI010, CI011, CI012, CI013, CI014, CI015, CI016, CICD
from .cicd_files import CI001, CI002, CI003, CICDFiles
from .common import (
    CANONICAL_WF,
    _first_doc_line,
    _interpret,
    all_workflows_content,
    file_contains,
    file_content,
    file_exists,
    is_mcp,
    readme_path,
    wf_content,
    wf_label,
    workflow_map,
)
from .dependabot import DB001, DB002, DB003, DB004, DB005, DB006, DB007, DB008, Dependabot
from .documentation import DOC001, DOC002, DOC003, DOC004, DOC005, DOC006, DOC007, Documentation
from .labeler import LB001, LB002, LB003, LB004, LB005, Labeler
from .mcp import MCP001, MCP002, MCP003, MCP004, MCP005, MCP006, MCP007, MCP
from .pre_commit import PC001, PC002, PC003, PC004, PC005, PC006, PC007, PC008, PC009, PC010, PreCommit
from .project_metadata import PM001, PM002, PM003, PM004, PM005, PM006, PM007, PM008, PM009, PM010, PM011, ProjectMetadata
from .readme import RM000, RM001, RM002, RM003, RM004, RM005, RM006, RM007, RM008, README
from .security import SEC001, SEC002, SEC003, SEC004, SEC005, Security
from .vale import VL001, VL002, VL003, VL004, VL005, Vale

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
    "repo_review_families",
    "repo_review_checks",
    "_first_doc_line",
    "_interpret",
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
    ]
    result = {}
    for family in families:
        for cls in family.__subclasses__():
            result[cls.__name__] = cls()
    return result


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
        has_pip = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?")
        )
        has_uv = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?")
        )
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
        return file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?github-actions[\"']?")
        )


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
        has_uv = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?uv[\"']?")
        )
        has_pip = file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"package-ecosystem:\s*[\"']?pip[\"']?")
        )
        if has_uv and not has_pip:
            return None
        if file_contains(
            root, _PATH_DEPENDABOT, re.compile(r"versioning-strategy:\s*[\"']?lockfile-only[\"']?")
        ):
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
        return '⚠️ pip groups wildcard pattern "- "*"" not found in dependabot.yml.'


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
        return file_contains(
            root, "doc/source/index.rst", re.compile(r"api.reference|api_reference", re.I)
        )


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
        if file_contains(
            root,
            readme_path,
            re.compile(
                r"badge\.svg[^)\"']*pyansys|pyansys[^)\"']*badge\.svg|img\.shields\.io[^)\"']*pyansys",
                re.I,
            ),
        ):
            return True
        return f"⚠️ PyAnsys badge image not found in {readme_path}."


class RM002(README):
    "README has PyPI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(
                r"img\.shields\.io[^)\"']*pypi|pypi\.org/project[^)\"']*badge|badge\.fury\.io/py",
                re.I,
            ),
        ):
            return True
        return f"⚠️ PyPI badge image not found in {readme_path}."


class RM003(README):
    "README has Codecov badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"codecov\.io[^)\"']*badge|badge\.svg[^)\"']*codecov", re.I),
        ):
            return True
        return f"⚠️ Codecov badge image not found in {readme_path}."


class RM004(README):
    "README has MIT license badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"shields\.io[^)\"']*mit|img\.shields\.io[^)\"']*license", re.I),
        ):
            return True
        return f"⚠️ MIT license badge image not found in {readme_path}."


class RM005(README):
    "README has GH-CI badge"

    requires = {"RM000"}

    @staticmethod
    def check(root: Traversable, readme_path: str | None) -> bool | None | str:
        if not readme_path:
            return None
        if file_contains(
            root,
            readme_path,
            re.compile(r"github\.com/[^/]+/[^/]+/actions/workflows/[^)\"']+badge\.svg", re.I),
        ):
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
            return (
                f"⚠️ Uses {name} — consider migrating to Flit, Hatch, or Poetry for simpler config."
            )
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
        required = [
            "LICENSE",
            "SECURITY.md",
            "CONTRIBUTING.md",
            "CHANGELOG.md",
            ".github/CODEOWNERS",
        ]
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
        if file_contains(
            root, ".pre-commit-config.yaml", re.compile(r"autoupdate_schedule:\s*weekly")
        ):
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
