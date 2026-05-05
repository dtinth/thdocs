"""Sphinx extension: download remote images and convert WebP for LaTeX builder."""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from docutils import nodes
from PIL import Image
from sphinx.application import Sphinx
from sphinx.util import logging

logger = logging.getLogger(__name__)


def _is_remote(uri: str) -> bool:
    return uri.startswith(("http://", "https://"))


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "thdocs/0.1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        dest.write_bytes(response.read())


def _convert_webp(src: Path, dest: Path) -> None:
    with Image.open(src) as im:
        # Convert to RGB if necessary (e.g., RGBA WebP)
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(dest, "PNG")


def _is_webp(path: Path) -> bool:
    ext = path.suffix.lower()
    if ext == ".webp":
        return True
    # Check file magic bytes (RIFF....WEBP)
    header = path.read_bytes()[:12]
    return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"


def _ensure_local_image(uri: str, cache_dir: Path) -> str:
    url_hash = hashlib.sha256(uri.encode()).hexdigest()[:16]
    ext = Path(uri).suffix.split("?")[0].lower() or ".bin"
    cached = cache_dir / f"{url_hash}{ext}"

    if not cached.exists():
        logger.info("Downloading remote image: %s", uri)
        _download(uri, cached)

    if _is_webp(cached):
        png_path = cached.with_suffix(".png")
        if not png_path.exists():
            logger.info("Converting WebP to PNG: %s", cached.name)
            _convert_webp(cached, png_path)
        return str(png_path)

    return str(cached)


def _process_doctree(app: Sphinx, doctree: nodes.document) -> None:
    if app.builder.name != "latex":
        return

    cache_dir = Path(app.outdir).parent / "_remote_images"

    for img in doctree.findall(nodes.image):
        uri = img.get("uri", "")
        if _is_remote(uri):
            try:
                local = _ensure_local_image(uri, cache_dir)
                img["uri"] = local
            except Exception as exc:
                logger.warning("Failed to fetch remote image %s: %s", uri, exc)


def setup(app: Sphinx):
    app.connect("doctree-read", _process_doctree)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
