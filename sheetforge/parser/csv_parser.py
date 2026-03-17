from __future__ import annotations

import csv
from pathlib import Path

from ..models import Column, TableSchema
from ..utils import TypeInferrer


def parse_delimited_file(path: Path, target: str) -> TableSchema:
    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=delimiter))

    if len(rows) < 3:
        raise ValueError(f"{path} must contain at least 3 metadata rows")

    var_row, desc_row, tag_row = rows[0], rows[1], rows[2]
    if not var_row or var_row[0] != "##var":
        raise ValueError(f"{path} row 1 must start with ##var")
    if not desc_row or desc_row[0] != "##desc":
        raise ValueError(f"{path} row 2 must start with ##desc")
    if not tag_row or tag_row[0] != "##tag":
        raise ValueError(f"{path} row 3 must start with ##tag")

    width = len(var_row)
    if len(desc_row) != width or len(tag_row) != width:
        raise ValueError(f"{path} metadata rows must have the same width")

    data_rows = [row for row in rows[3:] if any(cell.strip() for cell in row)]
    columns: list[Column] = []
    for index in range(1, width):
        raw_var = (var_row[index] or "").strip()
        description = (desc_row[index] or "").strip()
        tag = (tag_row[index] or "").strip()

        if ":" in raw_var:
            name, data_type = raw_var.split(":", 1)
            data_type = data_type.strip() or "string"
        else:
            name = raw_var
            values = []
            for row in data_rows:
                if len(row) >= index:
                    values.append((row[index - 1] or "").strip())
            data_type = TypeInferrer.infer_column(values)

        name = name.strip()
        if not name:
            raise ValueError(f"{path} column {index} has empty property name")

        if index == 1:
            if name != "id":
                raise ValueError(f"{path} first data column must be id")
            if tag != "all":
                raise ValueError(f"{path} id column tag must be all")
            if data_type not in {"int", "long"}:
                raise ValueError(f"{path} id column must be int or long")

        columns.append(
            Column(
                name=name,
                data_type=data_type,
                description=description,
                tag=tag,
                is_id=index == 1,
            )
        )

    active_columns = [column for column in columns if column.include_for(target)]
    seen_ids: dict[int, int] = {}
    parsed_rows: list[dict[str, object]] = []
    for row_index, raw_row in enumerate(data_rows, start=4):
        padded = raw_row + [""] * (len(columns) - len(raw_row))
        parsed: dict[str, object] = {}
        for offset, column in enumerate(columns):
            if not column.include_for(target):
                continue
            try:
                value = _parse_value((padded[offset] or "").strip(), column.data_type)
            except Exception as exc:
                raise ValueError(
                    f"{path} row {row_index} column '{column.name}' type mismatch: expected {column.data_type}"
                ) from exc
            parsed[column.name] = value

        row_id = int(parsed["id"])
        if row_id in seen_ids:
            raise ValueError(f"{path} row {row_index} duplicate id: {row_id}, first defined at row {seen_ids[row_id]}")
        seen_ids[row_id] = row_index
        parsed_rows.append(parsed)

    table_stem = path.stem.lower()
    logical_name = table_stem[3:] if table_stem.startswith("tb_") else table_stem
    return TableSchema(
        source_path=path,
        table_stem=table_stem,
        name=logical_name,
        columns=active_columns,
        rows=parsed_rows,
    )


def _parse_value(raw: str, data_type: str) -> object:
    data_type = data_type.strip()
    if data_type == "int":
        return int(raw)
    if data_type == "long":
        return int(raw[:-1] if raw.endswith(("L", "l")) else raw)
    if data_type == "float":
        normalized = raw[:-1] if raw.endswith(("f", "F")) else raw
        return float(normalized)
    if data_type == "double":
        return float(raw)
    if data_type == "bool":
        lowered = raw.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
        raise ValueError(raw)
    if data_type == "string":
        return raw
    if data_type == "int[]":
        return [] if raw == "" else [int(item.strip()) for item in raw.split(",")]
    if data_type == "long[]":
        return [] if raw == "" else [int(item.strip()[:-1] if item.strip().endswith(("L", "l")) else item.strip()) for item in raw.split(",")]
    if data_type == "float[]":
        return [] if raw == "" else [float(item.strip()[:-1] if item.strip().endswith(("f", "F")) else item.strip()) for item in raw.split(",")]
    if data_type == "double[]":
        return [] if raw == "" else [float(item.strip()) for item in raw.split(",")]
    if data_type == "bool[]":
        return [] if raw == "" else [_parse_value(item.strip(), "bool") for item in raw.split(",")]
    if data_type == "string[]":
        return [] if raw == "" else [item.strip() for item in raw.split(",")]
    if data_type == "int[][]":
        return _parse_array2d(raw, "int")
    if data_type == "long[][]":
        return _parse_array2d(raw, "long")
    if data_type == "float[][]":
        return _parse_array2d(raw, "float")
    if data_type == "double[][]":
        return _parse_array2d(raw, "double")
    if data_type == "string[][]":
        return _parse_array2d(raw, "string")
    if data_type == "set<int>":
        return set() if raw == "" else {int(item.strip()) for item in raw.split(",") if item.strip()}
    if data_type == "set<long>":
        return set() if raw == "" else {int(item.strip()[:-1] if item.strip().endswith(("L", "l")) else item.strip()) for item in raw.split(",") if item.strip()}
    if data_type == "set<string>":
        return set() if raw == "" else {item.strip() for item in raw.split(",") if item.strip()}
    if data_type == "int->int":
        return _parse_dict(raw, int, int)
    if data_type == "string->int":
        return _parse_dict(raw, str, int)
    if data_type == "int->string":
        return _parse_dict(raw, int, str)
    if data_type == "string->string":
        return _parse_dict(raw, str, str)
    raise ValueError(f"Unsupported data type for current implementation: {data_type}")


def _parse_array2d(raw: str, scalar_type: str) -> list[list[object]]:
    if raw == "":
        return []
    result: list[list[object]] = []
    for row in raw.split(";"):
        row = row.strip()
        if not row:
            continue
        result.append([_parse_value(item.strip(), scalar_type) for item in row.split(",") if item.strip()])
    return result


def _parse_dict(raw: str, key_parser, value_parser) -> dict[object, object]:
    if raw == "":
        return {}
    result: dict[object, object] = {}
    for pair in raw.split(","):
        key_text, value_text = [part.strip() for part in pair.split(":", 1)]
        key = key_parser(key_text) if key_parser is not str else key_text
        value = value_parser(value_text) if value_parser is not str else value_text
        result[key] = value
    return result
