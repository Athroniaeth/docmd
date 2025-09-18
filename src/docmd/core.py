import io
import re
from typing import Dict, Optional, Callable

import fitz
from markitdown import MarkItDown
from mdformat import text
from pymupdf4llm import to_markdown

ConverterFunc = Callable[[bytes], str]
StrategyReplace = Dict[str, str]
"""Dict representing a replacement strategy where keys are substrings to be replaced and values are their replacements."""

DEFAULT_STRATEGY_REPLACE: StrategyReplace = {
    "\n\n\n": "\n\n",
    "xxxxxxx": "xxx",
    "- -": "-",
}

# data:image/(png|jpeg|jpg|gif|webp|svg+xml);base64...
MIME_GROUP = r"(?:png|jpe?g|gif|webp|svg\+xml)"

# Remove markdown images that embed base64 data (supports alt text, optional title, whitespace)
REGEX_BASE64_EMBED = re.compile(
    rf"""
    !\[[^\]]*\]              # ![alt]
    \(
        \s*data:image/{MIME_GROUP};base64[^)\s]*   # data:image/...;base64...
        (?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?      # optional title: "t" or 't' or (t)
        \s*
    \)
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

# Replace parenthetical base64 URLs with "()"
RE_BASE64_PAREN = re.compile(
    rf"""
    \(
        \s*data:image/{MIME_GROUP};base64[^)\s]*   # data:image/...;base64...
        (?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?      # optional title
        \s*
    \)
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)


class DocmdError(Exception):
    """Custom exception class for Docmd-related errors."""

    ...


class UnsupportedFileExtensionError(DocmdError):
    """Exception raised for unsupported file extensions."""

    ...


def rreplace(string: str, substring: str, replace: str = "") -> str:
    """Recursively replaces all occurrences of a substring in a string.

    Args:
        string (str): The input string.
        substring (str): The substring to replace.
        replace (str): The replacement string. Default is "".

    Returns:
        str: The string with all occurrences of substring replaced.

    Examples:
        >>> rreplace("hellooo", "oo", "o")
        'hello'
        >>> rreplace("aaaa", "aa", "a")
        'a'
        >>> rreplace("banana", "na", "n")
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
        string = rreplace(string, k, v)
    return string


def clean_base64_images(md: str) -> str:
    """Remove embedded base64 images from Markdown and normalize base64 URLs in parentheses.

    Args:
        md (str): Markdown text possibly containing inline base64 images.

    Notes:
        The function performs two passes:

        - Remove Markdown images whose URL starts with data:image/(png|jpeg);base64...
          e.g. ![](data:image/png;base64,AAA...), ![alt](data:image/jpeg;base64,BBB...)

        - Replace any occurrence of (data:image/...;base64,...) with "()"
          (this mirrors the original replace("(data:image/png;base64...)", "()"))

    Examples:
        >>> clean_base64_images("before ![](data:image/png;base64,AAA) after")
        'before  after'
        >>> clean_base64_images("![alt](data:image/jpeg;base64,BBBB)")
        ''
        >>> clean_base64_images("![alt](data:image/jpg;base64,BBBB)")  # jpg alias
        ''
        >>> clean_base64_images("![a](data:image/webp;base64,XX 't')")  # webp + title
        ''
        >>> clean_base64_images("![a](data:image/svg+xml;base64,YY)")   # svg+xml
        ''
        >>> clean_base64_images("link(data:image/gif;base64,CCC)")
        'link()'
        >>> clean_base64_images("text (data:image/jpeg;base64,ZZZ) and ![](data:image/png;base64,YYY)")
        'text () and '
        >>> clean_base64_images("![](DATA:IMAGE/PNG;BASE64,AA)")  # case-insensitive
        ''
        >>> clean_base64_images("![Alt](data:image/png;base64,AAAB 'title')")  # with title
        ''
        >>> clean_base64_images("![](data:image/png;base64,AA) ![](data:image/jpeg;base64,BB)")  # multiples
        ' '
        >>> clean_base64_images("![x](https://example.com/img.png)")  # normal image untouched
        '![x](https://example.com/img.png)'
        >>> clean_base64_images("not an image: data:image/png;base64,AA")  # no parentheses: untouched
        'not an image: data:image/png;base64,AA'
    """
    md = REGEX_BASE64_EMBED.sub("", md)
    md = RE_BASE64_PAREN.sub("()", md)

    return md


class Converter:
    """A class to convert documents (pdf, docx) to markdown format.

    Attributes:
        strategy (StrategyReplace): A dict defining replacement strategies for formatting.
    """

    mapping: Dict[str, ConverterFunc]

    def __init__(
        self, strategy: Optional[StrategyReplace] = None, mid: Optional[MarkItDown] = None
    ):
        """Initializes the Converter with an optional replacement strategy.

        Args:
            strategy (StrategyReplace, optional): Custom replacement strategy. Defaults to DEFAULT_STRATEGY_REPLACE.
        """
        self.mapping = {
            ".pdf": self.pdf_to_md,
            ".docx": self.docx_to_md,
        }
        self.strategy = strategy or DEFAULT_STRATEGY_REPLACE
        self.mid = mid or MarkItDown()

    def format_md(self, md: str) -> str:
        """Internal function to format markdown text using a replacement strategy.

        Args:
            md (str): The markdown text.

        Returns:
            str: The formatted markdown.

        Examples:
            >>> converter = Converter(strategy={**DEFAULT_STRATEGY_REPLACE, "xxxxxxx": "ok"})
            >>> converter.format_md("# Title\\n\\n\\nParagraph")
            '# Title\\n\\nParagraph\\n'
            >>> converter.format_md("xxxxxxx text")
            'ok text\\n'
        """
        md = text(md)
        md = apply_strategy_replace(md, self.strategy)
        return md.strip() + "\n"

    def pdf_to_md(self, stream: bytes) -> str:
        """Converts a PDF byte stream to raw markdown text.

        Args:
            stream (bytes): PDF byte stream.

        Returns:
            str: Raw Markdown extracted from the PDF (not post-formatted).
        """
        with fitz.open(stream=stream, filetype="pdf") as doc:
            return to_markdown(
                doc,
                ignore_graphics=True,
                ignore_code=True,
                ignore_alpha=True,
            )

    def docx_to_md(self, stream: bytes) -> str:
        """Converts a DOCX byte stream to raw markdown text.

        Args:
            stream (bytes): DOCX byte stream.

        Returns:
            str: Raw Markdown extracted from the DOCX (not post-formatted).
        """
        doc = self.mid.convert_stream(
            io.BytesIO(stream),
            file_extension=".docx",
        )
        md = clean_base64_images(doc.markdown)
        return md

    def file_to_md(self, stream: bytes, file_extension: str) -> str:
        """Converts a document byte stream to formatted markdown text based on its file extension.

        Args:
            stream (bytes): Document byte stream.
            file_extension (str): File extension indicating the document type (e.g., '.pdf', '.docx').

        Returns:
            str: Markdown representation of the document.

        Raises:
            ValueError: If the file extension is unsupported.
        """
        func = self.mapping.get(file_extension)

        if not func:
            raise UnsupportedFileExtensionError(
                f"Unsupported file extension: '{file_extension}'. "
                f"Supported: {list(self.mapping.keys())}"
            )
        raw_md = func(stream=stream)
        return self.format_md(raw_md)
