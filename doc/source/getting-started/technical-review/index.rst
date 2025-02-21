``tech-review`` setup
=====================

The ``tech-review`` hook performs a brief technical review on repositories based on Ansys'
`technical review checklist <https://dev.docs.pyansys.com/getting-started/administration.html#technical>`_.

The hook checks the following aspects of your repository:

- The ``.github``, ``doc``, ``src``, and ``tests`` directories exist in the root of the repository.
- The ``AUTHORS``, ``CODE_OF_CONDUCT.md``, ``CONTRIBUTING.md``, ``CONTRIBUTORS.md``, ``LICENSE``,
  ``README.{rst|md}``, and ``.github/dependabot.yml`` files exist.

If any of the files are missing, the hook fails and add the missing files to the repository
using `jinja templates <https://github.com/ansys/pre-commit-hooks/tree/main/src/ansys/pre_commit_hooks/templates>`_.

If any of the directories are missing, the hook fails and add the missing directories to the
repository.

To get started, add the hook to your ``.pre-commit-config.yaml`` file:

.. tab-set::

  .. tab-item:: Product repositories

     The following configuration is required for product libraries, such as ``PyMechanical``,
     ``PyMAPDL``, or ``PyAEDT``, where ``{product}`` is the name of the product:

     .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.1
          hooks:
          - id: tech-review
            args:
            - --product={product}

     For example, for ``PyMechanical`` the ``{product}`` would be ``mechanical``.

  .. tab-item:: Other repositories

     The following configuration is required for libraries that do not fall under the product
     category, such as ``ansys-pre-commit-hooks``, ``ansys-sphinx-theme``, or ``ansys-actions``:

     .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.1
          hooks:
          - id: tech-review
            args:
            - --product={product}
            - --non_compliant_name

     Where ``{product}`` is the ``name`` variable under ``[tool.flit.module]`` in the
     ``pyproject.toml`` file. For example, for ``ansys-pre-commit-hooks`` the ``{product}`` is
     ``pre_commit_hooks``.

     The ``--non_compliant_name`` flag is used if the repository does not follow the typical naming
     convention of ``ansys-*-*``.

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
      - ``ANSYS, Inc.``
      - The name of the author and maintainer in the ``pyproject.toml`` file.
    * - ``--author_maint_email``
      - ``pyansys.core@ansys.com``
      - The email of the author and maintainer in the ``pyproject.toml`` file.
    * - ``--license``
      - ``MIT``
      - The license that is being used by your repository.
    * - ``--url``
      - ``https://github.com/ansys/{repo-name}``, replacing ``{repo-name}`` with the name of the repository
      - The URL of the repository.
    * - ``--product``
      - The name of the repository's product. For example, ``mechanical`` for ``PyMechanical``.
      - The product for the repository.
    * - ``--non_compliant_name``
      - N/A
      - Flag to use if the repository does not follow the typical naming convention of ``ansys-*-*``.
