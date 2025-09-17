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
    "xxxxxxx": "xxx",
    "- -": "-",
}


def _recursively_replace(string: str, substring: str, replace: str = "") -> str:
    """Recursively replaces all occurrences of a substring in a string.

    Args:
        string (str): The input string.
        substring (str): The substring to replace.
        replace (str): The replacement string. Default is "".

    Returns:
        str: The string with all occurrences of substring replaced.

    Examples:
        >>> _recursively_replace("hellooo", "oo", "o")
        'hello'
        >>> _recursively_replace("aaaa", "aa", "a")
        'a'
        >>> _recursively_replace("banana", "na", "n")
        'bann'
    """
    while substring in string:
        string = string.replace(substring, replace)
    return string


def apply_strategy_replace(string: str, strategy: StrategyReplace) -> str:
    """Applies a replacement strategy to a string.

    Args:
        string (str): The input string.
        strategy (StrategyReplace): A dict of replacements.

    Returns:
        str: The modified string.

    Examples:
        >>> s = "hello\\n\\n\\nworld"
        >>> strategy = {"\\n\\n\\n": "\\n\\n"}
        >>> apply_strategy_replace(s, strategy)
        'hello\\n\\nworld'
    """
    for k, v in strategy.items():
        string = _recursively_replace(string, k, v)
    return string


def _format_md(md: str, strategy=None) -> str:
    """Internal function to format markdown text using a replacement strategy.

    Args:
        md (str): The markdown text.
        strategy (StrategyReplace, optional): Custom replacement strategy. Defaults to DEFAULT_STRATEGY_REPLACE.

    Returns:
        str: The formatted markdown.

    Examples:
        >>> _format_md("# Title\\n\\n\\nParagraph")
        '# Title\\n\\nParagraph\\n'
        >>> _format_md("xxxxxxx text", {"xxxxxxx": "ok"})
        'ok text\\n'
    """
    if strategy is None:
        strategy = DEFAULT_STRATEGY_REPLACE

    md = text(md)
    md = apply_strategy_replace(md, strategy)
    return md


def pdf_to_md(stream: bytes) -> str:
    """Converts a PDF byte stream to formatted markdown text.

    Args:
        stream (bytes): PDF byte stream.

    Returns:
        str: Markdown representation of the PDF.
    """
    with fitz.open(stream=stream, filetype="pdf") as doc:
        md = to_markdown(
            doc,
            ignore_graphics=True,
            ignore_code=True,
            ignore_alpha=True,
        )
        return _format_md(md)


def docx_to_md(stream: bytes) -> str:
    """Converts a DOCX byte stream to formatted markdown text.

    Args:
        stream (bytes): DOCX byte stream.

    Returns:
        str: Markdown representation of the DOCX.
    """
    mid = MarkItDown()
    stream = io.BytesIO(stream)

    md = mid.convert_stream(stream, file_extension=".docx").markdown
    md = md.replace("![](data:image/png;base64...)", "")
    md = md.replace("(data:image/png;base64...)", "()")
    md = md.replace("![](data:image/jpeg;base64...)", "")

    return _format_md(md)
