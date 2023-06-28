from ansys.pre_commit_hooks.library import __version__


def test_pkg_version():
    assert __version__ == "0.1.dev0"
