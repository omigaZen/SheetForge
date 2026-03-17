from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import copytree


CASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def _prepare_case_input(tmp_path: Path) -> Path:
    input_dir = tmp_path / "input"
    copytree(REPO_ROOT / "tests" / "cases" / "tsv_to_python_runtime" / "input", input_dir)
    return input_dir


def _run_generate(input_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    code_output = output_dir / "csharp"
    data_output = output_dir / "data"
    command = [
        sys.executable,
        "-m",
        "sheetforge",
        "generate",
        "-i",
        str(input_dir),
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

    program_file = project_dir / "Program.cs"
    program_file.write_text(
        f'''using System;\nusing GameConfig;\n\ninternal static class Program\n{{\n    private static int Main()\n    {{\n        var dataPath = @"{data_output.as_posix()}";\n        var itemTable = TbItemTable.LoadFromFile(System.IO.Path.Combine(dataPath, "tb_item.sfc"));\n        var featureTable = TbFeatureTable.LoadFromFile(System.IO.Path.Combine(dataPath, "tb_feature.sfc"));\n        var comprehensiveTable = TbComprehensiveTable.LoadFromFile(System.IO.Path.Combine(dataPath, "tb_comprehensive.sfc"));\n\n        var item = itemTable.Get(1002);\n        var feature = featureTable.Get(2001);\n        var comprehensive = comprehensiveTable.Get(3001);\n        if (item == null || feature == null || comprehensive == null)\n        {{\n            return 2;\n        }}\n\n        if (item.Name != "mage") return 3;\n        if (!itemTable.Contains(1001)) return 4;\n        if (feature.Attrs["gold"] != 100) return 5;\n        if (!comprehensive.LongIds.Contains(11)) return 6;\n        if (comprehensive.TextText["x"] != "hello") return 7;\n\n        ConfigManager.LoadAll(dataPath);\n        var managed = ConfigManager.GetItems().Get(1001);\n        if (managed == null || managed.Name != "warrior") return 8;\n        Console.WriteLine($"{{item.Name}}|{{feature.Attrs[\"gold\"]}}|{{comprehensive.TextText[\"x\"]}}|{{ConfigManager.GetItems().Count}}");\n        return 0;\n    }}\n}}\n''',
        encoding="utf-8",
    )
    return project_file


def test_tsv_generates_csharp_and_runtime_loads_data(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output")

    expected = [
        code_output / "TbItem.cs",
        code_output / "TbItemTable.cs",
        code_output / "TbFeature.cs",
        code_output / "TbFeatureTable.cs",
        code_output / "TbComprehensive.cs",
        code_output / "TbComprehensiveTable.cs",
        code_output / "ConfigManager.cs",
        data_output / "tb_item.sfc",
        data_output / "tb_feature.sfc",
        data_output / "tb_comprehensive.sfc",
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
    assert output_lines[-1] == "mage|100|hello|3"
