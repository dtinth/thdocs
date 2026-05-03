import os
import tomllib
from pathlib import Path

_project_root = Path(os.environ["THDOCS_PROJECT"])
_cfg = tomllib.loads((_project_root / "thdocs.toml").read_text(encoding="utf-8"))

project = _cfg["site"]["title"]
author = _cfg["site"].get("author", "")
release = _cfg["site"].get("version", "")

extensions = ["myst_parser", "thdocs.sphinx.toctree_json", "thdocs.sphinx.index_json"]
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "thdocs"
pygments_style = "one-dark"

if os.environ.get("THDOCS_PDF_BUILD"):
    pygments_style = "default"

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
latex_use_xindy = False

if os.environ.get("THDOCS_PDF_BUILD"):
    _fonts_dir = (Path(__file__).parent.parent / "fonts").resolve()
    _fp = str(_fonts_dir) + "/"
    latex_elements = {
        "fontpkg": fr"""
\usepackage{{fontspec}}
\XeTeXlinebreaklocale "th"
\setmainfont[
  Path = {_fp},
  BoldFont = Sarabun-Bold.ttf,
  ItalicFont = Sarabun-Italic.ttf,
  BoldItalicFont = Sarabun-BoldItalic.ttf,
]{{Sarabun-Regular.ttf}}
\setsansfont[
  Path = {_fp},
  BoldFont = Sarabun-Bold.ttf,
  ItalicFont = Sarabun-Italic.ttf,
  BoldItalicFont = Sarabun-BoldItalic.ttf,
]{{Sarabun-Regular.ttf}}
\setmonofont[
  Path = {_fp},
  BoldFont = ComicMono-Bold.ttf,
]{{ComicMono.ttf}}
""",
    }
else:
    latex_elements = {}
latex_documents = [
    (master_doc, "index.tex", project, author, "howto", False),
]
