from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[3]


def _write_minimal_xlsx(path: Path, rows: list[list[object]]) -> None:
    sheet_xml = _build_sheet_xml(rows)
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>
  <Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>
</Relationships>""",
        )
        archive.writestr(
            "xl/workbook.xml",
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">
  <sheets>
    <sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/>
  </sheets>
</workbook>""",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>
</Relationships>""",
        )
        archive.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _build_sheet_xml(rows: list[list[object]]) -> str:
    body: list[str] = []
    for row_index, row in enumerate(rows, start=1):
        cells: list[str] = []
        for column_index, value in enumerate(row, start=1):
            if value is None or value == "":
                continue
            reference = f"{_column_name(column_index)}{row_index}"
            if isinstance(value, bool):
                cells.append(f'<c r="{reference}" t="b"><v>{1 if value else 0}</v></c>')
            elif isinstance(value, (int, float)):
                cells.append(f'<c r="{reference}"><v>{value}</v></c>')
            else:
                escaped = _escape_xml(str(value))
                cells.append(f'<c r="{reference}" t="inlineStr"><is><t>{escaped}</t></is></c>')
        body.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
        "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
        f"<sheetData>{''.join(body)}</sheetData>"
        "</worksheet>"
    )


def _column_name(index: int) -> str:
    name = ""
    current = index
    while current > 0:
        current, remainder = divmod(current - 1, 26)
        name = chr(ord("A") + remainder) + name
    return name


def _escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _run_generate(input_path: Path, output_dir: Path) -> tuple[Path, Path]:
    code_output = output_dir / "csharp"
    data_output = output_dir / "data"
    command = [
        sys.executable,
        "-m",
        "sheetforge",
        "generate",
        "-i",
        str(input_path),
        "-o",
        str(output_dir),
        "-t",
        "all",
        "-l",
        "csharp",
        "--code-output",
        str(code_output),
        "--data-output",
        str(data_output),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return code_output, data_output


def _write_test_app(project_dir: Path, code_output: Path, data_output: Path) -> Path:
    project_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir = REPO_ROOT / "runtimes" / "csharp" / "SheetForge.Runtime"

    compile_items = []
    for source in sorted(code_output.rglob("*.cs")):
        compile_items.append(f'    <Compile Include="{source.as_posix()}" Link="Generated/{source.name}" />')
    for source in sorted(runtime_dir.glob("*.cs")):
        compile_items.append(f'    <Compile Include="{source.as_posix()}" Link="Runtime/{source.name}" />')

    project_file = project_dir / "TestApp.csproj"
    project_file.write_text(
        "\n".join(
            [
                '<Project Sdk="Microsoft.NET.Sdk">',
                '  <PropertyGroup>',
                '    <OutputType>Exe</OutputType>',
                '    <TargetFramework>net7.0</TargetFramework>',
                '    <LangVersion>9.0</LangVersion>',
                '    <Nullable>enable</Nullable>',
                '    <ImplicitUsings>disable</ImplicitUsings>',
                '  </PropertyGroup>',
                '  <ItemGroup>',
                *compile_items,
                '  </ItemGroup>',
                '</Project>',
            ]
        ),
        encoding="utf-8",
    )

    (project_dir / "Program.cs").write_text(
        f'''using System;\nusing GameConfig;\n\ninternal static class Program\n{{\n    private static int Main()\n    {{\n        var dataPath = @"{data_output.as_posix()}";\n        var table = TbExcelItemTable.LoadFromFile(System.IO.Path.Combine(dataPath, "tb_excel_item.sfc"));\n        var item = table.Get(1002);\n        if (item == null) return 2;\n        if (item.Name != "wizard") return 3;\n        if (item.Tags.Length != 2 || item.Tags[0] != "magic" || item.Tags[1] != "ranged") return 4;\n        if (item.Power != 12) return 5;\n        ConfigManager.LoadAll(dataPath);\n        var managed = ConfigManager.GetExcelItems().Get(1001);\n        if (managed == null || managed.Name != "knight") return 6;\n        Console.WriteLine($"{{item.Name}}|{{item.Tags[0]}}|{{item.Power}}|{{ConfigManager.GetExcelItems().Count}}");\n        return 0;\n    }}\n}}\n''',
        encoding="utf-8",
    )
    return project_file


def test_xlsx_input_generates_csharp_and_loads_runtime(tmp_path: Path) -> None:
    input_file = tmp_path / "tb_excel_item.xlsx"
    _write_minimal_xlsx(
        input_file,
        [
            ["##var", "id:int", "name:string", "tags:string[]", "power"],
            ["##desc", "ID", "Name", "Tags", "Power"],
            ["##tag", "all", "all", "all", "all"],
            [1001, "knight", "melee,starter", 10],
            [1002, "wizard", "magic,ranged", 12],
        ],
    )

    code_output, data_output = _run_generate(input_file, tmp_path / "output")
    expected = [
        code_output / "TbExcelItem.cs",
        code_output / "TbExcelItemTable.cs",
        code_output / "ConfigManager.cs",
        data_output / "tb_excel_item.sfc",
    ]
    for path in expected:
        assert path.exists(), path

    project_file = _write_test_app(tmp_path / "csharp_app", code_output, data_output)
    env = os.environ.copy()
    app_home = tmp_path / ".dotnet_home"
    env["DOTNET_CLI_HOME"] = str(app_home)
    env["NUGET_PACKAGES"] = str(tmp_path / ".nuget")
    env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1"
    env["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1"
    env["DOTNET_NOLOGO"] = "1"
    env["LOCALAPPDATA"] = str(app_home / "local")
    env["APPDATA"] = str(app_home / "roaming")
    env["USERPROFILE"] = str(app_home / "profile")
    env["HOME"] = str(app_home / "profile")
    result = subprocess.run(
        ["dotnet", "run", "--project", str(project_file), "-c", "Release"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
    )
    assert result.returncode == 0, f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    assert output_lines[-1] == "wizard|magic|12|2"
