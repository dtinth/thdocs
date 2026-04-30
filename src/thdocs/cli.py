import argparse
import os
from pathlib import Path

from sphinx.cmd.build import build_main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="thdocs")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="Build the documentation site.")
    args = parser.parse_args(argv)

    if args.command == "build":
        return _build()
    raise AssertionError(f"unhandled command: {args.command}")


def _build() -> int:
    project_root = Path.cwd()
    if not (project_root / "thdocs.toml").exists():
        raise SystemExit("thdocs.toml not found in current directory")

    srcdir = project_root / "docs"
    outdir = project_root / "_build" / "html"
    confdir = Path(__file__).parent / "sphinx"

    os.environ["THDOCS_PROJECT"] = str(project_root)
    return build_main(["-c", str(confdir), "-b", "html", str(srcdir), str(outdir)])
