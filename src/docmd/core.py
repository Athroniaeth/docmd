import io
from typing import Dict

import fitz
from markitdown import MarkItDown
from mdformat import text
from pymupdf4llm import to_markdown

type StrategyReplace = Dict[str, str]
"""Dict representing a replacement strategy where keys are substrings to be replaced and values are their replacements."""

DEFAULT_STRATEGY_REPLACE: StrategyReplace = {
    "\n\n\n": "\n\n",
    "      - ": "- ",
    "xxxxxxx": "xxx",
    "- -": "-",
}


def _recursively_replace(string: str, substring: str, replace: str = "") -> str:
    """Recursively replaces all occurrences of a substring in a string."""
    while substring in string:
        string = string.replace(substring, replace)
    return string


def apply_strategy_replace(string: str, strategy: StrategyReplace) -> str:
    """Applies a replacement strategy to a string."""
    for k, v in strategy.items():
        string = _recursively_replace(string, k, v)
    return string


def _format_md(md: str, strategy=None) -> str:
    """Internal function to format markdown text using a replacement strategy."""
    if strategy is None:
        strategy = DEFAULT_STRATEGY_REPLACE

    md = text(md)
    md = apply_strategy_replace(md, strategy)
    return md


def pdf_to_md(stream: bytes) -> str:
    """Converts a PDF byte stream to formatted markdown text."""
    if isinstance(stream, bytes):
        stream = io.BytesIO(stream)

    with fitz.open(stream=stream, filetype="pdf") as doc:
        md = to_markdown(doc, ignore_graphics=True, ignore_code=True, ignore_alpha=True, )
        return _format_md(md)


def docx_to_md(stream: bytes) -> str:
    """Converts a DOCX byte stream to formatted markdown text."""
    mid = MarkItDown()
    md = mid.convert_stream(io.BytesIO(stream), file_extension=".docx").markdown
    md = md.replace("![](data:image/png;base64...)", "")
    md = md.replace("(data:image/png;base64...)", "()")
    md = md.replace("![](data:image/jpeg;base64...)", "")
    return _format_md(md)
