from importlib.metadata import version

from docmd.core import pdf_to_md, docx_to_md

__version__ = version("docmd")
__all__ = ["pdf_to_md", "docx_to_md"]
