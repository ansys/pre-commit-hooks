import os


def test_template_exists():
    """Test license format file exists."""
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    jinja_file = os.path.join(ROOT_DIR, ".reuse", "templates", "ansys.jinja2")
    assert os.path.exists(jinja_file)
