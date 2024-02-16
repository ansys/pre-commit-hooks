Ansys pre-commit hooks
======================
|pyansys| |python| |pypi| |GH-CI| |MIT| |black| |pre-commit-ci|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/ansys-pre-commit-hooks?logo=pypi
   :target: https://pypi.org/project/ansys-pre-commit-hooks/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/ansys-pre-commit-hooks.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/ansys-pre-commit-hooks
   :alt: PyPI

.. |GH-CI| image:: https://github.com/ansys/pre-commit-hooks/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/pre-commit-hooks/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black

.. |pre-commit-ci| image:: https://results.pre-commit.ci/badge/github/ansys/pre-commit-hooks/main.svg
   :target: https://results.pre-commit.ci/latest/github/ansys/pre-commit-hooks/main
   :alt: pre-commit.ci status

This Ansys repository contains `pre-commit`_ hooks for different purposes.
Currently, these hooks are available:

* ``add-license-headers``: Add missing license headers to files by using
  `REUSE <https://reuse.software/>`_ . To use this hook, you must
  have ``REUSE`` implemented in your repository.

|

``add-license-headers`` setup
-----------------------------

Add required directories
^^^^^^^^^^^^^^^^^^^^^^^^

If you are using the ansys.jinja2 template and MIT.txt license, skip this step. By default, the hook will make symbolic links
from its "assets" directory containing LICENSES/MIT.txt and .reuse/templates/ansys.jinja2
to your repository when the hook runs. The .reuse and LICENSES directories will be deleted once the hook is
done running.

If you are using a custom template, create a directory named ``.reuse``, and if you are using a custom license, create a directory
named ``LICENSES`` in the root of your repository. The custom template cannot be named ``ansys.jinja2``, otherwise it will be removed
after the hook is done running. The custom license cannot be named ``MIT.txt`` for the same reason. The ``.reuse`` and/or ``LICENSES``
directories will have to be committed to your repository and will not be removed once the hook is done running as long as there
are custom templates or licenses in those directories. Your project should have the following layout:

 ::

   project
   ├── LICENCES
   │   └── license_name.txt
   ├── .reuse
   │   └── templates
   │       └── template_name.jinja2
   ├── src
   ├── examples
   ├── tests
   ├── .pre-commit-config.yaml
   ├── pyproject.toml

Where ``license_name`` is the name of the license that is being used, for example, MIT.txt, and
``template_name`` is the name of the custom template being used. The jinja2 file contains the
template for the license headers that are added to the files.

Licenses that are supported by ``REUSE`` can be found in the
`spdx/license-list-data <https://github.com/spdx/license-list-data/tree/main/text>`_ repository.
Please select a license text file from that repository, and copy it to the LICENSES directory.

Set custom arguments
^^^^^^^^^^^^^^^^^^^^

.. code:: yaml

   - repo: https://github.com/ansys/pre-commit-hooks
   rev: v0.2.9
   hooks:
   - id: add-license-headers
     args: ["--custom_copyright", "custom copyright phrase", "--custom_template", "template_name", "--custom_license", "license_name", "--ignore_license_check", "--start_year", "2023"]

``args`` can also be formatted as follows:

.. code:: yaml

   args:
   - --custom_copyright=custom copyright phrase
   - --custom_template=template_name
   - --custom_license=license_name
   - --ignore_license_check
   - --start_year=2023

* ``custom copyright phrase`` is the copyright line you want to include in the license
  header. By default, it uses ``"ANSYS, Inc. and/or its affiliates."``.
* ``template_name`` is the name of the .jinja2 file located in ``.reuse/templates/``.
  By default, it uses ``ansys``.
* ``license_name`` is the name of the license being used. For example, MIT, ECL-1.0, etc.
  To view a list of licenses that are supported by ``REUSE``, see
  https://github.com/spdx/license-list-data/tree/main/text. By default it uses ``MIT``.
* ``ignore_license_check`` is whether or not to check for the license in the header. By default,
  it is ``False``, meaning the files are checked for both the copyright and licensing information
  in the header. Add ``--ignore_license_check`` to ignore checking for licensing information
  in the files.
* ``start_year`` is the start year of the copyright statement. By default, the ``start_year`` is
  the current year, making the copyright statement
  "Copyright (C) 2024 ANSYS, Inc. and/or its affiliates." If you are adding license headers
  to packages released before the current year, add the ``start_year`` argument with the year your
  package was released. For example, if ``start_year`` is 2023, the copyright statement would be
  "Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates." assuming the current year is 2024.

Specify directories to run the hook on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, the hook will run on proto files in any directory, as well as python files within
directories named ``src``, ``examples``, and ``tests``. To specify additional files and/or directories
the hook should run on, add the necessary regex to the ``files`` line in your
.pre-commit-config.yaml file:

.. code:: yaml

   - repo: https://github.com/ansys/pre-commit-hooks
     rev: v0.2.9
     hooks:
     - id: add-license-headers
       files: '(src|examples|tests|newFolder)/.*\.(py|newExtension)|\.(proto|newExtension)'

Ignore specific files or file types
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In .pre-commit-config.yaml:

.. code:: yaml

  - repo: https://github.com/ansys/pre-commit-hooks
    rev: v0.2.9
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
* ``path/to/.*\.(ts|cpp)`` excludes all .ts and .cpp files within the ``path/to`` directory.
* ``(.folder1|folder2)/.*`` excludes directories named .folder1 and folder2.
* ``.*\.js`` excludes all .js files in all directories.
* ``\..*`` excludes all hidden files.


How to install
--------------

The following sections provide instructions for installing the ``ansys-pre-commit-hooks``
package in two installation modes: user and developer.

For users
^^^^^^^^^

Before installing the package, to ensure that you
have the latest version of `pip`_, run this command:

.. code:: bash

    python -m pip install -U pip

Then, to install the package, run this command:

.. code:: bash

    python -m pip install ansys-pre-commit-hooks

For developers
^^^^^^^^^^^^^^

Installing the package in developer mode allows you to modify and
enhance the source code.

Before contributing to the project, ensure that you are familiar with
the `PyAnsys Developer's Guide`_.

For a developer installation, you must follow these steps:

#. Clone the repository with this command:

   .. code:: bash

      git clone https://github.com/ansys/pre-commit-hooks

#. Create a fresh-clean Python environment and activate it with these commands:

   .. code:: bash

      # Create a virtual environment
      python -m venv .venv

      # Activate it in a POSIX system
      source .venv/bin/activate

      # Activate it in Windows CMD environment
      .venv\Scripts\activate.bat

      # Activate it in Windows Powershell
      .venv\Scripts\Activate.ps1

#. Ensure that you have the latest required build system tools by
   running this command:

   .. code:: bash

      python -m pip install -U pip flit tox twine


#. Install the project in editable mode by running one of these commands:

   .. code:: bash

      # Install the minimum requirements
      python -m pip install -e .

      # Install the minimum + tests requirements
      python -m pip install -e .[tests]

      # Install the minimum + doc requirements
      python -m pip install -e .[doc]

      # Install all requirements
      python -m pip install -e .[tests,doc]

#. Verify your development installation by running this command:

   .. code:: bash

      tox


How to test it
--------------

This project takes advantage of `tox`_. This tool automates common
development tasks (similar to Makefile), but it is oriented towards
Python development.

Using ``tox``
^^^^^^^^^^^^^

While Makefile has rules, ``tox`` has environments. In fact, ``tox`` creates its
own virtual environment so that anything being tested is isolated from the project
to guarantee the project's integrity.

These environment commands are provided:

- **tox -e style**: Checks for coding style quality.
- **tox -e py**: Checks for unit tests.
- **tox -e py-coverage**: Checks for unit testing and code coverage.
- **tox -e doc**: Checks for successfully building the documentation.


Raw testing
^^^^^^^^^^^

If required, you can always call style commands, such as `black`_, `isort`_,
and `flake8`_, or unit testing commands, such as `pytest`_, from the command line.
However, calling these commands does not guarantee that your project is
being tested in an isolated environment, which is the reason why tools like
``tox`` exist.


A note on ``pre-commit``
^^^^^^^^^^^^^^^^^^^^^^^^

The style checks take advantage of `pre-commit`_. Developers are not forced but
encouraged to install this tool by running this command:

.. code:: bash

    python -m pip install pre-commit && pre-commit install


Documentation
-------------

For building documentation, you can run the usual rules provided in the
`Sphinx`_ Makefile with a command that is formatted like this:

.. code:: bash

    make -C doc/ html && your_browser_name doc/html/index.html

However, the recommended way of checking documentation integrity is by
running ``tox`` with a command that is formatted like this:

.. code:: bash

    tox -e doc && your_browser_name .tox/doc_out/index.html


Distributing
------------

If you would like to create either source or wheel files, install
the building requirements and then execute the build module with these commands:

.. code:: bash

    python -m pip install .
    python -m build
    python -m twine check dist/*


.. LINKS AND REFERENCES
.. _black: https://github.com/psf/black
.. _flake8: https://flake8.pycqa.org/en/latest/
.. _isort: https://github.com/PyCQA/isort
.. _pip: https://pypi.org/project/pip/
.. _pre-commit: https://pre-commit.com/
.. _PyAnsys Developer's Guide: https://dev.docs.pyansys.com/
.. _pytest: https://docs.pytest.org/en/stable/
.. _Sphinx: https://www.sphinx-doc.org/en/master/
.. _tox: https://tox.wiki/
