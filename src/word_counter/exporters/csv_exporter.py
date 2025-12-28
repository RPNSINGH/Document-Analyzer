"""
word_counter.exporters.csv_exporter
----------------------------------

Exporter that saves analysis results into a CSV file.

Why CSV exporter:
- Easy to open in Excel / Google Sheets
- Good for reporting and automation
- Easy to load into pandas later

Input:
- A single analyzer result dict OR a list of result dicts

Minimum expected keys per result:
- file_path (str)
- file_type (str)
- characters (int)
- lines (int)
- words (int)
- top_words (list of (word, count))

Optional keys supported:
- pages (int)            -> PDF metadata
- extracted_pages (int)  -> PDF metadata

We keep this exporter tolerant:
- Missing keys become empty/0
- Unknown extra keys are ignored
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union


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
    """Convert value to int safely; return default if conversion fails."""
    try:
        return int(value)  # type: ignore[arg-type]
    except Exception:
        return default


def _format_top_words(top_words: object, max_items: int = 10) -> str:
    """
    Convert top_words list into a compact CSV-friendly string.

    Example:
      [("the", 10), ("and", 8)] -> "the:10 | and:8"
    """
    if not isinstance(top_words, list):
        return ""

    pairs: List[Tuple[str, int]] = []
    for item in top_words:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            word, count = item[0], item[1]
            if isinstance(word, str):
                pairs.append((word, _safe_int(count, 0)))

    pairs = pairs[: max(0, max_items)]
    return " | ".join([f"{w}:{c}" for w, c in pairs])


def _normalize_results(
    results: Union[Dict[str, object], Sequence[Dict[str, object]]]
) -> List[Dict[str, object]]:
    """Normalize input into a list of result dicts."""
    if isinstance(results, dict):
        return [results]
    return list(results)


def export_csv(
    results: Union[Dict[str, object], Sequence[Dict[str, object]]],
    output_dir: Union[str, Path] = "outputs",
    output_name: str | None = None,
    top_n: int = 10,
) -> ExportedFile:
    """
    Export analysis result(s) to a CSV file.

    Parameters
    ----------
    results:
        Single analyzer result dict OR list of result dicts.
    output_dir:
        Directory where CSV will be saved.
    output_name:
        Optional file name (e.g., "report.csv").
        If None, a timestamped name is generated.
    top_n:
        Number of top words to store in `top_words` column.

    Returns
    -------
    ExportedFile
        Path to the saved CSV file.

    Notes
    -----
    - Creates output_dir if not present.
    - Overwrites existing file with same name.
    """
    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if output_name is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = f"word_counter_report_{stamp}.csv"

    if not output_name.lower().endswith(".csv"):
        output_name = f"{output_name}.csv"

    out_path = out_dir / output_name

    items = _normalize_results(results)

    # Fixed columns (stable schema)
    fieldnames = [
        "file_path",
        "file_type",
        "pages",
        "extracted_pages",
        "characters",
        "lines",
        "words",
        "top_words",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for r in items:
            row = {
                "file_path": str(r.get("file_path", "")),
                "file_type": str(r.get("file_type", "unknown")).lower(),
                "pages": _safe_int(r.get("pages", 0), 0),
                "extracted_pages": _safe_int(r.get("extracted_pages", 0), 0),
                "characters": _safe_int(r.get("characters", 0), 0),
                "lines": _safe_int(r.get("lines", 0), 0),
                "words": _safe_int(r.get("words", 0), 0),
                "top_words": _format_top_words(r.get("top_words"), max_items=top_n),
            }
            writer.writerow(row)

    return ExportedFile(path=out_path)
