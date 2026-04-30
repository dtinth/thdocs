import argparse
import os
from pathlib import Path

from sphinx.cmd.build import build_main
import sphinx_autobuild.__main__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="thdocs")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Build the documentation site.")
    sub.add_parser("dev", help="Live-reload dev server.")
    sub.add_parser("init", help="Scaffold a new docs project in the current directory.")
    args = parser.parse_args(argv)

    if args.command == "build":
        return _build()
    if args.command == "dev":
        return _dev()
    if args.command == "init":
        return _init()
    raise AssertionError(f"unhandled command: {args.command}")


def _init() -> int:
    project_root = Path.cwd()
    title = project_root.name or "Documentation"

    toml_path = project_root / "thdocs.toml"
    if not toml_path.exists():
        toml_path.write_text(
            f'[site]\ntitle = "{title}"\n',
            encoding="utf-8",
        )

    docs_dir = project_root / "docs"
    docs_dir.mkdir(exist_ok=True)
    index_md = docs_dir / "index.md"
    if not index_md.exists():
        index_md.write_text(
            f"# {title}\n"
            "\n"
            "Welcome. Add pages below and link them from the toctree.\n"
            "\n"
            "```{toctree}\n"
            ":maxdepth: 2\n"
            "```\n",
            encoding="utf-8",
        )

    gitignore = project_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if "_build" not in existing.splitlines():
        with gitignore.open("a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("_build/\n")

    return 0


def _get_project_paths() -> tuple[Path, Path, Path]:
    """Discover project paths and return (srcdir, outdir, confdir)."""
    project_root = Path.cwd()
    if not (project_root / "thdocs.toml").exists():
        raise SystemExit("thdocs.toml not found in current directory")

    srcdir = project_root / "docs"
    outdir = project_root / "_build" / "html"
    confdir = Path(__file__).parent / "sphinx"

    os.environ["THDOCS_PROJECT"] = str(project_root)
    return srcdir, outdir, confdir


def _dev() -> int:
    srcdir, outdir, confdir = _get_project_paths()
    return sphinx_autobuild.__main__.main(["-c", str(confdir), "-b", "html", str(srcdir), str(outdir)])


def _build() -> int:
    srcdir, outdir, confdir = _get_project_paths()
    return build_main(["-c", str(confdir), "-b", "html", str(srcdir), str(outdir)])
