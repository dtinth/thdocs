import shutil
from pathlib import Path

import pytest

from thdocs.cli import main


_has_xelatex = shutil.which("xelatex") is not None


def _write_project(
    root: Path,
    *,
    title: str,
    pages: dict[str, str],
    genindex: bool | None = None,
    author: str | None = None,
    version: str | None = None,
) -> None:
    lines = ["[site]", f'title = "{title}"']
    if author is not None:
        lines.append(f'author = "{author}"')
    if version is not None:
        lines.append(f'version = "{version}"')
    if genindex is not None:
        lines.append(f"genindex = {str(genindex).lower()}")
    (root / "thdocs.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
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


def test_toctree_external_links_preserved(tmp_path: Path, monkeypatch) -> None:
    index_md = (
        "# Welcome\n"
        "\n"
        "```{toctree}\n"
        "guide\n"
        "License <https://example.com/license>\n"
        "https://github.com/dtinth/bizdocgen/blob/main/LICENSE\n"
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
    toctree_js = (tmp_path / "_build" / "html" / "_static" / "toctree.js").read_text(
        encoding="utf-8"
    )

    import json

    # Strip the JS assignment to get the raw JSON payload
    json_payload = toctree_js.replace("window.TOCTREE_DATA = ", "").rstrip(";")
    data = json.loads(json_payload)

    items = data["items"]
    assert len(items) == 3

    # Explicit title is preserved
    license_item = items[1]
    assert license_item["title"] == "License"
    assert license_item["href"] == "https://example.com/license"
    assert license_item["id"] == "https://example.com/license"
    assert license_item["children"] == []

    # No explicit title falls back to the raw URL
    github_item = items[2]
    assert github_item["title"] == "https://github.com/dtinth/bizdocgen/blob/main/LICENSE"
    assert github_item["href"] == "https://github.com/dtinth/bizdocgen/blob/main/LICENSE"
    assert github_item["id"] == "https://github.com/dtinth/bizdocgen/blob/main/LICENSE"
    assert github_item["children"] == []


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
        genindex=True,
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


def test_sidebar_without_genindex_has_two_tabs(
    tmp_path: Path, monkeypatch
) -> None:
    _write_project(
        tmp_path,
        title="Site",
        pages={"index.md": "# Welcome\n"},
    )
    monkeypatch.chdir(tmp_path)

    assert main(["build"]) == 0

    rendered = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")

    # Only Contents and Search tabs exist.
    assert 'data-tab="contents"' in rendered
    assert 'data-tab="search"' in rendered
    assert 'data-tab="index"' not in rendered

    # Only Contents and Search panels exist.
    assert 'data-panel="contents"' in rendered
    assert 'data-panel="search"' in rendered
    assert 'data-panel="index"' not in rendered


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


def test_sidebar_is_visible_at_first_paint(
    tmp_path: Path, monkeypatch
) -> None:
    """The sidebar must be visible at first paint by overriding Sphinx's
    float/margin trick that hides it offscreen.
    """
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    css = (tmp_path / "_build" / "html" / "_static" / "thdocs.css").read_text(
        encoding="utf-8"
    )

    # The CSS must neutralize Sphinx's basic.css float and margin trick that
    # pushes the sidebar off-screen. We check for either explicit overrides
    # (margin-left: 0 or margin-left: unset) or a layout shift to flex/grid.
    # The simplest check: the compiled CSS must contain a rule that sets
    # margin-left on .sphinxsidebar to something other than -100%.
    assert ".sphinxsidebar" in css
    # Verify we're overriding the float and margin-left offscreen trick.
    # Look for margin-left: 0 or margin-left: unset or float: none.
    import re
    has_override = bool(
        re.search(
            r"\.sphinxsidebar\s*\{[^}]*(margin-left:\s*(0|unset|auto)|float:\s*none)[^}]*\}",
            css,
        )
    )
    assert has_override, "CSS must override .sphinxsidebar's float/margin-left offscreen trick"


def test_dark_theme_and_fonts_applied(tmp_path: Path, monkeypatch) -> None:
    """The thdocs theme applies the dark color scheme and custom fonts."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    # Check compiled CSS contains the dark body background color.
    css = (tmp_path / "_build" / "html" / "_static" / "thdocs.css").read_text(
        encoding="utf-8"
    )
    assert "#353433" in css, "CSS must contain dark body background color #353433"
    assert "Arimo" in css, "CSS must contain Arimo font name"

    # Check HTML head contains font loading links.
    index_html = (tmp_path / "_build" / "html" / "index.html").read_text(
        encoding="utf-8"
    )
    assert (
        "fonts.googleapis.com/css2?family=Arimo" in index_html
    ), "HTML must contain Google Fonts Arimo link"
    assert "comic-mono" in index_html, "HTML must contain Comic Mono CDN link"


def test_prose_dark_theme_applied(tmp_path: Path, monkeypatch) -> None:
    """Prose content uses dark theme colors, not Tailwind typography's light defaults."""
    markdown = (
        "# Heading\n"
        "\n"
        "This is a paragraph with `inline code` and a [link](https://example.com).\n"
        "\n"
        "```\ncode block\n```\n"
    )
    _write_project(tmp_path, title="Site", pages={"index.md": markdown})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    css = (tmp_path / "_build" / "html" / "_static" / "thdocs.css").read_text(
        encoding="utf-8"
    )

    # Verify key prose dark theme tokens are set (check for variable references or explicit values).
    assert "--tw-prose-body" in css, "CSS must set --tw-prose-body"
    assert "--tw-prose-pre-bg" in css, "CSS must set --tw-prose-pre-bg"
    assert "--tw-prose-links" in css, "CSS must set --tw-prose-links"

    # Verify the values match apiref's dark theme (body text light, pre bg dark, links yellow).
    # Body text should be light (#e9e8e7 or var reference to thdocs-text).
    assert (
        "#e9e8e7" in css or "var(--color-thdocs-text)" in css
    ), "Prose body text must be light (#e9e8e7)"
    # Pre bg should be dark sidebar color (#252423 or var reference to thdocs-sidebar).
    assert (
        "#252423" in css or "var(--color-thdocs-sidebar)" in css
    ), "Prose pre bg must be dark (#252423)"
    # Links should be yellow (#ffffbb, #ffb hex shorthand, or var reference to thdocs-accent-yellow).
    assert (
        "#ffffbb" in css or "#ffb" in css or "var(--color-thdocs-accent-yellow)" in css
    ), "Prose links must be yellow (#ffffbb)"


def test_sidebar_is_fixed_to_left(tmp_path: Path, monkeypatch) -> None:
    """The sidebar must be fixed positioned on the left side."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    css = (tmp_path / "_build" / "html" / "_static" / "thdocs.css").read_text(
        encoding="utf-8"
    )
    # The CSS must fix the sidebar to the left viewport edge
    assert ".sphinxsidebar" in css
    import re
    has_fixed_left = bool(
        re.search(
            r"\.sphinxsidebar\s*\{[^}]*position\s*:\s*fixed[^}]*\}",
            css,
        )
    ) and bool(
        re.search(
            r"\.sphinxsidebar\s*\{[^}]*left\s*:\s*0[^}]*\}",
            css,
        )
    )
    assert has_fixed_left, "CSS must set .sphinxsidebar to position: fixed with left: 0"


def test_page_toc_aside_renders_with_h2_links(tmp_path: Path, monkeypatch) -> None:
    """The right rail 'On this page' aside must render with h2/h3 links."""
    index_md = (
        "# Welcome\n"
        "\n"
        "## Section A\n"
        "\n"
        "Content here.\n"
        "\n"
        "## Section B\n"
        "\n"
        "More content.\n"
    )
    _write_project(tmp_path, title="Site", pages={"index.md": index_md})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")

    # The aside with class thdocs-page-toc must exist
    assert 'class="thdocs-page-toc"' in html

    # The heading "On this page" must exist
    assert "On this page" in html

    # Links to both sections must exist in the aside
    assert "#section-a" in html
    assert "#section-b" in html


def test_page_toc_scrollspy_js_is_shipped(tmp_path: Path, monkeypatch) -> None:
    """The scrollspy JS code must be present in the compiled bundle."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    js = (tmp_path / "_build" / "html" / "_static" / "thdocs.js").read_text(
        encoding="utf-8"
    )

    # The JS must contain IntersectionObserver and the scrollspy active class
    assert "IntersectionObserver" in js, "JS must contain IntersectionObserver"
    assert (
        "thdocs-toc-active" in js
    ), "JS must contain thdocs-toc-active class reference"


def test_bundled_docs_project_builds(monkeypatch) -> None:
    """The real docs/ project at the repo root builds successfully and renders the kitchen sink."""
    import subprocess

    # Find the repo root (parent of tests/ directory).
    test_file = Path(__file__)
    repo_root = test_file.parent.parent
    docs_dir = repo_root / "docs"

    assert docs_dir.exists(), f"docs/ directory not found at {docs_dir}"

    monkeypatch.chdir(repo_root)
    exit_code = main(["build"])

    assert exit_code == 0, "docs project build failed"

    index_html = repo_root / "_build" / "html" / "index.html"
    assert index_html.exists(), f"index.html not found at {index_html}"

    index_content = index_html.read_text(encoding="utf-8")
    assert "Getting Started" in index_content, "Landing page must mention 'Getting Started'"
    assert "Kitchen Sink" in index_content, "Landing page must mention 'Kitchen Sink'"
    assert "Internals" in index_content, "Landing page must mention 'Internals'"

    kitchen_sink_html = repo_root / "_build" / "html" / "kitchen-sink.html"
    assert kitchen_sink_html.exists(), f"kitchen-sink.html not found at {kitchen_sink_html}"

    ks_content = kitchen_sink_html.read_text(encoding="utf-8")
    assert "<table" in ks_content, "Kitchen sink must contain a table"
    assert "<details" in ks_content, "Kitchen sink must contain a details/summary block"
    assert "<kbd" in ks_content, "Kitchen sink must contain a <kbd> element"


def test_toctree_toggle_js_is_shipped(tmp_path: Path, monkeypatch) -> None:
    """The toctree collapse toggle functionality must be compiled into thdocs.js."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    js = (tmp_path / "_build" / "html" / "_static" / "thdocs.js").read_text(
        encoding="utf-8"
    )

    # The JS must contain the tree toggle icon class and aria-expanded attribute references.
    assert "thdocs-tree__icon" in js, "JS must contain thdocs-tree__icon class"
    assert "aria-expanded" in js, "JS must contain aria-expanded attribute"


def test_toctree_collapsed_by_default_via_js(tmp_path: Path, monkeypatch) -> None:
    """The toctree collapse JS must hide nested lists when parent is collapsed."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    js = (tmp_path / "_build" / "html" / "_static" / "thdocs.js").read_text(
        encoding="utf-8"
    )

    # The JS must set display:none on child <ul> when toggle is collapsed.
    assert "style.display" in js, "JS must hide nested <ul> via style.display"


def test_toctree_nav_memory_js_is_shipped(tmp_path: Path, monkeypatch) -> None:
    """The toctree nav memory JS (scroll and focus restoration) must be compiled into thdocs.js."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    js = (tmp_path / "_build" / "html" / "_static" / "thdocs.js").read_text(
        encoding="utf-8"
    )

    # The JS must contain the sessionStorage keys for scroll and focus restoration.
    assert "thdocs-tree-scroll" in js, "JS must contain thdocs-tree-scroll key"
    assert "thdocs-tree-focus" in js, "JS must contain thdocs-tree-focus key"
    # The JS must contain the preventScroll focus option.
    assert "preventScroll" in js, "JS must contain preventScroll for safe focus restoration"


def test_copyright_includes_author_name(tmp_path: Path, monkeypatch) -> None:
    """When author is set, the footer copyright includes the author name."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"}, author="Ada Lovelace")
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "Copyright" in html
    assert "Ada Lovelace" in html


def test_copyright_without_author_is_year_only(tmp_path: Path, monkeypatch) -> None:
    """When no author is set, the footer copyright shows only the year."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "Copyright" in html
    # Make sure no comma follows "Copyright <year>" when author is absent.
    import re

    match = re.search(r"Copyright\s+\d{4}([^<]*)\.", html)
    assert match is not None
    assert "," not in match.group(1), "Copyright should not have a comma when author is absent"


def test_version_from_toml_appears_in_page_title(tmp_path: Path, monkeypatch) -> None:
    """A version set in thdocs.toml appears in the rendered page title."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"}, version="3.2.1")
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "3.2.1" in html


def test_version_auto_detected_from_package_json(tmp_path: Path, monkeypatch) -> None:
    """If no version is set and package.json exists, version is auto-detected."""
    _write_project(tmp_path, title="Site", pages={"index.md": "# Hi\n"})
    (tmp_path / "package.json").write_text(
        '{"name": "test", "version": "7.8.9"}', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "7.8.9" in html


def test_version_from_custom_json_file(tmp_path: Path, monkeypatch) -> None:
    """A version ending in '.json' is treated as a JSON file path to read."""
    _write_project(
        tmp_path, title="Site", pages={"index.md": "# Hi\n"}, version="manifest.json"
    )
    (tmp_path / "manifest.json").write_text(
        '{"version": "4.5.6"}', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert main(["build"]) == 0

    html = (tmp_path / "_build" / "html" / "index.html").read_text(encoding="utf-8")
    assert "4.5.6" in html


@pytest.mark.skipif(not _has_xelatex, reason="xelatex not installed")
def test_pdf_external_links_use_footnotes(tmp_path: Path, monkeypatch) -> None:
    """External URLs in PDF appear as footnotes, not inline."""
    _write_project(
        tmp_path,
        title="Site",
        pages={"index.md": "# Hello\n\nVisit [example](https://example.com).\n"},
    )
    monkeypatch.chdir(tmp_path)
    assert main(["build", "--pdf"]) == 0

    tex = (tmp_path / "_build" / "pdf" / "latex" / "index.tex").read_text(encoding="utf-8")
    # Sphinx with latex_show_urls='footnote' puts the URL in a footnote.
    assert "\\sphinxhref{https://example.com}" in tex
    assert "\\begin{footnote}" in tex


@pytest.mark.skipif(not _has_xelatex, reason="xelatex not installed")
def test_pdf_internal_links_show_page_refs(tmp_path: Path, monkeypatch) -> None:
    """Internal cross-references in PDF include page numbers."""
    _write_project(
        tmp_path,
        title="Site",
        pages={
            "index.md": (
                "# Welcome\n\n"
                "```{toctree}\n"
                "guide\n"
                "```\n\n"
                "See {doc}`guide` for details.\n"
            ),
            "guide.md": "# Guide\n\nSome info.\n",
        },
    )
    monkeypatch.chdir(tmp_path)
    assert main(["build", "--pdf"]) == 0

    tex = (tmp_path / "_build" / "pdf" / "latex" / "index.tex").read_text(encoding="utf-8")
    # latex_show_pagerefs=True adds \autopageref* after internal cross-references.
    assert "\\autopageref" in tex
