import json
import os
import tomllib
from pathlib import Path

_project_root = Path(os.environ["THDOCS_PROJECT"])
_cfg = tomllib.loads((_project_root / "thdocs.toml").read_text(encoding="utf-8"))

project = _cfg["site"]["title"]
author = _cfg["site"].get("author", "")

# -- Version ---------------------------------------------------------------

release = _cfg["site"].get("version", "")
if not release and (_project_root / "package.json").exists():
    release = "package.json"

if release.endswith(".json"):
    json_path = _project_root / release
    release = json.loads(json_path.read_text(encoding="utf-8")).get("version", "")

# -- Copyright -------------------------------------------------------------

if author:
    copyright = f"%Y, {author}"
else:
    copyright = "%Y"

# ---------------------------------------------------------------------------

extensions = ["myst_parser", "thdocs.sphinx.toctree_json"]
if _cfg["site"].get("genindex"):
    extensions.append("thdocs.sphinx.index_json")
myst_enable_extensions = ["colon_fence", "deflist"]
myst_heading_anchors = 3
master_doc = "index"
exclude_patterns = ["_build"]
html_theme = "thdocs"
pygments_style = "one-dark"

if os.environ.get("THDOCS_PDF_BUILD"):
    pygments_style = "default"
    extensions.append("thdocs.sphinx.remote_images")
    latex_show_urls = "footnote"
    latex_show_pagerefs = True

_theme_dir = (Path(__file__).parent.parent / "theme").resolve()
html_theme_path = [str(_theme_dir)]

_static_dir = (Path(__file__).parent.parent / "static").resolve()
html_static_path = [str(_static_dir)]
html_css_files = ["thdocs.css"]
html_js_files = ["thdocs.js"]

html_sidebars = {"**": ["thdocs-sidebar.html"]}

html_context = {}

_pdf_url = os.environ.get("THDOCS_PDF")
if _pdf_url:
    html_context["pdf_url"] = _pdf_url

if _cfg["site"].get("genindex"):
    html_context["genindex"] = True

# -- LaTeX / PDF output --------------------------------------------------

latex_engine = "xelatex"
latex_use_xindy = False

if os.environ.get("THDOCS_PDF_BUILD"):
    _fonts_dir = (Path(__file__).parent.parent / "fonts").resolve()
    _fp = str(_fonts_dir) + "/"
    latex_elements = {
        "fontpkg": fr"""
\usepackage{{fontspec}}
\usepackage{{ucharclasses}}
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
\newfontfamily{{\emojifont}}[Path = {_fp}]{{NotoEmoji-Regular.ttf}}
\setTransitionsFor{{Dingbats}}{{\emojifont}}{{\normalfont}}
""",
    }
else:
    latex_elements = {}
latex_documents = [
    (master_doc, "index.tex", project, author, "howto", False),
]
