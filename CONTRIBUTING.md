# Contribute

Overall guidance on contributing to a PyAnsys library appears in the
[Contributing] topic in the *PyAnsys developer's guide*. Ensure that you
are thoroughly familiar with this guide before attempting to contribute to
Ansys Pre-Commit Hooks.

The following contribution information is specific to Ansys Pre-Commit Hooks.

[Contributing]: https://dev.docs.pyansys.com/how-to/contributing.html

Code style checks run with `pre-commit run --all-files`. Ruff replaces Black,
isort, Flake8, and pydocstyle for formatting, import sorting, and linting.
Its configuration in `pyproject.toml` preserves the 100-character line length,
import sorting within sections, and PEP 257 docstring convention.

Run `ruff check --fix .` followed by `ruff format .` to apply fixes manually.
The lint rules retain the previous unused-import, star-import, and line-length
checks; the formatter handles whitespace and indentation checks. Docstring
checks remain disabled in `tests/`, while the previous Flake8 exclusions for
`__init__.py` remain limited to the corresponding lint rules.
