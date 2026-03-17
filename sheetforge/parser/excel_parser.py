from __future__ import annotations

from pathlib import PurePosixPath
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .common import parse_table_rows


NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def parse_excel_file(path, target: str):
    rows = _load_first_sheet_rows(path)
    return parse_table_rows(path, rows, target)


def _load_first_sheet_rows(path) -> list[list[str]]:
    with ZipFile(path, "r") as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        first_sheet = workbook.find("main:sheets/main:sheet", NS)
        if first_sheet is None:
            raise ValueError(f"{path} does not contain any worksheet")

        relationship_id = first_sheet.attrib.get(f"{{{NS['rel']}}}id")
        if relationship_id is None:
            raise ValueError(f"{path} first worksheet is missing relationship id")

        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        target_name: str | None = None
        for relation in rels.findall("pkg:Relationship", NS):
            if relation.attrib.get("Id") == relationship_id:
                target_name = relation.attrib.get("Target")
                break
        if target_name is None:
            raise ValueError(f"{path} cannot resolve first worksheet target")

        worksheet_path = _resolve_workbook_target(target_name)
        shared_strings = _load_shared_strings(archive)
        worksheet = ET.fromstring(archive.read(worksheet_path))
        sheet_data = worksheet.find("main:sheetData", NS)
        if sheet_data is None:
            return []

        rows: list[list[str]] = []
        for row_node in sheet_data.findall("main:row", NS):
            parsed_row: list[str] = []
            for cell in row_node.findall("main:c", NS):
                reference = cell.attrib.get("r", "")
                column_index = _column_index(reference)
                while len(parsed_row) <= column_index:
                    parsed_row.append("")
                parsed_row[column_index] = _cell_value(cell, shared_strings)
            rows.append(parsed_row)
        return rows


def _resolve_workbook_target(target: str) -> str:
    base = PurePosixPath("xl/workbook.xml")
    resolved = (base.parent / target).as_posix()
    while resolved.startswith("../"):
        resolved = resolved[3:]
    return resolved


def _load_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for node in root.findall("main:si", NS):
        texts = [text_node.text or "" for text_node in node.findall(".//main:t", NS)]
        values.append("".join(texts))
    return values


def _column_index(reference: str) -> int:
    letters = "".join(ch for ch in reference if ch.isalpha())
    if not letters:
        return 0
    value = 0
    for letter in letters:
        value = value * 26 + (ord(letter.upper()) - ord("A") + 1)
    return value - 1


def _cell_value(cell, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        texts = [text_node.text or "" for text_node in cell.findall("main:is/main:t", NS)]
        return "".join(texts)

    value_node = cell.find("main:v", NS)
    if value_node is None or value_node.text is None:
        return ""

    raw = value_node.text
    if cell_type == "s":
        return shared_strings[int(raw)]
    if cell_type == "b":
        return "true" if raw == "1" else "false"
    return raw
