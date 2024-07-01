{{ doc_repo_name }}
{{ '=' * (doc_repo_name | length) }}
|pyansys| |python| |pypi| |GH-CI| |codecov| |MIT| |black|

.. |pyansys| image:: https://img.shields.io/badge/Py-Ansys-ffc107.svg?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABDklEQVQ4jWNgoDfg5mD8vE7q/3bpVyskbW0sMRUwofHD7Dh5OBkZGBgW7/3W2tZpa2tLQEOyOzeEsfumlK2tbVpaGj4N6jIs1lpsDAwMJ278sveMY2BgCA0NFRISwqkhyQ1q/Nyd3zg4OBgYGNjZ2ePi4rB5loGBhZnhxTLJ/9ulv26Q4uVk1NXV/f///////69du4Zdg78lx//t0v+3S88rFISInD59GqIH2esIJ8G9O2/XVwhjzpw5EAam1xkkBJn/bJX+v1365hxxuCAfH9+3b9/+////48cPuNehNsS7cDEzMTAwMMzb+Q2u4dOnT2vWrMHu9ZtzxP9vl/69RVpCkBlZ3N7enoDXBwEAAA+YYitOilMVAAAAAElFTkSuQmCC
   :target: https://docs.pyansys.com/
   :alt: PyAnsys

.. |python| image:: https://img.shields.io/pypi/pyversions/{{ project_name }}?logo=pypi
   :target: https://pypi.org/project/{{ project_name }}/
   :alt: Python

.. |pypi| image:: https://img.shields.io/pypi/v/{{ project_name }}.svg?logo=python&logoColor=white
   :target: https://pypi.org/project/{{ project_name }}
   :alt: PyPI

.. |codecov| image:: https://codecov.io/gh/ansys/{{ doc_repo_name }}/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/ansys/{{ doc_repo_name }}
   :alt: Codecov

.. |GH-CI| image:: https://github.com/ansys/{{ doc_repo_name }}/actions/workflows/ci_cd.yml/badge.svg
   :target: https://github.com/ansys/{{ doc_repo_name }}/actions/workflows/ci_cd.yml
   :alt: GH-CI

.. |MIT| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: MIT

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=flat
   :target: https://github.com/psf/black
   :alt: Black


Overview
--------

A Python wrapper for Ansys {{ product }}.

.. contribute_start

Installation
^^^^^^^^^^^^

You can use `pip <https://pypi.org/project/pip/>`_ to install {{ doc_repo_name }}.

.. code:: bash

    python -m pip install {{ project_name }}

To install the latest development version, run these commands:

.. code:: bash

    git clone {{ repository_url }}
    cd {{ doc_repo_name }}
    python -m pip install --editable .

For more information, see `Getting Started`_.

Basic usage
^^^^^^^^^^^

This code shows how to import {{ doc_repo_name }} and use some basic capabilities:

.. code:: python

    print("Put sample code here")

For comprehensive usage information, see `Examples`_ in the `{{ doc_repo_name }} documentation`_.

Documentation
^^^^^^^^^^^^^
Documentation for the latest stable release of {{ doc_repo_name }} is hosted at `{{ doc_repo_name }} documentation`_.

- `Getting Started <https://{{ product }}.docs.pyansys.com/version/stable/getting_started/index.html>`_: Information for setting up your system to use {{ doc_repo_name }}
- `Examples <https://{{ product }}.docs.pyansys.com/version/stable/examples.html>`_: Examples using {{ doc_repo_name }}
- `{{ doc_repo_name }} documentation: <https://{{ product }}.docs.pyansys.com/version/stable/index.html>`_: Documentation for {{ doc_repo_name }}

Troubleshooting
^^^^^^^^^^^^^^^

For troubleshooting or reporting issues, please open an issue in the project
repository.

Follow these steps when reporting an issue:

- Go to the project repository
- Click on the `Issues tab <{{ repository_url }}/issues>`_
- Click on the ``New Issue`` button
- Provide a clear and detailed description of the issue you are facing
- Include any relevant error messages, code snippets, or screenshots

Follow these steps when creating a discussion:

- Go to the project repository
- Click on the `Discussions tab <{{ repository_url }}/discussions>`_
or the `Discussions <https://discuss.ansys.com/>`_ page on the Ansys Developer portal
- Click on the ``New Discussion`` button
- Provide a clear and detailed description of the issue you are facing
- Include any relevant error messages, code snippets, or screenshots

To reach the project support team, email `pyansys.core@ansys.com <mailto:pyansys.core@ansys.com>`_.

.. LINKS AND REFERENCES
.. _Getting Started: https://{{ product }}.docs.pyansys.com/version/stable/getting_started/index.html
.. _Examples: https://{{ product }}.docs.pyansys.com/version/stable/examples.html
.. _{{ doc_repo_name }} documentation: https://{{ product }}.docs.pyansys.com/version/stable/index.html