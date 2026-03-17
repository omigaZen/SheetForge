# SheetForge 技术设计文档

## 1. 技术栈选型

### 1.1 工具端（Python）

| 模块 | 技术选型 | 版本要求 | 说明 |
|------|----------|----------|------|
| 运行时 | Python | >= 3.9 | 类型提示、match语法支持 |
| Excel解析 | openpyxl | >= 3.1 | xlsx格式，MIT协议 |
| CSV/TSV解析 | 内置csv模块 | - | 标准库 |
| CLI框架 | click | >= 8.0 | 成熟稳定 |
| 配置文件 | PyYAML | >= 6.0 | YAML解析 |
| 模板引擎 | Jinja2 | >= 3.0 | 代码生成 |
| 打包工具 | PyInstaller | >= 6.0 | 单文件exe分发 |

### 1.2 运行时端（多语言）

#### 1.2.1 C# 运行时

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| 目标框架 | .NET Standard 2.0 | 兼容Unity 2019.4+ |
| 二进制读取 | System.IO.BinaryReader | 标准库 |
| 集合类型 | System.Collections.Generic | 标准库 |

#### 1.2.2 Python 运行时

| 模块 | 技术选型 | 说明 |
|------|----------|------|
| Python版本 | >= 3.9 | 类型提示支持 |
| 二进制读取 | struct模块 | 标准库 |
| 类型定义 | dataclass | 标准库 |

#### 1.2.3 后续语言支持

| 语言 | 目标框架 | 优先级 |
|------|----------|--------|
| Go | Go 1.18+ | P1 |
| TypeScript | ES6+ | P1 |
| Java | Java 8+ | P2 |
| C++ | C++17 | P3 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     SheetForge Tool (Python)                │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐│
│  │   CLI    │  │  Config  │  │  Parser  │  │  Generator   ││
│  │  Module  │──│  Loader  │──│  Module  │──│    Module    ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘│
│                                      │              │       │
│                                      ▼              ▼       │
│                              ┌──────────┐  ┌──────────────┐│
│                              │  Schema  │  │   Template   ││
│                              │  Model   │  │    Engine    ││
│                              └──────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────┘
                          │                    │
                          ▼                    ▼
              ┌──────────────────┐  ┌──────────────────────────────┐
              │  .sfc 数据文件    │  │  多语言代码文件               │
              │  (统一二进制格式)  │  │  C# / Python / Go / TS ...  │
              └────────┬─────────┘  └──────────────┬───────────────┘
                       │                           │
         ┌─────────────┼─────────────┐             │
         │             │             │             │
         ▼             ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ C# Runtime  │ │Python Runtime│ │ Go Runtime  │ │TS Runtime   │
│  (Unity)    │ │  (Server)   │ │  (Server)   │ │  (Web)      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

### 2.2 数据流

```
Excel/CSV/TSV 文件
       │
       ▼
┌─────────────────┐
│ Parser Module   │  解析表格，提取元数据和数据行
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Schema Model    │  表结构定义：列名、类型、标记
└────────┬────────┘
         │
         ├──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
┌─────────────────────┐            ┌─────────────────┐
│  Code Generator     │            │ Data Generator  │
│  (多语言模板)        │            │ (二进制写入)    │
│  ├─ C# Generator    │            └────────┬────────┘
│  ├─ Python Generator│                     │
│  ├─ Go Generator    │                     │
│  └─ ...             │                     │
└─────────┬───────────┘                     │
          │                                 │
          ▼                                 ▼
   多语言代码文件                      xxx.sfc 文件
   ├─ TbXxx.cs                        (统一格式)
   ├─ tb_xxx.py                             │
   ├─ tb_xxx.go                             │
   └─ ...                                   │
          │                                 │
          └─────────────┬───────────────────┘
                        │
                        ▼
              多语言运行时加载解析
                        │
                        ▼
              游戏运行时使用
```

### 2.3 生成器插件架构

```
┌─────────────────────────────────────────────────────────────┐
│                   Generator Manager                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   generator_registry = {                                    │
│       "csharp": CSharpGenerator,                           │
│       "python": PythonGenerator,                           │
│       "go": GoGenerator,                                    │
│       "typescript": TypeScriptGenerator,
│   }                                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ generate(schema, target, options)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  BaseGenerator (抽象基类)                    │
├─────────────────────────────────────────────────────────────┤
│  + generate_item_class(schema, target) -> str              │
│  + generate_table_class(schema, target) -> str             │
│  + get_type_mapping() -> Dict[str, str]                    │
│  + get_file_extension() -> str                             │
│  + get_naming_convention() -> NamingConvention             │
└─────────────────────────────────────────────────────────────┘
                          △
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│CSharpGenerator│ │PythonGenerator│ │ GoGenerator   │
│               │ │               │ │               │
│模板: *.cs.j2  │ │模板: *.py.j2  │ │模板: *.go.j2  │
└───────────────┘ └───────────────┘ └───────────────┘
```

---

## 3. 模块设计

### 3.1 Python 工具模块

#### 3.1.1 目录结构

```
sheetforge/
├── __init__.py
├── __main__.py              # python -m sheetforge 入口
├── cli.py                   # 命令行接口
├── config.py                # 配置管理
├── parser/
│   ├── __init__.py
│   ├── base.py              # 解析器基类
│   ├── excel_parser.py      # Excel解析器
│   ├── csv_parser.py        # CSV/TSV解析器
│   └── table_parser.py      # 表格解析逻辑
├── generator/
│   ├── __init__.py
│   ├── base.py              # 生成器抽象基类
│   ├── manager.py           # 生成器管理器
│   ├── csharp_generator.py  # C#代码生成器
│   ├── python_generator.py  # Python代码生成器
│   ├── go_generator.py      # Go代码生成器（扩展）
│   ├── typescript_generator.py  # TypeScript生成器（扩展）
│   ├── binary_generator.py  # 二进制数据生成器
│   └── templates/
│       ├── csharp/
│       │   ├── item.cs.jinja2
│       │   ├── table.cs.jinja2
│       │   └── manager.cs.jinja2
│       ├── python/
│       │   ├── item.py.jinja2
│       │   ├── table.py.jinja2
│       │   └── manager.py.jinja2
│       └── go/
│           ├── item.go.jinja2
│           └── table.go.jinja2
├── models/
│   ├── __init__.py
│   ├── schema.py            # 表结构定义
│   ├── column.py            # 列定义
│   └── data_row.py          # 数据行
├── validator/
│   ├── __init__.py
│   └── table_validator.py   # 数据校验器
├── writer/
│   ├── __init__.py
│   ├── binary_writer.py     # 二进制写入器
│   └── code_writer.py       # 代码文件写入
└── utils/
    ├── __init__.py
    ├── type_utils.py        # 类型处理工具
    └── file_utils.py        # 文件工具
```

#### 3.1.2 核心类设计

##### Schema 模型 (models/schema.py)

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

class Tag(Enum):
    """列标记"""
    ALL = "all"           # 双端可见
    CLIENT = "client"     # 仅客户端
    SERVER = "server"     # 仅服务器
    IGNORE = ""           # 忽略

@dataclass
class Column:
    """列定义"""
    name: str                    # 属性名
    description: str             # 描述
    tag: Tag                     # 标记
    data_type: str = "auto"      # 数据类型
    is_id: bool = False          # 是否为ID列
    index: int = 0               # 列索引
    required: bool = True        # 是否必填

@dataclass
class TableSchema:
    """表结构定义"""
    name: str                           # 表名（从文件名推导）
    file_path: str                      # 源文件路径
    columns: List[Column] = field(default_factory=list)

    @property
    def client_columns(self) -> List[Column]:
        """获取客户端可见列"""
        return [c for c in self.columns
                if c.tag in (Tag.ALL, Tag.CLIENT)]

    @property
    def server_columns(self) -> List[Column]:
        """获取服务器可见列"""
        return [c for c in self.columns
                if c.tag in (Tag.ALL, Tag.SERVER)]

    @property
    def id_column(self) -> Optional[Column]:
        """获取ID列"""
        for c in self.columns:
            if c.is_id:
                return c
        return None
```

##### 解析器基类 (parser/base.py)

```python
from abc import ABC, abstractmethod
from typing import List, List[List[str]]
from pathlib import Path

class BaseParser(ABC):
    """解析器基类"""

    # 元数据行标识
    VAR_ROW = "##var"
    DESC_ROW = "##desc"
    TAG_ROW = "##tag"

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.raw_data: List[List[str]] = []

    @abstractmethod
    def load(self) -> List[List[str]]:
        """加载文件，返回二维数组"""
        pass

    def parse(self) -> tuple[TableSchema, List[Dict[str, Any]]]:
        """解析表格，返回(表结构, 数据行列表)"""
        self.raw_data = self.load()
        schema = self._parse_schema()
        rows = self._parse_rows(schema)
        return schema, rows

    def _parse_schema(self) -> TableSchema:
        """解析表结构"""
        # 实现细节...
        pass

    def _parse_rows(self, schema: TableSchema) -> List[Dict[str, Any]]:
        """解析数据行"""
        # 实现细节...
        pass
```

##### 代码生成器 (generator/csharp_generator.py)

```python
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class CSharpGenerator:
    """C#代码生成器"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate_item_class(
        self,
        schema: TableSchema,
        target: str = "all"
    ) -> str:
        """生成配置项类"""
        template = self.env.get_template("item.cs.jinja2")

        # 根据目标过滤列
        if target == "client":
            columns = schema.client_columns
        elif target == "server":
            columns = schema.server_columns
        else:
            columns = [c for c in schema.columns if c.tag != Tag.IGNORE]

        return template.render(
            class_name=f"Tb{schema.name}",
            columns=columns,
            table_name=schema.name
        )

    def generate_table_class(
        self,
        schema: TableSchema,
        target: str = "all"
    ) -> str:
        """生成配置表类"""
        template = self.env.get_template("table.cs.jinja2")
        # 实现细节...
        pass
```

##### 类型解析器 (utils/type_parser.py)

```python
"""
类型解析器
负责解析类型字符串和类型推断
"""
import re
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class ContainerType(Enum):
    """容器类型"""
    NONE = ""           # 非容器类型
    ARRAY = "array"     # 一维数组
    ARRAY2D = "array2d" # 二维数组
    SET = "set"         # 集合
    MAP = "map"         # 字典


class BaseType(Enum):
    """基础类型"""
    INT = "int"
    LONG = "long"
    FLOAT = "float"
    DOUBLE = "double"
    BOOL = "bool"
    STRING = "string"


@dataclass
class ParsedType:
    """解析后的类型信息"""
    raw: str                          # 原始类型字符串
    container: ContainerType          # 容器类型
    element_type: Optional[str]       # 元素类型（array/set）
    key_type: Optional[str]           # 键类型（map）
    value_type: Optional[str]         # 值类型（map）

    @property
    def is_container(self) -> bool:
        return self.container != ContainerType.NONE

    @property
    def is_map(self) -> bool:
        return self.container == ContainerType.MAP


class TypeParser:
    """类型解析器"""

    # 基础类型列表
    BASE_TYPES = {"int", "long", "float", "double", "bool", "string"}

    @classmethod
    def parse(cls, type_str: str) -> ParsedType:
        """
        解析类型字符串

        支持格式：
        - 基础类型: int, string, float, ...
        - 一维数组: int[], string[], ...
        - 二维数组: int[][], string[][], ...
        - 集合: set<int>, set<string>, ...
        - 字典: int->int, string->int, ...
        """
        type_str = type_str.strip()

        # 检测二维数组类型: T[][]
        if type_str.endswith("[][]"):
            element_type = type_str[:-4].strip()
            return ParsedType(
                raw=type_str,
                container=ContainerType.ARRAY2D,
                element_type=element_type if element_type in cls.BASE_TYPES else None,
                key_type=None,
                value_type=None
            )

        # 检测一维数组类型: T[]
        if type_str.endswith("[]"):
            element_type = type_str[:-2].strip()
            return ParsedType(
                raw=type_str,
                container=ContainerType.ARRAY,
                element_type=element_type if element_type in cls.BASE_TYPES else None,
                key_type=None,
                value_type=None
            )

        # 检测集合类型: set<T>
        if type_str.startswith("set<") and type_str.endswith(">"):
            element_type = type_str[4:-1].strip()
            return ParsedType(
                raw=type_str,
                container=ContainerType.SET,
                element_type=element_type if element_type in cls.BASE_TYPES else None,
                key_type=None,
                value_type=None
            )

        # 检测字典类型: K->V
        if "->" in type_str:
            parts = type_str.split("->")
            if len(parts) == 2:
                key_type = parts[0].strip()
                value_type = parts[1].strip()
                return ParsedType(
                    raw=type_str,
                    container=ContainerType.MAP,
                    element_type=None,
                    key_type=key_type if key_type in cls.BASE_TYPES else None,
                    value_type=value_type if value_type in cls.BASE_TYPES else None
                )

        # 基础类型
        return ParsedType(
            raw=type_str,
            container=ContainerType.NONE,
            element_type=type_str if type_str in cls.BASE_TYPES else None,
            key_type=None,
            value_type=None
        )


class TypeInferrer:
    """类型推断器"""

    @classmethod
    def infer(cls, value: str) -> str:
        """
        根据数据值推断类型

        优先级：
        1. 布尔值 -> bool
        2. 整数 -> int
        3. 长整数（带L后缀） -> long
        4. 浮点数 -> float
        5. 键值对 -> int->int
        6. 二维数组（分号分隔） -> int[][]
        7. 一维数组（逗号分隔） -> int[]
        8. 默认 -> string
        """
        if not value or not value.strip():
            return "string"

        value = value.strip()

        # 布尔值
        if value.lower() in ("true", "false", "yes", "no"):
            return "bool"

        # 键值对格式（map类型）
        if ":" in value and "," in value:
            return cls._infer_map_type(value)

        # 二维数组（分号分隔多行）
        if ";" in value:
            return cls._infer_array2d_type(value)

        # 一维数组（逗号分隔）
        if "," in value:
            return cls._infer_array_type(value)

        # 长整数（带L后缀）
        if value.endswith("L") or value.endswith("l"):
            try:
                int(value[:-1])
                return "long"
            except ValueError:
                pass

        # 浮点数
        if "." in value:
            try:
                float(value)
                return "float"
            except ValueError:
                pass

        # 整数
        try:
            int(value)
            return "int"
        except ValueError:
            pass

        # 默认字符串
        return "string"

    @classmethod
    def _infer_array_type(cls, value: str) -> str:
        """推断数组元素类型"""
        elements = [e.strip() for e in value.split(",")]

        # 尝试推断元素类型
        element_types = set()
        for elem in elements:
            if not elem:
                continue

            # 整数
            try:
                int(elem)
                element_types.add("int")
                continue
            except ValueError:
                pass

            # 浮点数
            if "." in elem:
                try:
                    float(elem)
                    element_types.add("float")
                    continue
                except ValueError:
                    pass

            # 默认字符串
            element_types.add("string")

        # 确定元素类型，返回 T[] 格式
        if "string" in element_types:
            return "string[]"
        elif "float" in element_types:
            return "float[]"
        elif "int" in element_types:
            return "int[]"
        else:
            return "string[]"

    @classmethod
    def _infer_array2d_type(cls, value: str) -> str:
        """推断二维数组元素类型"""
        rows = [r.strip() for r in value.split(";")]

        # 收集所有元素的类型
        element_types = set()
        for row in rows:
            if not row:
                continue
            elements = [e.strip() for e in row.split(",")]
            for elem in elements:
                if not elem:
                    continue

                # 整数
                try:
                    int(elem)
                    element_types.add("int")
                    continue
                except ValueError:
                    pass

                # 浮点数
                if "." in elem:
                    try:
                        float(elem)
                        element_types.add("float")
                        continue
                    except ValueError:
                        pass

                # 默认字符串
                element_types.add("string")

        # 确定元素类型，返回 T[][] 格式
        if "string" in element_types:
            return "string[][]"
        elif "float" in element_types:
            return "float[][]"
        elif "int" in element_types:
            return "int[][]"
        else:
            return "string[][]"

    @classmethod
    def _infer_map_type(cls, value: str) -> str:
        """推断map的键值类型"""
        pairs = [p.strip() for p in value.split(",")]

        key_types = set()
        value_types = set()

        for pair in pairs:
            if ":" not in pair:
                continue

            key, val = pair.split(":", 1)
            key = key.strip()
            val = val.strip()

            # 推断键类型
            try:
                int(key)
                key_types.add("int")
            except ValueError:
                key_types.add("string")

            # 推断值类型
            try:
                int(val)
                value_types.add("int")
            except ValueError:
                if "." in val:
                    try:
                        float(val)
                        value_types.add("float")
                    except ValueError:
                        value_types.add("string")
                else:
                    value_types.add("string")

        # 确定类型，返回 K->V 格式
        key_type = "string" if "string" in key_types else "int"
        value_type = "string" if "string" in value_types else (
            "float" if "float" in value_types else "int"
        )

        return f"{key_type}->{value_type}"
```

##### 二进制写入器 (writer/binary_writer.py)

```python
import struct
from typing import Any, BinaryIO

class BinaryWriter:
    """二进制数据写入器"""

    # 魔数
    MAGIC = b'SFGC'
    VERSION = 1

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.string_table: Dict[str, int] = {}  # 字符串去重
        self.string_list: List[str] = []

    def write_table(self, schema: TableSchema, rows: List[Dict], target: str):
        """写入整个配置表"""
        with open(self.file_path, 'wb') as f:
            self._write_header(f, len(rows))
            self._write_column_defs(f, schema, target)
            self._collect_strings(rows, schema, target)
            self._write_string_table(f)
            self._write_data_rows(f, schema, rows, target)

    def _write_header(self, f: BinaryIO, row_count: int):
        """写入文件头"""
        f.write(self.MAGIC)                           # 4 bytes
        f.write(struct.pack('<H', self.VERSION))      # 2 bytes
        f.write(struct.pack('<H', 0))                 # 2 bytes flags
        f.write(struct.pack('<I', row_count))         # 4 bytes
        f.write(struct.pack('<I', 0))                 # 4 bytes (占位，后续回填)

    def write_int32(self, f: BinaryIO, value: int):
        f.write(struct.pack('<i', value))

    def write_float(self, f: BinaryIO, value: float):
        f.write(struct.pack('<f', value))

    def write_string(self, f: BinaryIO, value: str):
        """写入字符串索引"""
        if value not in self.string_table:
            self.string_table[value] = len(self.string_list)
            self.string_list.append(value)
        f.write(struct.pack('<I', self.string_table[value]))
```

#### 3.1.3 CLI 设计 (cli.py)

```python
import click
from pathlib import Path

@click.group()
def cli():
    """SheetForge - 游戏配置工具"""
    pass

@cli.command()
@click.option('-i', '--input', required=True, help='输入文件或目录')
@click.option('-o', '--output', required=True, help='输出目录')
@click.option('-t', '--target', type=click.Choice(['client', 'server', 'all']),
              default='all', help='目标平台')
@click.option('-c', '--config', help='配置文件路径')
@click.option('--code-output', help='代码输出目录（默认与output相同）')
@click.option('--data-output', help='数据输出目录（默认与output相同）')
@click.option('-v', '--verbose', is_flag=True, help='详细输出')
def generate(input: str, output: str, target: str, config: str,
             code_output: str, data_output: str, verbose: bool):
    """生成配置代码和数据文件"""
    # 实现细节...
    pass

@cli.command()
@click.argument('input', type=click.Path(exists=True))
def validate(input: str):
    """校验配置文件"""
    # 实现细节...
    pass

@cli.command()
def init():
    """初始化配置文件"""
    # 实现细节...
    pass

if __name__ == '__main__':
    cli()
```

### 3.2 C# 运行时模块

#### 3.2.1 目录结构

```
SheetForge.Runtime/
├── SheetForge.Runtime.csproj
├── SheetReader.cs           # 二进制读取器
├── TableBase.cs             # 配置表基类
├── Exceptions.cs            # 异常定义
└── Properties/
    └── AssemblyInfo.cs
```

#### 3.2.2 核心类设计

##### SheetReader (SheetReader.cs)

```csharp
using System;
using System.IO;
using System.Text;

namespace SheetForge
{
    /// <summary>
    /// 配置表二进制读取器
    /// </summary>
    public class SheetReader : IDisposable
    {
        private readonly BinaryReader _reader;
        private readonly StringTable _stringTable;

        // 文件头常量
        private static readonly byte[] Magic = { (byte)'S', (byte)'F', (byte)'G', (byte)'C' };
        private const ushort CurrentVersion = 1;

        public int RowCount { get; private set; }
        public ushort Version { get; private set; }

        public SheetReader(string filePath)
        {
            var stream = File.OpenRead(filePath);
            _reader = new BinaryReader(stream);
            _stringTable = new StringTable();

            ReadHeader();
            ReadStringTable();
        }

        private void ReadHeader()
        {
            // 校验魔数
            var magic = _reader.ReadBytes(4);
            if (!magic.SequenceEqual(Magic))
                throw new InvalidDataException("Invalid file format: magic mismatch");

            Version = _reader.ReadUInt16();
            if (Version > CurrentVersion)
                throw new InvalidDataException($"Unsupported version: {Version}");

            _reader.ReadUInt16();  // flags, reserved
            RowCount = _reader.ReadInt32();
            _reader.ReadUInt32();  // string table offset, will use later
        }

        private void ReadStringTable()
        {
            // 读取字符串表
            // 实现细节...
        }

        public int ReadInt32() => _reader.ReadInt32();
        public long ReadInt64() => _reader.ReadInt64();
        public float ReadFloat() => _reader.ReadSingle();
        public double ReadDouble() => _reader.ReadDouble();
        public bool ReadBool() => _reader.ReadBoolean();

        public string ReadString()
        {
            var index = _reader.ReadUInt32();
            return _stringTable[index];
        }

        public int[] ReadIntArray()
        {
            var count = _reader.ReadInt32();
            var result = new int[count];
            for (int i = 0; i < count; i++)
                result[i] = _reader.ReadInt32();
            return result;
        }

        public void Dispose()
        {
            _reader?.Dispose();
        }
    }
}
```

##### TableBase (TableBase.cs)

```csharp
using System.Collections.Generic;

namespace SheetForge
{
    /// <summary>
    /// 配置表基类
    /// </summary>
    public abstract class TableBase
    {
        /// <summary>
        /// 配置表名称
        /// </summary>
        public abstract string TableName { get; }

        /// <summary>
        /// 数据加载时间(ms)
        /// </summary>
        public long LoadTimeMs { get; protected set; }

        /// <summary>
        /// 从文件加载
        /// </summary>
        public abstract void Load(string filePath);
    }

    /// <summary>
    /// 泛型配置表基类
    /// </summary>
    public abstract class TableBase<T> : TableBase where T : class
    {
        protected readonly Dictionary<int, T> _items = new();
        protected readonly List<T> _itemList = new();

        /// <summary>
        /// 配置项数量
        /// </summary>
        public int Count => _items.Count;

        /// <summary>
        /// 通过ID获取配置项
        /// </summary>
        public T Get(int id)
        {
            _items.TryGetValue(id, out var item);
            return item;
        }

        /// <summary>
        /// 尝试获取配置项
        /// </summary>
        public bool TryGet(int id, out T item)
        {
            return _items.TryGetValue(id, out item);
        }

        /// <summary>
        /// 检查ID是否存在
        /// </summary>
        public bool Contains(int id) => _items.ContainsKey(id);

        /// <summary>
        /// 获取所有配置项
        /// </summary>
        public IReadOnlyList<T> GetAll() => _itemList;

        /// <summary>
        /// 遍历所有配置项
        /// </summary>
        public IEnumerable<T> Enumerate() => _itemList;
    }
}
```

##### StringTable (StringTable.cs)

```csharp
using System.Collections.Generic;

namespace SheetForge
{
    /// <summary>
    /// 字符串表，用于字符串去重和索引访问
    /// </summary>
    internal class StringTable
    {
        private readonly List<string> _strings = new();
        private readonly Dictionary<uint, string> _cache = new();

        public string this[uint index]
        {
            get
            {
                if (_cache.TryGetValue(index, out var str))
                    return str;

                if (index < _strings.Count)
                    return _strings[(int)index];

                throw new KeyNotFoundException($"String index not found: {index}");
            }
        }

        public void Add(string value)
        {
            _strings.Add(value);
        }

        public void Clear()
        {
            _strings.Clear();
            _cache.Clear();
        }
    }
}
```

### 3.3 Python 运行时模块

#### 3.3.1 目录结构

```
sheetforge_runtime/
├── __init__.py              # 包入口，导出公共API
├── reader.py                # 二进制读取器
├── table_base.py            # 配置表基类
├── exceptions.py            # 异常定义
└── py.typed                 # PEP 561 类型标记
```

#### 3.3.2 核心类设计

##### SheetReader (reader.py)

```python
"""
配置表二进制读取器
"""
import struct
from typing import Dict, List, BinaryIO, Optional


class SheetReader:
    """配置表二进制读取器"""

    MAGIC = b'SFGC'
    CURRENT_VERSION = 1

    def __init__(self, file_path: str):
        self._file: BinaryIO = open(file_path, 'rb')
        self._string_table: Dict[int, str] = {}
        self.row_count: int = 0
        self.version: int = 0

        self._read_header()
        self._read_string_table()

    def _read_header(self) -> None:
        """读取文件头"""
        magic = self._file.read(4)
        if magic != self.MAGIC:
            raise ValueError(f"Invalid file format: magic mismatch, got {magic}")

        self.version = struct.unpack('<H', self._file.read(2))[0]
        if self.version > self.CURRENT_VERSION:
            raise ValueError(f"Unsupported version: {self.version}")

        self._file.read(2)  # flags, reserved
        self.row_count = struct.unpack('<I', self._file.read(4))[0]
        self._string_table_offset = struct.unpack('<I', self._file.read(4))[0]

    def _read_string_table(self) -> None:
        """读取字符串表"""
        # 保存当前位置
        current_pos = self._file.tell()

        # 跳转到字符串表
        self._file.seek(self._string_table_offset)

        # 读取字符串数量
        string_count = struct.unpack('<I', self._file.read(4))[0]

        # 读取所有字符串
        for i in range(string_count):
            length = struct.unpack('<H', self._file.read(2))[0]
            data = self._file.read(length)
            self._string_table[i] = data.decode('utf-8')

        # 返回原位置
        self._file.seek(current_pos)

    def read_int32(self) -> int:
        """读取32位整数"""
        return struct.unpack('<i', self._file.read(4))[0]

    def read_int64(self) -> int:
        """读取64位整数"""
        return struct.unpack('<q', self._file.read(8))[0]

    def read_float(self) -> float:
        """读取单精度浮点"""
        return struct.unpack('<f', self._file.read(4))[0]

    def read_double(self) -> float:
        """读取双精度浮点"""
        return struct.unpack('<d', self._file.read(8))[0]

    def read_bool(self) -> bool:
        """读取布尔值"""
        return struct.unpack('?', self._file.read(1))[0]

    def read_string(self) -> str:
        """读取字符串（从字符串表索引）"""
        index = struct.unpack('<I', self._file.read(4))[0]
        return self._string_table.get(index, "")

    def read_int32_list(self) -> List[int]:
        """读取整数列表"""
        count = struct.unpack('<I', self._file.read(4))[0]
        return [self.read_int32() for _ in range(count)]

    def read_string_list(self) -> List[str]:
        """读取字符串列表"""
        count = struct.unpack('<I', self._file.read(4))[0]
        return [self.read_string() for _ in range(count)]

    def close(self) -> None:
        """关闭文件"""
        if self._file:
            self._file.close()
            self._file = None

    def __enter__(self) -> 'SheetReader':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
```

##### TableBase (table_base.py)

```python
"""
配置表基类
"""
from typing import TypeVar, Generic, Dict, List, Optional, Iterator, ABC, abstractmethod

T = TypeVar('T')


class TableBase(Generic[T], ABC):
    """配置表基类"""

    def __init__(self):
        self._items: Dict[int, T] = {}
        self._item_list: List[T] = []
        self._load_time_ms: float = 0.0

    @property
    @abstractmethod
    def table_name(self) -> str:
        """配置表名称"""
        pass

    @property
    def count(self) -> int:
        """配置项数量"""
        return len(self._items)

    @property
    def load_time_ms(self) -> float:
        """加载耗时（毫秒）"""
        return self._load_time_ms

    def get(self, id: int) -> Optional[T]:
        """通过ID获取配置项"""
        return self._items.get(id)

    def try_get(self, id: int) -> tuple[bool, Optional[T]]:
        """尝试获取配置项，返回(是否成功, 配置项)"""
        item = self._items.get(id)
        return (item is not None, item)

    def contains(self, id: int) -> bool:
        """检查ID是否存在"""
        return id in self._items

    def get_all(self) -> List[T]:
        """获取所有配置项（返回副本）"""
        return self._item_list.copy()

    def __iter__(self) -> Iterator[T]:
        """迭代所有配置项"""
        return iter(self._item_list)

    def __len__(self) -> int:
        """配置项数量"""
        return len(self._items)

    def __getitem__(self, id: int) -> T:
        """通过索引获取配置项，不存在则抛出KeyError"""
        return self._items[id]

    @abstractmethod
    def load(self, file_path: str) -> None:
        """从文件加载配置表"""
        pass

    @classmethod
    @abstractmethod
    def load_from(cls, file_path: str) -> 'TableBase[T]':
        """从文件加载并返回新实例"""
        pass
```

##### Exceptions (exceptions.py)

```python
"""
SheetForge 异常定义
"""


class SheetForgeError(Exception):
    """SheetForge 基础异常"""
    pass


class DataLoadError(SheetForgeError):
    """数据加载错误"""

    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        super().__init__(f"Failed to load '{file_path}': {message}")


class InvalidDataFormatError(SheetForgeError):
    """无效数据格式错误"""

    def __init__(self, message: str):
        super().__init__(f"Invalid data format: {message}")


class StringTableError(SheetForgeError):
    """字符串表错误"""

    def __init__(self, index: int):
        super().__init__(f"String index not found: {index}")
        self.index = index
```

##### Package Init (__init__.py)

```python
"""
SheetForge Runtime - Python 运行时库

用于加载和解析 .sfc 配置文件
"""

from .reader import SheetReader
from .table_base import TableBase
from .exceptions import (
    SheetForgeError,
    DataLoadError,
    InvalidDataFormatError,
    StringTableError,
)

__all__ = [
    'SheetReader',
    'TableBase',
    'SheetForgeError',
    'DataLoadError',
    'InvalidDataFormatError',
    'StringTableError',
]

__version__ = '1.0.0'
```

### 3.4 多语言代码生成器设计

#### 3.4.1 生成器基类 (generator/base.py)

```python
"""
代码生成器基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List
from pathlib import Path

from ..models.schema import TableSchema, Column, Tag


@dataclass
class NamingConvention:
    """命名规范"""
    class_name_prefix: str = ""      # 类名前缀，如 "Tb"
    class_name_suffix: str = ""       # 类名后缀，如 "Table"
    property_case: str = "pascal"     # 属性命名：pascal, snake, camel


class BaseGenerator(ABC):
    """代码生成器基类"""

    def __init__(self, template_dir: Path = None):
        self.template_dir = template_dir

    @abstractmethod
    def generate_item_class(
        self,
        schema: TableSchema,
        target: str = "all"
    ) -> str:
        """生成配置项类代码"""
        pass

    @abstractmethod
    def generate_table_class(
        self,
        schema: TableSchema,
        target: str = "all"
    ) -> str:
        """生成配置表类代码"""
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        pass

    @abstractmethod
    def get_type_mapping(self) -> Dict[str, str]:
        """获取类型映射表"""
        pass

    @abstractmethod
    def get_naming_convention(self) -> NamingConvention:
        """获取命名规范"""
        pass

    def filter_columns(self, schema: TableSchema, target: str) -> List[Column]:
        """根据目标过滤列"""
        if target == "client":
            return schema.client_columns
        elif target == "server":
            return schema.server_columns
        else:
            return [c for c in schema.columns if c.tag != Tag.IGNORE]

    def convert_property_name(self, name: str) -> str:
        """根据命名规范转换属性名"""
        convention = self.get_naming_convention()

        if convention.property_case == "snake":
            # PascalCase -> snake_case
            return self._to_snake_case(name)
        elif convention.property_case == "camel":
            # PascalCase -> camelCase
            return self._to_camel_case(name)
        else:
            # 保持 PascalCase
            return name

    def _to_snake_case(self, name: str) -> str:
        """转换为 snake_case"""
        import re
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    def _to_camel_case(self, name: str) -> str:
        """转换为 camelCase"""
        return name[0].lower() + name[1:] if name else name
```

#### 3.4.2 C# 生成器 (generator/csharp_generator.py)

```python
"""
C# 代码生成器
"""
from typing import Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .base import BaseGenerator, NamingConvention
from ..models.schema import TableSchema


class CSharpGenerator(BaseGenerator):
    """C# 代码生成器"""

    # 基础类型映射
    BASE_TYPE_MAPPING = {
        "int": "int",
        "long": "long",
        "float": "float",
        "double": "double",
        "bool": "bool",
        "string": "string",
    }

    # 基础类型读取方法
    BASE_READ_METHOD = {
        "int": "ReadInt32",
        "long": "ReadInt64",
        "float": "ReadFloat",
        "double": "ReadDouble",
        "bool": "ReadBool",
        "string": "ReadString",
    }

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates" / "csharp"

        super().__init__(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def parse_type(self, type_str: str) -> tuple[str, str]:
        """
        解析类型字符串，返回 (C#类型, 读取方法)

        支持的类型格式：
        - 基础类型: int, string, float, ...
        - 一维数组: int[], string[], ...
        - 二维数组: int[][], string[][], ...
        - 集合: set<int>, set<string>, ...
        - 字典: int->int, string->int, ...
        """
        type_str = type_str.strip()

        # 二维数组类型: T[][]
        if type_str.endswith("[][]"):
            element_type = type_str[:-4].strip()
            cs_elem = self.BASE_TYPE_MAPPING.get(element_type, "object")
            read_elem = self.BASE_READ_METHOD.get(element_type, "ReadObject")
            return (
                f"{cs_elem}[][]",
                f"Read{read_elem.replace('Read', '')}Array2D"
            )

        # 一维数组类型: T[]
        if type_str.endswith("[]"):
            element_type = type_str[:-2].strip()
            cs_elem = self.BASE_TYPE_MAPPING.get(element_type, "object")
            read_elem = self.BASE_READ_METHOD.get(element_type, "ReadObject")
            return (
                f"{cs_elem}[]",
                f"Read{read_elem.replace('Read', '')}Array"
            )

        # 集合类型: set<T>
        if type_str.startswith("set<") and type_str.endswith(">"):
            element_type = type_str[4:-1].strip()
            cs_elem = self.BASE_TYPE_MAPPING.get(element_type, "object")
            read_elem = self.BASE_READ_METHOD.get(element_type, "ReadObject")
            return (
                f"HashSet<{cs_elem}>",
                f"Read{read_elem.replace('Read', '')}HashSet"
            )

        # 字典类型: K->V
        if "->" in type_str:
            parts = type_str.split("->")
            if len(parts) == 2:
                key_type = parts[0].strip()
                value_type = parts[1].strip()
                cs_key = self.BASE_TYPE_MAPPING.get(key_type, "object")
                cs_value = self.BASE_TYPE_MAPPING.get(value_type, "object")
                read_key = self.BASE_READ_METHOD.get(key_type, "ReadObject")
                read_value = self.BASE_READ_METHOD.get(value_type, "ReadObject")
                return (
                    f"Dictionary<{cs_key}, {cs_value}>",
                    f"Read{read_key.replace('Read', '')}{read_value.replace('Read', '')}Dictionary"
                )

        # 基础类型
        return (
            self.BASE_TYPE_MAPPING.get(type_str, "object"),
            self.BASE_READ_METHOD.get(type_str, "ReadObject")
        )
            cs_key = self.BASE_TYPE_MAPPING.get(key_type, "object")
            cs_value = self.BASE_TYPE_MAPPING.get(value_type, "object")
            read_key = self.BASE_READ_METHOD.get(key_type, "ReadObject")
            read_value = self.BASE_READ_METHOD.get(value_type, "ReadObject")
            return (
                f"Dictionary<{cs_key}, {cs_value}>",
                f"Read{read_key.replace('Read', '')}{read_value.replace('Read', '')}Dictionary"
            )

        return ("object", "ReadObject")

    def generate_item_class(self, schema: TableSchema, target: str = "all") -> str:
        columns = self.filter_columns(schema, target)
        template = self.env.get_template("item.cs.jinja2")

        # 准备列数据
        columns_data = []
        for col in columns:
            cs_type, read_method = self.parse_type(col.data_type)
            columns_data.append({
                "name": col.name,
                "description": col.description,
                "csharp_type": cs_type,
                "read_method": read_method,
            })

        return template.render(
            class_name=f"Tb{schema.name}",
            columns=columns_data,
            table_name=schema.name,
            namespace="GameConfig",
        )

    def generate_table_class(self, schema: TableSchema, target: str = "all") -> str:
        columns = self.filter_columns(schema, target)
        template = self.env.get_template("table.cs.jinja2")

        return template.render(
            class_name=f"Tb{schema.name}",
            table_name=schema.name,
            namespace="GameConfig",
        )

    def get_file_extension(self) -> str:
        return ".cs"

    def get_type_mapping(self) -> Dict[str, str]:
        return self.TYPE_MAPPING

    def get_naming_convention(self) -> NamingConvention:
        return NamingConvention(
            class_name_prefix="Tb",
            class_name_suffix="Table",
            property_case="pascal"
        )
```

#### 3.4.3 Python 生成器 (generator/python_generator.py)

```python
"""
Python 代码生成器
"""
from typing import Dict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from .base import BaseGenerator, NamingConvention
from ..models.schema import TableSchema, Column


class PythonGenerator(BaseGenerator):
    """Python 代码生成器"""

    # 基础类型映射
    BASE_TYPE_MAPPING = {
        "int": "int",
        "long": "int",
        "float": "float",
        "double": "float",
        "bool": "bool",
        "string": "str",
    }

    # 基础类型读取方法
    BASE_READ_METHOD = {
        "int": "read_int32",
        "long": "read_int64",
        "float": "read_float",
        "double": "read_double",
        "bool": "read_bool",
        "string": "read_string",
    }

    def __init__(self, template_dir: Path = None):
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates" / "python"

        super().__init__(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def parse_type(self, type_str: str) -> tuple[str, str]:
        """
        解析类型字符串，返回 (Python类型, 读取方法)

        支持的类型格式：
        - 基础类型: int, string, float, ...
        - 一维数组: int[], string[], ...
        - 二维数组: int[][], string[][], ...
        - 集合: set<int>, set<string>, ...
        - 字典: int->int, string->int, ...
        """
        type_str = type_str.strip()

        # 二维数组类型: T[][]
        if type_str.endswith("[][]"):
            element_type = type_str[:-4].strip()
            py_elem = self.BASE_TYPE_MAPPING.get(element_type, "Any")
            return (
                f"List[List[{py_elem}]]",
                f"read_{py_elem}_array2d"
            )

        # 一维数组类型: T[]
        if type_str.endswith("[]"):
            element_type = type_str[:-2].strip()
            py_elem = self.BASE_TYPE_MAPPING.get(element_type, "Any")
            return (
                f"List[{py_elem}]",
                f"read_{py_elem}_array"
            )

        # 集合类型: set<T>
        if type_str.startswith("set<") and type_str.endswith(">"):
            element_type = type_str[4:-1].strip()
            py_elem = self.BASE_TYPE_MAPPING.get(element_type, "Any")
            return (
                f"set[{py_elem}]",
                f"read_{py_elem}_set"
            )

        # 字典类型: K->V
        if "->" in type_str:
            parts = type_str.split("->")
            if len(parts) == 2:
                key_type = parts[0].strip()
                value_type = parts[1].strip()
                py_key = self.BASE_TYPE_MAPPING.get(key_type, "Any")
                py_value = self.BASE_TYPE_MAPPING.get(value_type, "Any")
                return (
                    f"Dict[{py_key}, {py_value}]",
                    f"read_{py_key}_{py_value}_dict"
                )

        # 基础类型
        return (
            self.BASE_TYPE_MAPPING.get(type_str, "Any"),
            self.BASE_READ_METHOD.get(type_str, "read_object")
        )

    def generate_item_class(self, schema: TableSchema, target: str = "all") -> str:
        columns = self.filter_columns(schema, target)
        template = self.env.get_template("item.py.jinja2")

        # 准备列数据（转换为snake_case）
        columns_data = []
        for col in columns:
            python_name = self.convert_property_name(col.name)
            py_type, read_method = self.parse_type(col.data_type)
            columns_data.append({
                "name": python_name,
                "original_name": col.name,  # 用于读取时映射
                "description": col.description,
                "python_type": py_type,
                "read_method": read_method,
            })

        return template.render(
            class_name=f"Tb{schema.name}",
            columns=columns_data,
            table_name=schema.name,
            package="game_config",
        )

    def generate_table_class(self, schema: TableSchema, target: str = "all") -> str:
        columns = self.filter_columns(schema, target)
        template = self.env.get_template("table.py.jinja2")

        return template.render(
            class_name=f"Tb{schema.name}",
            table_name=schema.name,
            package="game_config",
        )

    def get_file_extension(self) -> str:
        return ".py"

    def get_naming_convention(self) -> NamingConvention:
        return NamingConvention(
            class_name_prefix="Tb",
            class_name_suffix="Table",
            property_case="snake"  # Python使用snake_case
        )
```

#### 3.4.4 生成器管理器 (generator/manager.py)

```python
"""
代码生成器管理器
"""
from typing import Dict, List, Type
from pathlib import Path

from .base import BaseGenerator
from .csharp_generator import CSharpGenerator
from .python_generator import PythonGenerator


class GeneratorManager:
    """代码生成器管理器"""

    # 注册的生成器
    _generators: Dict[str, Type[BaseGenerator]] = {
        "csharp": CSharpGenerator,
        "python": PythonGenerator,
        # 后续扩展：
        # "go": GoGenerator,
        # "typescript": TypeScriptGenerator,
        # "java": JavaGenerator,
    }

    @classmethod
    def register(cls, name: str, generator_class: Type[BaseGenerator]) -> None:
        """注册新的生成器"""
        cls._generators[name] = generator_class

    @classmethod
    def get_generator(cls, name: str) -> BaseGenerator:
        """获取生成器实例"""
        if name not in cls._generators:
            raise ValueError(f"Unknown generator: {name}. "
                           f"Available: {list(cls._generators.keys())}")
        return cls._generators[name]()

    @classmethod
    def get_available_languages(cls) -> List[str]:
        """获取所有支持的语言"""
        return list(cls._generators.keys())

    @classmethod
    def generate_for_languages(
        cls,
        schema: 'TableSchema',
        languages: List[str],
        target: str = "all",
        output_dir: Path = None
    ) -> Dict[str, Dict[str, str]]:
        """
        为多种语言生成代码

        Returns:
            Dict[str, Dict[str, str]]: {语言: {文件名: 代码内容}}
        """
        result = {}

        for lang in languages:
            generator = cls.get_generator(lang)
            ext = generator.get_file_extension()

            result[lang] = {
                f"tb_{schema.name.lower()}{ext}": generator.generate_item_class(schema, target),
                f"tb_{schema.name.lower()}_table{ext}": generator.generate_table_class(schema, target),
            }

        return result
```

---

## 4. 二进制文件格式规范

### 4.1 文件结构

```
┌─────────────────────────────────────────────────────┐
│                 File Header (16 bytes)              │
├─────────────────────────────────────────────────────┤
│                 Column Definitions                   │
├─────────────────────────────────────────────────────┤
│                 String Table                         │
├─────────────────────────────────────────────────────┤
│                 Data Rows                            │
└─────────────────────────────────────────────────────┘
```

### 4.2 详细格式定义

#### 4.2.1 文件头（16字节）

| 偏移 | 长度 | 字段 | 类型 | 说明 |
|------|------|------|------|------|
| 0 | 4 | magic | char[4] | 固定为 `SFGC` |
| 4 | 2 | version | uint16 | 格式版本，当前为 1 |
| 6 | 2 | flags | uint16 | 标志位，保留 |
| 8 | 4 | row_count | uint32 | 数据行数 |
| 12 | 4 | string_table_offset | uint32 | 字符串表偏移量 |

#### 4.2.2 列定义区域

```
┌────────────────────────────────────────┐
│ column_count (uint16)                  │
├────────────────────────────────────────┤
│ Column Def 1                           │
│   ├─ name_length (uint16)              │
│   ├─ name (utf-8 bytes)                │
│   ├─ data_type (uint8)                 │
│   └─ flags (uint8)                     │
├────────────────────────────────────────┤
│ Column Def 2                           │
│   └─ ...                               │
└────────────────────────────────────────┘
```

**数据类型编码**：

基础类型（0x00-0x0F）：

| 编码 | 类型 | C#类型 | Python类型 | 大小 |
|------|------|--------|------------|------|
| 0x00 | int32 | int | int | 4 bytes |
| 0x01 | int64 | long | int | 8 bytes |
| 0x02 | float32 | float | float | 4 bytes |
| 0x03 | float64 | double | float | 8 bytes |
| 0x04 | bool | bool | bool | 1 byte |
| 0x05 | string | string | str | 4 bytes (索引) |

容器类型（0x10-0x4F）：

| 编码 | 类型 | 格式 | 说明 |
|------|------|------|------|
| 0x10 | array | 0x10 + 元素类型 | 一维数组，元素类型为后4位 |
| 0x20 | array2d | 0x20 + 元素类型 | 二维数组，元素类型为后4位 |
| 0x30 | set | 0x30 + 元素类型 | 集合，元素类型为后4位 |
| 0x40 | map | 0x40 + 键类型, 值类型 | 字典，键值类型编码 |

**容器类型编码详解**：

```
容器类型字节 = (容器类型码 << 4) | 元素类型码

array,int    = 0x10 | 0x00 = 0x10
array,string = 0x10 | 0x05 = 0x15
array2d,int  = 0x20 | 0x00 = 0x20
array2d,string = 0x20 | 0x05 = 0x25
set,int      = 0x30 | 0x00 = 0x30
set,string   = 0x30 | 0x05 = 0x35

map 类型使用2字节编码：
字节1: 0x40 | 键类型
字节2: 值类型
例如 map,int,string = 0x40, 0x05
```

**容器数据存储格式**：

```
array 数据格式：
┌────────────────────────────────────────┐
│ count (uint32)                         │  元素数量
├────────────────────────────────────────┤
│ element_1                              │
│ element_2                              │
│ ...                                    │
└────────────────────────────────────────┘

array2d 数据格式：
┌────────────────────────────────────────┐
│ row_count (uint32)                     │  行数
├────────────────────────────────────────┤
│ Row 1                                  │
│   ├─ col_count (uint32)                │  列数
│   ├─ element_1                         │
│   ├─ element_2                         │
│   └─ ...                               │
├────────────────────────────────────────┤
│ Row 2                                  │
│   └─ ...                               │
└────────────────────────────────────────┘

set 数据格式：
┌────────────────────────────────────────┐
│ count (uint32)                         │  元素数量
├────────────────────────────────────────┤
│ element_1                              │
│ element_2                              │
│ ...                                    │  注：已去重
└────────────────────────────────────────┘

map 数据格式：
┌────────────────────────────────────────┐
│ count (uint32)                         │  键值对数量
├────────────────────────────────────────┤
│ key_1 | value_1                        │
│ key_2 | value_2                        │
│ ...                                    │
└────────────────────────────────────────┘
```

#### 4.2.3 字符串表

```
┌────────────────────────────────────────┐
│ string_count (uint32)                  │
├────────────────────────────────────────┤
│ String 1                               │
│   ├─ length (uint16)                   │
│   └─ utf8_bytes (length bytes)         │
├────────────────────────────────────────┤
│ String 2                               │
│   └─ ...                               │
└────────────────────────────────────────┘
```

#### 4.2.4 数据区域

按行存储，每行数据按列顺序连续排列：

```
┌────────────────────────────────────────┐
│ Row 1                                  │
│   ├─ col1_value (按类型大小)           │
│   ├─ col2_value                        │
│   └─ ...                               │
├────────────────────────────────────────┤
│ Row 2                                  │
│   └─ ...                               │
└────────────────────────────────────────┘
```

### 4.3 示例

假设有以下配置表：

| id | name | hp | atk |
|----|------|----|----|
| 1 | warrior | 100 | 20 |
| 2 | mage | 60 | 35 |

二进制文件内容（十六进制）：

```
# Header
53 46 47 43          # magic "SFGC"
01 00                # version 1
00 00                # flags
02 00 00 00          # row_count 2
XX XX XX XX          # string_table_offset

# Column Definitions
04 00                # column_count 4
02 00 69 64          # name: "id" (length=2)
00                   # type: int32
01                   # flags: is_id
04 00 6E 61 6D 65    # name: "name"
05                   # type: string
00                   # flags
... (其他列定义)

# String Table
02 00 00 00          # string_count 2
07 00                # length 7
77 61 72 72 69 6F 72 # "warrior"
04 00                # length 4
6D 61 67 65          # "mage"

# Data Rows
# Row 1
01 00 00 00          # id = 1
00 00 00 00          # name string index = 0
64 00 00 00          # hp = 100
14 00 00 00          # atk = 20

# Row 2
02 00 00 00          # id = 2
01 00 00 00          # name string index = 1
3C 00 00 00          # hp = 60
23 00 00 00          # atk = 35
```

---

## 5. 代码生成模板设计

### 5.1 配置项类模板 (item.cs.jinja2)

```jinja2
// ============================================================
// 由 SheetForge 自动生成，请勿手动修改
// 源文件: {{ table_name }}
// 生成时间: {{ generation_time }}
// ============================================================

using System;
using System.Collections.Generic;
using SheetForge;

namespace {{ namespace }}
{
    /// <summary>
    /// {{ table_name }} 配置项
    /// </summary>
    public partial class Tb{{ table_name }}
    {
        {% for column in columns %}
        /// <summary>
        /// {{ column.description }}
        /// </summary>
        public {{ column.csharp_type }} {{ column.name }} { get; private set; }
        {% endfor %}

        /// <summary>
        /// 从读取器加载配置项
        /// </summary>
        internal static Tb{{ table_name }} Load(SheetReader reader)
        {
            var item = new Tb{{ table_name }}();
            {% for column in columns %}
            item.{{ column.name }} = reader.Read{{ column.read_method }}();
            {% endfor %}
            return item;
        }

        private Tb{{ table_name }}() { }
    }
}
```

### 5.2 配置表类模板 (table.cs.jinja2)

```jinja2
// ============================================================
// 由 SheetForge 自动生成，请勿手动修改
// 源文件: {{ table_name }}
// 生成时间: {{ generation_time }}
// ============================================================

using System;
using System.Collections.Generic;
using SheetForge;

namespace {{ namespace }}
{
    /// <summary>
    /// {{ table_name }} 配置表
    /// </summary>
    public partial class Tb{{ table_name }}Table : TableBase<Tb{{ table_name }}>
    {
        public override string TableName => "{{ table_name }}";

        /// <summary>
        /// 从文件加载配置表
        /// </summary>
        public override void Load(string filePath)
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();

            using var reader = new SheetReader(filePath);

            _items.Clear();
            _itemList.Clear();

            for (int i = 0; i < reader.RowCount; i++)
            {
                var item = Tb{{ table_name }}.Load(reader);
                _items[item.Id] = item;
                _itemList.Add(item);
            }

            sw.Stop();
            LoadTimeMs = sw.ElapsedMilliseconds;
        }

        /// <summary>
        /// 静态加载方法
        /// </summary>
        public static Tb{{ table_name }}Table LoadFromFile(string filePath)
        {
            var table = new Tb{{ table_name }}Table();
            table.Load(filePath);
            return table;
        }
    }
}
```

---

## 6. 配置文件格式

### 6.1 sheetforge.yaml

```yaml
# SheetForge 配置文件

# 输入配置
input:
  paths:
    - ./config/**/*.xlsx
    - ./config/**/*.tsv
    - ./config/**/*.csv
  exclude:
    - ./config/~*     # 排除临时文件
    - ./config/.~*    # 排除Excel临时文件

# 输出配置
output:
  client:
    code: ./output/client/Config
    data: ./output/client/Data
  server:
    code: ./output/server/Config
    data: ./output/server/Data

# 代码生成配置
code:
  namespace: GameConfig
  indent: spaces      # spaces | tabs
  indent_size: 4
  newline: lf         # lf | crlf
  partial_class: true

# 数据类型映射
types:
  # 自定义类型映射
  custom_types: []

# 校验配置
validation:
  check_duplicate_id: true
  check_empty_required: true
  check_type_mismatch: true

# 日志配置
logging:
  level: info         # debug | info | warning | error
  color: true
```

---

## 7. 错误处理设计

### 7.1 Python 端错误类型

```python
# exceptions.py

class SheetForgeError(Exception):
    """SheetForge 基础异常"""
    pass

class ParseError(SheetForgeError):
    """解析错误"""
    def __init__(self, file_path: str, row: int, col: int, message: str):
        self.file_path = file_path
        self.row = row
        self.col = col
        super().__init__(f"[{file_path}] Row {row}, Col {col}: {message}")

class ValidationError(SheetForgeError):
    """校验错误"""
    def __init__(self, file_path: str, row: int, message: str):
        self.file_path = file_path
        self.row = row
        super().__init__(f"[{file_path}] Row {row}: {message}")

class DuplicateIdError(ValidationError):
    """ID重复错误"""
    def __init__(self, file_path: str, row: int, id_value: int, first_row: int):
        super().__init__(
            file_path, row,
            f"Duplicate ID '{id_value}', first defined at row {first_row}"
        )

class TypeMismatchError(ValidationError):
    """类型不匹配错误"""
    def __init__(self, file_path: str, row: int, col_name: str,
                 expected: str, actual: str):
        super().__init__(
            file_path, row,
            f"Type mismatch in column '{col_name}': expected {expected}, got {actual}"
        )
```

### 7.2 C# 端异常

```csharp
// Exceptions.cs
namespace SheetForge
{
    public class SheetForgeException : Exception
    {
        public string TableName { get; }

        public SheetForgeException(string message) : base(message) { }
        public SheetForgeException(string tableName, string message)
            : base($"[{tableName}] {message}")
        {
            TableName = tableName;
        }
    }

    public class DataLoadException : SheetForgeException
    {
        public string FilePath { get; }

        public DataLoadException(string filePath, string message)
            : base($"Failed to load '{filePath}': {message}")
        {
            FilePath = filePath;
        }
    }

    public class InvalidDataFormatException : SheetForgeException
    {
        public InvalidDataFormatException(string message) : base(message) { }
    }
}
```

---

## 8. 性能考量

### 8.1 内存优化

- **字符串去重**：相同字符串只存储一次，通过索引引用
- **按列存储**：同类数据连续存放，提高缓存命中率
- **延迟加载**：大表可考虑分块加载（后续迭代）

### 8.2 加载性能目标

| 数据规模 | 目标加载时间 |
|----------|--------------|
| 1000 行 | < 10ms |
| 10000 行 | < 50ms |
| 100000 行 | < 200ms |

### 8.3 文件体积对比

| 格式 | 相对体积 |
|------|----------|
| JSON | 100% (基准) |
| CSV | ~70% |
| MessagePack | ~45% |
| SheetForge Binary | ~40% |

---

## 9. 测试策略

### 9.1 单元测试

```python
# tests/test_parser.py

def test_parse_xlsx_header():
    """测试Excel文件头解析"""
    parser = ExcelParser("tests/data/simple.xlsx")
    schema, _ = parser.parse()

    assert schema.name == "simple"
    assert len(schema.columns) == 4
    assert schema.columns[0].name == "id"
    assert schema.columns[0].is_id == True

def test_tag_parsing():
    """测试标记解析"""
    parser = ExcelParser("tests/data/tags.xlsx")
    schema, _ = parser.parse()

    assert schema.client_columns == 3
    assert schema.server_columns == 4
```

### 9.2 集成测试

```python
# tests/test_end_to_end.py

def test_generate_and_load():
    """端到端测试：生成 -> 加载"""
    # 1. 生成代码和数据
    result = runner.invoke(cli, [
        'generate', '-i', 'tests/data', '-o', 'tests/output', '-t', 'client'
    ])
    assert result.exit_code == 0

    # 2. 编译C#代码
    # 3. 运行加载测试
    # 4. 验证数据正确
```

---

## 10. 开发里程碑

### Phase 1: 核心功能（3周）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| Python项目骨架搭建 | 1天 | P0 |
| TSV/CSV解析器 | 2天 | P0 |
| 表结构模型 | 1天 | P0 |
| 二进制写入器 | 2天 | P0 |
| C#代码生成器 | 2天 | P0 |
| C#运行时库 | 2天 | P0 |
| Python代码生成器 | 2天 | P0 |
| Python运行时库 | 1天 | P0 |
| CLI基础命令 | 1天 | P0 |
| 单元测试 | 2天 | P1 |

### Phase 2: 功能增强（2周）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| Excel解析器 | 2天 | P0 |
| 数据校验器 | 2天 | P1 |
| 配置文件支持 | 1天 | P1 |
| 数组类型支持 | 2天 | P1 |
| 错误报告优化 | 1天 | P1 |
| 集成测试 | 2天 | P1 |

### Phase 3: 生产优化（1周）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| PyInstaller打包 | 1天 | P2 |
| 性能优化 | 1天 | P2 |
| 文档完善 | 1天 | P2 |
| 示例项目（Unity/Python） | 2天 | P2 |

### Phase 4: 多语言扩展（按需）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| Go代码生成器 | 2天 | P1 |
| Go运行时库 | 2天 | P1 |
| TypeScript代码生成器 | 2天 | P2 |
| TypeScript运行时库 | 2天 | P2 |
| Java代码生成器 | 2天 | P3 |
| Java运行时库 | 2天 | P3 |
| C++代码生成器 | 3天 | P3 |
| C++运行时库 | 3天 | P3 |

---

## 附录 A: 命名规范

### A.1 Python 工具代码规范

- 文件名：`snake_case.py`
- 类名：`PascalCase`
- 函数/方法：`snake_case`
- 常量：`UPPER_SNAKE_CASE`
- 私有成员：`_leading_underscore`

### A.2 C# 运行时代码规范

- 文件名：与主类名一致 `PascalCase`
- 类名：`PascalCase`
- 属性：`PascalCase`
- 方法：`PascalCase`
- 私有字段：`_camelCase`
- 常量：`PascalCase`

### A.3 Python 运行时代码规范

- 文件名：`snake_case.py`
- 类名：`PascalCase`（配置项类保持一致性）
- 属性：`snake_case`
- 方法：`snake_case`
- 私有属性：`_snake_case`

### A.4 配置表命名（跨语言统一）

| 类型 | 规范 | C# 示例 | Python 示例 |
|------|------|---------|-------------|
| 源文件 | snake_case | `item_config.xlsx` | `item_config.xlsx` |
| 配置项类 | Tb + PascalCase | `TbItem` | `TbItem` |
| 配置表类 | Tb + PascalCase + Table | `TbItemTable` | `TbItemTable` |
| 数据文件 | snake_case + .sfc | `item_config.sfc` | `item_config.sfc` |
| 属性名 | 语言惯例 | `MaxHp` | `max_hp` |

### A.5 多语言命名规范对比

| 语言 | 类名 | 属性名 | 方法名 | 文件名 |
|------|------|--------|--------|--------|
| C# | PascalCase | PascalCase | PascalCase | PascalCase.cs |
| Python | PascalCase | snake_case | snake_case | snake_case.py |
| Go | PascalCase | PascalCase | PascalCase | snake_case.go |
| TypeScript | PascalCase | camelCase | camelCase | kebab-case.ts |

---

## 附录 B: 类型映射表

### B.1 基础类型映射

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| int | int | int | int32 | number |
| long | long | int | int64 | number |
| float | float | float | float32 | number |
| double | double | float | float64 | number |
| bool | bool | bool | bool | boolean |
| string | string | str | string | string |

### B.2 容器类型映射

#### 一维数组 (array)

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int[]` | `int[]` | `List[int]` | `[]int32` | `number[]` |
| `long[]` | `long[]` | `List[int]` | `[]int64` | `number[]` |
| `float[]` | `float[]` | `List[float]` | `[]float32` | `number[]` |
| `double[]` | `double[]` | `List[float]` | `[]float64` | `number[]` |
| `bool[]` | `bool[]` | `List[bool]` | `[]bool` | `boolean[]` |
| `string[]` | `string[]` | `List[str]` | `[]string` | `string[]` |

#### 二维数组 (array2d)

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int[][]` | `int[][]` | `List[List[int]]` | `[][]int32` | `number[][]` |
| `long[][]` | `long[][]` | `List[List[int]]` | `[][]int64` | `number[][]` |
| `float[][]` | `float[][]` | `List[List[float]]` | `[][]float32` | `number[][]` |
| `string[][]` | `string[][]` | `List[List[str]]` | `[][]string` | `string[][]` |

#### 集合 (set)

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `set<int>` | `HashSet<int>` | `set[int]` | `map[int32]struct{}` | `Set<number>` |
| `set<long>` | `HashSet<long>` | `set[int]` | `map[int64]struct{}` | `Set<number>` |
| `set<string>` | `HashSet<string>` | `set[str]` | `map[string]struct{}` | `Set<string>` |

#### map 类型

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int->int` | `Dictionary<int,int>` | `Dict[int,int]` | `map[int32]int32` | `Map<number,number>` |
| `string->int` | `Dictionary<string,int>` | `Dict[str,int]` | `map[string]int32` | `Map<string,number>` |
| `int->string` | `Dictionary<int,string>` | `Dict[int,str]` | `map[int32]string` | `Map<number,string>` |
| `string->string` | `Dictionary<string,string>` | `Dict[str,str]` | `map[string]string` | `Map<string,string>` |

### B.3 各语言读取方法映射

#### C# 读取方法

| Schema类型 | SheetReader方法 |
|------------|-----------------|
| int | ReadInt32() |
| long | ReadInt64() |
| float | ReadFloat() |
| double | ReadDouble() |
| bool | ReadBool() |
| string | ReadString() |
| `int[]` | ReadInt32Array() |
| `string[]` | ReadStringArray() |
| `int[][]` | ReadInt32Array2D() |
| `string[][]` | ReadStringArray2D() |
| `set<int>` | ReadInt32HashSet() |
| `int->int` | ReadInt32Int32Dictionary() |

#### Python 读取方法

| Schema类型 | SheetReader方法 |
|------------|-----------------|
| int | read_int32() |
| long | read_int64() |
| float | read_float() |
| double | read_double() |
| bool | read_bool() |
| string | read_string() |
| `int[]` | read_int32_array() |
| `string[]` | read_string_array() |
| `int[][]` | read_int32_array2d() |
| `string[][]` | read_string_array2d() |
| `set<int>` | read_int32_set() |
| `int->int` | read_int32_int32_dict() |

### B.4 类型推断规则

**优先级**：
1. 显式类型声明（`name:int`）→ 使用声明的类型
2. 数据内容特征匹配 → 推断类型
3. 默认 → `string`

**推断规则**：

| 数据特征 | 推断类型 | 示例 |
|----------|----------|------|
| 纯整数数字 | int | `100`, `-5`, `0` |
| 整数带 `L` 后缀 | long | `9999999999L` |
| 包含小数点 | float | `3.14`, `1.0` |
| 布尔关键词 | bool | `true`, `false`, `yes`, `no` |
| 逗号分隔的数字 | `int[]` | `1,2,3,4,5` |
| 逗号分隔的字符串 | `string[]` | `a,b,c` |
| 分号分隔的多行数据 | `int[][]` | `1,2,3;4,5,6` |
| 冒号分隔的键值对 | `int->int` | `1:10,2:20` |
| 其他 | string | `hello world` |
