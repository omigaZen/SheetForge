from __future__ import annotations

import csv
from pathlib import Path

from .common import parse_table_rows


def parse_delimited_file(path: Path, target: str) -> object:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))
    return parse_table_rows(path, rows, target)
