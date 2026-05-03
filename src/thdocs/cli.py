import argparse
import os
import shutil
import tomllib
from pathlib import Path

from sphinx.cmd.build import build_main
from sphinx.cmd import make_mode
import sphinx_autobuild.__main__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="thdocs")
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="Build the documentation site.")
    build_parser.add_argument("--pdf", action="store_true", help="Build only the PDF.")
    build_parser.add_argument("--with-pdf", action="store_true", help="Build HTML + PDF and include a PDF download link in the site.")
    dev = sub.add_parser("dev", help="Live-reload dev server.")
    dev.add_argument("--host", default="0.0.0.0", help="Bind address (default: 0.0.0.0).")
    dev.add_argument("--port", default="20080", help="Bind port (default: 20080).")
    sub.add_parser("init", help="Scaffold a new docs project in the current directory.")
    args = parser.parse_args(argv)

    if args.command == "build":
        return _build(pdf=args.pdf, with_pdf=args.with_pdf)
    if args.command == "dev":
        return _dev(host=args.host, port=args.port)
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


def _dev(*, host: str, port: str) -> int:
    srcdir, outdir, confdir = _get_project_paths()
    return sphinx_autobuild.__main__.main(
        [
            "--host", host,
            "--port", port,
            "-c", str(confdir),
            "-b", "html",
            str(srcdir),
            str(outdir),
        ]
    )


def _slugify(title: str) -> str:
    return title.lower().replace(" ", "-")


def _build(*, pdf: bool = False, with_pdf: bool = False) -> int:
    srcdir, outdir, confdir = _get_project_paths()

    if pdf:
        return _build_pdf_only(srcdir, confdir)

    if with_pdf:
        return _build_with_pdf(srcdir, outdir, confdir)

    return build_main(["-c", str(confdir), "-b", "html", str(srcdir), str(outdir)])


def _build_pdf_only(srcdir: Path, confdir: Path) -> int:
    os.environ["THDOCS_PDF_BUILD"] = "1"
    pdf_outdir = srcdir.parent / "_build" / "pdf"
    ret = make_mode.run_make_mode(
        ["latexpdf", str(srcdir), str(pdf_outdir), "-c", str(confdir)]
    )
    if ret:
        print("PDF build failed — is LaTeX (xelatex) installed?")
    return ret


def _build_with_pdf(srcdir: Path, outdir: Path, confdir: Path) -> int:
    toml_path = srcdir.parent / "thdocs.toml"
    cfg = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    title = cfg["site"]["title"]
    pdf_filename = _slugify(title) + ".pdf"

    os.environ["THDOCS_PDF"] = pdf_filename

    ret = build_main(["-c", str(confdir), "-b", "html", str(srcdir), str(outdir)])
    if ret:
        return ret

    os.environ["THDOCS_PDF_BUILD"] = "1"
    pdf_outdir = srcdir.parent / "_build" / "pdf"
    ret = make_mode.run_make_mode(
        ["latexpdf", str(srcdir), str(pdf_outdir), "-c", str(confdir)]
    )
    if ret:
        print("PDF build failed — is LaTeX (xelatex) installed?")
        return ret

    src = pdf_outdir / "latex" / "index.pdf"
    dst = outdir / "_static" / pdf_filename
    shutil.copy2(src, dst)
    print(f"PDF copied to {dst}")
    return 0
