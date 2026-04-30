import os
from pathlib import Path

from thdocs.cli import main


def test_build_renders_title_into_index_html(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "thdocs.toml").write_text(
        '[site]\ntitle = "Foobar"\n',
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Welcome\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    exit_code = main(["build"])

    assert exit_code == 0
    rendered = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "Foobar" in rendered
