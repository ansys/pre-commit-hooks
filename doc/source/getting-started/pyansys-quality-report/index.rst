``pyansys-quality-report`` setup
================================

The ``pyansys-quality-report`` command runs repository quality checks.

Setup
-----

Add the hook to ``.pre-commit-config.yaml``:

.. code:: yaml

   - repo: https://github.com/ansys/pre-commit-hooks
     rev: v0.8.0
     hooks:
     - id: pyansys-quality-report
       args: [--show-all]
       verbose: true

Run the hook on the whole repository with ``pre-commit`` or ``prek``:

.. code:: bash

   pre-commit run pyansys-quality-report --all-files
   prek run pyansys-quality-report --all-files

The ``verbose: true`` option makes pre-commit print the report even when the hook
passes. Without it, output from a passing hook, including ``--show-all`` results,
is hidden.

The project root is the nearest directory, starting from the current one and moving
up, that contains a ``pyproject.toml``. If none does, the current directory is used.

Rules
-----

Checks are grouped into rule families, and each rule has a unique ID.
Use ``--metadata`` to list the available rules and their descriptions.
Select individual rules with ``--check``, exclude them with ``--ignore``,
or select a family with ``--family``. All registered families run by default.
Use ``--help`` to see the available command options.

CLI options
-----------

Passing checks are hidden by default. Use ``--show-all`` to include them. Select
or ignore checks with comma-separated or repeated IDs:

.. code:: bash

   pyansys-quality-report --show-all
   pyansys-quality-report --check RM003
   pyansys-quality-report --ignore RM004,RM005
   pyansys-quality-report --color always
   pyansys-quality-report --json
   pyansys-quality-report --metadata

Every rule reports one of three statuses: ``PASSED``, ``WARNING``, or ``ERROR``.
The text report colors these statuses green, yellow, and red by default,
including captured pre-commit and CI output. Use ``--color never`` for plain
text or ``--color auto`` to enable colors only for interactive terminals. In
automatic mode, ``NO_COLOR`` disables color and a nonzero ``FORCE_COLOR`` value
enables it.
Warnings and errors display their actual message once. Warnings do not produce
a non-zero exit code; errors do. The score uses passed and error results only.
The ``tech-review`` hook remains unchanged.
