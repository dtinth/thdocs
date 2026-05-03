import os
import tomllib
from pathlib import Path

_project_root = Path(os.environ["THDOCS_PROJECT"])
_cfg = tomllib.loads((_project_root / "thdocs.toml").read_text(encoding="utf-8"))

project = _cfg["site"]["title"]
author = _cfg["site"].get("author", "")
release = _cfg["site"].get("version", "")

extensions = ["myst_parser", "thdocs.sphinx.toctree_json"]
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "thdocs"
pygments_style = "one-dark"

_theme_dir = (Path(__file__).parent.parent / "theme").resolve()
html_theme_path = [str(_theme_dir)]

_static_dir = (Path(__file__).parent.parent / "static").resolve()
html_static_path = [str(_static_dir)]
html_css_files = ["thdocs.css"]
html_js_files = ["thdocs.js"]

html_sidebars = {"**": ["thdocs-sidebar.html"]}

_pdf_url = os.environ.get("THDOCS_PDF")
if _pdf_url:
    html_context = {"pdf_url": _pdf_url}

# -- LaTeX / PDF output --------------------------------------------------

latex_engine = "xelatex"
latex_elements = {
    "fontpkg": r"""
\usepackage{fontspec}
\setmainfont{Sarabun}
\setsansfont{FreeSans}
\setmonofont{Comic Mono}
""",
}
latex_documents = [
    (master_doc, "index.tex", project, author, "howto", False),
]
