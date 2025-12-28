"""
word_counter.utils.file_detect
------------------------------

This module contains small, reusable helpers for working with input paths.

Primary responsibility:
- Validate a given path (file or directory).
- Detect file type based on extension.
- Collect supported files from a directory (optional, for later CLI features).

Why this module exists:
The CLI should NOT contain file detection logic. The CLI should ask this module:
"Given this path, what is it and what type is it?"

This keeps the project clean and modular.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, List, Optional


class FileType(str, Enum):
    """
    Supported file types for the analyzer.

    Using Enum avoids magic strings and reduces bugs.
    """
    TXT = "txt"
    DOCX = "docx"
    PDF = "pdf"
    UNKNOWN = "unknown"


SUPPORTED_EXTENSIONS = {
    ".txt": FileType.TXT,
    ".docx": FileType.DOCX,
    ".pdf": FileType.PDF,
}


@dataclass(frozen=True)
class PathInfo:
    """
    A small container describing the input path.

    Attributes
    ----------
    path:
        The resolved absolute path.
    exists:
        True if the path exists on disk.
    is_file:
        True if path exists and is a file.
    is_dir:
        True if path exists and is a directory.
    file_type:
        Detected file type by extension if it's a file, else UNKNOWN.
    """
    path: Path
    exists: bool
    is_file: bool
    is_dir: bool
    file_type: FileType


def detect_file_type(path: Path) -> FileType:
    """
    Detect the file type based on the file extension.

    Parameters
    ----------
    path:
        The file path whose extension should be checked.

    Returns
    -------
    FileType
        TXT, DOCX, PDF if supported; otherwise UNKNOWN.

    Notes
    -----
    - Extension matching is case-insensitive ('.PDF' works).
    - If the path has no extension, returns UNKNOWN.
    """
    ext = path.suffix.lower().strip()
    return SUPPORTED_EXTENSIONS.get(ext, FileType.UNKNOWN)


def inspect_path(raw_path: str | Path) -> PathInfo:
    """
    Inspect any input path string/path and return structured info.

    Parameters
    ----------
    raw_path:
        A path provided by the user (string or Path).

    Returns
    -------
    PathInfo
        A normalized object telling you:
        - does it exist?
        - is it file or dir?
        - if file, what file type?

    Examples
    --------
    >>> inspect_path("notes.txt").is_file
    True
    >>> inspect_path("data/").is_dir
    True
    """
    p = Path(raw_path).expanduser()

    # Resolve only if it exists (resolve() can error on some systems for missing paths)
    exists = p.exists()
    resolved = p.resolve() if exists else p

    is_file = exists and resolved.is_file()
    is_dir = exists and resolved.is_dir()

    ftype = detect_file_type(resolved) if is_file else FileType.UNKNOWN

    return PathInfo(
        path=resolved,
        exists=exists,
        is_file=is_file,
        is_dir=is_dir,
        file_type=ftype,
    )


def iter_supported_files(
    directory: str | Path,
    recursive: bool = False,
) -> List[Path]:
    """
    Collect supported files from a directory.

    This will be useful later when your CLI supports folder analysis.

    Parameters
    ----------
    directory:
        Directory to scan.
    recursive:
        If True, scan subfolders too.

    Returns
    -------
    list[Path]
        A list of paths to supported files (.txt, .docx, .pdf).

    Raises
    ------
    NotADirectoryError
        If the given path is not an existing directory.
    """
    dir_path = Path(directory).expanduser()

    if not dir_path.exists():
        raise NotADirectoryError(f"Directory does not exist: {dir_path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    pattern = "**/*" if recursive else "*"
    candidates: Iterable[Path] = dir_path.glob(pattern)

    supported_files: List[Path] = []
    for p in candidates:
        if p.is_file() and detect_file_type(p) != FileType.UNKNOWN:
            supported_files.append(p.resolve())

    # Keep stable ordering (helps testing + predictable output)
    supported_files.sort(key=lambda x: str(x).lower())
    return supported_files


def ensure_supported_file(path_info: PathInfo) -> None:
    """
    Validate that PathInfo points to a supported file.

    Parameters
    ----------
    path_info:
        Result from inspect_path(...)

    Raises
    ------
    FileNotFoundError
        If the path doesn't exist.
    IsADirectoryError
        If the path is a directory (not a file).
    ValueError
        If the file type is not supported.
    """
    if not path_info.exists:
        raise FileNotFoundError(f"Path does not exist: {path_info.path}")

    if path_info.is_dir:
        raise IsADirectoryError(f"Expected a file but got a directory: {path_info.path}")

    if not path_info.is_file:
        raise FileNotFoundError(f"Expected a file but got: {path_info.path}")

    if path_info.file_type == FileType.UNKNOWN:
        raise ValueError(
            f"Unsupported file type: {path_info.path.suffix or '(no extension)'} "
            f"for file: {path_info.path}"
        )
