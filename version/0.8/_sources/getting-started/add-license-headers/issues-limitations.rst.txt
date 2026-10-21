Known issues and limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. dropdown:: After running the hook, I am seeing a "Skipped unrecognized file" message
    :animate: fade-in-slide-down

    The hook skips files that are not recognized by `REUSE <https://reuse.software/>`_.
    If you see this message, the file type is not supported by the hook.  For a list of
    supported file types, see the
    `EXTENSION_COMMENT_STYLE_MAP <https://github.com/fsfe/reuse-tool/blob/v5.0.2/src/reuse/comment.py>`_
    in the `reuse-tool <https://github.com/fsfe/reuse-tool/tree/v5.0.2>`_ repository.

    To request support for an unrecognized file type, open an
    `issue <https://github.com/ansys/pre-commit-hooks/issues>`_ in the ``ansys/pre-commit-hooks``
    repository.

.. dropdown:: I am getting a "OSError: [WinError 1314] A required privilege is not held by the client" error when running the hook on Windows
    :animate: fade-in-slide-down

    This issue is fixed in version 0.7.1 and later. If you are using an older version of the hook
    and do not want to upgrade, you can fix this issue by enabling Developer Mode on Windows. To
    enable Developer Mode, see Microsoft's `Settings for developers <https://learn.microsoft.com/en-us/windows/advanced-settings/developer-mode>`_
    documentation.