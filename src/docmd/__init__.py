from importlib.metadata import version

from docmd.core import Converter

__version__ = version("docmd")
__all__ = ["Converter"]


def _lint():
    """Helper dev function to lint, format and type-check the codebase."""
    import subprocess

    subprocess.run(["ruff", "check", "src", "tests", "--fix"])
    subprocess.run(["ruff", "format", "src", "tests"])
    subprocess.run(["ty", "check", "src", "tests"])
