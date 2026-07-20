"""Authentication + profile routes."""
import secrets
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import jwt

from ..db import db, now_utc, now_iso, new_id
from ..security import (
    hash_pw, verify_pw, make_access, make_refresh, set_auth_cookies,
    clear_auth_cookies, get_current_user, strip_user, JWT_SECRET, JWT_ALGO,
)
from ..models import RegisterIn, LoginIn, ForgotIn, ResetIn, ChangePwIn, ProfileIn
from ..emailer import send_email, welcome_email, reset_email

log = logging.getLogger("homefix.auth")
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(body: RegisterIn):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    role = body.role if body.role in ("customer", "technician") else "customer"
    user = {
        "id": new_id(), "email": email, "name": body.name, "phone": body.phone,
        "role": role, "password_hash": hash_pw(body.password),
        "email_verified": True, "created_at": now_iso(),
        "address": None, "city": None, "bio": None, "avatar_url": None,
        "skills": [] if role == "technician" else None,
        "is_available": True if role == "technician" else None,
        "rating_avg": 0, "rating_count": 0,
    }
    await db.users.insert_one(user)
    subj, title, body_html = welcome_email(body.name)
    try:
        await send_email(email, subj, title, body_html)
    except Exception as e:
        log.warning(f"welcome mail failed: {e}")
    access = make_access(user["id"], role)
    refresh = make_refresh(user["id"])
    res = JSONResponse(strip_user(dict(user)))
    set_auth_cookies(res, access, refresh)
    return res


@router.post("/login")
async def login(body: LoginIn):
    email = body.email.lower()
    ident = f"login:{email}"
    lock = await db.login_attempts.find_one({"identifier": ident})
    if lock and lock.get("count", 0) >= 5 and lock.get("locked_until") and lock["locked_until"] > now_iso():
        raise HTTPException(429, "Too many failed attempts. Try again later.")
    user = await db.users.find_one({"email": email})
    if not user or not verify_pw(body.password, user["password_hash"]):
        await db.login_attempts.update_one(
            {"identifier": ident},
            {"$inc": {"count": 1}, "$set": {"locked_until": (now_utc() + timedelta(minutes=15)).isoformat()}},
            upsert=True,
        )
        raise HTTPException(401, "Invalid email or password")
    await db.login_attempts.delete_one({"identifier": ident})
    access = make_access(user["id"], user["role"])
    refresh = make_refresh(user["id"])
    res = JSONResponse(strip_user(dict(user)))
    set_auth_cookies(res, access, refresh)
    return res


@router.post("/logout")
async def logout():
    res = JSONResponse({"ok": True})
    clear_auth_cookies(res)
    return res


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/refresh")
async def refresh_token(request: Request):
    t = request.cookies.get("refresh_token")
    if not t:
        raise HTTPException(401, "No refresh token")
    try:
        p = jwt.decode(t, JWT_SECRET, algorithms=[JWT_ALGO])
        if p.get("type") != "refresh":
            raise HTTPException(401, "Invalid token")
        user = await db.users.find_one({"id": p["sub"]})
        if not user:
            raise HTTPException(401, "User not found")
        access = make_access(user["id"], user["role"])
        res = JSONResponse({"ok": True})
        res.set_cookie("access_token", access, httponly=True, secure=True,
                       samesite="none", max_age=8 * 3600, path="/")
        return res
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")


@router.post("/forgot-password")
async def forgot(body: ForgotIn, request: Request):
    user = await db.users.find_one({"email": body.email.lower()})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token, "user_id": user["id"],
            "expires_at": (now_utc() + timedelta(hours=1)).isoformat(),
            "used": False,
        })
        origin = request.headers.get("Origin") or str(request.base_url).rstrip("/")
        subj, title, html = reset_email(user["name"], token, origin)
        try:
            await send_email(user["email"], subj, title, html)
        except Exception as e:
            log.warning(f"reset mail failed: {e}")
        return {"ok": True, "reset_token": token}  # token echoed for demo/testing
    return {"ok": True}


@router.post("/reset-password")
async def reset(body: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": body.token})
    if not rec or rec.get("used") or rec["expires_at"] < now_iso():
        raise HTTPException(400, "Invalid or expired token")
    await db.users.update_one({"id": rec["user_id"]}, {"$set": {"password_hash": hash_pw(body.password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"ok": True}


@router.post("/change-password")
async def change_pw(body: ChangePwIn, user: dict = Depends(get_current_user)):
    row = await db.users.find_one({"id": user["id"]})
    if not verify_pw(body.current_password, row["password_hash"]):
        raise HTTPException(400, "Current password is incorrect")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_pw(body.new_password)}})
    return {"ok": True}


# ---------- Profile ----------
profile_router = APIRouter(tags=["profile"])


@profile_router.put("/users/me")
async def update_profile(body: ProfileIn, user: dict = Depends(get_current_user)):
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    if upd:
        await db.users.update_one({"id": user["id"]}, {"$set": upd})
    u = await db.users.find_one({"id": user["id"]})
    return strip_user(u)
