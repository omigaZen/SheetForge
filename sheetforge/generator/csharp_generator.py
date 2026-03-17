from __future__ import annotations

from pathlib import Path

from ..models import Column, TableSchema


TYPE_MAPPING = {
    "int": "int",
    "long": "long",
    "float": "float",
    "double": "double",
    "bool": "bool",
    "string": "string",
    "int[]": "int[]",
    "long[]": "long[]",
    "float[]": "float[]",
    "double[]": "double[]",
    "bool[]": "bool[]",
    "string[]": "string[]",
    "int[][]": "int[][]",
    "long[][]": "long[][]",
    "float[][]": "float[][]",
    "double[][]": "double[][]",
    "string[][]": "string[][]",
    "set<int>": "HashSet<int>",
    "set<long>": "HashSet<long>",
    "set<string>": "HashSet<string>",
    "int->int": "Dictionary<int, int>",
    "string->int": "Dictionary<string, int>",
    "int->string": "Dictionary<int, string>",
    "string->string": "Dictionary<string, string>",
}

READ_METHODS = {
    "int": "ReadInt32",
    "long": "ReadInt64",
    "float": "ReadFloat",
    "double": "ReadDouble",
    "bool": "ReadBool",
    "string": "ReadString",
    "int[]": "ReadInt32Array",
    "long[]": "ReadInt64Array",
    "float[]": "ReadFloatArray",
    "double[]": "ReadDoubleArray",
    "bool[]": "ReadBoolArray",
    "string[]": "ReadStringArray",
    "int[][]": "ReadInt32Array2D",
    "long[][]": "ReadInt64Array2D",
    "float[][]": "ReadFloatArray2D",
    "double[][]": "ReadDoubleArray2D",
    "string[][]": "ReadStringArray2D",
    "set<int>": "ReadInt32HashSet",
    "set<long>": "ReadInt64HashSet",
    "set<string>": "ReadStringHashSet",
    "int->int": "ReadInt32Int32Dictionary",
    "string->int": "ReadStringInt32Dictionary",
    "int->string": "ReadInt32StringDictionary",
    "string->string": "ReadStringStringDictionary",
}


class CSharpGenerator:
    def __init__(self, namespace: str = "GameConfig") -> None:
        self.namespace = namespace

    def generate(self, schema: TableSchema, output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        item_class = _item_class_name(schema)
        table_class = _table_class_name(schema)
        (output_dir / f"{item_class}.cs").write_text(self.generate_item_class(schema), encoding="utf-8")
        (output_dir / f"{table_class}.cs").write_text(self.generate_table_class(schema), encoding="utf-8")

    def write_support_files(self, schemas: list[TableSchema], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "ConfigManager.cs").write_text(self.generate_config_manager(schemas), encoding="utf-8")

    def generate_item_class(self, schema: TableSchema) -> str:
        class_name = _item_class_name(schema)
        properties = "\n\n".join(self._property_block(column) for column in schema.columns)
        assignments = "\n".join(
            f"            item.{_property_name(column.name)} = reader.{READ_METHODS[column.data_type]}();"
            for column in schema.columns
        )
        return (
            "using SheetForge;\n"
            "using System.Collections.Generic;\n\n"
            f"namespace {self.namespace}\n"
            "{\n"
            f"    public partial class {class_name}\n"
            "    {\n"
            f"{properties}\n\n"
            f"        internal static {class_name} Load(SheetReader reader)\n"
            "        {\n"
            f"            var item = new {class_name}();\n"
            f"{assignments}\n"
            "            return item;\n"
            "        }\n\n"
            f"        private {class_name}()\n"
            "        {\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

    def generate_table_class(self, schema: TableSchema) -> str:
        class_name = _item_class_name(schema)
        table_class = _table_class_name(schema)
        id_property = _property_name(schema.columns[0].name)
        return (
            "using SheetForge;\n"
            "using System.Diagnostics;\n\n"
            f"namespace {self.namespace}\n"
            "{\n"
            f"    public partial class {table_class} : TableBase<{class_name}>\n"
            "    {\n"
            f"        public override string TableName => \"{schema.name}\";\n\n"
            "        public override void Load(string filePath)\n"
            "        {\n"
            "            var stopwatch = Stopwatch.StartNew();\n"
            "            using var reader = new SheetReader(filePath);\n"
            "            _items.Clear();\n"
            "            _itemList.Clear();\n\n"
            "            for (var index = 0; index < reader.RowCount; index++)\n"
            "            {\n"
            f"                var item = {class_name}.Load(reader);\n"
            f"                _items[item.{id_property}] = item;\n"
            "                _itemList.Add(item);\n"
            "            }\n\n"
            "            stopwatch.Stop();\n"
            "            LoadTimeMs = stopwatch.Elapsed.TotalMilliseconds;\n"
            "        }\n\n"
            f"        public static {table_class} LoadFromFile(string filePath)\n"
            "        {\n"
            f"            var table = new {table_class}();\n"
            "            table.Load(filePath);\n"
            "            return table;\n"
            "        }\n"
            "    }\n"
            "}\n"
        )

    def generate_config_manager(self, schemas: list[TableSchema]) -> str:
        if not schemas:
            return (
                f"namespace {self.namespace}\n"
                "{\n"
                "    public static class ConfigManager\n"
                "    {\n"
                "    }\n"
                "}\n"
            )

        properties = "\n".join(
            f"        public static {_table_class_name(schema)} {_manager_property_name(schema)} {{ get; private set; }}"
            for schema in schemas
        )
        loads = "\n".join(
            f"            {_manager_property_name(schema)} = {_table_class_name(schema)}.LoadFromFile(Path.Combine(configPath, \"{schema.table_stem}.sfc\"));"
            for schema in schemas
        )
        unloads = "\n".join(
            f"            {_manager_property_name(schema)} = null;"
            for schema in schemas
        )
        getters = "\n\n".join(
            f"        public static {_table_class_name(schema)} {_getter_name(schema)}()\n"
            "        {\n"
            f"            return {_manager_property_name(schema)};\n"
            "        }"
            for schema in schemas
        )

        return (
            "using System.IO;\n\n"
            f"namespace {self.namespace}\n"
            "{\n"
            "    public static class ConfigManager\n"
            "    {\n"
            f"{properties}\n\n"
            "        public static void LoadAll(string configPath)\n"
            "        {\n"
            f"{loads}\n"
            "        }\n\n"
            "        public static void UnloadAll()\n"
            "        {\n"
            f"{unloads}\n"
            "        }\n\n"
            f"{getters}\n"
            "    }\n"
            "}\n"
        )

    def _property_block(self, column: Column) -> str:
        description = (column.description or column.name).replace("\n", " ").replace("\r", " ")
        return (
            "        /// <summary>\n"
            f"        /// {description}\n"
            "        /// </summary>\n"
            f"        public {TYPE_MAPPING[column.data_type]} {_property_name(column.name)} {{ get; private set; }}"
        )


def _item_class_name(schema: TableSchema) -> str:
    return "Tb" + "".join(part.capitalize() for part in schema.name.split("_"))


def _table_class_name(schema: TableSchema) -> str:
    return f"{_item_class_name(schema)}Table"


def _property_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _manager_property_name(schema: TableSchema) -> str:
    name = schema.name.lower()
    if name.endswith("y"):
        name = name[:-1] + "ies"
    else:
        name = name + "s"
    return "".join(part.capitalize() for part in name.split("_"))


def _getter_name(schema: TableSchema) -> str:
    return f"Get{_manager_property_name(schema)}"
