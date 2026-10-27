import ast
from pathlib import Path

def test_gui_source_compiles():
    source = Path(__file__).parents[1] / "xana_desktop.py"
    ast.parse(source.read_text(encoding="utf-8"))

def test_gui_has_no_network_imports():
    source = Path(__file__).parents[1] / "xana_desktop.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = {alias.name for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not ({"requests", "urllib3", "httpx", "aiohttp"} & imports)
