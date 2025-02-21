.. title:: Creating pre-commit hooks

Creating a pre-commit hook
==========================

1. Create a Python file in the `src/ansys/pre_commit_hooks <https://github.com/ansys/pre-commit-hooks/tree/main/src/ansys/pre_commit_hooks>`_
   directory. For example, ``new_hook.py``, with a main function:

   .. code:: python

      def main():
          print("New hook!")
          return 0

      if __name__ == "__main__":
          main()

   .. note::

      The ``main`` function of the hook must return a non-zero exit code if the hook fails. For the
      hooks in the Ansys Pre-Commit Hooks repository, the exit code is set to 1 if the hook fails
      and 0 if the hook passes.

2. Create a Python file to test the hook in the `tests <https://github.com/ansys/pre-commit-hooks/tree/main/tests>`_
   directory. For example, ``test_new_hook.py``.

3. Add the hook to the ``.pre-commit-hooks.yaml`` file:

   .. code:: yaml

      - id: "new-hook"
        name: "New Hook"
        description: "A new pre-commit hook for the Ansys Pre-Commit Hooks repository"
        entry: new-hook
        language: python

   Additional information about the hook can be added to the ``.pre-commit-hooks.yaml`` file, such as the
   ``files``, ``requires-serial``, or ``pass_filenames`` fields. See the
   `pre-commit documentation <https://pre-commit.com/#creating-new-hooks>`_ for more information
   on the available fields.

4. Add the hook to the ``entry_points`` dictionary in the ``setup.py`` file:

   .. code:: python

      entry_points = {
          "console_scripts": [
              "new-hook = ansys.pre_commit_hooks.new_hook:main",
          ],
      },

5. After adding code to the pre-commit hook file, for example, ``new_hook.py``, add the hook's
   required dependencies to the ``pyproject.toml`` and ``setup.py`` files if they are not already
   there:

   In the ``pyproject.toml`` file, add the dependency in the ``requires`` list under the
   ``[build-system]`` section, pinning the dependency to a specific version:

   .. code:: toml

      [build-system]
      requires = [
          "setuptools>=42.0",
          "GitPython==3.1.44",
      ]

   In the ``setup.py`` file, add the dependency to the ``install_requires`` list, pinning
   the dependency to a specific version:

   .. code:: python

       install_requires = [
           "GitPython==3.1.44",
           "importlib-metadata==8.6.1",
       ]