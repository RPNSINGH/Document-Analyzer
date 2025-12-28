"""
word_counter.cli
----------------

Command Line Interface (CLI) for the Word Counter / Document Analyzer project.

What this CLI does:
1) Accepts an input path (file or directory)
2) Detects supported file types (.txt, .docx, .pdf)
3) Runs the correct analyzer
4) Prints the result in a readable format
5) Optionally exports output to TXT or CSV via exporters

Run examples
------------
# Analyze a single file
python -m word_counter.cli "sample.txt"

# Analyze a DOCX file and export TXT report
python -m word_counter.cli "report.docx" --export txt --outdir outputs

# Analyze a folder (non-recursive) and export CSV
python -m word_counter.cli "./docs" --export csv --outdir outputs

# Analyze a folder recursively
python -m word_counter.cli "./docs" --recursive --export csv

Notes
-----
- For folder analysis, only supported files are analyzed.
- For PDFs that are scanned images (no embedded text), extraction may be empty.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Sequence

from word_counter.analyzers.docx_analyzer import analyze_docx
from word_counter.analyzers.pdf_analyzer import analyze_pdf
from word_counter.analyzers.txt_analyzer import analyze_txt
from word_counter.exporters.csv_exporter import export_csv
from word_counter.exporters.txt_exporter import export_txt
from word_counter.utils.file_detect import (
    FileType,
    ensure_supported_file,
    inspect_path,
    iter_supported_files,
)


# ----------------------------
# Analyzer router
# ----------------------------

def analyze_file(file_path: Path, top_n: int) -> Dict[str, object]:
    """
    Analyze a single file by detecting its extension and calling the right analyzer.

    Parameters
    ----------
    file_path:
        Path to the file (must exist).
    top_n:
        Number of top words to compute.

    Returns
    -------
    dict
        Normalized analysis output dictionary.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return analyze_txt(file_path, top_n=top_n)
    if suffix == ".docx":
        return analyze_docx(file_path, top_n=top_n)
    if suffix == ".pdf":
        return analyze_pdf(file_path, top_n=top_n)

    # Should not happen if we validate earlier, but kept as safety.
    raise ValueError(f"Unsupported file type: {suffix}")


# ----------------------------
# Output helpers
# ----------------------------

def print_result(result: Dict[str, object]) -> None:
    """
    Print a single analysis result in a clean, human-readable way.
    """
    file_path = str(result.get("file_path", ""))
    file_type = str(result.get("file_type", "unknown")).lower()

    pages = result.get("pages")
    extracted_pages = result.get("extracted_pages")

    characters = int(result.get("characters", 0) or 0)
    lines = int(result.get("lines", 0) or 0)
    words = int(result.get("words", 0) or 0)
    top_words = result.get("top_words", []) or []

    print("=" * 72)
    print(f"FILE : {file_path}")
    print(f"TYPE : {file_type}")

    # Optional PDF metadata
    if pages is not None:
        print(f"PAGES          : {pages}")
    if extracted_pages is not None:
        print(f"EXTRACTED_PAGES: {extracted_pages}")

    print("-" * 72)
    print(f"Characters : {characters}")
    print(f"Lines      : {lines}")
    print(f"Words      : {words}")
    print("-" * 72)

    print("Top words:")
    if not top_words:
        print("  (No words found)")
    else:
        for i, pair in enumerate(top_words, start=1):
            # pair is expected to be (word, count)
            try:
                w, c = pair
                print(f"  {i:>2}. {str(w):<20} {int(c)}")
            except Exception:
                # If format is unexpected, just print raw
                print(f"  {i:>2}. {pair}")

    print()  # spacing


def print_json(data: object) -> None:
    """Print JSON output to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ----------------------------
# CLI implementation
# ----------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the CLI argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="word_counter",
        description="Analyze TXT/DOCX/PDF files and count words, lines, characters + top words.",
    )

    parser.add_argument(
        "path",
        type=str,
        help="Path to a file (.txt/.docx/.pdf) or a directory containing supported files.",
    )

    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many top words to show (default: 10).",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        help="When a directory is provided, scan subfolders too.",
    )

    parser.add_argument(
        "--export",
        choices=["txt", "csv", "none"],
        default="none",
        help="Export results to a file (txt/csv). Default: none.",
    )

    parser.add_argument(
        "--outdir",
        type=str,
        default="outputs",
        help="Output directory for exports (default: outputs).",
    )

    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Optional export file name (e.g., report.txt or report.csv).",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON output instead of formatted text.",
    )

    return parser


def get_project_root() -> Path:
    """
    Return project root directory (parent of 'src').

    Assumes this file lives in:
    project_root/src/word_counter/cli.py
    """
    return Path(__file__).resolve().parents[2]


def run(args: argparse.Namespace) -> int:
    """
    Execute the CLI logic.

    Returns
    -------
    int
        Exit code (0 = success, non-zero = error)
    """
    path_info = inspect_path(args.path)

    if not path_info.exists:
        print(f"[ERROR] Path does not exist: {path_info.path}", file=sys.stderr)
        return 2

    results: List[Dict[str, object]] = []

    # Case 1: user provided a file
    if path_info.is_file:
        try:
            ensure_supported_file(path_info)
            results.append(analyze_file(path_info.path, top_n=args.top))
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 2

    # Case 2: user provided a directory
    elif path_info.is_dir:
        try:
            files = iter_supported_files(path_info.path, recursive=args.recursive)
        except Exception as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            return 2

        if not files:
            print(
                f"[INFO] No supported files found in directory: {path_info.path}",
                file=sys.stderr,
            )
            return 0

        for fp in files:
            try:
                results.append(analyze_file(fp, top_n=args.top))
            except Exception as e:
                # For directory mode: continue on errors, but report them
                print(f"[WARN] Failed to analyze {fp.name}: {e}", file=sys.stderr)

    else:
        print(f"[ERROR] Unsupported path type: {path_info.path}", file=sys.stderr)
        return 2

    # Output to console
    if args.json:
        # Print list if multiple, dict if single
        if len(results) == 1:
            print_json(results[0])
        else:
            print_json(results)
    else:
        for r in results:
            print_result(r)

    # Export if requested
    export_mode = args.export.lower()
    if export_mode != "none":
        try:
            if export_mode == "txt":
                project_root = get_project_root()
                output_dir = project_root / args.outdir

                exported = export_txt(
                    results if len(results) > 1 else results[0],
                    output_dir=output_dir,
                    output_name=args.name,
                    top_n=args.top,
                )
                print(f"[OK] TXT report saved to: {exported.path}")
            elif export_mode == "csv":
                project_root = get_project_root()
                output_dir = project_root / args.outdir

                exported = export_txt(
                    results if len(results) > 1 else results[0],
                    output_dir=output_dir,
                    output_name=args.name,
                    top_n=args.top,
                )
                print(f"[OK] CSV report saved to: {exported.path}")
        except Exception as e:
            print(f"[ERROR] Export failed: {e}", file=sys.stderr)
            return 2

    return 0


def main(argv: Sequence[str] | None = None) -> None:
    """
    Entry point for `python -m word_counter.cli`.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run(args)
    raise SystemExit(code)


if __name__ == "__main__":
    main()
