import importlib
import subprocess
import sys
from pathlib import Path
from shutil import copytree


CASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


def _run_generate(input_dir: Path, output_dir: Path, target: str = "server") -> tuple[Path, Path]:
    code_output = output_dir / "python"
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
        target,
        "-l",
        "python",
        "--code-output",
        str(code_output),
        "--data-output",
        str(data_output),
    ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        "Generate command failed.\n"
        f"command: {' '.join(command)}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    return code_output, data_output


def _run_generate_expect_failure(input_dir: Path, output_dir: Path, target: str = "server") -> subprocess.CompletedProcess[str]:
    code_output = output_dir / "python"
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
        target,
        "-l",
        "python",
        "--code-output",
        str(code_output),
        "--data-output",
        str(data_output),
    ]
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _prepare_case_input(tmp_path: Path) -> Path:
    input_dir = tmp_path / "input"
    copytree(CASE_DIR / "input", input_dir)

    tsv_path = input_dir / "tb_item.tsv"
    original = tsv_path.read_text(encoding="utf-8")
    edited = original.replace(
        "1002\tmage\t80\t35",
        "1002\tarchmage\t80\t42",
    )
    tsv_path.write_text(edited, encoding="utf-8")
    return input_dir


def _find_generated_file(root: Path, filename: str) -> Path:
    matches = list(root.rglob(filename))
    assert matches, f"Generated file not found: {filename} in {root}"
    return matches[0]


def _clear_generated_modules() -> None:
    for name in list(sys.modules):
        if name == "game_config" or name.startswith("game_config."):
            del sys.modules[name]


def _bootstrap_generated_package(code_output: Path) -> str:
    runtime_root = REPO_ROOT / "runtimes" / "python"
    if runtime_root.exists():
        sys.path.insert(0, str(runtime_root))

    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(code_output))
    _clear_generated_modules()

    try:
        runtime_module = importlib.import_module("sheetforge_runtime")
        sys.modules.setdefault("sheetforge", runtime_module)
    except ModuleNotFoundError:
        try:
            runtime_module = importlib.import_module("sheetforge")
            sys.modules.setdefault("sheetforge_runtime", runtime_module)
        except ModuleNotFoundError:
            pass

    package_init = _find_generated_file(code_output, "__init__.py")
    package_dir = package_init.parent
    sys.path.insert(0, str(package_dir.parent))
    return package_dir.name


def test_generate_python_code_and_data_files(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output")

    for name in [
        "tb_item.py",
        "tb_item_table.py",
        "tb_feature.py",
        "tb_feature_table.py",
        "tb_comprehensive.py",
        "tb_comprehensive_table.py",
        "config_manager.py",
    ]:
        _find_generated_file(code_output, name)

    for name in ["tb_item.sfc", "tb_feature.sfc", "tb_comprehensive.sfc"]:
        _find_generated_file(data_output, name)


def test_python_runtime_loads_latest_edited_tsv_data(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output")

    package_name = _bootstrap_generated_package(code_output)
    package_module = importlib.import_module(package_name)
    assert hasattr(package_module, "TbItemTable")
    assert hasattr(package_module, "TbFeatureTable")
    assert hasattr(package_module, "TbComprehensiveTable")
    assert hasattr(package_module, "ConfigManager")

    item_table_module = importlib.import_module(f"{package_name}.tb_item_table")
    item_table_class = getattr(item_table_module, "TbItemTable")

    item_data_file = _find_generated_file(data_output, "tb_item.sfc")
    item_table = item_table_class.load_from(str(item_data_file))

    item = item_table.get(1002)
    assert item is not None
    assert item.id == 1002
    assert item.name == "archmage"
    assert item.hp == 80
    assert item.atk == 42
    assert item_table.get(9999) is None
    assert len(item_table) == 3
    assert item_table.count == 3
    assert [row.id for row in item_table] == [1001, 1002, 1003]


def test_python_runtime_loads_container_and_inferred_types(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output")

    package_name = _bootstrap_generated_package(code_output)
    feature_table_module = importlib.import_module(f"{package_name}.tb_feature_table")
    feature_table_class = getattr(feature_table_module, "TbFeatureTable")

    generated_item_module = _find_generated_file(code_output, "tb_feature.py")
    generated_code = generated_item_module.read_text(encoding="utf-8")
    assert "tags: List[str]" in generated_code
    assert "terrain: List[List[int]]" in generated_code
    assert "weights: List[float]" in generated_code
    assert "item_ids: set[int]" in generated_code
    assert "attrs: Dict[str, int]" in generated_code
    assert "drops: Dict[int, int]" in generated_code

    feature_data_file = _find_generated_file(data_output, "tb_feature.sfc")
    feature_table = feature_table_class.load_from(str(feature_data_file))
    feature = feature_table.get(2001)

    assert feature is not None
    assert feature.tags == ["fire", "magic"]
    assert feature.terrain == [[1, 2], [3, 4]]
    assert feature.weights == [1.0, 2.5, 3.75]
    assert feature.item_ids == {10, 20, 30}
    assert feature.attrs == {"gold": 100, "gem": 5}
    assert feature.drops == {1001: 2, 1002: 3}


def test_python_runtime_supports_all_documented_scalar_and_container_types(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output", target="server")

    package_name = _bootstrap_generated_package(code_output)
    table_module = importlib.import_module(f"{package_name}.tb_comprehensive_table")
    table_class = getattr(table_module, "TbComprehensiveTable")

    generated_item_module = _find_generated_file(code_output, "tb_comprehensive.py")
    generated_code = generated_item_module.read_text(encoding="utf-8")
    assert "long_value: int" in generated_code
    assert "precise: float" in generated_code
    assert "enabled: bool" in generated_code
    assert "longs: List[int]" in generated_code
    assert "doubles: List[float]" in generated_code
    assert "flags: List[bool]" in generated_code
    assert "long_grid: List[List[int]]" in generated_code
    assert "double_grid: List[List[float]]" in generated_code
    assert "labels_grid: List[List[str]]" in generated_code
    assert "long_ids: set[int]" in generated_code
    assert "aliases: set[str]" in generated_code
    assert "num_map: Dict[int, int]" in generated_code
    assert "text_num: Dict[str, int]" in generated_code
    assert "num_text: Dict[int, str]" in generated_code
    assert "text_text: Dict[str, str]" in generated_code
    assert "server_only: int" in generated_code
    assert "client_only: int" not in generated_code
    assert "note:" not in generated_code

    data_file = _find_generated_file(data_output, "tb_comprehensive.sfc")
    table = table_class.load_from(str(data_file))
    item = table.get(3001)
    assert item is not None
    assert item.long_value == 9999999999
    assert abs(item.precise - 3.14159265) < 1e-9
    assert item.enabled is True
    assert item.text == "alpha"
    assert item.longs == [1, 2, 3]
    assert item.doubles == [1.25, 2.5, 3.75]
    assert item.flags == [True, False, True]
    assert item.names == ["red", "green", "blue"]
    assert item.long_grid == [[1, 2], [3, 4]]
    assert item.double_grid == [[1.1, 2.2], [3.3, 4.4]]
    assert item.labels_grid == [["a", "b"], ["c", "d"]]
    assert item.long_ids == {11, 22}
    assert item.aliases == {"foo", "bar"}
    assert item.num_map == {1: 10, 2: 20}
    assert item.text_num == {"gold": 100, "gem": 5}
    assert item.num_text == {1: "one", 2: "two"}
    assert item.text_text == {"x": "hello", "y": "world"}
    assert item.server_only == 8
    assert item.text_text["x"] == "hello"


def test_target_filtering_supports_client_server_and_all_tags(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)

    server_code_output, server_data_output = _run_generate(input_dir, tmp_path / "server_output", target="server")
    client_code_output, client_data_output = _run_generate(input_dir, tmp_path / "client_output", target="client")
    all_code_output, all_data_output = _run_generate(input_dir, tmp_path / "all_output", target="all")

    server_pkg = _bootstrap_generated_package(server_code_output)
    server_table_module = importlib.import_module(f"{server_pkg}.tb_comprehensive_table")
    server_table_class = getattr(server_table_module, "TbComprehensiveTable")
    server_code = _find_generated_file(server_code_output, "tb_comprehensive.py").read_text(encoding="utf-8")
    assert "server_only: int" in server_code
    assert "client_only: int" not in server_code
    server_table = server_table_class.load_from(str(_find_generated_file(server_data_output, "tb_comprehensive.sfc")))
    assert server_table.get(3001).server_only == 8

    client_pkg = _bootstrap_generated_package(client_code_output)
    client_table_module = importlib.import_module(f"{client_pkg}.tb_comprehensive_table")
    client_table_class = getattr(client_table_module, "TbComprehensiveTable")
    client_code = _find_generated_file(client_code_output, "tb_comprehensive.py").read_text(encoding="utf-8")
    assert "client_only: int" in client_code
    assert "server_only: int" not in client_code
    client_table = client_table_class.load_from(str(_find_generated_file(client_data_output, "tb_comprehensive.sfc")))
    assert client_table.get(3001).client_only == 7

    all_pkg = _bootstrap_generated_package(all_code_output)
    all_table_module = importlib.import_module(f"{all_pkg}.tb_comprehensive_table")
    all_table_class = getattr(all_table_module, "TbComprehensiveTable")
    all_code = _find_generated_file(all_code_output, "tb_comprehensive.py").read_text(encoding="utf-8")
    assert "client_only: int" in all_code
    assert "server_only: int" in all_code
    assert "note:" not in all_code
    all_table = all_table_class.load_from(str(_find_generated_file(all_data_output, "tb_comprehensive.sfc")))
    all_item = all_table.get(3001)
    assert all_item.client_only == 7
    assert all_item.server_only == 8


def test_runtime_base_apis_and_config_manager_work(tmp_path: Path) -> None:
    input_dir = _prepare_case_input(tmp_path)
    code_output, data_output = _run_generate(input_dir, tmp_path / "output", target="all")

    package_name = _bootstrap_generated_package(code_output)
    package_module = importlib.import_module(package_name)
    manager_module = importlib.import_module(f"{package_name}.config_manager")
    table_module = importlib.import_module(f"{package_name}.tb_item_table")
    table_class = getattr(table_module, "TbItemTable")
    manager_class = getattr(manager_module, "ConfigManager")

    item_table = table_class.load_from(str(_find_generated_file(data_output, "tb_item.sfc")))
    found, item = item_table.try_get(1001)
    assert found is True
    assert item is not None and item.name == "warrior"
    missing, item = item_table.try_get(9999)
    assert missing is False and item is None
    assert item_table.contains(1001) is True
    assert item_table.contains(9999) is False
    assert len(item_table.get_all()) == 3
    assert item_table[1001].name == "warrior"
    assert item_table.load_time_ms >= 0.0

    manager = manager_class.get_instance()
    manager.load_all(str(data_output))
    assert manager.items is not None
    assert manager.features is not None
    assert manager.comprehensives is not None
    assert manager.items.get(1002).name == "archmage"
    assert package_module.get_items().get(1001).name == "warrior"
    manager.unload_all()
    assert manager.items is None
    assert manager.features is None
    assert manager.comprehensives is None


def test_generate_fails_for_duplicate_id_and_type_mismatch(tmp_path: Path) -> None:
    input_dir = tmp_path / "bad_input"
    input_dir.mkdir(parents=True, exist_ok=True)

    duplicate_path = input_dir / "tb_duplicate.tsv"
    duplicate_path.write_text(
        "##var\tid:int\tname:string\n"
        "##desc\tID\tName\n"
        "##tag\tall\tall\n"
        "1\tone\n"
        "1\ttwo\n",
        encoding="utf-8",
    )
    result = _run_generate_expect_failure(input_dir, tmp_path / "dup_out")
    assert result.returncode != 0
    assert "duplicate id" in result.stderr.lower()

    duplicate_path.unlink()
    mismatch_path = input_dir / "tb_mismatch.tsv"
    mismatch_path.write_text(
        "##var\tid:int\thp:int\n"
        "##desc\tID\tHP\n"
        "##tag\tall\tall\n"
        "1\tabc\n",
        encoding="utf-8",
    )
    result = _run_generate_expect_failure(input_dir, tmp_path / "mismatch_out")
    assert result.returncode != 0
    assert "type mismatch" in result.stderr.lower()
