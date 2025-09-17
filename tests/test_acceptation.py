import importlib


def test_version():
    """Ensure the version attribute is present and correctly formatted."""
    module = importlib.import_module("docmd")

    assert hasattr(module, "__version__")
    assert isinstance(module.__version__, str)
    assert module.__version__ == "0.1.0"  # Replace with the expected version


def test_import_docmd_public_api():
    """Ensure importing docmd works and exposes the public API."""
    module = importlib.import_module("docmd")

    assert hasattr(module, "pdf_to_md")
    assert hasattr(module, "docx_to_md")

    # The functions should be callable
    assert callable(module.pdf_to_md)
    assert callable(module.docx_to_md)
