import os


def test_template_exists():
    """Test license format file exists."""
    jinja_file = os.path.join(".", ".reuse", "templates", "ansys.jinja2")
    assert os.path.exists(jinja_file)
