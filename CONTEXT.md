# thdocs — Context

## Purpose

A reusable **documentation generator** the author can apply to all their
projects. Input: Markdown files. Output: a documentation site (and PDF).
Sphinx is an *implementation detail*, not the product.

The author is docs-tool-fatigued (Jekyll, Middleman, Read the Docs,
Docusaurus, VuePress, VitePress, Antora, MkDocs) and was nearly going to
build a generator from scratch. Sphinx was chosen because it now supports
CommonMark (via MyST) and modern themes, and it generates PDFs natively.

Aesthetic / feature inspiration: classic Windows **CHM** help files —
comprehensive feature set, well-considered structure.

## Glossary

- **thdocs** — the documentation generator being built here. Not a single
  site; a tool/template the author will reuse across projects.
- **Source** — Markdown files authored by the user. The input contract.
- **Site** — the rendered HTML output (and PDF as a secondary target).
- **Sphinx** — implementation engine. Not exposed in the user-facing
  contract; could in principle be swapped.
- **Design language** — the author's personal visual identity, shared with
  their website. The thdocs theme must render sites that feel like part of
  the same family.
- **apiref** — the author's separate API-reference generator
  (`dtinth/apiref`). thdocs is a *sibling* tool, not a fork; they should
  share the design language but solve different problems.
- **shell** — `@apiref/shell`, the design-system package inside apiref. A
  pnpm-workspace package that builds to `dist/styles.css` (Tailwind v4,
  `@theme` tokens) plus `dist/shell.js` (Lit web components: `<ar-shell>`,
  `<ar-header>`, `<ar-nav>`, `<ar-outline>`). For thdocs, shell is a
  **visual reference**, not a runtime dependency: we read its CSS, copy
  tokens and prose treatments, and adapt them to fit Sphinx's HTML shape.

## Shape

`thdocs` is a **CLI wrapper**: `thdocs build ./docs` takes a directory of
Markdown and emits a site. Sphinx runs underneath.

**Boundary.** Sphinx *config* is invisible (no `conf.py`, no extension
names, no theme paths). Sphinx *content authoring* — MyST directives,
notably `{toctree}`, plus MyST cross-refs — is part of the user-facing
contract. The author learns a small set of directives; they do not learn
Sphinx configuration.

**Structure source.** The page hierarchy lives in the Markdown itself, via
`{toctree}` directives in section `index.md` files. There is no `[nav]`
section in any config file, no frontmatter `order:`, no filesystem-implied
ordering. The directive owns it.

**Site config.** A small `thdocs.toml` at the project root carries
*site identity* only: title, base URL, repo URL (for edit links), PDF
metadata, theme toggles. Not navigation.

## Distribution

For now, the author installs from source: `uv tool install -e . --reinstall`.
No PyPI publishing yet. The package is structured as a normal,
publishable Python package (proper `[project.scripts]` entry, real
version, no hardcoded local paths) so that the future plan —
`uv tool install thdocs` globally + per-project pinning via mise
(`[tools] "uv:thdocs" = "..."`) — is a no-op when reproducible builds
across projects become important. Don't optimize for the editable case at
the cost of the publishable one.

## Theme strategy

- **shell is a visual reference, not a runtime dependency.** thdocs's
  theme has its own class names, its own Jinja templates, and its own
  CSS — written to fit Sphinx's HTML output. We read shell's CSS, copy
  tokens and prose treatments we want, and adapt them. We do not link
  shell's compiled stylesheet, and we do not use its Lit components.
  Server-rendered HTML works for both web and PDF builds, and lets thdocs
  reuse Sphinx's mature `toctree` model instead of fighting it.
- **Tailwind compiles at theme-author time.** thdocs's repo runs
  `tailwindcss` (with `@tailwindcss/typography`) to produce a single
  `thdocs.css` bundled into the published Python wheel as a static asset.
  End users only need `uv` — no Node toolchain.
- **Tokens are vendored.** shell's `@theme` block (and any prose CSS we
  borrow) is copy-pasted into thdocs's Tailwind input. Tokens are stable
  enough that automated sync (submodule / npm dep) isn't worth its
  complexity. Drift is managed by occasional manual re-sync.

## Sphinx invocation

thdocs ships a static `conf.py` inside its own package (e.g.
`src/thdocs/sphinx/conf.py`). The CLI invokes Sphinx as
`sphinx-build -c <thdocs-pkg>/sphinx <project>/docs <project>/_build/html`,
passing the project root via `THDOCS_PROJECT` env var. The shipped
`conf.py` reads `<project>/thdocs.toml` and translates it into Sphinx
settings (project, author, extensions, theme path, static path).

This keeps the project repo free of Sphinx config files while staying
fully compatible with `sphinx-autobuild` (used by `thdocs dev`).

## Working style

Build in small steps with TDD. Each change is gated by a simple
acceptance test calibrated to the right granularity — neither a snapshot
of exact HTML shape nor "doesn't crash." The reference pattern:

> *Set `title = "Foobar"` in `thdocs.toml`, run `thdocs build`,
> assert the word "Foobar" appears in `_build/html/index.html`.*

Tests describe externally observable behavior of the CLI + rendered site,
not internal implementation details.

## CLI surface

Three verbs in v1:

- **`thdocs build`** — one-shot build. Orchestrates `sphinx-build` then
  `pagefind` over the HTML output. `--pdf` adds the LaTeX builder pass.
  `--strict` is `sphinx-build -W` (treat warnings as errors).
- **`thdocs dev`** — live-reload dev server (essentially a wrapper around
  `sphinx-autobuild`). Skips Pagefind for speed; the Search tab shows a
  "disabled in dev mode" message. Skips PDF.
- **`thdocs init`** — scaffold a new docs project in cwd: writes
  `thdocs.toml`, `docs/index.md` (with a sample `{toctree}`), and
  appends `_build/` to `.gitignore`.

No `check` or `clean` in v1.

## Feature set (v1)

CHM-inspired chrome — the left sidebar has **three tabs**, for CHM
nostalgia:

1. **Contents** — tree-style TOC, server-rendered from `{toctree}`.
2. **Index** — alphabetical index, server-rendered from `{index}`
   directives (Sphinx's `genindex`), inlined into the sidebar by the theme.
3. **Search** — full-text search powered by **Pagefind**. Run as a
   post-build step over Sphinx's HTML output. The theme uses Pagefind's
   JS API to render results into the tab; we do not use Pagefind's
   default modal UI.

Plus:

- **Glossary with hovercard popups.** The `glossary` directive renders a
  glossary page; theme JS turns `{term}` links into hover-cards. This is
  the one custom JS surface in the theme.
- **PDF output.** Sphinx LaTeX builder. Server-rendered, so it just works.

Authors write MyST Markdown and use Sphinx-native directives directly:
`{toctree}`, `{index}`, `{glossary}`, `{seealso}`, `{ref}`, `{doc}`.
No premature abstraction over them — Sphinx is stable, the theme is the
part still in flux.

## Non-goals

- reStructuredText as an input format (author dislikes it).
- AsciiDoc as an input format (author dislikes it).
- Bookmarks / favorites (per-user state — out of scope for a static
  generator).
- Context-sensitive help / app-integration help IDs — apps can deep-link
  to the rendered help page directly.
- An abstraction layer over Sphinx's authoring directives. The user
  contract embraces MyST + Sphinx directives as-is.
