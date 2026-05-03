from pathlib import Path

from thdocs.cli import main


def _write_project(root: Path, *, title: str, pages: dict[str, str]) -> None:
    (root / "thdocs.toml").write_text(
        f'[site]\ntitle = "{title}"\n',
        encoding="utf-8",
    )
    docs_dir = root / "docs"
    docs_dir.mkdir()
    for name, body in pages.items():
        (docs_dir / name).write_text(body, encoding="utf-8")


def test_index_role_creates_entry_at_inline_location(tmp_path: Path, monkeypatch) -> None:
    index_md = (
        "# Welcome\n"
        "\n"
        "This page covers {index}`Quickstart` and {index}`Installation`.\n"
        "\n"
        "## Quickstart\n"
        "\n"
        "Run the tool.\n"
        "\n"
        "## Installation\n"
        "\n"
        "Use uv.\n"
    )
    _write_project(
        tmp_path,
        title="Site",
        pages={"index.md": index_md},
    )

    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    genindex = (tmp_path / "_build" / "html" / "genindex.html").read_text(encoding="utf-8")
    assert "Quickstart" in genindex
    assert "Installation" in genindex
