"""Local filesystem storage used for uploaded files."""
import logging
import os
from pathlib import Path, PurePosixPath

log = logging.getLogger("homefix.storage")

APP_NAME = "homefix-pro"
DEFAULT_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "data" / "uploads"
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", DEFAULT_UPLOAD_DIR)).resolve()


def init_storage() -> str:
    """Create the upload directory and return its absolute location."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Local file storage ready at %s", UPLOAD_DIR)
    return str(UPLOAD_DIR)


def _safe_path(path: str) -> Path:
    """Resolve a logical object path without allowing directory traversal."""
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Invalid storage path")

    target = UPLOAD_DIR.joinpath(*relative.parts).resolve()
    if UPLOAD_DIR not in target.parents:
        raise ValueError("Invalid storage path")
    return target


def put_object(path: str, data: bytes, content_type: str) -> dict:
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return {"path": path, "size": len(data), "content_type": content_type}


def get_object(path: str) -> tuple[bytes, str]:
    target = _safe_path(path)
    if not target.is_file():
        raise FileNotFoundError(path)
    return target.read_bytes(), "application/octet-stream"
