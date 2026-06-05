from __future__ import annotations

import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import UploadFile

from backend.app.core.config import settings


ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2")
REPO_ROOT = Path(__file__).resolve().parents[3]


def _normalized_name(filename: str | None) -> str:
    raw_name = filename or "upload.bin"
    return Path(raw_name).name


async def save_upload(task_id: str, upload: UploadFile) -> Path:
    settings.ensure_directories()
    target_dir = settings.upload_root / task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / _normalized_name(upload.filename)

    with target_path.open("wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    await upload.close()
    return target_path


def build_demo_upload(task_id: str) -> Path:
    settings.ensure_directories()
    source_dir = REPO_ROOT / "examples" / "vulnerable_python_app"
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)

    target_dir = settings.upload_root / task_id
    target_dir.mkdir(parents=True, exist_ok=True)
    archive_path = target_dir / "vulnerable_python_app.zip"

    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.relative_to(source_dir.parent))

    return archive_path


def prepare_project_path(task_id: str) -> Path:
    project_dir = settings.project_root / task_id
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def extract_project(task_id: str, upload_path: Path) -> Path:
    project_dir = prepare_project_path(task_id)
    lowered_name = upload_path.name.lower()

    if lowered_name.endswith(ARCHIVE_SUFFIXES):
        shutil.unpack_archive(str(upload_path), str(project_dir))
        return project_dir

    shutil.copy2(upload_path, project_dir / upload_path.name)
    return project_dir


def list_project_files(project_path: Path) -> list[Path]:
    return [path for path in project_path.rglob("*") if path.is_file()]
