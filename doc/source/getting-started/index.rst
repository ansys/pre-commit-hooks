.. title:: Getting Started

Getting started
===============

Learn how to set up the available pre-commit hooks:

.. grid:: 3

    .. grid-item-card:: Add license headers :octicon:`note`
        :padding: 2 2 2 2
        :link: add-license-headers/index
        :link-type: doc

        A hook that adds and updates license headers in specified directories and file types
        using the ``REUSE`` repository.

        :bdg-primary-line:`Set-up`

    .. grid-item-card:: Technical review :octicon:`checklist`
        :padding: 2 2 2 2
        :link: technical-review/index
        :link-type: doc

        A hook that performs a brief technical review on repositories based on the
        Ansys repository requirements.

        :bdg-primary-line:`Set-up`

    .. grid-item-card:: Pin GitHub Actions :octicon:`pin`
        :padding: 2 2 2 2
        :link: gh-pin/index
        :link-type: doc

        A hook that pins every ``uses:`` line in GitHub Actions workflow files
        to a full commit SHA for supply-chain security.

        :bdg-primary-line:`Set-up`

.. toctree::
   :hidden:
   :maxdepth: 3

   add-license-headers/index
   technical-review/index
   gh-pin/index
