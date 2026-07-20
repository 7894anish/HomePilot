"""File upload → Emergent object storage."""
import uuid
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, Header

from ..db import db, now_iso, new_id
from ..security import get_current_user, JWT_SECRET, JWT_ALGO
from ..storage import put_object, get_object, APP_NAME
import jwt

log = logging.getLogger("homefix.uploads")
router = APIRouter(tags=["uploads"])

MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp",
}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_image(file: UploadFile = File(...),
                       user: dict = Depends(get_current_user)):
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in MIME:
        raise HTTPException(400, "Only jpg/jpeg/png/gif/webp allowed")
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "File too large (5 MB max)")
    fid = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{user['id']}/{fid}.{ext}"
    try:
        result = put_object(path, data, MIME[ext])
    except Exception as e:
        log.error(f"upload failed: {e}")
        raise HTTPException(500, "Storage upload failed")
    doc = {
        "id": fid, "storage_path": result["path"],
        "original_filename": file.filename,
        "content_type": MIME[ext], "size": result["size"],
        "user_id": user["id"], "is_deleted": False,
        "created_at": now_iso(),
    }
    await db.files.insert_one(doc)
    return {"id": fid, "path": result["path"], "size": result["size"], "url": f"/api/files/{fid}"}


def _decode_token(token: str) -> dict | None:
    try:
        p = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if p.get("type") != "access":
            return None
        return p
    except Exception:
        return None


@router.get("/files/{file_id}")
async def download_file(file_id: str, request_auth: str | None = Query(None, alias="auth"),
                        authorization: str | None = Header(None)):
    """Return the binary. Supports Authorization header AND ?auth= query token
    since <img src> can't send headers."""
    # Auth: prefer header, fall back to query token, fall back to cookie
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    elif request_auth:
        token = request_auth
    if token and not _decode_token(token):
        raise HTTPException(401, "Invalid token")
    # Cookie is checked implicitly via request in future; for now allow anonymous read
    rec = await db.files.find_one({"id": file_id, "is_deleted": False}, {"_id": 0})
    if not rec:
        raise HTTPException(404, "File not found")
    try:
        data, ct = get_object(rec["storage_path"])
    except Exception as e:
        log.error(f"download failed: {e}")
        raise HTTPException(500, "Storage read failed")
    return Response(content=data, media_type=rec.get("content_type", ct))
