"""
word_counter.analyzers.txt_analyzer
----------------------------------

Analyzer for plain text (.txt) files.

Responsibilities:
- Read text content from a .txt file safely.
- Compute basic statistics:
  - number of characters
  - number of words
  - number of lines
- Extract top N most common words.

This module is intentionally simple and beginner-friendly, so later
we can follow the same output format for PDF and DOCX analyzers.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Union


# A simple regex to pull "word-like" tokens.
# This captures sequences of letters/numbers and also allows apostrophes inside words
# like: don't, it's, user's
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", re.UNICODE)


@dataclass(frozen=True)
class TextAnalysisResult:
    """
    Structured result of a text file analysis.

    Attributes
    ----------
    file_path:
        Absolute or resolved file path that was analyzed.
    file_type:
        Always "txt" for this analyzer.
    characters:
        Total number of characters in the file (including whitespace).
    lines:
        Total number of lines.
    words:
        Total number of word tokens found.
    top_words:
        Most common words as (word, count) pairs (already lowercased).
    """
    file_path: str
    file_type: str
    characters: int
    lines: int
    words: int
    top_words: List[Tuple[str, int]]

    def to_dict(self) -> Dict[str, object]:
        """
        Convert the dataclass into a JSON-friendly dict.

        Returns
        -------
        dict
            A dictionary representation (safe to print or export).
        """
        return {
            "file_path": self.file_path,
            "file_type": self.file_type,
            "characters": self.characters,
            "lines": self.lines,
            "words": self.words,
            "top_words": self.top_words,
        }


def read_text_file(path: Union[str, Path]) -> str:
    """
    Read a text file safely.

    Why this exists:
    Some .txt files might not be UTF-8. We try UTF-8 first, then fall back
    to latin-1 (which can decode any byte 0-255 without crashing).

    Parameters
    ----------
    path:
        Path to a .txt file.

    Returns
    -------
    str
        Entire file content as a string.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    IsADirectoryError
        If the path points to a directory.
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    if p.is_dir():
        raise IsADirectoryError(f"Expected a file but got directory: {p}")

    # Try UTF-8 first (most common)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback: latin-1 never fails, but may produce odd characters
        return p.read_text(encoding="latin-1")


def tokenize_words(text: str) -> List[str]:
    """
    Convert raw text into a list of word tokens.

    Rules:
    - Extracts word-like tokens using regex.
    - Converts everything to lowercase for counting.

    Parameters
    ----------
    text:
        Raw text.

    Returns
    -------
    list[str]
        Lowercased word tokens.
    """
    return [m.group(0).lower() for m in _WORD_RE.finditer(text)]


def analyze_txt(path: Union[str, Path], top_n: int = 10) -> Dict[str, object]:
    """
    Analyze a .txt file and return a JSON-friendly dictionary.

    Parameters
    ----------
    path:
        Path to a .txt file.
    top_n:
        Number of most common words to return.

    Returns
    -------
    dict
        Example:
        {
          "file_path": "...",
          "file_type": "txt",
          "characters": 1234,
          "lines": 56,
          "words": 234,
          "top_words": [("the", 20), ("and", 18), ...]
        }

    Notes
    -----
    - "characters" includes spaces and newlines (true character count).
    - "lines" uses splitlines(), which handles different newline styles.
    """
    p = Path(path).resolve()
    text = read_text_file(p)

    characters = len(text)
    lines = len(text.splitlines())

    tokens = tokenize_words(text)
    words = len(tokens)

    counts = Counter(tokens)
    top_words = counts.most_common(max(0, top_n))

    result = TextAnalysisResult(
        file_path=str(p),
        file_type="txt",
        characters=characters,
        lines=lines,
        words=words,
        top_words=top_words,
    )
    return result.to_dict()
