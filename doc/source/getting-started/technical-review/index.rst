``tech-review`` setup
=====================

The technical review hook checks the following aspects of your repository:

- The ``.github``, ``doc``, ``src``, and ``tests`` directories exist in the root of the repository.
- The ``AUTHORS``, ``CODE_OF_CONDUCT.md``, ``CONTRIBUTING.md``, ``CONTRIBUTORS.md``, ``LICENSE``,
  ``README.{rst|md}``, and ``.github/dependabot.yml`` files exist.

If any of the files are missing, the hook will fail and add the missing files to the repository
using `jinja templates <https://github.com/ansys/pre-commit-hooks/tree/main/src/ansys/pre_commit_hooks/templates>_`.

If any of the directories are missing, the hook will fail and add the missing directories to the
repository.

To get started, add the hook to your ``.pre-commit-config.yaml`` file:

.. tab-set::

  .. tab-item:: Product libraries

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

  .. tab-item:: Other libraries

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

The default values of the ``tech-review`` hook are as follows:

* ``--author_maint_name=ANSYS, Inc.``
* ``--author_maint_email=pyansys.core@ansys.com``
* ``--license=MIT``
* ``--url=https://github.com/ansys/{repo-name}``, replacing ``repo-name`` with the name of the repository

The ``--author_maint_name`` is the name of the author and maintainer in the ``pyproject.toml`` file.
By default, it is "Ansys, Inc.".

The ``--author_maint_email`` is the email of the author and maintainer in the ``pyproject.toml`` file.
By default, it is "pyansys.core@ansys.com".

The ``--license`` argument is the license that is being used by your repository. By default, it is
MIT.

The ``--url`` argument is automatically rendered based on the repository name. If your repository
is not in the Ansys organization, please add this argument to your configuration in
.pre-commit-config.yaml.

The ``--product`` argument is required if a ``README.rst`` or ``README.md`` file does not
exist in your repository and you want the template to render correctly. The product
for ``PyMechanical`` would be ``mechanical``, for example.

The ``--non_compliant_name`` flag can be used if your repository does not follow the typical
naming convention of ``ansys-*-*``.
