from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import UploadFile

from backend.app.core.config import settings


ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2")
REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class SavedUploadBundle:
    path: Path
    names: list[str]


def _normalized_relative_path(filename: str | None) -> Path:
    raw_name = (filename or "upload.bin").replace("\\", "/")
    safe_parts = [part for part in PurePosixPath(raw_name).parts if part not in {"", ".", "..", "/"}]
    if not safe_parts:
        return Path("upload.bin")
    return Path(*safe_parts)


async def _write_upload(upload: UploadFile, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("wb") as buffer:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            buffer.write(chunk)
    await upload.close()


async def save_upload(task_id: str, upload: UploadFile) -> Path:
    bundle = await save_uploads(task_id, [upload])
    return bundle.path


async def save_uploads(task_id: str, uploads: list[UploadFile]) -> SavedUploadBundle:
    if not uploads:
        raise ValueError("No uploads provided")

    settings.ensure_directories()
    target_dir = settings.upload_root / task_id
    target_dir.mkdir(parents=True, exist_ok=True)

    normalized_names = [_normalized_relative_path(upload.filename) for upload in uploads]
    normalized_name_strings = [path.as_posix() for path in normalized_names]
    if len(set(normalized_name_strings)) != len(normalized_name_strings):
        raise ValueError("Duplicate upload paths detected in request")

    if len(uploads) == 1 and len(normalized_names[0].parts) == 1:
        target_path = target_dir / normalized_names[0]
        await _write_upload(uploads[0], target_path)
        return SavedUploadBundle(path=target_path, names=normalized_name_strings)

    bundle_dir = target_dir / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    for upload, relative_path in zip(uploads, normalized_names, strict=True):
        await _write_upload(upload, bundle_dir / relative_path)
    return SavedUploadBundle(path=bundle_dir, names=normalized_name_strings)


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
    if upload_path.is_dir():
        shutil.copytree(upload_path, project_dir, dirs_exist_ok=True)
        return project_dir

    lowered_name = upload_path.name.lower()
    if lowered_name.endswith(ARCHIVE_SUFFIXES):
        shutil.unpack_archive(str(upload_path), str(project_dir))
        return project_dir

    shutil.copy2(upload_path, project_dir / upload_path.name)
    return project_dir


def list_project_files(project_path: Path) -> list[Path]:
    return [path for path in project_path.rglob("*") if path.is_file()]
