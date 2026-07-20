"""JWT / password / auth-dependency helpers."""
import os
from datetime import timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Request, Response, Depends

from .db import db, now_utc

JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-very-long-secret-key-32chars")
JWT_ALGO = "HS256"


def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def make_access(user_id: str, role: str) -> str:
    return jwt.encode(
        {"sub": user_id, "role": role, "type": "access",
         "exp": now_utc() + timedelta(hours=8)},
        JWT_SECRET, algorithm=JWT_ALGO,
    )


def make_refresh(user_id: str) -> str:
    return jwt.encode(
        {"sub": user_id, "type": "refresh",
         "exp": now_utc() + timedelta(days=7)},
        JWT_SECRET, algorithm=JWT_ALGO,
    )


def set_auth_cookies(res: Response, access: str, refresh: str) -> None:
    res.set_cookie("access_token", access, httponly=True, secure=True, samesite="none",
                   max_age=8 * 3600, path="/")
    res.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="none",
                   max_age=7 * 86400, path="/")


def clear_auth_cookies(res: Response) -> None:
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")


def strip_user(user: dict) -> dict:
    user.pop("password_hash", None)
    user.pop("_id", None)
    return user


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]})
        if not user:
            raise HTTPException(401, "User not found")
        return strip_user(user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


def require_role(*roles: str):
    async def _dep(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(403, "Forbidden")
        return user
    return _dep
