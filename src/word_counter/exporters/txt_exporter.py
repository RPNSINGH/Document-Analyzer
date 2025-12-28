"""
word_counter.exporters.txt_exporter
----------------------------------

Exporter that saves analysis results into a readable .txt report.

Why this module exists:
- Analyzers produce a normalized Python dict (result).
- Exporters take that dict and write it into a desired output format.

This exporter focuses on:
- Clean, human-friendly summary
- Works for single-file results
- Can also handle a list of results (folder mode later)

Expected input shape (minimum keys):
- file_path (str)
- file_type (str)
- characters (int)
- lines (int)
- words (int)
- top_words (list[tuple[str, int]])

Optional keys supported (if present):
- pages (int)
- extracted_pages (int)

If your analyzers add more keys later, this exporter will ignore them safely.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple, Union


@dataclass(frozen=True)
class ExportedFile:
    """
    Represents an exported output file.

    Attributes
    ----------
    path:
        Absolute path of the saved file.
    """
    path: Path


def _safe_int(value: object, default: int = 0) -> int:
    """Convert value to int safely; return default if it fails."""
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _format_top_words(top_words: object, max_items: int = 10) -> List[Tuple[str, int]]:
    """
    Normalize and limit the top_words list to a clean [(word, count), ...] format.
    """
    if not isinstance(top_words, list):
        return []

    cleaned: List[Tuple[str, int]] = []
    for item in top_words:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            word, count = item[0], item[1]
            if isinstance(word, str):
                cleaned.append((word, _safe_int(count, 0)))

    return cleaned[: max(0, max_items)]


def _build_report_block(result: Dict[str, object], top_n: int = 10) -> str:
    """
    Build a human-readable report block for a single analysis result.

    Parameters
    ----------
    result:
        Analyzer output dictionary.
    top_n:
        Number of top words to show.

    Returns
    -------
    str
        A formatted multi-line report block.
    """
    file_path = str(result.get("file_path", ""))
    file_type = str(result.get("file_type", "unknown")).lower()

    characters = _safe_int(result.get("characters"), 0)
    lines = _safe_int(result.get("lines"), 0)
    words = _safe_int(result.get("words"), 0)

    pages = result.get("pages")
    extracted_pages = result.get("extracted_pages")

    top_words = _format_top_words(result.get("top_words"), max_items=top_n)

    # Header
    parts: List[str] = []
    parts.append("=" * 72)
    parts.append(f"FILE: {file_path}")
    parts.append(f"TYPE: {file_type}")

    # Optional PDF metadata if present
    if pages is not None:
        parts.append(f"PAGES: {_safe_int(pages, 0)}")
    if extracted_pages is not None:
        parts.append(f"EXTRACTED_PAGES: {_safe_int(extracted_pages, 0)}")

    parts.append("-" * 72)
    parts.append(f"Characters : {characters}")
    parts.append(f"Lines      : {lines}")
    parts.append(f"Words      : {words}")
    parts.append("-" * 72)

    # Top words section
    parts.append(f"Top {min(top_n, len(top_words))} words:")
    if not top_words:
        parts.append("  (No words found)")
    else:
        for i, (word, count) in enumerate(top_words, start=1):
            parts.append(f"  {i:>2}. {word:<20} {count}")

    parts.append("")  # trailing newline separation
    return "\n".join(parts)


def export_txt(
    results: Union[Dict[str, object], Sequence[Dict[str, object]]],
    output_dir: Union[str, Path] = "outputs",
    output_name: str | None = None,
    top_n: int = 10,
) -> ExportedFile:
    """
    Export analysis result(s) to a .txt report file.

    Parameters
    ----------
    results:
        Either a single result dict OR a list of result dicts.
    output_dir:
        Directory where output file will be created.
    output_name:
        Optional file name (example: "report.txt").
        If None, a timestamped name is generated.
    top_n:
        Number of top words to include per file.

    Returns
    -------
    ExportedFile
        The path of the saved .txt report.

    Notes
    -----
    - This function creates output_dir if it doesn't exist.
    - It overwrites the output file if it already exists.
    """
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_name is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"word_counter_report_{stamp}.txt"

    if not output_name.lower().endswith(".txt"):
        output_name = f"{output_name}.txt"

    out_path = out_dir / output_name

    # Normalize results to a list
    if isinstance(results, dict):
        items: List[Dict[str, object]] = [results]
    else:
        items = list(results)

    # Build full report
    header = []
    header.append("WORD COUNTER REPORT")
    header.append(f"Generated at: {datetime.now().isoformat(timespec='seconds')}")
    header.append(f"Total files: {len(items)}")
    header.append("=" * 72)
    header.append("")

    blocks = [_build_report_block(r, top_n=top_n) for r in items]
    content = "\n".join(header + blocks)

    out_path.write_text(content, encoding="utf-8")
    return ExportedFile(path=out_path)
