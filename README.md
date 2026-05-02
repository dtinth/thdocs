# thdocs — Development

See [CONTEXT.md](CONTEXT.md) for project design and philosophy.

## Setup

Install toolchain versions via mise:

```bash
mise install
```

This activates Node.js, pnpm, Python, and uv as defined in `mise.toml`.

## Development

**Build theme assets** (TypeScript + Tailwind CSS):

```bash
just build-theme
```

Outputs `_static/thdocs.css` and `_static/thdocs.js`, consumed by the theme.

**Build documentation site** (one-shot):

```bash
just build
```

Builds the demo site from `/docs` into `_build/html`. Requires theme assets to exist.

**Live-reload dev server**:

```bash
just dev
```

Watches `/docs` and rebuilds on file changes. Skips Pagefind (search) and PDF for speed.
Access at `http://localhost:8000`.

**Rebuild theme on changes** (when editing `theme-src/src/`):

Theme assets don't rebuild automatically yet. Rerun `just build-theme` after edits.

## Testing

**All tests** (Python pytest + Playwright):

```bash
uv run pytest
```

This runs two suites:

1. **Static tests** (`tests/test_build.py`, 24 tests) — Verify build artifacts: HTML structure, CSS linking, directive rendering, toctree generation. Run offline.
2. **Browser tests** (`tests/test_browser.py`, 5 tests) — Verify JS behaviors in a real Chromium instance: sidebar layout, toctree collapse persistence, scroll/focus restoration, scrollspy. Load HTML via `file://` (no HTTP server).

**Run one suite**:

```bash
uv run pytest tests/test_build.py
uv run pytest tests/test_browser.py
```

**Run a single test**:

```bash
uv run pytest tests/test_browser.py::test_sidebar_renders_on_left -v
```

All tests scaffold a temporary project, build it, and validate the output.

## File structure

- `src/thdocs/` — Python package (CLI, Sphinx config, Jinja templates)
- `theme-src/` — Node.js + TypeScript (theme assets)
  - `src/main.ts` — JS behaviors (sidebar tabs, scrollspy, toctree collapse, scroll/focus memory)
  - `src/main.css` — Dark prose theme (Tailwind v4, unlayered rules, CSS grid layout)
- `docs/` — Demo documentation site (tests `thdocs` against itself)
  - `index.md`, `getting-started.md`, `cli.md`, `theming.md`, `kitchen-sink.md`
  - `adr/` — Architecture decision records
- `tests/` — Python pytest + Playwright browser tests
- `justfile` — Task runner (build, dev, build-theme)
- `thdocs.toml` — Demo site config (title, theme toggles)

## Full rebuild

```bash
just build-theme && just build
```

## Updating theme tokens

The Tailwind theme variables in `theme-src/src/main.css` are vendored from `shell`'s design system (at `~/ghq/dtinth/apiref`). Edit manually as needed; there's no automated sync yet.
