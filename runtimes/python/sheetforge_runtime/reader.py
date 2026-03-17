from __future__ import annotations

import struct
from typing import BinaryIO


class SheetReader:
    MAGIC = b"SFGC"
    CURRENT_VERSION = 1

    def __init__(self, file_path: str):
        self._file: BinaryIO = open(file_path, "rb")
        self._string_table: dict[int, str] = {}
        self.row_count: int = 0
        self.version: int = 0
        self._string_table_offset: int = 0
        self._data_offset: int = 0

        self._read_header()
        self._read_column_definitions()
        self._read_string_table()
        self._file.seek(self._data_offset)

    def _read_header(self) -> None:
        magic = self._file.read(4)
        if magic != self.MAGIC:
            raise ValueError(f"Invalid file format: magic mismatch, got {magic!r}")

        self.version = struct.unpack("<H", self._file.read(2))[0]
        if self.version > self.CURRENT_VERSION:
            raise ValueError(f"Unsupported version: {self.version}")

        self._file.read(2)
        self.row_count = struct.unpack("<I", self._file.read(4))[0]
        self._string_table_offset = struct.unpack("<I", self._file.read(4))[0]

    def _read_column_definitions(self) -> None:
        column_count = struct.unpack("<H", self._file.read(2))[0]
        for _ in range(column_count):
            name_length = struct.unpack("<H", self._file.read(2))[0]
            self._file.read(name_length)
            self._file.read(2)

    def _read_string_table(self) -> None:
        self._file.seek(self._string_table_offset)
        string_count = struct.unpack("<I", self._file.read(4))[0]
        for index in range(string_count):
            length = struct.unpack("<H", self._file.read(2))[0]
            data = self._file.read(length)
            self._string_table[index] = data.decode("utf-8")
        self._data_offset = self._file.tell()

    def read_int32(self) -> int:
        return struct.unpack("<i", self._file.read(4))[0]

    def read_int64(self) -> int:
        return struct.unpack("<q", self._file.read(8))[0]

    def read_float(self) -> float:
        return struct.unpack("<f", self._file.read(4))[0]

    def read_double(self) -> float:
        return struct.unpack("<d", self._file.read(8))[0]

    def read_bool(self) -> bool:
        return struct.unpack("<?", self._file.read(1))[0]

    def read_string(self) -> str:
        index = struct.unpack("<I", self._file.read(4))[0]
        return self._string_table[index]

    def read_int32_array(self) -> list[int]:
        return self._read_array(self.read_int32)

    def read_int64_array(self) -> list[int]:
        return self._read_array(self.read_int64)

    def read_float_array(self) -> list[float]:
        return self._read_array(self.read_float)

    def read_double_array(self) -> list[float]:
        return self._read_array(self.read_double)

    def read_bool_array(self) -> list[bool]:
        return self._read_array(self.read_bool)

    def read_string_array(self) -> list[str]:
        return self._read_array(self.read_string)

    def read_int32_array2d(self) -> list[list[int]]:
        return self._read_array2d(self.read_int32)

    def read_int64_array2d(self) -> list[list[int]]:
        return self._read_array2d(self.read_int64)

    def read_float_array2d(self) -> list[list[float]]:
        return self._read_array2d(self.read_float)

    def read_double_array2d(self) -> list[list[float]]:
        return self._read_array2d(self.read_double)

    def read_string_array2d(self) -> list[list[str]]:
        return self._read_array2d(self.read_string)

    def read_int32_set(self) -> set[int]:
        return set(self._read_array(self.read_int32))

    def read_int64_set(self) -> set[int]:
        return set(self._read_array(self.read_int64))

    def read_string_set(self) -> set[str]:
        return set(self._read_array(self.read_string))

    def read_int32_int32_dict(self) -> dict[int, int]:
        return self._read_dict(self.read_int32, self.read_int32)

    def read_string_int32_dict(self) -> dict[str, int]:
        return self._read_dict(self.read_string, self.read_int32)

    def read_int32_string_dict(self) -> dict[int, str]:
        return self._read_dict(self.read_int32, self.read_string)

    def read_string_string_dict(self) -> dict[str, str]:
        return self._read_dict(self.read_string, self.read_string)

    def _read_array(self, item_reader):
        count = struct.unpack("<I", self._file.read(4))[0]
        return [item_reader() for _ in range(count)]

    def _read_array2d(self, item_reader):
        row_count = struct.unpack("<I", self._file.read(4))[0]
        rows: list[list[object]] = []
        for _ in range(row_count):
            column_count = struct.unpack("<I", self._file.read(4))[0]
            rows.append([item_reader() for _ in range(column_count)])
        return rows

    def _read_dict(self, key_reader, value_reader):
        count = struct.unpack("<I", self._file.read(4))[0]
        result = {}
        for _ in range(count):
            key = key_reader()
            value = value_reader()
            result[key] = value
        return result

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> "SheetReader":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
