from __future__ import annotations

from pathlib import Path

from ..models import Column, TableSchema


TYPE_MAPPING = {
    "int": "int",
    "long": "int",
    "float": "float",
    "double": "float",
    "bool": "bool",
    "string": "str",
    "int[]": "List[int]",
    "long[]": "List[int]",
    "float[]": "List[float]",
    "double[]": "List[float]",
    "bool[]": "List[bool]",
    "string[]": "List[str]",
    "int[][]": "List[List[int]]",
    "long[][]": "List[List[int]]",
    "float[][]": "List[List[float]]",
    "double[][]": "List[List[float]]",
    "string[][]": "List[List[str]]",
    "set<int>": "set[int]",
    "set<long>": "set[int]",
    "set<string>": "set[str]",
    "int->int": "Dict[int, int]",
    "string->int": "Dict[str, int]",
    "int->string": "Dict[int, str]",
    "string->string": "Dict[str, str]",
}

READ_METHODS = {
    "int": "read_int32",
    "long": "read_int64",
    "float": "read_float",
    "double": "read_double",
    "bool": "read_bool",
    "string": "read_string",
    "int[]": "read_int32_array",
    "long[]": "read_int64_array",
    "float[]": "read_float_array",
    "double[]": "read_double_array",
    "bool[]": "read_bool_array",
    "string[]": "read_string_array",
    "int[][]": "read_int32_array2d",
    "long[][]": "read_int64_array2d",
    "float[][]": "read_float_array2d",
    "double[][]": "read_double_array2d",
    "string[][]": "read_string_array2d",
    "set<int>": "read_int32_set",
    "set<long>": "read_int64_set",
    "set<string>": "read_string_set",
    "int->int": "read_int32_int32_dict",
    "string->int": "read_string_int32_dict",
    "int->string": "read_int32_string_dict",
    "string->string": "read_string_string_dict",
}


class PythonGenerator:
    def __init__(self, package_name: str = "game_config") -> None:
        self.package_name = package_name

    def generate(self, schema: TableSchema, output_dir: Path) -> None:
        package_dir = output_dir / self.package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        item_module = f"{schema.table_stem}.py"
        table_module = f"{schema.table_stem}_table.py"

        (package_dir / item_module).write_text(self.generate_item_class(schema), encoding="utf-8")
        (package_dir / table_module).write_text(self.generate_table_class(schema), encoding="utf-8")

    def write_package_init(self, schemas: list[TableSchema], output_dir: Path) -> None:
        package_dir = output_dir / self.package_name
        package_dir.mkdir(parents=True, exist_ok=True)
        package_dir.joinpath("__init__.py").write_text(self.generate_package_init(schemas), encoding="utf-8")
        package_dir.joinpath("config_manager.py").write_text(self.generate_config_manager(schemas), encoding="utf-8")

    def generate_item_class(self, schema: TableSchema) -> str:
        class_name = _item_class_name(schema)
        imports = self._typing_imports(schema.columns)
        fields = "\n\n".join(self._field_block(column) for column in schema.columns)
        assignments = ",\n".join(
            f"            {column.name}=reader.{READ_METHODS[column.data_type]}()"
            for column in schema.columns
        )
        return (
            "from __future__ import annotations\n\n"
            "from dataclasses import dataclass\n"
            f"{imports}\n\n"
            "@dataclass\n"
            f"class {class_name}:\n"
            f"    \"\"\"{schema.name} config item\"\"\"\n\n"
            f"{fields}\n\n"
            "    @classmethod\n"
            f"    def from_reader(cls, reader: 'SheetReader') -> '{class_name}':\n"
            "        return cls(\n"
            f"{assignments}\n"
            "        )\n"
        )

    def generate_table_class(self, schema: TableSchema) -> str:
        class_name = _item_class_name(schema)
        table_class = _table_class_name(schema)
        return (
            "from __future__ import annotations\n\n"
            f"from .{schema.table_stem} import {class_name}\n"
            "from time import perf_counter\n"
            "from sheetforge import SheetReader, TableBase\n\n\n"
            f"class {table_class}(TableBase[{class_name}]):\n"
            f"    \"\"\"{schema.name} config table\"\"\"\n\n"
            "    @property\n"
            "    def table_name(self) -> str:\n"
            f"        return \"{schema.name}\"\n\n"
            "    def load(self, file_path: str) -> None:\n"
            "        _start = perf_counter()\n"
            "        with SheetReader(file_path) as reader:\n"
            "            self._items.clear()\n"
            "            self._item_list.clear()\n\n"
            "            for _ in range(reader.row_count):\n"
            f"                item = {class_name}.from_reader(reader)\n"
            "                self._items[item.id] = item\n"
            "                self._item_list.append(item)\n"
            "        self._load_time_ms = (perf_counter() - _start) * 1000.0\n\n"
            "    @classmethod\n"
            f"    def load_from(cls, file_path: str) -> '{table_class}':\n"
            "        table = cls()\n"
            "        table.load(file_path)\n"
            "        return table\n"
        )

    def generate_package_init(self, schemas: list[TableSchema]) -> str:
        lines: list[str] = []
        exports: list[str] = []
        for schema in schemas:
            class_name = _item_class_name(schema)
            table_class = _table_class_name(schema)
            lines.append(f"from .{schema.table_stem} import {class_name}")
            lines.append(f"from .{schema.table_stem}_table import {table_class}")
            exports.extend([class_name, table_class])
        getter_names = [_getter_name(schema) for schema in schemas]
        config_exports = ", ".join(["ConfigManager", *getter_names])
        lines.append(f"from .config_manager import {config_exports}")
        exports.append("ConfigManager")
        exports.extend(getter_names)
        joined = ", ".join(repr(name) for name in exports)
        return "\n".join(lines) + f"\n\n__all__ = [{joined}]\n"

    def generate_config_manager(self, schemas: list[TableSchema]) -> str:
        import_lines: list[str] = []
        attr_lines: list[str] = []
        load_lines: list[str] = []
        unload_lines: list[str] = []
        getter_lines: list[str] = []

        for schema in schemas:
            table_class = _table_class_name(schema)
            attr_name = _manager_attr_name(schema)
            getter_name = _getter_name(schema)
            import_lines.append(f"from .{schema.table_stem}_table import {table_class}")
            attr_lines.append(f"        self.{attr_name}: Optional[{table_class}] = None")
            load_lines.append(f"        self.{attr_name} = {table_class}.load_from(str(path / '{schema.table_stem}.sfc'))")
            unload_lines.append(f"        self.{attr_name} = None")
            getter_lines.append(
                f"def {getter_name}() -> {table_class}:\n"
                f"    return ConfigManager.get_instance().{attr_name}\n"
            )

        import_block = "\n".join(import_lines)
        attr_block = "\n".join(attr_lines)
        load_block = "\n".join(load_lines)
        unload_block = "\n".join(unload_lines)
        getter_block = "\n".join(getter_lines)

        return (
            "from __future__ import annotations\n\n"
            "from pathlib import Path\n"
            "from typing import Optional\n\n"
            + import_block
            + "\n\n\n"
            + "class ConfigManager:\n"
            + "    _instance: Optional['ConfigManager'] = None\n\n"
            + "    def __init__(self):\n"
            + attr_block
            + "\n\n"
            + "    @classmethod\n"
            + "    def get_instance(cls) -> 'ConfigManager':\n"
            + "        if cls._instance is None:\n"
            + "            cls._instance = cls()\n"
            + "        return cls._instance\n\n"
            + "    def load_all(self, config_path: str) -> None:\n"
            + "        path = Path(config_path)\n"
            + load_block
            + "\n\n"
            + "    def unload_all(self) -> None:\n"
            + unload_block
            + "\n\n"
            + getter_block
            + "\n"
        )

    def _field_block(self, column: Column) -> str:
        py_type = TYPE_MAPPING[column.data_type]
        description = (column.description or column.name).replace('"""', "'''")
        return f"    {column.name}: {py_type}\n    \"\"\"{description}\"\"\""

    def _typing_imports(self, columns: list[Column]) -> str:
        needed: set[str] = set()
        for column in columns:
            mapped = TYPE_MAPPING[column.data_type]
            if "List[" in mapped:
                needed.add("List")
            if "Dict[" in mapped:
                needed.add("Dict")
        if not needed:
            return ""
        return f"from typing import {', '.join(sorted(needed))}"


def _item_class_name(schema: TableSchema) -> str:
    return "Tb" + "".join(part.capitalize() for part in schema.name.split("_"))


def _table_class_name(schema: TableSchema) -> str:
    return f"{_item_class_name(schema)}Table"


def _manager_attr_name(schema: TableSchema) -> str:
    name = schema.name.lower()
    if name.endswith("y"):
        return name[:-1] + "ies"
    return name + "s"


def _getter_name(schema: TableSchema) -> str:
    return f"get_{_manager_attr_name(schema)}"
