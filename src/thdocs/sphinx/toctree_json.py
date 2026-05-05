"""Sphinx extension that generates toctree.js from toctree directives."""

import json
import re
from pathlib import Path
from typing import Any

from docutils import nodes as docnodes
from sphinx.addnodes import toctree as toctree_node
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

EXTERNAL_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _is_external(ref: str) -> bool:
    return EXTERNAL_URL_RE.match(ref) is not None


def get_toctree_from_doctree(doctree: docnodes.document, env: BuildEnvironment | None = None) -> list[dict[str, Any]]:
    """Extract toctree structure from a doctree document node."""
    items = []
    for node in doctree.traverse(toctree_node):
        items.extend(_process_toctree_node(node, env))
    return items


def _process_toctree_node(node: toctree_node, env: BuildEnvironment | None = None) -> list[dict[str, Any]]:
    """Convert a toctree node to a list of tree items."""
    items = []

    # The toctree node has a 'caption' attribute for the section title
    caption = node.get("caption")
    entries = node.get("entries", [])

    if not entries:
        return items

    # If this toctree has a caption, wrap all entries in a section node
    children = []
    for entry_title, docname in entries:
        children.append(_build_tree_item(docname, env, entry_title))

    if caption:
        # Wrap in a section
        items.append(
            {
                "id": caption.lower().replace(" ", "-"),
                "title": caption,
                "type": "section",
                "children": children,
            }
        )
    else:
        # No section wrapper, just add the items
        items.extend(children)

    return items


def _build_tree_item(docname: str | tuple[str, str], env: BuildEnvironment | None = None, entry_title: str | None = None) -> dict[str, Any]:
    """Build a single tree item from a docname reference."""
    if isinstance(docname, tuple):
        docname, title = docname
    else:
        title = entry_title

    # Handle external links
    if _is_external(docname):
        return {
            "id": docname,
            "title": title or docname,
            "type": "page",
            "href": docname,
            "children": [],
        }

    # Prefer Sphinx's parsed page title (env.titles[docname] is the H1 node)
    if not title and env and docname in env.titles:
        title = env.titles[docname].astext()

    item = {
        "id": docname.replace("/", "-"),
        "title": title or _docname_to_title(docname),
        "type": "page",
        "href": f"{docname}.html",
        "children": [],
    }

    # If the page itself has a toctree, include those items as children
    if env and docname in env.found_docs:
        try:
            doctree = env.get_doctree(docname)
            children = get_toctree_from_doctree(doctree, env)
            item["children"] = children
        except Exception:
            # If we can't get the doctree, just skip nested items
            pass

    return item


def _docname_to_title(docname: str) -> str:
    """Convert a docname like 'getting-started' to title 'Getting Started'."""
    return " ".join(w.capitalize() for w in docname.replace("/", " ").split("-"))


def generate_toctree_json(app: Sphinx, env: BuildEnvironment) -> list[dict[str, Any]]:
    """Generate toctree.js from the environment's toctree data. Returns the tree items."""
    items = []

    # Only process the master document's toctree to build the tree structure
    # Nested documents' toctrees will be included as children of their parent pages
    master_doc = env.config.master_doc or "index"
    doctree = env.get_doctree(master_doc)
    items.extend(get_toctree_from_doctree(doctree, env))

    # Write toctree.js that sets a global variable
    static_dir = Path(app.outdir) / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)

    toctree_js_file = static_dir / "toctree.js"
    toctree_data_json = json.dumps({"items": items})
    toctree_js_file.write_text(
        f"window.TOCTREE_DATA = {toctree_data_json};",
        encoding="utf-8",
    )

    return items


def setup(app: Sphinx) -> dict[str, Any]:
    """Set up the extension."""
    app.connect("build-finished", _on_build_finished)
    return {"version": "1.0", "parallel_read_safe": True}


def _on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    """Called when the build is finished."""
    if exception is not None:
        return

    # Generate toctree.js file
    generate_toctree_json(app, app.env)
