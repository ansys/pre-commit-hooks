``tech-review`` setup
=====================

The ``tech-review`` hook is a compatibility alias for ``pyansys-quality-report``.
Both names run the same rule-based repository report. New configurations should
use ``pyansys-quality-report``; see :doc:`../pyansys-quality-report/index` for
the current rule catalog, CLI options, output format, and ignore settings.

By default, the report only checks the repository and does not create missing
files or directories. To use the legacy scaffolding behavior, pass
``--fix-missing``. Missing baseline files are then generated using
`Jinja templates <https://github.com/ansys/pre-commit-hooks/tree/main/src/ansys/pre_commit_hooks/templates>`_
before the quality checks run. Existing files are not automatically rewritten
to resolve every warning or failure.

To get started, add the hook to your ``.pre-commit-config.yaml`` file:

.. tab-set::

  .. tab-item:: Product repositories

    To enable legacy scaffolding for product libraries such as ``PyMechanical``,
    ``PyMAPDL``, or ``PyAEDT``, supply the product used in generated README content:

     .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.8.0
          hooks:
          - id: tech-review
            args:
            - --fix-missing
            - --product={product}

     For example, for ``PyMechanical`` the ``{product}`` would be ``mechanical``.

  .. tab-item:: Other repositories

    For repositories without product-specific README generation, run the report
    without bootstrap arguments:

     .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.8.0
          hooks:
          - id: tech-review
            args:
                 - --repo-root=.
                 - --show-all

               Use a revision containing the current quality-report implementation.
               To generate missing README content, add ``--fix-missing`` and an explicit
               ``--product`` value, such as ``pre_commit_hooks`` for this repository.

``tech-review`` hook arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
    :header-rows: 1
    :widths: 20 20 60
    :width: 100%

    * - Argument
      - Default value
      - Description
    * - ``--author_maint_name``
      - ``Synopsys, Inc. and ANSYS, Inc.``
      - Author and maintainer name used by legacy bootstrap, not a rule-policy override.
    * - ``--author_maint_email``
      - ``pyansys-core@synopsys.com``
      - Author and maintainer email used by legacy bootstrap.
    * - ``--license``
      - ``Apache-2.0``
      - Expected license for PM028/PM029 and bootstrap. Only ``Apache-2.0`` is supported.
    * - ``--url``
      - ``https://github.com/ansys/{repo-name}``, replacing ``{repo-name}`` with the name of the repository
      - URL of the repository.
    * - ``--product``
      - Empty
      - Product used in generated README content; required when that file must be generated.
    * - ``--fix-missing``
      - ``False``
      - Enable legacy baseline file and directory generation before the report.
    * - ``--show-all``
      - ``False``
      - Include passing checks in the report.
