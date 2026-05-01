default: dev

dev:
    uv run thdocs dev

build:
    uv run thdocs build

build-theme:
    cd theme-src && pnpm build
