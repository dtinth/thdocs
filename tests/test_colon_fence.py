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


def test_colon_fence_admonition_renders_correctly(tmp_path: Path, monkeypatch) -> None:
    index_md = (
        "# Welcome\n"
        "\n"
        ":::{admonition} Custom title\n"
        ":class: note\n"
        ":collapsible: closed\n"
        "\n"
        "Hidden content\n"
        ":::\n"
    )
    _write_project(
        tmp_path,
        title="Site",
        pages={"index.md": index_md},
    )

    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    rendered = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "Custom title" in rendered
    assert "Hidden content" in rendered
