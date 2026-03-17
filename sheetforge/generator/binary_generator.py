from __future__ import annotations

import struct
from pathlib import Path

from ..models import Column, TableSchema


BASE_CODES = {
    "int": 0x00,
    "long": 0x01,
    "float": 0x02,
    "double": 0x03,
    "bool": 0x04,
    "string": 0x05,
}

TYPE_CODES = {
    "int": 0x00,
    "long": 0x01,
    "float": 0x02,
    "double": 0x03,
    "bool": 0x04,
    "string": 0x05,
    "int[]": 0x10 | BASE_CODES["int"],
    "long[]": 0x10 | BASE_CODES["long"],
    "float[]": 0x10 | BASE_CODES["float"],
    "double[]": 0x10 | BASE_CODES["double"],
    "bool[]": 0x10 | BASE_CODES["bool"],
    "string[]": 0x10 | BASE_CODES["string"],
    "int[][]": 0x20 | BASE_CODES["int"],
    "long[][]": 0x20 | BASE_CODES["long"],
    "float[][]": 0x20 | BASE_CODES["float"],
    "double[][]": 0x20 | BASE_CODES["double"],
    "string[][]": 0x20 | BASE_CODES["string"],
    "set<int>": 0x30 | BASE_CODES["int"],
    "set<long>": 0x30 | BASE_CODES["long"],
    "set<string>": 0x30 | BASE_CODES["string"],
    "int->int": 0x40 | BASE_CODES["int"],
    "string->int": 0x40 | BASE_CODES["string"],
    "int->string": 0x40 | BASE_CODES["int"],
    "string->string": 0x40 | BASE_CODES["string"],
}

MAP_VALUE_CODES = {
    "int->int": BASE_CODES["int"],
    "string->int": BASE_CODES["int"],
    "int->string": BASE_CODES["string"],
    "string->string": BASE_CODES["string"],
}


class BinaryGenerator:
    MAGIC = b"SFGC"
    VERSION = 1

    def write(self, schema: TableSchema, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{schema.table_stem}.sfc"

        string_index: dict[str, int] = {}
        string_values: list[str] = []
        for row in schema.rows:
            for column in schema.columns:
                self._collect_strings(row[column.name], column.data_type, string_index, string_values)

        column_blob = self._build_column_blob(schema.columns)
        string_blob = self._build_string_blob(string_values)
        string_offset = 16 + len(column_blob)
        data_blob = self._build_data_blob(schema, string_index)

        with output_path.open("wb") as handle:
            handle.write(self.MAGIC)
            handle.write(struct.pack("<H", self.VERSION))
            handle.write(struct.pack("<H", 0))
            handle.write(struct.pack("<I", len(schema.rows)))
            handle.write(struct.pack("<I", string_offset))
            handle.write(column_blob)
            handle.write(string_blob)
            handle.write(data_blob)
        return output_path

    def _build_column_blob(self, columns: list[Column]) -> bytes:
        parts = [struct.pack("<H", len(columns))]
        for column in columns:
            encoded = column.name.encode("utf-8")
            flags = 0x01 if column.is_id else 0x00
            if column.data_type in MAP_VALUE_CODES:
                flags = MAP_VALUE_CODES[column.data_type]
            parts.append(struct.pack("<H", len(encoded)))
            parts.append(encoded)
            parts.append(struct.pack("<B", TYPE_CODES[column.data_type]))
            parts.append(struct.pack("<B", flags))
        return b"".join(parts)

    def _build_string_blob(self, strings: list[str]) -> bytes:
        parts = [struct.pack("<I", len(strings))]
        for value in strings:
            encoded = value.encode("utf-8")
            parts.append(struct.pack("<H", len(encoded)))
            parts.append(encoded)
        return b"".join(parts)

    def _build_data_blob(self, schema: TableSchema, string_index: dict[str, int]) -> bytes:
        parts: list[bytes] = []
        for row in schema.rows:
            for column in schema.columns:
                parts.append(self._encode_value(row[column.name], column.data_type, string_index))
        return b"".join(parts)

    def _collect_strings(self, value: object, data_type: str, string_index: dict[str, int], string_values: list[str]) -> None:
        if data_type == "string":
            self._add_string(str(value), string_index, string_values)
            return
        if data_type in {"string[]", "set<string>"}:
            for item in value:
                self._add_string(str(item), string_index, string_values)
            return
        if data_type == "string[][]":
            for row in value:
                for item in row:
                    self._add_string(str(item), string_index, string_values)
            return
        if data_type in {"int->string", "string->string"}:
            for key, item in value.items():
                if data_type.startswith("string->"):
                    self._add_string(str(key), string_index, string_values)
                self._add_string(str(item), string_index, string_values)
            return
        if data_type == "string->int":
            for key in value.keys():
                self._add_string(str(key), string_index, string_values)

    def _add_string(self, value: str, string_index: dict[str, int], string_values: list[str]) -> None:
        if value not in string_index:
            string_index[value] = len(string_values)
            string_values.append(value)

    def _encode_value(self, value: object, data_type: str, string_index: dict[str, int]) -> bytes:
        if data_type == "int":
            return struct.pack("<i", int(value))
        if data_type == "long":
            return struct.pack("<q", int(value))
        if data_type == "float":
            return struct.pack("<f", float(value))
        if data_type == "double":
            return struct.pack("<d", float(value))
        if data_type == "bool":
            return struct.pack("<?", bool(value))
        if data_type == "string":
            return struct.pack("<I", string_index[str(value)])
        if data_type == "int[]":
            return self._encode_array(value, lambda item: struct.pack("<i", int(item)))
        if data_type == "long[]":
            return self._encode_array(value, lambda item: struct.pack("<q", int(item)))
        if data_type == "float[]":
            return self._encode_array(value, lambda item: struct.pack("<f", float(item)))
        if data_type == "double[]":
            return self._encode_array(value, lambda item: struct.pack("<d", float(item)))
        if data_type == "bool[]":
            return self._encode_array(value, lambda item: struct.pack("<?", bool(item)))
        if data_type == "string[]":
            return self._encode_array(value, lambda item: struct.pack("<I", string_index[str(item)]))
        if data_type == "int[][]":
            return self._encode_array2d(value, lambda item: struct.pack("<i", int(item)))
        if data_type == "long[][]":
            return self._encode_array2d(value, lambda item: struct.pack("<q", int(item)))
        if data_type == "float[][]":
            return self._encode_array2d(value, lambda item: struct.pack("<f", float(item)))
        if data_type == "double[][]":
            return self._encode_array2d(value, lambda item: struct.pack("<d", float(item)))
        if data_type == "string[][]":
            return self._encode_array2d(value, lambda item: struct.pack("<I", string_index[str(item)]))
        if data_type == "set<int>":
            return self._encode_array(sorted(value), lambda item: struct.pack("<i", int(item)))
        if data_type == "set<long>":
            return self._encode_array(sorted(value), lambda item: struct.pack("<q", int(item)))
        if data_type == "set<string>":
            return self._encode_array(sorted(value), lambda item: struct.pack("<I", string_index[str(item)]))
        if data_type == "int->int":
            return self._encode_dict(value.items(), lambda item: struct.pack("<i", int(item)), lambda item: struct.pack("<i", int(item)))
        if data_type == "string->int":
            return self._encode_dict(value.items(), lambda item: struct.pack("<I", string_index[str(item)]), lambda item: struct.pack("<i", int(item)))
        if data_type == "int->string":
            return self._encode_dict(value.items(), lambda item: struct.pack("<i", int(item)), lambda item: struct.pack("<I", string_index[str(item)]))
        if data_type == "string->string":
            return self._encode_dict(value.items(), lambda item: struct.pack("<I", string_index[str(item)]), lambda item: struct.pack("<I", string_index[str(item)]))
        raise ValueError(f"Unsupported data type for current implementation: {data_type}")

    def _encode_array(self, values, encode_item) -> bytes:
        items = list(values)
        return struct.pack("<I", len(items)) + b"".join(encode_item(item) for item in items)

    def _encode_array2d(self, rows: list[list[object]], encode_item) -> bytes:
        parts = [struct.pack("<I", len(rows))]
        for row in rows:
            parts.append(struct.pack("<I", len(row)))
            parts.extend(encode_item(item) for item in row)
        return b"".join(parts)

    def _encode_dict(self, items, encode_key, encode_value) -> bytes:
        pairs = list(items)
        parts = [struct.pack("<I", len(pairs))]
        for key, value in pairs:
            parts.append(encode_key(key))
            parts.append(encode_value(value))
        return b"".join(parts)
