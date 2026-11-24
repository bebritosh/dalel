"""File storage on disk. Files are saved with uuid names only, never originals."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

from app.core.config import settings

# Allowed upload types: extension -> canonical mime type.
ALLOWED_TYPES: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".json": "application/json",
}


def data_root() -> Path:
    """Return the configured data directory as a Path, creating it if needed."""
    root = Path(settings.data_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_hex(content: bytes) -> str:
    """Return the hex SHA-256 of the given bytes."""
    return hashlib.sha256(content).hexdigest()


def extension_for(filename: str | None) -> str | None:
    """Return the lowercased extension if it is allowed, else None."""
    if not filename:
        return None
    ext = Path(filename).suffix.lower()
    return ext if ext in ALLOWED_TYPES else None


def case_dir(case_id: int) -> Path:
    """Return (and create) the directory that holds a case's files."""
    path = data_root() / "cases" / str(case_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_bytes(case_id: int, content: bytes, ext: str) -> Path:
    """Save content under a uuid filename and return the stored path."""
    target = case_dir(case_id) / f"{uuid.uuid4().hex}{ext}"
    target.write_bytes(content)
    return target


def delete_case_files(case_id: int) -> None:
    """Remove all files stored for a case. Silent if nothing exists."""
    path = data_root() / "cases" / str(case_id)
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
