from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .generator import BinaryGenerator, CSharpGenerator, PythonGenerator
from .parser import parse_table_file


SUPPORTED_LANGUAGES = {"python", "csharp"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sheetforge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate")
    generate.add_argument("-i", "--input", required=True)
    generate.add_argument("-o", "--output", required=True)
    generate.add_argument("-t", "--target", choices=["client", "server", "all"], default="all")
    generate.add_argument("-l", "--lang", required=True)
    generate.add_argument("-c", "--config")
    generate.add_argument("--code-output")
    generate.add_argument("--data-output")
    generate.add_argument("-v", "--verbose", action="store_true")
    generate.set_defaults(handler=handle_generate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args) or 0)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


def handle_generate(args: argparse.Namespace) -> int:
    languages = [language.strip() for language in args.lang.split(",") if language.strip()]
    unsupported = [language for language in languages if language not in SUPPORTED_LANGUAGES]
    if unsupported:
        raise ValueError(f"Unsupported language(s): {', '.join(unsupported)}")

    input_path = Path(args.input)
    output_path = Path(args.output)
    code_output = Path(args.code_output) if args.code_output else output_path
    data_output = Path(args.data_output) if args.data_output else output_path

    generators: dict[str, object] = {}
    if "python" in languages:
        generators["python"] = PythonGenerator(package_name="game_config")
    if "csharp" in languages:
        generators["csharp"] = CSharpGenerator(namespace="GameConfig")

    schemas = []
    for source in _discover_sources(input_path):
        schema = parse_table_file(source, args.target)
        schemas.append(schema)
        for generator in generators.values():
            generator.generate(schema, code_output)
        BinaryGenerator().write(schema, data_output)

        if args.verbose:
            print(f"generated {source.name}")

    if schemas:
        python_generator = generators.get("python")
        if python_generator is not None:
            python_generator.write_package_init(schemas, code_output)
        csharp_generator = generators.get("csharp")
        if csharp_generator is not None:
            csharp_generator.write_support_files(schemas, code_output)
    return 0


def _discover_sources(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    return sorted(
        path
        for path in input_path.rglob("*")
        if path.is_file() and path.suffix.lower() in {".tsv", ".csv", ".xlsx"}
    )
