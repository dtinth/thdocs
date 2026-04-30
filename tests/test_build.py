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


def test_build_renders_title_into_index_html(tmp_path: Path, monkeypatch) -> None:
    _write_project(
        tmp_path,
        title="Foobar",
        pages={"index.md": "# Welcome\n"},
    )

    monkeypatch.chdir(tmp_path)
    exit_code = main(["build"])

    assert exit_code == 0
    rendered = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "Foobar" in rendered


def test_index_directive_surfaces_term_in_genindex(tmp_path: Path, monkeypatch) -> None:
    index_md = (
        "# Welcome\n"
        "\n"
        "```{index} Quickstart\n"
        "```\n"
        "\n"
        "Some content here.\n"
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


def test_thdocs_css_is_linked_in_built_html(tmp_path: Path, monkeypatch) -> None:
    _write_project(
        tmp_path,
        title="Site",
        pages={"index.md": "# Hi\n"},
    )

    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    assert (tmp_path / "_build" / "html" / "_static" / "thdocs.css").exists()
    index_html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "thdocs.css" in index_html


def test_init_scaffolds_a_buildable_project(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 0

    assert (tmp_path / "thdocs.toml").exists()
    assert (tmp_path / "docs" / "index.md").exists()
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "_build" in gitignore

    assert main(["build"]) == 0
    assert (tmp_path / "_build" / "html" / "index.html").exists()


def test_toctree_links_subpage(tmp_path: Path, monkeypatch) -> None:
    index_md = (
        "# Welcome\n"
        "\n"
        "```{toctree}\n"
        "guide\n"
        "```\n"
    )
    _write_project(
        tmp_path,
        title="Site",
        pages={
            "index.md": index_md,
            "guide.md": "# Setup steps\n\nDo the thing.\n",
        },
    )

    monkeypatch.chdir(tmp_path)
    exit_code = main(["build"])

    assert exit_code == 0
    html_dir = tmp_path / "_build" / "html"
    guide_html = (html_dir / "guide.html").read_text(encoding="utf-8")
    assert "Setup steps" in guide_html
    index_html = (html_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="guide.html"' in index_html
