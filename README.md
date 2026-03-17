# SheetForge

游戏配置工具，支持从 Excel/CSV/TSV 文件生成多语言配置代码和高效二进制数据文件。

## 特性

- **多格式支持**：Excel (.xlsx/.xls)、CSV、TSV
- **多语言代码生成**：C#、Python（可扩展 Go、TypeScript、Java 等）
- **高效二进制格式**：小体积、快解析
- **客户端/服务器分离**：支持字段级别可见性控制
- **类型推断**：自动推断数据类型，也支持显式声明

## 快速开始

### 安装

```bash
pip install sheetforge
```

### 使用

```bash
# 生成 C# 配置
sheetforge generate -i ./config -o ./output -l csharp

# 生成 Python 配置
sheetforge generate -i ./config -o ./output -l python

# 生成多语言配置
sheetforge generate -i ./config -o ./output -l csharp,python
```

## 表格格式

表格前三行为元数据：

| ##var | id:int | name:string | hp:int | skills:int[] |
|-------|--------|-------------|--------|--------------|
| ##desc | ID | 名称 | 生命值 | 技能列表 |
| ##tag | all | all | all | all |
| 1 | 战士 | 1000 | 1,2,3 |
| 2 | 法师 | 800 | 4,5,6 |

### 支持的类型

| 类型 | 语法 | 示例 |
|------|------|------|
| 整数 | `int` | `100` |
| 长整数 | `long` | `9999999999L` |
| 浮点数 | `float` | `3.14` |
| 布尔值 | `bool` | `true` |
| 字符串 | `string` | `hello` |
| 数组 | `T[]` | `int[]`, `string[]` |
| 二维数组 | `T[][]` | `int[][]` |
| 集合 | `set<T>` | `set<int>` |
| 字典 | `K->V` | `int->int` |

## 文档

- [需求文档](docs/requirements.md)
- [技术设计文档](docs/design.md)

## License

MIT
