"""Sphinx extension that generates index_entries.js from index entries."""

import json
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx


def generate_index_json(app: Sphinx) -> None:
    static_dir = Path(app.outdir) / "_static"
    static_dir.mkdir(parents=True, exist_ok=True)

    from sphinx.environment.adapters.indexentries import IndexEntries

    genindex = IndexEntries(app.env).create_index(app.builder)

    data = []
    for letter, entries in genindex:
        letter_data: dict[str, Any] = {"letter": letter, "entries": []}
        for entry_name, (targets, subitems, _category_key) in entries:
            url = targets[0][1] if targets else False
            sub_data = []
            for sub_name, sub_targets in subitems:
                sub_url = sub_targets[0][1] if sub_targets else False
                sub_data.append({"name": sub_name, "url": sub_url})
            letter_data["entries"].append({
                "name": entry_name,
                "url": url,
                "subitems": sub_data,
            })
        data.append(letter_data)

    js_file = static_dir / "index_entries.js"
    js_file.write_text(
        f"window.THINDEX_DATA = {json.dumps(data, ensure_ascii=False)};",
        encoding="utf-8",
    )


def setup(app: Sphinx) -> dict[str, Any]:
    app.connect("build-finished", _on_build_finished)
    return {"version": "1.0", "parallel_read_safe": True}


def _on_build_finished(app: Sphinx, exception: Exception | None) -> None:
    if exception is not None:
        return
    generate_index_json(app)
