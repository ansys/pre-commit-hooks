``pyansys-quality-report`` setup
================================

The ``pyansys-quality-report`` command runs repository quality checks. Its first
release provides README checks only; additional rule families can be introduced
in later releases.

Setup
-----

Add the hook to ``.pre-commit-config.yaml``:

.. code:: yaml

   - repo: https://github.com/ansys/pre-commit-hooks
     rev: v0.8.0
     hooks:
     - id: pyansys-quality-report
       args: [--repo-root, ., --show-all]

Run it directly from a repository root:

.. code:: bash

   pyansys-quality-report --repo-root .

README rules
------------

- ``RM000``: README.rst exists; README.md is accepted with a warning.
- ``RM001``: README contains a PyAnsys badge.
- ``RM002``: README contains a PyPI badge.
- ``RM003``: README license badge matches ``[project].license`` metadata.
- ``RM004``: README contains a GitHub Actions badge.
- ``RM005``: README has an installation heading.
- ``RM006``: README has a documentation heading.
- ``RM007``: README has a license heading.

Section checks require a heading containing the term, either a Markdown ``#``
heading or an underlined reStructuredText heading. The word elsewhere in the
text, such as in a badge URL, does not count.

``RM003`` reads a string license identifier or the ``text`` or ``file`` form
from ``pyproject.toml``. If project license metadata is not available, the rule
is not applicable.

CLI options
-----------

Passing checks are hidden by default. Use ``--show-all`` to include them. Select
or ignore checks with comma-separated or repeated IDs:

.. code:: bash

   pyansys-quality-report --repo-root . --show-all
   pyansys-quality-report --repo-root . --check RM003
   pyansys-quality-report --repo-root . --ignore RM004,RM005
   pyansys-quality-report --repo-root . --json
   pyansys-quality-report --metadata

Warnings and failures display their actual message once. Warnings do not produce
a non-zero exit code; failures do. The score uses pass and fail results only.
The ``--family`` option accepts ``readme`` in this release. The ``tech-review``
hook remains unchanged.
