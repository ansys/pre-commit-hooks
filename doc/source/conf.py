"""Sphinx documentation configuration file."""

from datetime import datetime
import os
from pathlib import Path

from ansys_sphinx_theme import get_autoapi_templates_dir_relative_path, get_version_match
from ansys_sphinx_theme import pyansys_logo_black as logo

# Project information
project = "ansys-pre-commit-hooks"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "ANSYS, Inc."
cname = os.getenv("DOCUMENTATION_CNAME", "pre-commit-hooks.docs.ansys.com")

# Read version from VERSION file in base root directory
source_dir = Path(__file__).parent.resolve().absolute()
version_file = source_dir / "../../src/ansys/pre_commit_hooks/VERSION"
with open(str(version_file), "r") as file:
    __version__ = file.read().splitlines()[0]
release = version = __version__

# Select desired logo, theme, and declare the html title
html_logo = logo
html_theme = "ansys_sphinx_theme"
html_short_title = html_title = "ansys-pre-commit-hooks"

# specify the location of your github repo
html_theme_options = {
    "github_url": "https://github.com/ansys/pre-commit-hooks",
    "show_prev_next": False,
    "show_breadcrumbs": True,
    "additional_breadcrumbs": [
        ("PyAnsys", "https://docs.pyansys.com/"),
    ],
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
}

# Sphinx extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "autoapi.extension",
    "sphinx_autodoc_typehints",
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_design",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    # "numpy": ("https://numpy.org/devdocs", None),
    # "matplotlib": ("https://matplotlib.org/stable", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    # "pyvista": ("https://docs.pyvista.org/", None),
    # "grpc": ("https://grpc.github.io/grpc/python/", None),
}

# numpydoc configuration
numpydoc_show_class_members = False
numpydoc_xref_param_type = True

# Consider enabling numpydoc validation. See:
# https://numpydoc.readthedocs.io/en/latest/validation.html#
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}


# static path
html_static_path = ["_static"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# Configuration for Sphinx autoapi
autoapi_type = "python"
autoapi_dirs = ["../../src/"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_template_dir = get_autoapi_templates_dir_relative_path(Path(__file__))
autoapi_python_use_implicit_namespaces = True
autoapi_keep_files = True
autoapi_own_page_level = "method"
