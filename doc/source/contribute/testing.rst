.. title:: Testing pre-commit hooks

Testing a pre-commit hook
=========================

Running ``pre-commit`` locally
------------------------------

To ensure a pre-commit hook works as expected, run ``pre-commit`` locally on the repository. First,
install the ``ansys/pre-commit-hooks`` project in a virtual environment:

.. tab-set::

  .. tab-item:: Linux

     .. code:: bash

        python -m venv .venv
        source .venv/bin/activate
        pip install -e .

  .. tab-item:: Windows

     .. code:: batch

        python -m venv .venv
        .venv\Scripts\activate
        pip install -e .

Next, add the pre-commit hook to the repository's ``.pre-commit-config.yaml`` file, copying the
details of the hook from the ``.pre-commit-hooks.yaml`` file. For example, to add the ``new-hook``
hook:

.. code:: yaml

   - repo: local
     hooks:
     - id: "new-hook"
       name: "New Hook"
       description: "A new pre-commit hook for the Ansys Pre-Commit Hooks repository"
       entry: new-hook
       language: python

Run ``pre-commit`` on the repository:

.. code:: bash

   pre-commit run --all-files --verbose

Make sure to test the hook locally on both Linux and Windows operating systems.

Running ``pytest`` tests
------------------------

Create tests using ``pytest`` in the ``tests`` directory to ensure functions in the hook work as
expected. For example, in ``test_new_hook.py``:

.. code:: python

    import pytest
    import ansys.pre_commit_hooks.new_hook as hook

    def test_main():
        """Test the main function of the new-hook."""
        # Assert main passes
        assert hook.main() == 0

See the `pytest documentation <https://docs.pytest.org/en/stable/>`_ for more information on
writing tests.