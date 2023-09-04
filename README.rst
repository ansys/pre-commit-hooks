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

  #. Copy the .reuse directory from this repository into your repository.
  #. Ensure your repository has the "src" directory.

     .. note::

        If the ``src`` directory does not exist, specify which directory should
        be checked for files missing license headers. To do so, add the args line
        to ``.pre-commit-config.yaml`` in your repository:

        .. code:: yaml

           - repo: https://github.com/ansys/pre-commit-hooks
             rev: v0.1.1
             hooks:
             - id: add-license-headers
                 args:
                 - --loc=mydir

        Where ``mydir`` is a directory containing files that are checked for license headers.

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
