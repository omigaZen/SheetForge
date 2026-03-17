# SheetForge - 游戏配置工具需求文档

## 1. 项目概述

### 1.1 项目背景
游戏开发过程中，策划通常使用Excel/CSV等表格工具配置游戏数据。开发团队需要将这些表格数据转换为程序可读的代码类和运行时数据，以供游戏客户端和服务器使用。

### 1.2 项目目标
开发一款命令行配置工具，支持从TSV、Excel、CSV文件读取配置数据，自动生成：
- 多语言配置类代码（C#、Python，可扩展更多语言）
- 配置表类代码（支持客户端/服务器分离）
- 高效的二进制数据文件
- 多语言运行时加载库

### 1.3 设计理念
- **简洁性**：表格格式简单直观，降低策划学习成本
- **高性能**：生成紧凑的二进制格式，解析速度快
- **灵活性**：支持客户端/服务器代码分离，便于扩展
- **类型安全**：生成强类型代码，编译期/运行时检查错误
- **多语言支持**：统一的二进制格式，多语言运行时共享同一数据文件
- **可扩展性**：代码生成器插件化设计，易于添加新语言支持

---

## 2. 表格格式规范

### 2.1 文件格式支持
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| TSV | `.tsv` | Tab分隔，推荐使用 |
| CSV | `.csv` | 逗号分隔 |
| Excel | `.xlsx`, `.xls` | Excel工作表 |

### 2.2 表格结构定义

表格的前三行为元数据行，第四行起为数据行：

```
| ##var    | id        | name     | desc       | hp   | atk   | note        |
| ##desc   | 唯一ID    | 名称     | 描述       | 生命值 | 攻击力 | 备注说明    |
| ##tag    | all       | all      | all        | all  | server |             |
|----------|-----------|----------|------------|------|--------|-------------|
| 1        | warrior   | 战士     | 勇敢的战士  | 100  | 20     | 这是备注    |
| 2        | mage      | 法师     | 神秘的法师  | 60   | 35     |             |
```

#### 2.2.1 元数据行说明

| 行号 | 前缀 | 用途 | 说明 |
|------|------|------|------|
| 第1行 | `##var` | 属性名称 | 定义C#类的属性名，必须符合C#命名规范 |
| 第2行 | `##desc` | 属性描述 | 属性的中文描述，用于代码注释 |
| 第3行 | `##tag` | 标记 | 定义属性的可见性范围 |

#### 2.2.2 标记(Tag)定义

| 标记值 | 含义 | 客户端生成 | 服务器生成 |
|--------|------|------------|------------|
| `all` | 双端可见 | ✅ 生成 | ✅ 生成 |
| `client` | 仅客户端 | ✅ 生成 | ❌ 跳过 |
| `server` | 仅服务器 | ❌ 跳过 | ✅ 生成 |
| 空值 | 忽略列 | ❌ 跳过 | ❌ 跳过 |

> 空值标记的列不参与代码生成和数据处理，可用于策划写备注说明。

### 2.3 特殊列

#### 2.3.1 ID列（第一列）
- 第一列固定为ID列，作为配置项的唯一标识
- ID列标记必须为`all`，确保双端都能索引
- ID值必须唯一，工具需校验重复ID

#### 2.3.2 第一列特殊标记
第一列首单元格用于标识表格类型：
- `##var` - 变量定义行
- 可扩展其他指令前缀

---

## 3. 数据类型支持

### 3.1 基础类型

| 类型名 | C#类型 | Python类型 | 说明 | 示例值 |
|--------|--------|------------|------|--------|
| `int` | `int` | `int` | 32位整数 | `100`, `-5` |
| `long` | `long` | `int` | 64位整数 | `9999999999`, `123L` |
| `float` | `float` | `float` | 单精度浮点 | `3.14`, `1.5f` |
| `double` | `double` | `float` | 双精度浮点 | `3.14159265` |
| `bool` | `bool` | `bool` | 布尔值 | `true`, `false`, `1`, `0` |
| `string` | `string` | `str` | 字符串 | `hello world` |

### 3.2 容器类型

容器类型语法设计直观，类似常见编程语言的类型声明：

#### 3.2.1 array - 一维数组

语法：`元素类型[]`（后缀方括号）

生成对应语言的原生数组类型，适用于配置数据（加载后只读，固定大小，性能最优）。

| 类型语法 | C#类型 | Python类型 | 说明 | 示例值 |
|----------|--------|------------|------|--------|
| `int[]` | `int[]` | `List[int]` | 整数数组 | `1,2,3,4,5` |
| `string[]` | `string[]` | `List[str]` | 字符串数组 | `a,b,c` |
| `float[]` | `float[]` | `List[float]` | 浮点数组 | `1.0,2.5,3.14` |

**数据填写格式**：元素之间用逗号分隔，如 `1,2,3,4,5`

#### 3.2.2 array2d - 二维数组

语法：`元素类型[][]`（双后缀方括号）

生成对应语言的二维数组类型，适用于矩阵、地图等二维数据结构。

| 类型语法 | C#类型 | Python类型 | 说明 | 示例值 |
|----------|--------|------------|------|--------|
| `int[][]` | `int[][]` | `List[List[int]]` | 整数二维数组 | `1,2,3;4,5,6` |
| `string[][]` | `string[][]` | `List[List[str]]` | 字符串二维数组 | `a,b;c,d` |
| `float[][]` | `float[][]` | `List[List[float]]` | 浮点二维数组 | `1.0,2.0;3.0,4.0` |

**数据填写格式**：
- 行内元素用逗号 `,` 分隔
- 行与行之间用分号 `;` 分隔
- 示例：`1,2,3;4,5,6` 表示 `[[1,2,3], [4,5,6]]`

**二维数组应用场景**：
- 游戏地图配置（地形、障碍物）
- 技能伤害矩阵
- 关卡布局数据
- 宝箱掉落表

#### 3.2.3 set - 集合类型

#### 3.2.3 set - 集合类型

语法：`set<元素类型>`（泛型语法）

生成对应语言的集合容器类型，自动去重，适用于需要唯一性检查的数据。

| 类型语法 | C#类型 | Python类型 | 说明 | 示例值 |
|----------|--------|------------|------|--------|
| `set<int>` | `HashSet<int>` | `set[int]` | 整数集合 | `1,2,3` |
| `set<string>` | `HashSet<string>` | `set[str]` | 字符串集合 | `a,b,c` |

**数据填写格式**：元素之间用逗号分隔，重复元素会被自动去重

#### 3.2.4 map - 字典类型

语法：`键类型->值类型`（箭头语法，直观表示映射关系）

生成对应语言的字典容器类型，键必须唯一，适用于键值对配置。

| 类型语法 | C#类型 | Python类型 | 说明 | 示例值 |
|----------|--------|------------|------|--------|
| `int->int` | `Dictionary<int,int>` | `Dict[int,int]` | 整数-整数字典 | `1:10,2:20,3:30` |
| `string->int` | `Dictionary<string,int>` | `Dict[str,int]` | 字符串-整数字典 | `a:1,b:2,c:3` |
| `int->string` | `Dictionary<int,string>` | `Dict[int,str]` | 整数-字符串字典 | `1:a,2:b,3:c` |

**数据填写格式**：键值对用冒号连接，对之间用逗号分隔，如 `1:10,2:20,3:30`

#### 3.2.5 容器类型语法总结

| 类型 | 语法 | 含义 | 示例 |
|------|------|------|------|
| 一维数组 | `T[]` | 有序元素列表 | `int[]`, `string[]` |
| 二维数组 | `T[][]` | 二维矩阵数据 | `int[][]`, `string[][]` |
| 集合 | `set<T>` | 唯一元素集合 | `set<int>`, `set<string>` |
| 字典 | `K->V` | 键值映射 | `int->int`, `string->int` |

#### 3.2.6 容器类型选择建议

| 场景 | 推荐类型 | 理由 |
|------|----------|------|
| 有序列表数据 | `T[]` | 性能最优，内存紧凑 |
| 矩阵/地图数据 | `T[][]` | 直观表达二维结构 |
| 需要唯一性 | `set<T>` | 自动去重，快速查找 |
| 键值映射 | `K->V` | 快速通过键查找值 |

### 3.3 类型定义语法

在 `##var` 行可使用冒号语法显式指定类型：

```
| ##var | id:int | name:string | level:int | rate:float | tags:string[] | attrs:string->int |
```

**语法规则**：
- 格式：`属性名:类型`
- 数组：`元素类型[]`，如 `int[]`、`string[]`
- 集合：`set<元素类型>`，如 `set<int>`
- 字典：`键类型->值类型`，如 `int->int`、`string->int`
- 基础类型：`int`、`string`、`float`、`bool` 等

### 3.4 类型推断规则

当未显式指定类型（没有 `:类型` 后缀）时，根据数据内容自动推断：

| 数据特征 | 推断类型 | 示例 |
|----------|----------|------|
| 纯整数数字 | `int` | `100`, `-5`, `0` |
| 整数带 `L` 后缀 | `long` | `9999999999L` |
| 包含小数点 | `float` | `3.14`, `1.0`, `.5` |
| 布尔关键词 | `bool` | `true`, `false`, `yes`, `no` |
| 逗号分隔的数字 | `int[]` | `1,2,3,4,5` |
| 逗号分隔的字符串 | `string[]` | `a,b,c` |
| 冒号分隔的键值对 | `int->int` | `1:10,2:20` |
| 其他 | `string` | `hello world` |

**推断优先级**：
1. 显式类型声明（`name:int`）→ 使用声明的类型
2. 数据内容特征匹配 → 推断类型
3. 默认 → `string`

### 3.5 多语言容器类型映射总表

#### 一维数组

| Schema语法 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int[]` | `int[]` | `List[int]` | `[]int32` | `number[]` |
| `string[]` | `string[]` | `List[str]` | `[]string` | `string[]` |
| `float[]` | `float[]` | `List[float]` | `[]float32` | `number[]` |

#### 二维数组

| Schema语法 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int[][]` | `int[][]` | `List[List[int]]` | `[][]int32` | `number[][]` |
| `string[][]` | `string[][]` | `List[List[str]]` | `[][]string` | `string[][]` |
| `float[][]` | `float[][]` | `List[List[float]]` | `[][]float32` | `number[][]` |

#### 集合

| Schema语法 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `set<int>` | `HashSet<int>` | `set[int]` | `map[int32]struct{}` | `Set<number>` |
| `set<string>` | `HashSet<string>` | `set[str]` | `map[string]struct{}` | `Set<string>` |

#### 字典

| Schema语法 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| `int->int` | `Dictionary<int,int>` | `Dict[int,int]` | `map[int32]int32` | `Map<number,number>` |
| `string->int` | `Dictionary<string,int>` | `Dict[str,int]` | `map[string]int32` | `Map<string,number>` |
| `int->string` | `Dictionary<int,string>` | `Dict[int,str]` | `map[int32]string` | `Map<number,string>` |

---

## 4. 代码生成规范

### 4.1 配置项类（Item Class）

生成的配置项类对应表格的一行数据：

```csharp
// 文件: TbItem.cs（自动生成，勿手动修改）
// ============================================================
// 由SheetForge自动生成，请勿手动修改
// ============================================================

namespace GameConfig
{
    /// <summary>
    /// 物品配置表
    /// </summary>
    public partial class TbItem
    {
        /// <summary>
        /// 唯一ID
        /// </summary>
        public int Id { get; private set; }

        /// <summary>
        /// 名称
        /// </summary>
        public string Name { get; private set; }

        /// <summary>
        /// 生命值
        /// </summary>
        public int Hp { get; private set; }

        // 私有构造函数，强制通过Table类创建
        private TbItem() { }
    }
}
```

### 4.2 配置表类（Table Class）

```csharp
// 文件: TbItemTable.cs（自动生成，勿手动修改）
// ============================================================
// 由SheetForge自动生成，请勿手动修改
// ============================================================

namespace GameConfig
{
    /// <summary>
    /// 物品配置表
    /// </summary>
    public partial class TbItemTable
    {
        private readonly Dictionary<int, TbItem> _items;
        private readonly List<TbItem> _itemList;

        /// <summary>
        /// 配置表名称
        /// </summary>
        public string TableName => "TbItem";

        /// <summary>
        /// 通过ID获取配置项
        /// </summary>
        public TbItem Get(int id) => _items.TryGetValue(id, out var item) ? item : null;

        /// <summary>
        /// 获取所有配置项
        /// </summary>
        public IReadOnlyList<TbItem> GetAll() => _itemList;

        /// <summary>
        /// 检查ID是否存在
        /// </summary>
        public bool Contains(int id) => _items.ContainsKeyKey(id);

        /// <summary>
        /// 获取配置项数量
        /// </summary>
        public int Count => _items.Count;

        // 私有构造，通过Load方法创建
        private TbItemTable(Dictionary<int, TbItem> items)
        {
            _items = items;
            _itemList = items.Values.ToList();
        }

        /// <summary>
        /// 从文件加载配置表
        /// </summary>
        public static TbItemTable Load(string filePath)
        {
            // 解析逻辑...
        }
    }
}
```

### 4.3 Partial类扩展示例

用户可创建扩展文件添加自定义逻辑：

```csharp
// 文件: TbItemTable.Ext.cs（用户手动维护）
namespace GameConfig
{
    public partial class TbItem
    {
        /// <summary>
        /// 用户自定义扩展方法
        /// </summary>
        public int GetTotalPower()
        {
            return Hp + Atk * 2;
        }
    }

    public partial class TbItemTable
    {
        /// <summary>
        /// 按名称查找
        /// </summary>
        public TbItem FindByName(string name)
        {
            return _itemList.FirstOrDefault(x => x.Name == name);
        }
    }
}
```

---

## 5. 多语言代码生成

### 5.1 语言支持规划

| 语言 | 优先级 | 状态 | 适用场景 |
|------|--------|------|----------|
| C# | P0 | 首批支持 | Unity客户端、.NET服务器 |
| Python | P0 | 首批支持 | 游戏服务器、工具脚本、数据分析 |
| Go | P1 | 后续支持 | 游戏服务器 |
| TypeScript | P1 | 后续支持 | 前端H5、Node.js服务器 |
| Java | P2 | 后续支持 | Android、Java服务器 |
| C++ | P2 | 后续支持 | 游戏引擎底层 |

### 5.2 生成器架构

采用插件化设计，每种语言对应一个生成器插件：

```
┌─────────────────────────────────────────────────────┐
│                  SheetForge Core                    │
├─────────────────────────────────────────────────────┤
│                   Schema Model                      │
└───────────────────────┬─────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ C# Generator  │ │Python Generator│ │  Go Generator │
│    Plugin     │ │    Plugin     │ │    Plugin     │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 5.3 Python 代码生成示例

#### 5.3.1 配置项类（Python）

```python
# 文件: tb_item.py（自动生成，勿手动修改）
# ============================================================
# 由 SheetForge 自动生成，请勿手动修改
# ============================================================
from dataclasses import dataclass
from typing import Optional

@dataclass
class TbItem:
    """物品配置项"""

    id: int
    """唯一ID"""

    name: str
    """名称"""

    hp: int
    """生命值"""

    atk: int
    """攻击力"""

    @classmethod
    def from_reader(cls, reader: 'SheetReader') -> 'TbItem':
        """从读取器加载"""
        return cls(
            id=reader.read_int32(),
            name=reader.read_string(),
            hp=reader.read_int32(),
            atk=reader.read_int32(),
        )
```

#### 5.3.2 配置表类（Python）

```python
# 文件: tb_item_table.py（自动生成，勿手动修改）
# ============================================================
# 由 SheetForge 自动生成，请勿手动修改
# ============================================================
from typing import Dict, List, Optional
from .tb_item import TbItem
from sheetforge import SheetReader, TableBase

class TbItemTable(TableBase[TbItem]):
    """物品配置表"""

    @property
    def table_name(self) -> str:
        return "item"

    def load(self, file_path: str) -> None:
        """从文件加载配置表"""
        with SheetReader(file_path) as reader:
            self._items.clear()
            self._item_list.clear()

            for _ in range(reader.row_count):
                item = TbItem.from_reader(reader)
                self._items[item.id] = item
                self._item_list.append(item)

    @classmethod
    def load_from(cls, file_path: str) -> 'TbItemTable':
        """从文件加载并返回新实例"""
        table = cls()
        table.load(file_path)
        return table
```

#### 5.3.3 用户扩展示例（Python）

```python
# 文件: tb_item_table_ext.py（用户手动维护）
from .tb_item import TbItem
from .tb_item_table import TbItemTable

# 方式一：继承扩展
class TbItemTableExt(TbItemTable):
    """扩展配置表"""

    def find_by_name(self, name: str) -> Optional[TbItem]:
        """按名称查找"""
        for item in self._item_list:
            if item.name == name:
                return item
        return None

    def get_by_quality(self, quality: str) -> List[TbItem]:
        """按品质筛选"""
        return [item for item in self._item_list if item.quality == quality]

# 方式二：猴子补丁（可选）
def get_total_power(self: TbItem) -> int:
    """计算总战力"""
    return self.hp + self.atk * 2

TbItem.get_total_power = get_total_power
```

### 5.4 语言特性适配

| 特性 | C# | Python | Go |
|------|-----|--------|-----|
| 类型系统 | 静态强类型 | 动态类型(类型提示) | 静态强类型 |
| 类定义 | partial class | @dataclass | struct |
| 扩展方式 | partial class | 继承/猴子补丁 | 嵌入/组合 |
| 命名规范 | PascalCase | snake_case | PascalCase |
| 访问修饰 | public/private | 无(约定_) | 首字母大小写 |
| 集合类型 | Dictionary, List | dict, list | map, slice |

### 5.5 类型映射表

| Schema类型 | C# | Python | Go | TypeScript |
|------------|-----|--------|-----|------------|
| int | int | int | int32 | number |
| long | long | int | int64 | number |
| float | float | float | float32 | number |
| double | double | float | float64 | number |
| bool | bool | bool | bool | boolean |
| string | string | str | string | string |
| int[] | int[] | List[int] | []int32 | number[] |
| string[] | string[] | List[str] | []string | string[] |

---

## 6. 运行时架构

### 6.1 多语言运行时设计

```
┌─────────────────────────────────────────────────────────────┐
│                    .sfc 二进制数据文件                       │
│                 (统一格式，所有语言共享)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ C# Runtime    │ │Python Runtime │ │ Go Runtime    │
│               │ │               │ │               │
│ SheetReader   │ │ SheetReader   │ │ SheetReader   │
│ TableBase<T>  │ │ TableBase[T]  │ │ TableBase[T]  │
└───────────────┘ └───────────────┘ └───────────────┘
```

### 6.2 运行时核心接口

每种语言的运行时需实现以下核心功能：

| 接口/类 | 职责 |
|---------|------|
| SheetReader | 二进制文件读取、类型解析 |
| TableBase | 配置表基类，提供ID索引、遍历等通用功能 |
| StringTable | 字符串表管理（内部使用） |
| Exceptions | 异常定义 |

### 6.3 Python 运行时核心

```python
# sheetforge/reader.py
import struct
from typing import Dict, List, BinaryIO

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
        magic = self._file.read(4)
        if magic != self.MAGIC:
            raise ValueError(f"Invalid file format: magic mismatch")

        self.version = struct.unpack('<H', self._file.read(2))[0]
        self._file.read(2)  # flags
        self.row_count = struct.unpack('<I', self._file.read(4))[0]
        self._file.read(4)  # string_table_offset

    def read_int32(self) -> int:
        return struct.unpack('<i', self._file.read(4))[0]

    def read_int64(self) -> int:
        return struct.unpack('<q', self._file.read(8))[0]

    def read_float(self) -> float:
        return struct.unpack('<f', self._file.read(4))[0]

    def read_double(self) -> float:
        return struct.unpack('<d', self._file.read(8))[0]

    def read_bool(self) -> bool:
        return struct.unpack('?', self._file.read(1))[0]

    def read_string(self) -> str:
        index = struct.unpack('<I', self._file.read(4))[0]
        return self._string_table[index]

    def read_int32_list(self) -> List[int]:
        count = struct.unpack('<I', self._file.read(4))[0]
        return [self.read_int32() for _ in range(count)]

    def read_string_list(self) -> List[str]:
        count = struct.unpack('<I', self._file.read(4))[0]
        return [self.read_string() for _ in range(count)]

    def __enter__(self) -> 'SheetReader':
        return self

    def __exit__(self, *args) -> None:
        self._file.close()
```

```python
# sheetforge/table_base.py
from typing import TypeVar, Generic, Dict, List, Optional, Iterator

T = TypeVar('T')

class TableBase(Generic[T]):
    """配置表基类"""

    def __init__(self):
        self._items: Dict[int, T] = {}
        self._item_list: List[T] = []

    @property
    def table_name(self) -> str:
        raise NotImplementedError

    @property
    def count(self) -> int:
        return len(self._items)

    def get(self, id: int) -> Optional[T]:
        return self._items.get(id)

    def try_get(self, id: int) -> tuple[bool, Optional[T]]:
        item = self._items.get(id)
        return (item is not None, item)

    def contains(self, id: int) -> bool:
        return id in self._items

    def get_all(self) -> List[T]:
        return self._item_list.copy()

    def __iter__(self) -> Iterator[T]:
        return iter(self._item_list)

    def __len__(self) -> int:
        return len(self._items)
```

### 6.4 运行时目录结构

```
runttimes/
├── csharp/
│   └── SheetForge.Runtime/
│       ├── SheetForge.Runtime.csproj
│       ├── SheetReader.cs
│       ├── TableBase.cs
│       ├── StringTable.cs
│       └── Exceptions.cs
├── python/
│   └── sheetforge/
│       ├── __init__.py
│       ├── reader.py
│       ├── table_base.py
│       └── exceptions.py
├── go/
│   └── sheetforge/
│       ├── reader.go
│       ├── table_base.go
│       └── errors.go
└── typescript/
    └── sheetforge/
        ├── reader.ts
        ├── table_base.ts
        └── index.ts
```

---

## 7. 数据文件格式

### 5.1 设计目标
- **小体积**：二进制格式，无冗余文本
- **快解析**：无需复杂解析逻辑，直接内存映射
- **跨平台**：字节序统一为Little-Endian

### 5.2 文件结构

```
┌─────────────────────────────────────┐
│          File Header (16 bytes)     │
├─────────────────────────────────────┤
│          Column Definitions         │
├─────────────────────────────────────┤
│          Data Rows                  │
├─────────────────────────────────────┤
│          String Table (optional)    │
└─────────────────────────────────────┘
```

#### 5.2.1 文件头（16字节）

| 偏移 | 长度 | 字段 | 说明 |
|------|------|------|------|
| 0 | 4 | Magic | 魔数 `SFGC` (SheetForge Config) |
| 4 | 2 | Version | 格式版本号 |
| 6 | 2 | Flags | 标志位 |
| 8 | 4 | RowCount | 数据行数 |
| 12 | 4 | StringTableOffset | 字符串表偏移量 |

#### 5.2.2 列定义区域

每列定义包含：
- 列名（变长字符串）
- 数据类型（1字节）
- 偏移量（根据行数计算）

#### 5.2.3 数据区域

按列存储，同类数据连续存放，便于压缩和缓存命中：
- 数值类型：直接写入二进制
- 字符串：写入字符串表索引

#### 5.2.4 字符串表

所有字符串集中存储，去重后按索引引用：
- 4字节：字符串数量
- 每个字符串：长度(2字节) + UTF-8字节

### 5.3 文件扩展名
- `.sfc` - SheetForge Config 二进制配置文件

---

## 8. 工具命令行接口

### 8.1 基本命令

```bash
# 生成 C# 客户端配置
sheetforge generate --input ./config --output ./output/client --target client --lang csharp

# 生成 Python 服务器配置
sheetforge generate --input ./config --output ./output/server --target server --lang python

# 生成双端配置（同时生成 C# 和 Python）
sheetforge generate --input ./config --output ./output --target all --lang csharp,python

# 指定不同语言的输出目录
sheetforge generate --input ./config \
    --lang csharp --code-output ./client/Config --data-output ./client/Data \
    --lang python --code-output ./server/config --data-output ./server/data
```

### 8.2 配置文件

支持YAML/JSON配置文件：

```yaml
# sheetforge.yaml
input:
  paths:
    - ./config/**/*.xlsx
    - ./config/**/*.tsv
    - ./config/**/*.csv
  exclude:
    - ./config/~*
    - ./config/.~*

# 多语言输出配置
output:
  languages:
    - lang: csharp
      target: client
      code: ./output/client/Config
      data: ./output/client/Data
      namespace: GameConfig
    - lang: python
      target: server
      code: ./output/server/config
      data: ./output/server/data
      package: game_config
    - lang: go
      target: server
      code: ./output/go/config
      data: ./output/go/data
      package: config

# 代码生成选项
options:
  indent_size: 4
  newline: lf

# 校验配置
validation:
  check_duplicate_id: true
  check_empty_required: true
  check_type_mismatch: true
```

### 8.3 命令参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--input` | `-i` | 输入文件或目录 |
| `--output` | `-o` | 输出目录 |
| `--target` | `-t` | 目标平台：client/server/all |
| `--lang` | `-l` | 目标语言：csharp/python/go/typescript/java，支持逗号分隔多语言 |
| `--config` | `-c` | 配置文件路径 |
| `--verbose` | `-v` | 详细输出 |
| `--help` | `-h` | 显示帮助 |

---

## 9. 数据加载器

### 9.1 C# 运行时加载

```csharp
// 加载单个配置表
var itemTable = TbItemTable.Load("Config/tb_item.sfc");

// 通过ID获取
var item = itemTable.Get(1001);

// 遍历所有
foreach (var config in itemTable.GetAll())
{
    Console.WriteLine($"Item: {config.Name}");
}
```

### 9.2 Python 运行时加载

```python
from game_config import TbItemTable

# 加载配置表
item_table = TbItemTable.load_from("config/tb_item.sfc")

# 通过ID获取
item = item_table.get(1001)
if item:
    print(f"Item: {item.name}")

# 遍历所有
for item in item_table:
    print(f"Item: {item.name}, HP: {item.hp}")

# 使用扩展方法
from game_config import TbItemTableExt
ext_table = TbItemTableExt.load_from("config/tb_item.sfc")
warrior = ext_table.find_by_name("warrior")
```

### 9.3 C# 配置管理器

```csharp
// 文件: ConfigManager.cs（自动生成或模板生成）
public static class ConfigManager
{
    public static TbItemTable Items { get; private set; }
    public static TbHeroTable Heroes { get; private set; }
    // ... 其他配置表

    /// <summary>
    /// 加载所有配置表
    /// </summary>
    public static void LoadAll(string configPath)
    {
        Items = TbItemTable.Load($"{configPath}/tb_item.sfc");
        Heroes = TbHeroTable.Load($"{configPath}/tb_hero.sfc");
        // ...
    }

    /// <summary>
    /// 卸载所有配置表
    /// </summary>
    public static void UnloadAll()
    {
        Items = null;
        Heroes = null;
        // ...
    }
}
```

### 9.4 Python 配置管理器

```python
# 文件: config_manager.py（自动生成或模板生成）
from typing import Optional
from pathlib import Path

from game_config import (
    TbItemTable,
    TbHeroTable,
    TbSkillTable,
)


class ConfigManager:
    """配置管理器"""

    _instance: Optional['ConfigManager'] = None

    def __init__(self):
        self.items: Optional[TbItemTable] = None
        self.heroes: Optional[TbHeroTable] = None
        self.skills: Optional[TbSkillTable] = None

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_all(self, config_path: str) -> None:
        """加载所有配置表"""
        path = Path(config_path)
        self.items = TbItemTable.load_from(str(path / "tb_item.sfc"))
        self.heroes = TbHeroTable.load_from(str(path / "tb_hero.sfc"))
        self.skills = TbSkillTable.load_from(str(path / "tb_skill.sfc"))

    def unload_all(self) -> None:
        """卸载所有配置表"""
        self.items = None
        self.heroes = None
        self.skills = None


# 便捷访问
def get_items() -> TbItemTable:
    return ConfigManager.get_instance().items
```

---

## 8. 错误处理与校验

### 8.1 编译期校验

| 校验项 | 错误级别 | 说明 |
|--------|----------|------|
| ID重复 | Error | 同一配置表内ID必须唯一 |
| 属性名非法 | Error | 必须符合C#变量命名规范 |
| 类型不匹配 | Error | 数据值与定义类型不符 |
| 必填列为空 | Warning | 标记为非空的列存在空值 |
| 空数据行 | Warning | 存在全空的数据行 |

### 8.2 错误输出格式

```
[ERROR] tb_item.xlsx:15 - ID重复: 1001 (第10行已定义)
[ERROR] tb_hero.xlsx:5 - 类型错误: 期望int, 实际为 "abc"
[WARN]  tb_skill.xlsx:20 - 空值: 必填字段"Name"为空
```

---

## 9. 扩展功能（后续迭代）

### 9.1 引用校验
- 检测外键引用是否存在
- 配置项之间的依赖关系

### 9.2 多语言支持
- 多语言文本分离
- 自动生成多语言Key

### 9.3 数据版本控制
- 配置变更追踪
- 增量更新支持

### 9.4 其他语言支持
- 支持生成Go、Java、TypeScript等语言的配置类

---

## 10. 项目结构

```
SheetForge/
├── sheetforge/                      # Python 工具包
│   ├── __init__.py
│   ├── __main__.py                  # python -m sheetforge 入口
│   ├── cli.py                       # 命令行接口
│   ├── config.py                    # 配置管理
│   ├── parser/                      # 解析器模块
│   │   ├── __init__.py
│   │   ├── base.py                  # 解析器基类
│   │   ├── excel_parser.py          # Excel解析
│   │   ├── csv_parser.py            # CSV/TSV解析
│   │   └── table_parser.py          # 表格解析逻辑
│   ├── generator/                   # 代码生成器模块
│   │   ├── __init__.py
│   │   ├── base.py                  # 生成器基类
│   │   ├── csharp_generator.py      # C#代码生成器
│   │   ├── python_generator.py      # Python代码生成器
│   │   ├── go_generator.py          # Go代码生成器（扩展）
│   │   ├── binary_generator.py      # 二进制数据生成器
│   │   └── templates/               # Jinja2模板
│   │       ├── csharp/
│   │       │   ├── item.cs.jinja2
│   │       │   └── table.cs.jinja2
│   │       └── python/
│   │           ├── item.py.jinja2
│   │           └── table.py.jinja2
│   ├── models/                      # 数据模型
│   │   ├── __init__.py
│   │   ├── schema.py                # 表结构定义
│   │   └── column.py                # 列定义
│   ├── validator/                   # 校验器
│   │   ├── __init__.py
│   │   └── table_validator.py
│   └── utils/                       # 工具函数
│       ├── __init__.py
│       ├── type_utils.py
│       └── file_utils.py
├── runtimes/                        # 多语言运行时
│   ├── csharp/                      # C# 运行时
│   │   ├── SheetForge.Runtime/
│   │   │   ├── SheetForge.Runtime.csproj
│   │   │   ├── SheetReader.cs
│   │   │   ├── TableBase.cs
│   │   │   ├── StringTable.cs
│   │   │   └── Exceptions.cs
│   │   └── SheetForge.Runtime.sln
│   ├── python/                      # Python 运行时
│   │   └── sheetforge_runtime/
│   │       ├── __init__.py
│   │       ├── reader.py
│   │       ├── table_base.py
│   │       └── exceptions.py
│   ├── go/                          # Go 运行时（扩展）
│   │   └── sheetforge/
│   │       ├── reader.go
│   │       ├── table_base.go
│   │       └── errors.go
│   └── typescript/                  # TypeScript 运行时（扩展）
│       └── sheetforge-runtime/
│           ├── reader.ts
│           ├── table_base.ts
│           └── index.ts
├── tests/                           # 测试
│   ├── test_parser.py
│   ├── test_generator_csharp.py
│   ├── test_generator_python.py
│   ├── test_runtime_csharp.py
│   └── test_runtime_python.py
├── docs/                            # 文档
│   ├── requirements.md
│   ├── design.md
│   ├── binary_format.md             # 二进制格式详细文档
│   └── language_support.md          # 多语言支持指南
├── examples/                        # 示例
│   ├── unity_project/               # Unity集成示例
│   ├── python_server/               # Python服务器示例
│   └── config_files/                # 配置文件示例
├── pyproject.toml                   # Python项目配置
├── requirements.txt
├── setup.py
└── sheetforge.yaml                  # 工具默认配置
```

---

## 11. 开发阶段规划

### Phase 1: 核心功能（3周）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| Python项目骨架搭建 | 1天 | P0 |
| TSV/CSV解析器 | 2天 | P0 |
| 表结构模型 | 1天 | P0 |
| 二进制数据生成器 | 2天 | P0 |
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
| 数组/List类型支持 | 2天 | P1 |
| 类型推断 | 1天 | P1 |
| 错误报告优化 | 1天 | P1 |
| 集成测试 | 2天 | P1 |

### Phase 3: 生产优化（1周）

| 任务 | 预计时间 | 优先级 |
|------|----------|--------|
| PyInstaller打包 | 1天 | P2 |
| 性能优化 | 1天 | P2 |
| 文档完善 | 1天 | P2 |
| 示例项目 | 1天 | P2 |

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

## 附录A: 命名约定

### A.1 通用约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 源文件 | snake_case | `item_config.xlsx` |
| 数据文件 | snake_case + .sfc | `item_config.sfc` |
| Schema属性 | snake_case | `max_hp`, `attack_speed` |

### A.2 C# 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 配置项类 | Tb + PascalCase | `TbItem`, `TbHero` |
| 配置表类 | Tb + PascalCase + Table | `TbItemTable` |
| 属性名 | PascalCase | `MaxHp`, `AttackSpeed` |
| 私有字段 | _camelCase | `_items` |

### A.3 Python 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 配置项类 | Tb + PascalCase | `TbItem`, `TbHero` |
| 配置表类 | Tb + PascalCase + Table | `TbItemTable` |
| 属性名 | snake_case | `max_hp`, `attack_speed` |
| 方法名 | snake_case | `find_by_name` |
| 私有属性 | _snake_case | `_items` |

### A.4 Go 命名约定

| 类型 | 约定 | 示例 |
|------|------|------|
| 配置项结构体 | Tb + PascalCase | `TbItem`, `TbHero` |
| 配置表结构体 | Tb + PascalCase + Table | `TbItemTable` |
| 字段名 | PascalCase（公开） | `MaxHp`, `AttackSpeed` |
| 方法名 | PascalCase | `FindByName` |

---

## 附录B: 示例配置表

### B.1 物品配置表 (tb_item.xlsx)

| ##var | id | name | desc | type | quality | max_stack | price |
|-------|----|----|------|------|---------|-----------|-------|
| ##desc | ID | 名称 | 描述 | 类型 | 品质 | 最大堆叠 | 价格 |
| ##tag | all | all | all | all | all | all | server |
| 1001 | 生命药水 | 恢复100点生命值 | consumable | common | 99 | 100 |
| 1002 | 魔法药水 | 恢复50点魔法值 | consumable | common | 99 | 120 |
| 2001 | 铁剑 | 普通的铁剑 | weapon | common | 1 | 500 |
| 2002 | 钢剑 | 锋利的钢剑 | weapon | rare | 1 | 2000 |

### B.2 英雄配置表 (tb_hero.tsv)

```tsv
##var	id:name:int	name:string	hp:int	atk:int	def:int	skill_ids:array,int
##desc	ID	名称	生命值	攻击力	防御力	技能ID列表
##tag	all	all	all	all	all	all
1	战士	1000	100	50	1,2,3
2	法师	600	150	30	4,5,6
3	弓手	800	120	40	7,8,9
```

### B.3 技能配置表 - 包含容器类型 (tb_skill.xlsx)

| ##var | id:int | name:string | damage:int | targets:int[] | tags:string[] | effects:int->string |
|-------|--------|-------------|------------|---------------|---------------|---------------------|
| ##desc | ID | 名称 | 伤害值 | 目标ID数组 | 标签数组 | 效果映射（ID:描述） |
| ##tag | all | all | all | all | all | all |
| 1001 | 火球术 | 150 | 1,2,3 | fire,magic,damage | 1:灼烧,2:击退 |
| 1002 | 冰冻术 | 80 | 4,5 | ice,magic,control | 1:减速,2:冻结 |
| 1003 | 治疗术 | 0 | 10,11,12 | heal,support | 1:回复生命,2:解除异常 |

### B.4 地图配置表 - 二维数组示例 (tb_map.xlsx)

| ##var | id:int | name:string | width:int | height:int | terrain:int[][] | obstacles:int[][] |
|-------|--------|-------------|-----------|------------|-----------------|-------------------|
| ##desc | ID | 名称 | 宽度 | 高度 | 地形矩阵（0:平地 1:山地 2:水域） | 障碍物矩阵（0:无 1:有） |
| ##tag | all | all | all | all | all | all |
| 1 | 新手村 | 10 | 8 | 0,0,0,1,1,0,0,0,0,0;0,0,0,1,1,0,0,0,0,0;0,0,0,0,0,0,2,2,0,0;0,0,0,0,0,2,2,2,2,0;0,0,0,0,0,0,2,2,0,0;0,0,1,1,0,0,0,0,0,0;0,0,1,1,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0 | 0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0;0,0,0,0,0,0,0,0,0,0 |
| 2 | 副本入口 | 5 | 5 | 0,0,0,0,0;0,1,1,1,0;0,1,0,1,0;0,1,1,1,0;0,0,0,0,0 | 0,0,0,0,0;0,0,0,0,0;0,0,1,0,0;0,0,0,0,0;0,0,0,0,0 |

### B.5 奖励配置表 - 复杂容器类型 (tb_reward.xlsx)

| ##var | id:int | name:string | item_ids:set<int> | rewards:int->int | multipliers:float[] |
|-------|--------|-------------|-------------------|------------------|---------------------|
| ##desc | ID | 名称 | 物品ID集合 | 奖励映射（物品ID:数量） | 倍率数组 |
| ##tag | all | all | all | all | server |
| 1 | 新手礼包 | 1001,1002,1003 | 1001:10,1002:5,1003:1 | 1.0,1.5,2.0 |
| 2 | 首充礼包 | 2001,2002 | 2001:1,2002:1 | 1.0 |
| 3 | 签到奖励 | 3001,3002,3003,3004 | 3001:100,3002:50 | 1.0,1.2,1.5,2.0 |

**容器类型数据填写格式说明**：

| 容器类型 | 填写格式 | 示例 |
|----------|----------|------|
| `int[]` | 逗号分隔的整数 | `1,2,3,4,5` |
| `string[]` | 逗号分隔的字符串 | `fire,ice,thunder` |
| `int[][]` | 行内逗号分隔，行间分号分隔 | `1,2,3;4,5,6` → `[[1,2,3],[4,5,6]]` |
| `set<int>` | 逗号分隔的整数（自动去重） | `1,2,3,2,1` → `{1,2,3}` |
| `int->int` | `键:值`对，逗号分隔 | `1:10,2:20,3:30` |
| `string->int` | 字符串键，整数值 | `gold:100,gem:50` |
