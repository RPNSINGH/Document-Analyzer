"""
word_counter.analyzers.pdf_analyzer
----------------------------------

Analyzer for PDF (.pdf) files using `pypdf`.

Responsibilities:
- Extract text from a PDF file (page by page).
- Compute basic statistics:
  - characters
  - lines
  - words
- Extract top N most common words.

Important note about PDFs:
- PDF is not a "text-first" format. Some PDFs store text as positioned glyphs,
  and some PDFs are scanned images (no text). In such cases, extraction may
  return empty text.
- OCR (reading scanned images) is not implemented here (we can add later).

Output format:
Matches txt_analyzer.analyze_txt() and docx_analyzer.analyze_docx():
{
  "file_path": "...",
  "file_type": "pdf",
  "characters": ...,
  "lines": ...,
  "words": ...,
  "top_words": [(word, count), ...]
}
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union

try:
    # pypdf is the actively maintained successor ecosystem (commonly used)
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Missing dependency: 'pypdf'. Install it with: pip install pypdf"
    ) from exc


_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", re.UNICODE)


@dataclass(frozen=True)
class PdfAnalysisResult:
    """
    Structured result of a PDF analysis.

    Attributes
    ----------
    file_path:
        Absolute file path that was analyzed.
    file_type:
        Always "pdf" for this analyzer.
    characters:
        Total extracted text characters (including whitespace/newlines).
    lines:
        Total number of lines in extracted text.
    words:
        Total number of word tokens found.
    top_words:
        Most common words as (word, count) pairs (lowercased).
    pages:
        Total number of pages in the PDF (metadata from reader).
    extracted_pages:
        Number of pages from which we successfully extracted any non-empty text.
    """
    file_path: str
    file_type: str
    characters: int
    lines: int
    words: int
    top_words: List[Tuple[str, int]]
    pages: int
    extracted_pages: int

    def to_dict(self) -> Dict[str, object]:
        """Convert result to a JSON-friendly dict."""
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "pages": self.pages,
            "extracted_pages": self.extracted_pages,
            "characters": self.characters,
            "lines": self.lines,
            "words": self.words,
            "top_words": self.top_words,
        }


def _validate_pdf_path(path: Union[str, Path]) -> Path:
    """
    Validate and normalize input PDF path.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    IsADirectoryError
        If the path points to a directory.
    ValueError
        If the extension is not .pdf.
    """
    p = Path(path).expanduser()

    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    if p.is_dir():
        raise IsADirectoryError(f"Expected a file but got directory: {p}")

    if p.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file but got: {p.name}")

    return p.resolve()


def extract_pdf_text(path: Union[str, Path]) -> str:
    """
    Extract text from a PDF, page-by-page.

    Parameters
    ----------
    path:
        Path to a .pdf file.

    Returns
    -------
    str
        Extracted text joined by newlines.

    Raises
    ------
    ValueError
        If the PDF is encrypted and cannot be read.
    """
    p = _validate_pdf_path(path)
    reader = PdfReader(str(p))

    if reader.is_encrypted:
        # We can try a blank password, but if it fails, raise a clear error.
        try:
            reader.decrypt("")  # type: ignore[attr-defined]
        except Exception as e:
            raise ValueError(
                f"PDF is encrypted and cannot be read without password: {p}"
            ) from e

    # Collect page texts (some pages may return None or empty)
    parts: List[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_text = page_text.strip()
        if page_text:
            parts.append(page_text)

    return "\n".join(parts)


def tokenize_words(text: str) -> List[str]:
    """
    Convert extracted text into word tokens (lowercased).

    Parameters
    ----------
    text:
        Extracted text.

    Returns
    -------
    list[str]
        Lowercased tokens.
    """
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def analyze_pdf(path: Union[str, Path], top_n: int = 10) -> Dict[str, object]:
    """
    Analyze a PDF file and return a JSON-friendly dictionary.

    Parameters
    ----------
    path:
        Path to a .pdf file.
    top_n:
        Number of most common words to return.

    Returns
    -------
    dict
        Example:
        {
          "file_path": "...",
          "file_type": "pdf",
          "pages": 12,
          "extracted_pages": 10,
          "characters": 1234,
          "lines": 56,
          "words": 234,
          "top_words": [("the", 20), ("and", 18), ...]
        }

    Notes
    -----
    - If the PDF is scanned (images only), extracted text may be empty.
    - "extracted_pages" counts pages where extract_text() produced non-empty text.
    """
    p = _validate_pdf_path(path)
    reader = PdfReader(str(p))

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # type: ignore[attr-defined]
        except Exception as e:
            raise ValueError(
                f"PDF is encrypted and cannot be read without password: {p}"
            ) from e

    total_pages = len(reader.pages)

    extracted_page_count = 0
    page_texts: List[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            extracted_page_count += 1
            page_texts.append(text)

    full_text = "\n".join(page_texts)

    characters = len(full_text)
    lines = len(full_text.splitlines())

    tokens = tokenize_words(full_text)
    words = len(tokens)

    counts = Counter(tokens)
    top_words = counts.most_common(max(0, top_n))

    result = PdfAnalysisResult(
        file_path=str(p),
        file_type="pdf",
        pages=total_pages,
        extracted_pages=extracted_page_count,
        characters=characters,
        lines=lines,
        words=words,
        top_words=top_words,
    )
    return result.to_dict()
