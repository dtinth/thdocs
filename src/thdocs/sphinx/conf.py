import os
import tomllib
from pathlib import Path

_project_root = Path(os.environ["THDOCS_PROJECT"])
_cfg = tomllib.loads((_project_root / "thdocs.toml").read_text(encoding="utf-8"))

project = _cfg["site"]["title"]
author = _cfg["site"].get("author", "")
release = _cfg["site"].get("version", "")

extensions = ["myst_parser"]
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "alabaster"

_static_dir = (Path(__file__).parent.parent / "static").resolve()
html_static_path = [str(_static_dir)]
html_css_files = ["thdocs.css"]
