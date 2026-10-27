``pyansys-quality-report`` setup
================================

The ``pyansys-quality-report`` command runs README and project metadata quality
checks.

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

README rules
------------

The README rules are formatted as ``RMXXX``. Each rule is documented in the
:doc:`API reference </api/src/ansys/pre_commit_hooks/quality_rules/readme/index>`,
including what it checks and whether an unmet rule produces a ``WARNING`` or an
``ERROR``. Use the rule IDs with the ``--check`` and ``--ignore`` options.

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
The ``--family`` option accepts ``readme`` and ``project_metadata``. Both families
run by default. The ``tech-review`` hook remains unchanged.

Project metadata rules
----------------------

The project metadata rules use ``PMXXX`` IDs. In addition to repository layout,
governance, and licensing checks, they validate:

* ``PM002``: ``CHANGELOG.md`` exists, or ``doc/source/changelog.rst`` has an RST
  title with a matching underline and non-placeholder content.
* ``PM009``: README file references in ``[project].readme`` exist inside the
  repository. String and file-table declarations are supported, as are
  setuptools dynamic README file references. Inline README text needs no file.
* ``PM016``: ``requires-python`` is parsed with
  ``packaging.specifiers.SpecifierSet`` and contains an explicit lower
  (``>`` or ``>=``) and upper (``<`` or ``<=``) comparator. The existing
  ``setup.py`` fallback is retained.
* ``PM020``: Issues, Discussions, and Documentation HTTP(S) URLs belong to
  ``[project.urls]``. Quoted and unquoted TOML keys are accepted; matching text
  in other tables or comments does not count.
* ``PM023``: Python minor-version classifiers are declared in
  ``[project].classifiers`` and each series has at least one stable patch
  release allowed by ``requires-python``. This does not require classifiers
  for every version the specifier could allow. Dynamic classifiers that cannot
  be checked statically produce a warning.

Malformed TOML and invalid or unverifiable declarations produce explicit
warnings. These content checks warn rather than fail the hook; missing
changelog files and a missing README declaration remain errors.
