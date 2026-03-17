# SheetForge

游戏配置工具，支持从 Excel/CSV/TSV 文件生成多语言配置代码和高效二进制数据文件。

## 特性

- 多格式输入：Excel（规划中）、CSV、TSV
- 多语言代码生成：当前已实现 Python 运行时链路
- 二进制数据导出：生成 `.sfc` 数据文件
- 客户端/服务端列过滤：支持 `client` / `server` / `all`
- 类型系统：支持基础类型、数组、二维数组、集合、字典和类型推断

## 当前状态

当前仓库已实现并验证这条链路：

`TSV -> Python 配置类/数据文件 -> Python Runtime 读取`

已通过集成测试验证：

- 基础类型：`int` `long` `float` `double` `bool` `string`
- 容器类型：`T[]` `T[][]` `set<T>` `K->V`
- 标签过滤：`client` `server` `all`
- 运行时访问：`load_from()` `get()` `try_get()` `contains()` `get_all()`
- 配置管理：`ConfigManager.load_all()` `unload_all()` 和包级 `get_items()`

## 安装

`pip install sheetforge` 目前不能用。

原因：仓库还没有提供 `pyproject.toml` / `setup.py` 打包配置，也没有发布到 PyPI。

当前可用方式：克隆仓库后，直接在仓库根目录运行。

```bash
git clone https://github.com/omigaZen/SheetForge.git
cd SheetForge
python -m sheetforge --help
```

## 使用

```bash
# 生成 Python 配置和数据
python -m sheetforge generate -i ./config -o ./output -t server -l python

# 指定代码和数据输出目录
python -m sheetforge generate \
  -i ./config \
  -o ./output \
  -t all \
  -l python \
  --code-output ./output/python \
  --data-output ./output/data
```

## 表格格式

表格前三行为元数据：

| ##var | id:int | name:string | hp:int | skills:int[] |
|-------|--------|-------------|--------|--------------|
| ##desc | ID | 名称 | 生命值 | 技能列表 |
| ##tag | all | all | all | all |
| 1 | warrior | 1000 | 1,2,3 |
| 2 | mage | 800 | 4,5,6 |

## 支持的类型

| 类型 | 语法 | 示例 |
|------|------|------|
| 整数 | `int` | `100` |
| 长整数 | `long` | `9999999999L` |
| 浮点数 | `float` / `double` | `3.14` |
| 布尔 | `bool` | `true` |
| 字符串 | `string` | `hello` |
| 数组 | `T[]` | `int[]`, `string[]` |
| 二维数组 | `T[][]` | `int[][]` |
| 集合 | `set<T>` | `set<int>` |
| 字典 | `K->V` | `int->int` |

## 文档

- [需求文档](docs/requirements.md)
- [技术设计文档](docs/design.md)
- [TSV -> Python Runtime 测试用例](tests/cases/tsv_to_python_runtime/README.md)

## License

MIT
