"""Installation file for ansys-pre-commit-hooks."""

import os
import sys

from setuptools import find_namespace_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install

SCRIPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "ansys")

sys.path.append(os.path.dirname(SCRIPT_DIR))

from ansys.pre_commit_hooks.tech_review import JSON_URL, LICENSES_JSON, download_license_json


class CustomInstallCommand(install):
    """Custom install command to download the license json file."""

    def run(self):
        """Download the license json file."""
        install.run(self)
        download_license_json(JSON_URL, LICENSES_JSON)


class CustomDevelopCommand(develop):
    """Custom develop command to download the license json file."""

    def run(self):
        """Download the license json file."""
        develop.run(self)
        download_license_json(JSON_URL, LICENSES_JSON)


HERE = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(HERE, "src", "ansys", "pre_commit_hooks", "VERSION"), encoding="utf-8") as f:
    version = f.read().strip()

# Get the long description from the README file
with open(os.path.join(HERE, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

description = "A Python wrapper to create Ansys-tailored pre-commit hooks"

setup(
    name="ansys-pre-commit-hooks",
    packages=find_namespace_packages(where="src", include="ansys*"),
    package_dir={"": "src"},
    version=version,
    description=description,
    long_description=long_description,
    license="MIT",
    author="ANSYS, Inc.",
    author_email="pyansys.core@ansys.com",
    maintainer="ANSYS, Inc.",
    maintainer_email="pyansys.core@ansys.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    url="https://github.com/ansys/pre-commit-hooks",
    python_requires=">=3.9,<4",
    install_requires=[
        "GitPython==3.1.44",
        "importlib-metadata==8.5.0",
        "Jinja2==3.1.5",
        "reuse==5.0.2",
        "requests==2.32.3",
        "semver==3.0.2",
        "toml==0.10.2",
    ],
    extras_require={
        "doc": [
            "ansys-sphinx-theme[autoapi]==1.2.4",
            "numpydoc==1.8.0",
            "sphinx==8.1.3",
            "sphinx-autodoc-typehints==3.0.0",
            "sphinx-copybutton==0.5.1",
        ],
        "tests": [
            "pytest==8.3.4",
            "pytest-cov==6.0.0",
        ],
    },
    project_urls={
        "Source": "https://github.com/ansys/pre-commit-hooks/",
        "Tracker": "https://github.com/ansys/pre-commit-hooks/issues",
        "Homepage": "https://github.com/ansys/pre-commit-hooks",
        "Documentation": "https://pre-commit-hooks.docs.pyansys.com",
    },
    include_package_data=True,
    cmdclass={
        "develop": CustomDevelopCommand,
        "install": CustomInstallCommand,
    },
    entry_points={
        "console_scripts": [
            "add-license-headers=ansys.pre_commit_hooks.add_license_headers:main",
            "tech-review=ansys.pre_commit_hooks.tech_review:main",
        ],
    },
)
