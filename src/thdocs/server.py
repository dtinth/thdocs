import asyncio
import io
import logging
import os
import secrets
import sys
import zipfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends

app = FastAPI()
security = HTTPBasic(auto_error=False)

logger = logging.getLogger("thdocs.server")

THDOCS_PASSWORD = os.environ.get("THDOCS_SERVER_PASSWORD")
MAX_UPLOAD_BYTES = 100 * 1024 * 1024

if THDOCS_PASSWORD is None:
    logger.warning(
        "THDOCS_SERVER_PASSWORD is not set. Authentication is disabled. "
        "Set the environment variable to enable basic auth."
    )


def _require_auth(credentials: HTTPBasicCredentials | None) -> None:
    if THDOCS_PASSWORD is None:
        return
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not (
        secrets.compare_digest(credentials.username, "thdocs")
        and secrets.compare_digest(credentials.password, THDOCS_PASSWORD)
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _find_project_root(base: Path) -> Path | None:
    """Find thdocs.toml in base or one level of subdirectory."""
    if (base / "thdocs.toml").exists():
        return base
    for child in base.iterdir():
        if child.is_dir() and (child / "thdocs.toml").exists():
            return child
    return None


def _zip_directory(directory: Path) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                arcname = str(file_path.relative_to(directory))
                zf.write(file_path, arcname)
    buf.seek(0)
    return buf.read()


@app.post("/")
async def build_docs(
    file: UploadFile = File(...),
    credentials: HTTPBasicCredentials | None = Depends(security),
):
    _require_auth(credentials)

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Upload exceeds 100MB limit")

    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        upload_zip = tmpdir / "upload.zip"
        upload_zip.write_bytes(contents)

        project_dir = tmpdir / "project"
        project_dir.mkdir()

        with zipfile.ZipFile(upload_zip, "r") as zf:
            for member in zf.namelist():
                member_path = Path(member)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise HTTPException(status_code=400, detail="Invalid archive path")
            zf.extractall(project_dir)

        actual_root = _find_project_root(project_dir)
        if actual_root is None:
            raise HTTPException(status_code=400, detail="thdocs.toml not found in archive")

        logger.info("Building project at %s", actual_root)
        env = {**os.environ, "THDOCS_PROJECT": str(actual_root)}
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "thdocs",
            "build",
            "--with-pdf",
            cwd=str(actual_root),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            detail = f"Build failed (exit {proc.returncode}):\n{stderr.decode()}\n{stdout.decode()}"
            logger.error(detail)
            raise HTTPException(status_code=500, detail=detail)

        logger.info("Build succeeded, zipping output")
        zip_bytes = await asyncio.get_event_loop().run_in_executor(
            None, _zip_directory, actual_root
        )
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": 'attachment; filename="thdocs-build.zip"'},
        )
