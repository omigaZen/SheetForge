from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    description: str
    tag: str
    is_id: bool = False

    def include_for(self, target: str) -> bool:
        if self.tag == "":
            return False
        if target == "all":
            return self.tag in {"all", "client", "server"}
        return self.tag in {"all", target}


@dataclass(frozen=True)
class TableSchema:
    source_path: Path
    table_stem: str
    name: str
    columns: list[Column]
    rows: list[dict[str, object]]

    def columns_for(self, target: str) -> list[Column]:
        return [column for column in self.columns if column.include_for(target)]
