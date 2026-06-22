``gh-pin`` setup
================

The ``gh-pin`` hook rewrites every ``uses:`` line in GitHub Actions workflow
files to pin the action to a full 40-character commit SHA.  The original ref
(tag or branch) is preserved as an inline comment for human readability.

Before::

    uses: ansys/actions/code-style@v10.3.2

After::

    uses: ansys/actions/code-style@d946b24b9a765f4169bcc94afdb27bd1a0533741 # v10.3.2

Pinning to a commit SHA prevents a mutable tag from silently pointing to
different code in the future.

To get started, add the hook to your ``.pre-commit-config.yaml`` file:

.. code:: yaml

  - repo: https://github.com/ansys/pre-commit-hooks
    rev: v0.9.0
    hooks:
    - id: gh-pin

The hook runs on any ``*.yml`` and ``*.yaml`` files that are staged for
commit.  Pass individual workflow files or directories to restrict which
files are processed.

Known limitations
-----------------

Internet access required
~~~~~~~~~~~~~~~~~~~~~~~~

The hook resolves each ref to a commit SHA by calling the GitHub commits API
(``https://api.github.com``).  **It will not work on**
`pre-commit.ci <https://pre-commit.ci>`_ because that service blocks all
outbound network traffic.

Run ``gh-pin`` locally or in a CI environment that allows internet access,
such as GitHub Actions.  You can exclude it from ``pre-commit.ci`` by adding
the hook ID to the ``ci.skip`` list:

.. code:: yaml

  ci:
    skip:
    - gh-pin

Anonymous rate limit
~~~~~~~~~~~~~~~~~~~~

The hook uses the unauthenticated GitHub API, which is limited to 60 requests
per hour per IP address.  Each unique ``owner/repo@ref`` combination counts as
one request; results are cached within a single run.  If you hit the rate
limit, wait for the hour window to reset before running the hook again.

Actions with no version ref
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``uses:`` line that has no ``@ref`` at all (for example,
``uses: my-org/my-action``) cannot be pinned automatically.  The hook emits a
warning and leaves the line unchanged.  Add a version tag or SHA manually
before running the hook again.
