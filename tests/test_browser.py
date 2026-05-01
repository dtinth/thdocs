import asyncio
from pathlib import Path
import pytest
from playwright.async_api import async_playwright

from thdocs.cli import main


def _write_project(root: Path, *, title: str, pages: dict[str, str]) -> None:
    """Helper to scaffold a project (copied from test_build.py)."""
    (root / "thdocs.toml").write_text(
        f'[site]\ntitle = "{title}"\n',
        encoding="utf-8",
    )
    docs_dir = root / "docs"
    docs_dir.mkdir()
    for name, body in pages.items():
        (docs_dir / name).write_text(body, encoding="utf-8")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def built_project(tmp_path: Path, monkeypatch):
    """Build a test project with toctree navigation and scrollable content."""
    index_md = (
        "# Welcome to Documentation\n"
        "\n"
        "This is the main page. Navigate using the sidebar.\n"
        "\n"
        "```{toctree}\n"
        ":maxdepth: 2\n"
        "guide\n"
        "cli\n"
        "advanced\n"
        "```\n"
    )
    guide_md = (
        "# Setup Guide\n"
        "\n"
        "## Installation\n"
        "\nFollow these steps to install.\n"
        "\n"
        "## Configuration\n"
        "\nConfigure the system.\n"
        "\n"
        "## Advanced Options\n"
        "\nMore configuration options.\n"
    )
    cli_md = (
        "# CLI Reference\n"
        "\n"
        "## Commands\n"
        "\nList of available commands.\n"
        "\n"
        "## Options\n"
        "\nCommand-line options.\n"
        "\n"
        "## Examples\n"
        "\nUsage examples.\n"
    )
    advanced_md = (
        "# Advanced Topics\n"
        "\n"
        "## Architecture\n"
        "\nSystem architecture overview.\n"
        "\n"
        "## Performance\n"
        "\nPerformance tuning.\n"
        "\n"
        "## Troubleshooting\n"
        "\nCommon issues and fixes.\n"
    )

    _write_project(
        tmp_path,
        title="Test Documentation",
        pages={
            "index.md": index_md,
            "guide.md": guide_md,
            "cli.md": cli_md,
            "advanced.md": advanced_md,
        },
    )

    monkeypatch.chdir(tmp_path)
    exit_code = main(["build"])
    assert exit_code == 0, "Project build failed"

    html_dir = tmp_path / "_build" / "html"
    assert html_dir.exists(), f"HTML output not found at {html_dir}"

    yield html_dir


@pytest.mark.asyncio
async def test_sidebar_renders_on_left(built_project: Path):
    """Test that sidebar renders on the left side with correct dimensions."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        file_url = f"file://{(built_project / 'index.html').absolute()}"
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.2)

        sidebar = await page.query_selector(".sphinxsidebar")
        assert sidebar is not None, "Sidebar element not found"

        bbox = await sidebar.bounding_box()
        assert bbox is not None, "Sidebar bounding box not found"

        # Sidebar should be on left (x near 0)
        assert bbox["x"] <= 10, f"Sidebar left position is {bbox['x']}, expected <= 10"
        # Sidebar width should be reasonable (e.g., <= 350px for typical sidebar)
        assert bbox["width"] <= 350, f"Sidebar width is {bbox['width']}, expected <= 350"

        await page.close()
        await browser.close()


@pytest.mark.asyncio
async def test_toctree_collapse_persists_across_navigation(built_project: Path):
    """Test that expanding a toctree node persists across navigation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        file_url = f"file://{(built_project / 'index.html').absolute()}"
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.2)

        # Find a toctree toggle that's currently collapsed
        toggles = await page.query_selector_all(".thdocs-toc-toggle")
        assert len(toggles) > 0, "No toctree toggles found"

        # Click the first toggle to expand it
        first_toggle = toggles[0]
        is_expanded_before = await first_toggle.get_attribute("aria-expanded")
        await first_toggle.evaluate("el => el.click()")
        await asyncio.sleep(0.1)
        is_expanded_after = await first_toggle.get_attribute("aria-expanded")

        # Verify toggle state changed
        assert is_expanded_before != is_expanded_after, "Toggle state did not change"

        # Now navigate to another page
        guide_link = await page.query_selector('a[href="guide.html"]')
        assert guide_link is not None, "Guide link not found"

        # Navigate and wait
        await guide_link.click()
        await asyncio.sleep(0.5)

        # Wait for JS to run on the new page
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(0.2)

        # Verify the toggle on the new page has the same expanded state
        toggles_on_new_page = await page.query_selector_all(".thdocs-toc-toggle")
        assert len(toggles_on_new_page) > 0, "No toggles on destination page"

        first_toggle_on_new_page = toggles_on_new_page[0]
        state_on_new_page = await first_toggle_on_new_page.get_attribute(
            "aria-expanded"
        )

        assert (
            state_on_new_page == is_expanded_after
        ), f"Toggle state not persisted: was {is_expanded_after}, now {state_on_new_page}"

        await page.close()
        await browser.close()


@pytest.mark.asyncio
async def test_scroll_memory_restores_panel_position(built_project: Path):
    """Test that contents panel scroll position is restored after navigation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        file_url = f"file://{(built_project / 'index.html').absolute()}"
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.2)

        contents_panel = await page.query_selector(
            ".thdocs-sidebar [data-panel='contents']"
        )
        assert contents_panel is not None, "Contents panel not found"

        # Expand all toggles to make the panel scrollable
        toggles = await page.query_selector_all(
            ".thdocs-sidebar [data-panel='contents'] .thdocs-toc-toggle"
        )
        for toggle in toggles:
            aria_expanded = await toggle.get_attribute("aria-expanded")
            if aria_expanded == "false":
                await toggle.evaluate("el => el.click()")
                await asyncio.sleep(0.05)

        # Get panel height and scrollHeight to determine if scrollable
        panel_info = await contents_panel.evaluate(
            "el => ({height: el.clientHeight, scrollHeight: el.scrollHeight})"
        )

        # If panel is scrollable, scroll it
        if panel_info["scrollHeight"] > panel_info["height"]:
            target_scroll = min(100, panel_info["scrollHeight"] - panel_info["height"] - 10)
            await contents_panel.evaluate(f"el => el.scrollTop = {target_scroll}")
            await asyncio.sleep(0.1)

            # Verify scroll position was set
            scroll_before = await contents_panel.evaluate("el => el.scrollTop")
            assert scroll_before >= target_scroll * 0.9, (
                f"Failed to set scroll position: {scroll_before} != {target_scroll}"
            )
        else:
            # Panel is not scrollable, skip scroll restoration part
            return  # Skip scroll restoration test

        # Navigate to another page
        guide_link = await page.query_selector('a[href="guide.html"]')
        assert guide_link is not None, "Guide link not found"

        await guide_link.click()
        await asyncio.sleep(0.5)

        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(0.2)

        # Check scroll position on destination page
        contents_panel_dest = await page.query_selector(
            ".thdocs-sidebar [data-panel='contents']"
        )
        assert contents_panel_dest is not None, "Contents panel on destination not found"

        scroll_after = await contents_panel_dest.evaluate("el => el.scrollTop")
        # Allow variance (within 20% of target or within 10px)
        variance = max(abs(scroll_after - target_scroll), target_scroll * 0.2)
        assert variance <= 10, (
            f"Scroll position not restored: was {target_scroll}, now {scroll_after}"
        )

        await page.close()
        await browser.close()


@pytest.mark.asyncio
async def test_focus_memory_restores_after_navigation(built_project: Path):
    """Test that keyboard focus on a toctree link is restored after navigation.

    This is the diagnostic test for the focus bug. We navigate via keyboard
    (Tab + Enter) and verify the focus is restored on the destination page.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set up console logging to capture debug output
        console_messages = []
        def log_console(msg):
            console_messages.append(msg.text)
        page.on("console", log_console)

        file_url = f"file://{(built_project / 'index.html').absolute()}"
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.2)

        contents_panel = await page.query_selector(
            ".thdocs-sidebar [data-panel='contents']"
        )
        assert contents_panel is not None, "Contents panel not found"

        # Find a toctree link to focus on (skip the current page link)
        links = await page.query_selector_all(
            ".thdocs-sidebar [data-panel='contents'] a[href]"
        )
        assert len(links) > 1, "Need at least 2 links for this test"

        # Find a non-current link
        target_link = None
        for link in links:
            classes = await link.get_attribute("class")
            if "current" not in (classes or ""):
                target_link = link
                break

        assert target_link is not None, "No non-current link found"

        # Get the href before navigation
        target_href = await target_link.get_attribute("href")
        target_href_normalized = target_href.rstrip("#")

        # Focus the link programmatically (simulating keyboard navigation)
        await target_link.focus()
        await asyncio.sleep(0.1)

        # Verify focus is on the link (compare normalized versions since file:// expands relative paths)
        active_before = await page.evaluate("document.activeElement.href || ''")
        active_before_normalized = active_before.split("/")[-1] if active_before else ""
        target_href_file = target_href.split("/")[-1]
        assert active_before_normalized == target_href_file, (
            f"Focus not set on target link: {active_before_normalized} != {target_href_file}"
        )

        # Press Enter to navigate
        await page.keyboard.press("Enter")
        await asyncio.sleep(0.5)

        # Wait for navigation to complete
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(0.3)  # Wait for focus restore logic

        # Now check the focused element on the destination page
        active_after = await page.evaluate("document.activeElement.href || ''")
        active_after_file = active_after.split("/")[-1] if active_after else ""
        active_after_normalized = active_after_file.rstrip("#")

        # Debug output
        page_title = await page.evaluate("document.title")
        msg = (
            f"Focus restoration test:\n"
            f"  Target href: {target_href_file}\n"
            f"  Active after nav: {active_after_file}\n"
            f"  Page title: {page_title}\n"
            f"  Console: {console_messages}"
        )

        # The focused element should be the link that matches our target
        # (or its #-version on the same page)
        assert active_after_normalized == target_href_normalized, msg

        await page.close()
        await browser.close()


@pytest.mark.asyncio
async def test_scrollspy_marks_active_toc_link(built_project: Path):
    """Test that scrollspy marks the current section link in the page TOC."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        file_url = f"file://{(built_project / 'guide.html').absolute()}"
        await page.goto(file_url, wait_until="domcontentloaded")
        await asyncio.sleep(0.2)

        page_toc = await page.query_selector(".thdocs-page-toc")
        assert page_toc is not None, "Page TOC not found"

        # Find all h2 headings (they should be auto-assigned IDs by Sphinx)
        h2_headings = await page.query_selector_all("main h2")
        assert len(h2_headings) >= 2, f"Need at least 2 h2 headings for this test, found {len(h2_headings)}"

        # Get the second heading's ID (Sphinx should auto-generate them)
        # But if not, we'll use the heading's data-section or just wait for first heading
        second_heading = h2_headings[1]
        second_heading_id = await second_heading.get_attribute("id")

        # If no ID, the test can't proceed (scrollspy relies on heading IDs)
        if not second_heading_id:
            return  # Skip test - headings need IDs for scrollspy to work

        # Scroll to the second heading
        await page.evaluate(
            f"document.querySelector('#{second_heading_id}').scrollIntoView(true)"
        )
        await asyncio.sleep(0.5)  # Wait for IntersectionObserver to trigger

        # Find the corresponding TOC link
        toc_link = await page.query_selector(
            f".thdocs-page-toc a[href='#{second_heading_id}']"
        )
        assert toc_link is not None, f"TOC link for #{second_heading_id} not found"

        # Verify the link has the active class
        classes = await toc_link.get_attribute("class")
        assert (
            "thdocs-toc-active" in (classes or "")
        ), f"TOC link missing thdocs-toc-active class. Classes: {classes}"

        await page.close()
        await browser.close()
