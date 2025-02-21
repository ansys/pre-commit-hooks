Known issues and limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. dropdown:: After running the hook, I am seeing a "Skipped unrecognised file" message
    :animate: fade-in-slide-down

    The hook will skip files that are not recognized by `REUSE <https://reuse.software/>`_.
    If you see this message, the file type is not supported by the hook. See the
    `EXTENSION_COMMENT_STYLE_MAP <https://github.com/fsfe/reuse-tool/blob/v5.0.2/src/reuse/comment.py>`_
    in the `reuse-tool <https://github.com/fsfe/reuse-tool/tree/v5.0.2>`_ repository for a list of
    supported file types.

    If you would like to add support for the unrecognized file type, please open an
    `issue <https://github.com/ansys/pre-commit-hooks/issues>`_ in the ``ansys/pre-commit-hooks``
    repository.
