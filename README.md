# docmd

A simple Python utility to convert **PDF** and **DOCX** documents into clean **Markdown**.  
It uses [PyMuPDF](https://github.com/pymupdf/PyMuPDF), [pymupdf4llm](https://github.com/pymupdf/RAG), [MarkItDown](https://github.com/microsoft/markitdown), and [mdformat](https://github.com/executablebooks/mdformat) to extract, normalize, and format content, then applies custom replacement strategies for cleaner output.

---

## Why docmd?

While many libraries exist for extracting text from documents, **docmd** is designed for:

* People with **low or no compute resources (no GPU required)**
* Users who want the **fastest possible Markdown extraction**
* Clean Markdown output that **preserves formatting** (headings, italics, tables, etc.)
* Workflows that **only need text content**, without images or heavy post-processing

---

## Features

* Convert **PDF** to Markdown
* Convert **DOCX** to Markdown
* Clean and format output using custom replacement strategies
* Simple API and command-line usage

---

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/Athroniaeth/docmd.git
cd docmd

# Install dependencies
uv sync
```

---

## Usage

### Python API

```python
from docmd import pdf_to_md, docx_to_md

# Convert PDF
with open("data/cv.pdf", "rb") as f:
    pdf_content = f.read()
    markdown_pdf = pdf_to_md(pdf_content)
    print(markdown_pdf)

# Convert DOCX
with open("data/cv.docx", "rb") as f:
    docx_content = f.read()
    markdown_docx = docx_to_md(docx_content)
    print(markdown_docx)
```

## Custom Replacement Strategy

The library uses a configurable recursively replacement strategy to clean the Markdown (for `docx`):

```python
from docmd.core import apply_strategy_replace

text = "hello\n\n\n\nworld"
strategy = {"\n\n\n": "\n\n"}
print(apply_strategy_replace(text, strategy))  # "hello\n\nworld"
```

---

## Development

Format code and run tests:

```bash
uv run ruff check .
uv run pytest
```

---

## License

MIT License. See [LICENSE](./LICENSE).
