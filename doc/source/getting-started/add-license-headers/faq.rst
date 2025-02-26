Frequently asked questions
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. dropdown:: How do you specify additional directories and files to run the hook on?
    :animate: fade-in-slide-down

    To specify additional files and/or directories the hook should run on, add the necessary regex
    to the ``files`` line in your ``.pre-commit-config.yaml`` file:

    .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.2
          hooks:
          - id: add-license-headers
            files: '(src|examples|tests|doc)/.*\.(py|rst)|\.(proto|cpp)'

    This would run the hook on Python and ReStructuredText (RST) files in the ``src``,
    ``examples``, ``tests``, and ``doc`` directories, as well as PROTO and CPP files
    in any directory.

    .. note::

        The default regex for the ``files`` field is ``'(src|examples|tests)/.*\.(py)|\.(proto)'``.
        Add onto this regex to specify additional files and directories to ensure that the hook
        runs on Python files in the ``src``, ``examples``, and ``tests`` directories, as well as
        PROTO files in any directory at the minimum.

.. dropdown:: How do you ignore specific files or file types?
   :animate: fade-in-slide-down

   To ignore specific files or file types, add the ``exclude`` argument to the hook in your
   ``.pre-commit-config.yaml`` file:

   .. code:: yaml

      - repo: https://github.com/ansys/pre-commit-hooks
        rev: v0.5.2
        hooks:
        - id: add-license-headers
          exclude: |
              (?x)^(
                  path/to/file1.py |
                  path/to/.*\.(ts|cpp) |
                  (.folder1|folder2)/.* |
                  .*\.js |
                  \..* |
              )$

   * ``path/to/file1.py`` excludes the stated file.
   * ``path/to/.*\.(ts|cpp)`` excludes all TS and CPP files within the ``path/to`` directory.
   * ``(.folder1|folder2)/.*`` excludes directories named ``.folder1`` and ``folder2``.
   * ``.*\.js`` excludes all JS files in all directories.
   * ``\..*`` excludes all hidden files.

.. dropdown:: How do you change the copyright phrase from "ANSYS, Inc. and/or its affiliates."?
    :animate: fade-in-slide-down

    To change the copyright phrase in the copyright line, add the ``--custom_copyright`` argument
    to the hook in your ``.pre-commit-config.yaml`` file:

    .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.2
          hooks:
          - id: add-license-headers
            args:
            - --custom_copyright="custom copyright phrase"

    This would change the copyright line to ``Copyright (C) 2025 custom copyright phrase.``

.. dropdown:: How do you ignore checking for licensing information in the files?
    :animate: fade-in-slide-down

    To ignore checking for the MIT license in the files, add the ``--ignore_license_check``
    argument to the hook in your ``.pre-commit-config.yaml`` file:

    .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.2
          hooks:
          - id: add-license-headers
            args:
            - --ignore_license_check

.. dropdown:: How do you use a custom template?
    :animate: fade-in-slide-down

    To use a custom template, create the ``.reuse/templates/`` directory in the root of your
    repository and add the Jinja template to that directory. The custom template cannot be named
    ``ansys.jinja2``. Otherwise, it would be removed after the hook is done running.

    ::

      project
      ├── .reuse
      │   └── templates
      │       └── template_name.jinja2
      ├── src
      ├── examples
      ├── tests
      ├── .pre-commit-config.yaml
      ├── pyproject.toml

    Add the ``--custom_template`` argument to the hook in your ``.pre-commit-config.yaml`` file:

    .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.2
          hooks:
          - id: add-license-headers
            args:
            - --custom_template=template_name

.. dropdown:: How do you use a custom license?
    :animate: fade-in-slide-down

    To use a custom license, create the ``LICENSES`` directory in the root of your
    repository and add the license to that directory. The custom license cannot be named
    ``MIT.txt``. Otherwise, it would be removed after the hook is done running.

    ::

      project
      ├── LICENCES
      │   └── license_name.txt
      ├── src
      ├── examples
      ├── tests
      ├── .pre-commit-config.yaml
      ├── pyproject.toml

    To use a custom license, add the ``--custom_license`` argument to the hook in your
    ``.pre-commit-config.yaml`` file:

    .. code:: yaml

        - repo: https://github.com/ansys/pre-commit-hooks
          rev: v0.5.2
          hooks:
          - id: add-license-headers
            args:
            - --custom_license=license_name

    Licenses supported by ``REUSE`` can be found in the
    `spdx/license-list-data <https://github.com/spdx/license-list-data/tree/main/text>`_ repository.
    Select a license text file from that repository and copy it to the ``LICENSES`` directory.

.. dropdown:: What should the start year be if my repository was created before the current year?
    :animate: fade-in-slide-down

    If you are adding license headers to repositories that were started prior to the current year,
    add the ``--start_year`` argument with the year that your first file was committed. For
    example, if ``start_year`` is 2023 and the current year is 2025, the copyright statement would
    be:

    ``Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.``