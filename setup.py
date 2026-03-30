"""Installation file for ansys-pre-commit-hooks."""

import os

from setuptools import find_namespace_packages, setup

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
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    url="https://github.com/ansys/pre-commit-hooks",
    python_requires=">=3.10,<4",
    install_requires=[
        "GitPython==3.1.46",
        "importlib-metadata==8.7.1",
        "Jinja2==3.1.6",
        "reuse==6.2.0",
        "requests==2.32.5",
        "semver==3.0.4",
        "toml==0.10.2",
    ],
    extras_require={
        "doc": [
            "ansys-sphinx-theme[autoapi]==1.7.2",
            "numpydoc==1.10.0",
            "sphinx==8.2.3",
            "sphinx-autodoc-typehints==3.1.0",
            "sphinx-copybutton==0.5.1",
            "sphinx_design==0.6.1",
        ],
        "tests": [
            "pytest==9.0.2",
            "pytest-cov==7.1.0",
        ],
    },
    project_urls={
        "Source": "https://github.com/ansys/pre-commit-hooks/",
        "Issues": "https://github.com/ansys/pre-commit-hooks/issues",
        "Discussions": "https://github.com/ansys/pre-commit-hooks/discussions",
        "Documentation": "https://pre-commit-hooks.docs.pyansys.com",
        "Releases": "https://github.com/ansys/pre-commit-hooks/releases",
        "Changelog": "https://github.com/ansys/pre-commit-hooks/blob/main/doc/source/changelog.rst",
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "add-license-headers=ansys.pre_commit_hooks.add_license_headers:main",
            "tech-review=ansys.pre_commit_hooks.tech_review:main",
        ],
    },
)
