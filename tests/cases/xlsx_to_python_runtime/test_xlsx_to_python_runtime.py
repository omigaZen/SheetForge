from __future__ import annotations

import importlib
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
    code_output = output_dir / "python"
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
        "python",
        "--code-output",
        str(code_output),
        "--data-output",
        str(data_output),
    ]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return code_output, data_output


def _bootstrap_generated_package(code_output: Path) -> str:
    sys.path.insert(0, str(REPO_ROOT / "runtimes" / "python"))
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(code_output))
    runtime_module = importlib.import_module("sheetforge_runtime")
    sys.modules.setdefault("sheetforge", runtime_module)
    package_dir = next(path.parent for path in code_output.rglob("__init__.py"))
    sys.path.insert(0, str(package_dir.parent))
    return package_dir.name


def test_xlsx_input_generates_python_and_loads_runtime(tmp_path: Path) -> None:
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
    package_name = _bootstrap_generated_package(code_output)
    table_module = importlib.import_module(f"{package_name}.tb_excel_item_table")
    table_class = getattr(table_module, "TbExcelItemTable")
    table = table_class.load_from(str(next(data_output.rglob("tb_excel_item.sfc"))))

    item = table.get(1002)
    assert item is not None
    assert item.name == "wizard"
    assert item.tags == ["magic", "ranged"]
    assert item.power == 12
