from __future__ import annotations

from pathlib import Path

from .csv_parser import parse_delimited_file
from .excel_parser import parse_excel_file


def parse_table_file(path: Path, target: str):
    suffix = path.suffix.lower()
    if suffix in {".tsv", ".csv"}:
        return parse_delimited_file(path, target)
    if suffix == ".xlsx":
        return parse_excel_file(path, target)
    raise ValueError(f"Unsupported input format: {path}")


__all__ = ["parse_table_file", "parse_delimited_file", "parse_excel_file"]
