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


def test_thdocs_theme_marks_rendered_pages(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)

    assert main(["build"]) == 0

    index_html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert '<meta name="generator" content="thdocs">' in index_html


def test_rendered_pages_wrap_body_in_prose_main(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Welcome\n\nHello there.\n"})
    monkeypatch.chdir(tmp_path)

    assert main(["build"]) == 0

    index_html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert '<main class="prose">' in index_html
    # The rendered content (the H1 title) must appear inside the wrapper, not before it.
    main_open = index_html.index('<main class="prose">')
    main_close = index_html.index("</main>")
    # Search for "Welcome" starting after the opening <main> tag to find the rendered content, not the <title>
    welcome_pos = index_html.index("Welcome", main_open)
    assert main_open < welcome_pos < main_close


def test_sidebar_skeleton_has_three_tabs_with_contents_filled(
    tmp_path: Path, monkeypatch
) -> None:
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
            "guide.md": "# Guide\n",
        },
    )
    monkeypatch.chdir(tmp_path)

    assert main(["build"]) == 0

    rendered = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")

    # All three tab buttons exist.
    assert 'data-tab="contents"' in rendered
    assert 'data-tab="index"' in rendered
    assert 'data-tab="search"' in rendered

    # All three panels exist.
    contents_panel = rendered.index('data-panel="contents"')
    index_panel = rendered.index('data-panel="index"')
    search_panel = rendered.index('data-panel="search"')

    # Panels appear in the expected order.
    assert contents_panel < index_panel < search_panel

    # The Contents panel actually contains the toctree (link to guide.html
    # appears between the Contents panel marker and the next panel marker).
    guide_link = rendered.index('href="guide.html"', contents_panel)
    assert contents_panel < guide_link < index_panel


def test_compiled_thdocs_css_includes_tailwind_typography(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0
    css = (tmp_path / "_build" / "html" / "_static" / "thdocs.css").read_text(
        encoding="utf-8"
    )
    # @tailwindcss/typography must have run.
    assert ".prose" in css


def test_thdocs_js_is_linked_in_built_html(tmp_path: Path, monkeypatch) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0
    assert (tmp_path / "_build" / "html" / "_static" / "thdocs.js").exists()
    index_html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "thdocs.js" in index_html


def _capture_autobuild_argv(monkeypatch) -> dict:
    import sphinx_autobuild.__main__

    captured: dict = {}

    def fake_main(argv):
        captured["argv"] = list(argv)
        return 0

    monkeypatch.setattr(sphinx_autobuild.__main__, "main", fake_main)
    return captured


def test_dev_invokes_sphinx_autobuild_with_project_paths(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)

    captured = _capture_autobuild_argv(monkeypatch)

    assert main(["dev"]) == 0

    argv = captured["argv"]
    assert "-b" in argv and argv[argv.index("-b") + 1] == "html"
    assert str(tmp_path / "docs") in argv
    assert str(tmp_path / "_build" / "html") in argv
    assert any(arg.endswith("/sphinx") and "thdocs" in arg for arg in argv)


def test_dev_defaults_host_to_0_0_0_0_and_port_to_20080(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)

    captured = _capture_autobuild_argv(monkeypatch)

    assert main(["dev"]) == 0

    argv = captured["argv"]
    assert "--host" in argv and argv[argv.index("--host") + 1] == "0.0.0.0"
    assert "--port" in argv and argv[argv.index("--port") + 1] == "20080"


def test_dev_passes_explicit_host_and_port_through(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)

    captured = _capture_autobuild_argv(monkeypatch)

    assert main(["dev", "--host", "127.0.0.1", "--port", "9000"]) == 0

    argv = captured["argv"]
    assert "--host" in argv and argv[argv.index("--host") + 1] == "127.0.0.1"
    assert "--port" in argv and argv[argv.index("--port") + 1] == "9000"


def test_compiled_assets_carry_sidebar_contract(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    static = tmp_path / "_build" / "html" / "_static"
    js = (static / "thdocs.js").read_text(encoding="utf-8")
    css = (static / "thdocs.css").read_text(encoding="utf-8")

    # The JS bundle has to know about the data attributes the sidebar template uses,
    # otherwise the tabs won't switch when clicked. Strings survive minification.
    assert "data-tab" in js
    assert "data-panel" in js

    # The CSS bundle has to carry our sidebar component styles. We check for two
    # selectors so that a regression in either the @layer components block or the
    # token-using rule gets caught.
    assert ".thdocs-tabs" in css
    assert ".thdocs-tab-panel" in css
