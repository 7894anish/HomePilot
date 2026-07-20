"""HomeFix Pro — Home services booking platform (single-file FastAPI backend)."""
from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import uuid
import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

import bcrypt
import jwt
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

# ---------- Config ----------
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-very-long-secret-key-32chars")
JWT_ALGO = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@homefix.pro")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("homefix")

app = FastAPI(title="HomeFix Pro API")
api = APIRouter(prefix="/api")


# ---------- Helpers ----------
def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def now_iso() -> str:
    return now_utc().isoformat()

def new_id() -> str:
    return str(uuid.uuid4())

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
    res.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=8*3600, path="/")
    res.set_cookie("refresh_token", refresh, httponly=True, secure=True, samesite="none", max_age=7*86400, path="/")

def clear_auth_cookies(res: Response) -> None:
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")

def _strip(user: dict) -> dict:
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
        return _strip(user)
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


# ---------- Models ----------
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    phone: Optional[str] = None
    role: Optional[str] = "customer"  # customer or technician

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotIn(BaseModel):
    email: EmailStr

class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=6)

class ChangePwIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)

class ProfileIn(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    skills: Optional[List[str]] = None

class CategoryIn(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class ServiceIn(BaseModel):
    name: str
    category_id: str
    description: str
    price: float
    duration_minutes: int = 60
    image_url: Optional[str] = None
    features: List[str] = []
    active: bool = True

class CityIn(BaseModel):
    name: str
    state: Optional[str] = None
    active: bool = True

class CouponIn(BaseModel):
    code: str
    discount_percent: float
    max_discount: Optional[float] = None
    min_order: float = 0
    valid_until: Optional[str] = None
    active: bool = True

class BookingCreate(BaseModel):
    service_id: str
    scheduled_date: str  # YYYY-MM-DD
    scheduled_time: str  # HH:MM
    address: str
    city: str
    problem_description: str
    images: List[str] = []
    coupon_code: Optional[str] = None
    payment_method: str = "cash"  # cash or online

class BookingStatusIn(BaseModel):
    status: str  # confirmed, assigned, in_progress, completed, cancelled, rejected
    note: Optional[str] = None

class AssignTechIn(BaseModel):
    technician_id: str

class ReviewIn(BaseModel):
    booking_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class ContactIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str

class CheckoutIn(BaseModel):
    booking_id: str
    origin_url: str


# ---------- Auth Routes ----------
@api.post("/auth/register")
async def register(body: RegisterIn):
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(400, "Email already registered")
    role = body.role if body.role in ("customer", "technician") else "customer"
    user = {
        "id": new_id(),
        "email": email,
        "name": body.name,
        "phone": body.phone,
        "role": role,
        "password_hash": hash_pw(body.password),
        "email_verified": True,  # skipping verification for MVP
        "created_at": now_iso(),
        "address": None, "city": None, "bio": None, "avatar_url": None,
        "skills": [] if role == "technician" else None,
        "is_available": True if role == "technician" else None,
        "rating_avg": 0, "rating_count": 0,
    }
    await db.users.insert_one(user)
    access = make_access(user["id"], role)
    refresh = make_refresh(user["id"])
    res = JSONResponse(_strip(dict(user)))
    set_auth_cookies(res, access, refresh)
    return res

@api.post("/auth/login")
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
    res = JSONResponse(_strip(dict(user)))
    set_auth_cookies(res, access, refresh)
    return res

@api.post("/auth/logout")
async def logout():
    res = JSONResponse({"ok": True})
    clear_auth_cookies(res)
    return res

@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

@api.post("/auth/refresh")
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
        res.set_cookie("access_token", access, httponly=True, secure=True, samesite="none", max_age=8*3600, path="/")
        return res
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

@api.post("/auth/forgot-password")
async def forgot(body: ForgotIn):
    user = await db.users.find_one({"email": body.email.lower()})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token, "user_id": user["id"],
            "expires_at": (now_utc() + timedelta(hours=1)).isoformat(),
            "used": False,
        })
        log.info(f"Password reset link: /reset-password?token={token}")
        return {"ok": True, "reset_token": token}  # For MVP demo
    return {"ok": True}

@api.post("/auth/reset-password")
async def reset(body: ResetIn):
    rec = await db.password_reset_tokens.find_one({"token": body.token})
    if not rec or rec.get("used") or rec["expires_at"] < now_iso():
        raise HTTPException(400, "Invalid or expired token")
    await db.users.update_one({"id": rec["user_id"]}, {"$set": {"password_hash": hash_pw(body.password)}})
    await db.password_reset_tokens.update_one({"token": body.token}, {"$set": {"used": True}})
    return {"ok": True}

@api.post("/auth/change-password")
async def change_pw(body: ChangePwIn, user: dict = Depends(get_current_user)):
    row = await db.users.find_one({"id": user["id"]})
    if not verify_pw(body.current_password, row["password_hash"]):
        raise HTTPException(400, "Current password is incorrect")
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": hash_pw(body.new_password)}})
    return {"ok": True}


# ---------- Profile / Users ----------
@api.put("/users/me")
async def update_profile(body: ProfileIn, user: dict = Depends(get_current_user)):
    upd = {k: v for k, v in body.model_dump().items() if v is not None}
    if upd:
        await db.users.update_one({"id": user["id"]}, {"$set": upd})
    u = await db.users.find_one({"id": user["id"]})
    return _strip(u)

@api.get("/admin/users")
async def list_users(role: Optional[str] = None, _: dict = Depends(require_role("admin"))):
    q = {"role": role} if role else {}
    users = await db.users.find(q, {"password_hash": 0, "_id": 0}).to_list(1000)
    return users

@api.delete("/admin/users/{uid}")
async def delete_user(uid: str, _: dict = Depends(require_role("admin"))):
    await db.users.delete_one({"id": uid})
    return {"ok": True}


# ---------- Categories ----------
@api.get("/categories")
async def list_categories():
    return await db.categories.find({}, {"_id": 0}).to_list(200)

@api.post("/categories")
async def create_category(body: CategoryIn, _: dict = Depends(require_role("admin"))):
    cat = {"id": new_id(), **body.model_dump(), "created_at": now_iso()}
    await db.categories.insert_one(cat)
    cat.pop("_id", None)
    return cat

@api.put("/categories/{cid}")
async def update_category(cid: str, body: CategoryIn, _: dict = Depends(require_role("admin"))):
    await db.categories.update_one({"id": cid}, {"$set": body.model_dump()})
    c = await db.categories.find_one({"id": cid}, {"_id": 0})
    return c

@api.delete("/categories/{cid}")
async def delete_category(cid: str, _: dict = Depends(require_role("admin"))):
    await db.categories.delete_one({"id": cid})
    return {"ok": True}


# ---------- Services ----------
@api.get("/services")
async def list_services(category_id: Optional[str] = None, q: Optional[str] = None,
                        page: int = 1, size: int = 24):
    filt: Dict[str, Any] = {"active": True}
    if category_id:
        filt["category_id"] = category_id
    if q:
        filt["name"] = {"$regex": q, "$options": "i"}
    skip = max(0, (page - 1) * size)
    total = await db.services.count_documents(filt)
    items = await db.services.find(filt, {"_id": 0}).skip(skip).limit(size).to_list(size)
    return {"items": items, "total": total, "page": page, "size": size}

@api.get("/services/{sid}")
async def get_service(sid: str):
    s = await db.services.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Service not found")
    cat = await db.categories.find_one({"id": s["category_id"]}, {"_id": 0})
    reviews = await db.reviews.find({"service_id": sid}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"service": s, "category": cat, "reviews": reviews}

@api.post("/services")
async def create_service(body: ServiceIn, _: dict = Depends(require_role("admin"))):
    s = {"id": new_id(), **body.model_dump(), "rating_avg": 0, "rating_count": 0, "created_at": now_iso()}
    await db.services.insert_one(s)
    s.pop("_id", None)
    return s

@api.put("/services/{sid}")
async def update_service(sid: str, body: ServiceIn, _: dict = Depends(require_role("admin"))):
    await db.services.update_one({"id": sid}, {"$set": body.model_dump()})
    return await db.services.find_one({"id": sid}, {"_id": 0})

@api.delete("/services/{sid}")
async def delete_service(sid: str, _: dict = Depends(require_role("admin"))):
    await db.services.delete_one({"id": sid})
    return {"ok": True}


# ---------- Cities ----------
@api.get("/cities")
async def list_cities():
    return await db.cities.find({"active": True}, {"_id": 0}).to_list(500)

@api.post("/cities")
async def create_city(body: CityIn, _: dict = Depends(require_role("admin"))):
    c = {"id": new_id(), **body.model_dump()}
    await db.cities.insert_one(c)
    c.pop("_id", None)
    return c

@api.delete("/cities/{cid}")
async def delete_city(cid: str, _: dict = Depends(require_role("admin"))):
    await db.cities.delete_one({"id": cid})
    return {"ok": True}


# ---------- Coupons ----------
@api.get("/coupons")
async def list_coupons(_: dict = Depends(require_role("admin"))):
    return await db.coupons.find({}, {"_id": 0}).to_list(200)

@api.post("/coupons")
async def create_coupon(body: CouponIn, _: dict = Depends(require_role("admin"))):
    c = {"id": new_id(), **body.model_dump(), "code": body.code.upper()}
    await db.coupons.insert_one(c)
    c.pop("_id", None)
    return c

@api.delete("/coupons/{cid}")
async def delete_coupon(cid: str, _: dict = Depends(require_role("admin"))):
    await db.coupons.delete_one({"id": cid})
    return {"ok": True}

@api.post("/coupons/validate")
async def validate_coupon(payload: dict):
    code = (payload.get("code") or "").upper()
    amount = float(payload.get("amount") or 0)
    c = await db.coupons.find_one({"code": code, "active": True}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Invalid coupon code")
    if amount < c.get("min_order", 0):
        raise HTTPException(400, f"Minimum order ₹{c['min_order']} required")
    if c.get("valid_until") and c["valid_until"] < now_iso():
        raise HTTPException(400, "Coupon expired")
    disc = amount * (c["discount_percent"] / 100)
    if c.get("max_discount"):
        disc = min(disc, c["max_discount"])
    return {"discount": round(disc, 2), "coupon": c}


# ---------- Bookings ----------
async def _hydrate_booking(b: dict) -> dict:
    b.pop("_id", None)
    b["service"] = await db.services.find_one({"id": b["service_id"]}, {"_id": 0})
    if b.get("customer_id"):
        c = await db.users.find_one({"id": b["customer_id"]}, {"_id": 0, "password_hash": 0})
        b["customer"] = c
    if b.get("technician_id"):
        t = await db.users.find_one({"id": b["technician_id"]}, {"_id": 0, "password_hash": 0})
        b["technician"] = t
    return b

@api.post("/bookings")
async def create_booking(body: BookingCreate, user: dict = Depends(require_role("customer"))):
    service = await db.services.find_one({"id": body.service_id}, {"_id": 0})
    if not service:
        raise HTTPException(404, "Service not found")
    amount = float(service["price"])
    discount = 0.0
    if body.coupon_code:
        c = await db.coupons.find_one({"code": body.coupon_code.upper(), "active": True})
        if c and amount >= c.get("min_order", 0):
            d = amount * (c["discount_percent"] / 100)
            if c.get("max_discount"):
                d = min(d, c["max_discount"])
            discount = round(d, 2)
    total = round(amount - discount, 2)
    booking = {
        "id": new_id(),
        "customer_id": user["id"],
        "technician_id": None,
        "service_id": body.service_id,
        "service_name": service["name"],
        "scheduled_date": body.scheduled_date,
        "scheduled_time": body.scheduled_time,
        "address": body.address,
        "city": body.city,
        "problem_description": body.problem_description,
        "images": body.images,
        "coupon_code": body.coupon_code,
        "amount": amount,
        "discount": discount,
        "total": total,
        "payment_method": body.payment_method,
        "payment_status": "pending",
        "status": "pending_payment" if body.payment_method == "online" else "confirmed",
        "work_images": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "status_history": [{"status": "created", "at": now_iso()}],
    }
    await db.bookings.insert_one(booking)
    # Notify admin
    await db.notifications.insert_one({
        "id": new_id(), "user_id": None, "role": "admin",
        "title": "New booking", "message": f"{user['name']} booked {service['name']}",
        "booking_id": booking["id"], "read": False, "created_at": now_iso(),
    })
    return await _hydrate_booking(booking)

@api.get("/bookings/mine")
async def my_bookings(user: dict = Depends(get_current_user)):
    if user["role"] == "customer":
        q = {"customer_id": user["id"]}
    elif user["role"] == "technician":
        q = {"technician_id": user["id"]}
    else:
        q = {}
    items = await db.bookings.find(q).sort("created_at", -1).to_list(500)
    return [await _hydrate_booking(b) for b in items]

@api.get("/bookings/{bid}")
async def get_booking(bid: str, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"id": bid})
    if not b:
        raise HTTPException(404, "Not found")
    if user["role"] == "customer" and b["customer_id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if user["role"] == "technician" and b.get("technician_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    return await _hydrate_booking(b)

@api.get("/admin/bookings")
async def all_bookings(status: Optional[str] = None, _: dict = Depends(require_role("admin"))):
    q = {"status": status} if status else {}
    items = await db.bookings.find(q).sort("created_at", -1).to_list(1000)
    return [await _hydrate_booking(b) for b in items]

@api.post("/admin/bookings/{bid}/assign")
async def assign_technician(bid: str, body: AssignTechIn, _: dict = Depends(require_role("admin"))):
    tech = await db.users.find_one({"id": body.technician_id, "role": "technician"})
    if not tech:
        raise HTTPException(404, "Technician not found")
    await db.bookings.update_one({"id": bid}, {
        "$set": {"technician_id": body.technician_id, "status": "assigned", "updated_at": now_iso()},
        "$push": {"status_history": {"status": "assigned", "at": now_iso(), "technician_id": body.technician_id}},
    })
    b = await db.bookings.find_one({"id": bid})
    await db.notifications.insert_one({
        "id": new_id(), "user_id": body.technician_id, "role": "technician",
        "title": "New job assigned", "message": f"You've been assigned {b['service_name']}",
        "booking_id": bid, "read": False, "created_at": now_iso(),
    })
    await db.notifications.insert_one({
        "id": new_id(), "user_id": b["customer_id"], "role": "customer",
        "title": "Technician assigned", "message": f"{tech['name']} will handle your booking",
        "booking_id": bid, "read": False, "created_at": now_iso(),
    })
    return await _hydrate_booking(b)

@api.post("/bookings/{bid}/status")
async def update_booking_status(bid: str, body: BookingStatusIn, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"id": bid})
    if not b:
        raise HTTPException(404, "Not found")
    # Permissions
    if user["role"] == "technician":
        if b.get("technician_id") != user["id"]:
            raise HTTPException(403, "Forbidden")
        if body.status not in ("accepted", "rejected", "in_progress", "completed"):
            raise HTTPException(400, "Invalid status for technician")
    elif user["role"] == "customer":
        if b["customer_id"] != user["id"]:
            raise HTTPException(403, "Forbidden")
        if body.status != "cancelled":
            raise HTTPException(400, "Customers can only cancel")
    # admin: any
    upd = {"status": body.status, "updated_at": now_iso()}
    if body.status == "rejected":
        upd["technician_id"] = None
    await db.bookings.update_one({"id": bid}, {
        "$set": upd,
        "$push": {"status_history": {"status": body.status, "at": now_iso(), "note": body.note}},
    })
    await db.notifications.insert_one({
        "id": new_id(), "user_id": b["customer_id"], "role": "customer",
        "title": f"Booking {body.status}", "message": body.note or f"Your booking is now {body.status}",
        "booking_id": bid, "read": False, "created_at": now_iso(),
    })
    return await _hydrate_booking(await db.bookings.find_one({"id": bid}))

@api.post("/bookings/{bid}/work-images")
async def upload_work_images(bid: str, payload: dict, user: dict = Depends(require_role("technician"))):
    b = await db.bookings.find_one({"id": bid})
    if not b or b.get("technician_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    imgs = payload.get("images", [])
    await db.bookings.update_one({"id": bid}, {"$push": {"work_images": {"$each": imgs}}, "$set": {"updated_at": now_iso()}})
    return {"ok": True}


# ---------- Reviews ----------
@api.post("/reviews")
async def create_review(body: ReviewIn, user: dict = Depends(require_role("customer"))):
    b = await db.bookings.find_one({"id": body.booking_id})
    if not b or b["customer_id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if b["status"] != "completed":
        raise HTTPException(400, "Can only review completed bookings")
    if await db.reviews.find_one({"booking_id": body.booking_id}):
        raise HTTPException(400, "Already reviewed")
    rev = {
        "id": new_id(),
        "booking_id": body.booking_id,
        "service_id": b["service_id"],
        "technician_id": b.get("technician_id"),
        "customer_id": user["id"],
        "customer_name": user["name"],
        "rating": body.rating,
        "comment": body.comment,
        "created_at": now_iso(),
    }
    await db.reviews.insert_one(rev)
    # Update service rating
    stats = await db.reviews.aggregate([
        {"$match": {"service_id": b["service_id"]}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "cnt": {"$sum": 1}}}
    ]).to_list(1)
    if stats:
        await db.services.update_one({"id": b["service_id"]},
            {"$set": {"rating_avg": round(stats[0]["avg"], 2), "rating_count": stats[0]["cnt"]}})
    if b.get("technician_id"):
        tstats = await db.reviews.aggregate([
            {"$match": {"technician_id": b["technician_id"]}},
            {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "cnt": {"$sum": 1}}}
        ]).to_list(1)
        if tstats:
            await db.users.update_one({"id": b["technician_id"]},
                {"$set": {"rating_avg": round(tstats[0]["avg"], 2), "rating_count": tstats[0]["cnt"]}})
    rev.pop("_id", None)
    return rev

@api.get("/reviews/mine")
async def my_reviews(user: dict = Depends(get_current_user)):
    if user["role"] == "customer":
        q = {"customer_id": user["id"]}
    elif user["role"] == "technician":
        q = {"technician_id": user["id"]}
    else:
        q = {}
    return await db.reviews.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)

@api.get("/admin/reviews")
async def all_reviews(_: dict = Depends(require_role("admin"))):
    return await db.reviews.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)

@api.delete("/admin/reviews/{rid}")
async def delete_review(rid: str, _: dict = Depends(require_role("admin"))):
    await db.reviews.delete_one({"id": rid})
    return {"ok": True}


# ---------- Notifications ----------
@api.get("/notifications")
async def my_notifications(user: dict = Depends(get_current_user)):
    q = {"$or": [{"user_id": user["id"]}, {"role": user["role"], "user_id": None}]}
    return await db.notifications.find(q, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)

@api.post("/notifications/{nid}/read")
async def mark_read(nid: str, _: dict = Depends(get_current_user)):
    await db.notifications.update_one({"id": nid}, {"$set": {"read": True}})
    return {"ok": True}


# ---------- Contact ----------
@api.post("/contact")
async def create_contact(body: ContactIn):
    c = {"id": new_id(), **body.model_dump(), "status": "new", "created_at": now_iso()}
    await db.contact_requests.insert_one(c)
    c.pop("_id", None)
    return c

@api.get("/admin/contact")
async def list_contact(_: dict = Depends(require_role("admin"))):
    return await db.contact_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


# ---------- Technicians ----------
@api.get("/technicians")
async def list_technicians():
    techs = await db.users.find({"role": "technician"}, {"password_hash": 0, "_id": 0}).to_list(500)
    return techs

@api.get("/technicians/available")
async def available_technicians(_: dict = Depends(require_role("admin"))):
    return await db.users.find({"role": "technician", "is_available": True}, {"password_hash": 0, "_id": 0}).to_list(500)


# ---------- Payments (Stripe Flow B) ----------
def _get_stripe(request: Request) -> StripeCheckout:
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

@api.post("/payments/checkout")
async def create_checkout(body: CheckoutIn, request: Request, user: dict = Depends(require_role("customer"))):
    b = await db.bookings.find_one({"id": body.booking_id})
    if not b or b["customer_id"] != user["id"]:
        raise HTTPException(404, "Booking not found")
    if b.get("payment_status") == "paid":
        raise HTTPException(400, "Already paid")
    amount = float(b["total"])
    origin = body.origin_url.rstrip("/")
    checkout = _get_stripe(request)
    req = CheckoutSessionRequest(
        amount=amount,
        currency="inr",
        success_url=f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin}/payment/cancel?booking_id={b['id']}",
        metadata={"booking_id": b["id"], "user_id": user["id"]},
    )
    session = await checkout.create_checkout_session(req)
    await db.payment_transactions.insert_one({
        "id": new_id(),
        "session_id": session.session_id,
        "booking_id": b["id"],
        "user_id": user["id"],
        "amount": amount,
        "currency": "inr",
        "status": "initiated",
        "payment_status": "pending",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}

@api.get("/payments/status/{session_id}")
async def payment_status(session_id: str, request: Request):
    rec = await db.payment_transactions.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Not found")
    if rec.get("payment_status") != "paid":
        try:
            checkout = _get_stripe(request)
            s = await checkout.get_checkout_status(session_id)
            if s.payment_status == "paid" or s.status == "complete":
                await db.payment_transactions.update_one(
                    {"session_id": session_id, "payment_status": {"$ne": "paid"}},
                    {"$set": {"status": "completed", "payment_status": "paid", "updated_at": now_iso()}},
                )
                await db.bookings.update_one(
                    {"id": rec["booking_id"], "payment_status": {"$ne": "paid"}},
                    {"$set": {"payment_status": "paid", "status": "confirmed", "updated_at": now_iso()},
                     "$push": {"status_history": {"status": "paid", "at": now_iso()}}},
                )
                rec = await db.payment_transactions.find_one({"session_id": session_id})
        except Exception as e:
            log.warning(f"payment poll error: {e}")
    return {"session_id": rec["session_id"], "status": rec["status"],
            "payment_status": rec["payment_status"], "booking_id": rec.get("booking_id")}

@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    checkout = _get_stripe(request)
    body_bytes = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        resp = await checkout.handle_webhook(body_bytes, signature)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")
    if resp.payment_status == "paid":
        await db.payment_transactions.update_one(
            {"session_id": resp.session_id, "payment_status": {"$ne": "paid"}},
            {"$set": {"status": "completed", "payment_status": "paid", "updated_at": now_iso()}},
        )
        rec = await db.payment_transactions.find_one({"session_id": resp.session_id})
        if rec:
            await db.bookings.update_one(
                {"id": rec["booking_id"], "payment_status": {"$ne": "paid"}},
                {"$set": {"payment_status": "paid", "status": "confirmed", "updated_at": now_iso()},
                 "$push": {"status_history": {"status": "paid", "at": now_iso()}}},
            )
    return {"ok": True}

@api.get("/payments/mine")
async def my_payments(user: dict = Depends(get_current_user)):
    q = {"user_id": user["id"]} if user["role"] != "admin" else {}
    return await db.payment_transactions.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)


# ---------- Dashboard Analytics ----------
@api.get("/dashboard/admin")
async def admin_dash(_: dict = Depends(require_role("admin"))):
    total_bookings = await db.bookings.count_documents({})
    completed = await db.bookings.count_documents({"status": "completed"})
    pending = await db.bookings.count_documents({"status": {"$in": ["confirmed", "assigned", "in_progress", "accepted", "pending_payment"]}})
    customers = await db.users.count_documents({"role": "customer"})
    technicians = await db.users.count_documents({"role": "technician"})
    revenue_pipeline = await db.bookings.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "sum": {"$sum": "$total"}}}
    ]).to_list(1)
    revenue = revenue_pipeline[0]["sum"] if revenue_pipeline else 0
    # last 7 days
    week_ago = (now_utc() - timedelta(days=7)).isoformat()
    weekly = await db.bookings.aggregate([
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": {"$substr": ["$created_at", 0, 10]}, "count": {"$sum": 1}, "revenue": {"$sum": "$total"}}},
        {"$sort": {"_id": 1}},
    ]).to_list(30)
    by_status = await db.bookings.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]).to_list(20)
    top_services = await db.bookings.aggregate([
        {"$group": {"_id": "$service_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 6}
    ]).to_list(6)
    return {
        "kpi": {"total_bookings": total_bookings, "completed": completed, "pending": pending,
                "customers": customers, "technicians": technicians, "revenue": round(revenue, 2)},
        "weekly": weekly, "by_status": by_status, "top_services": top_services,
    }

@api.get("/dashboard/customer")
async def customer_dash(user: dict = Depends(require_role("customer"))):
    total = await db.bookings.count_documents({"customer_id": user["id"]})
    completed = await db.bookings.count_documents({"customer_id": user["id"], "status": "completed"})
    pending = await db.bookings.count_documents({"customer_id": user["id"], "status": {"$nin": ["completed", "cancelled", "rejected"]}})
    spend = await db.bookings.aggregate([
        {"$match": {"customer_id": user["id"], "payment_status": "paid"}},
        {"$group": {"_id": None, "s": {"$sum": "$total"}}}
    ]).to_list(1)
    return {"total": total, "completed": completed, "pending": pending,
            "total_spent": spend[0]["s"] if spend else 0}

@api.get("/dashboard/technician")
async def tech_dash(user: dict = Depends(require_role("technician"))):
    assigned = await db.bookings.count_documents({"technician_id": user["id"]})
    completed = await db.bookings.count_documents({"technician_id": user["id"], "status": "completed"})
    active = await db.bookings.count_documents({"technician_id": user["id"], "status": {"$in": ["assigned", "accepted", "in_progress"]}})
    earn = await db.bookings.aggregate([
        {"$match": {"technician_id": user["id"], "status": "completed"}},
        {"$group": {"_id": None, "s": {"$sum": "$total"}}}
    ]).to_list(1)
    return {"assigned": assigned, "completed": completed, "active": active,
            "earnings": round((earn[0]["s"] if earn else 0) * 0.7, 2),
            "rating": (await db.users.find_one({"id": user["id"]}, {"_id": 0, "rating_avg": 1, "rating_count": 1})) or {}}


# ---------- Health ----------
@api.get("/")
async def root():
    return {"service": "HomeFix Pro", "status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Startup: seed data ----------
CATEGORIES_SEED = [
    {"name": "Home Cleaning", "slug": "cleaning", "icon": "Sparkles",
     "description": "Deep cleaning, kitchen, bathroom & sofa cleaning experts.",
     "image_url": "https://images.unsplash.com/photo-1563453392212-326f5e854473?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"},
    {"name": "Plumbing", "slug": "plumbing", "icon": "Wrench",
     "description": "Leak repairs, tap installation & bathroom fittings.",
     "image_url": "https://images.unsplash.com/photo-1676210134188-4c05dd172f89?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"},
    {"name": "Electrical", "slug": "electrical", "icon": "Zap",
     "description": "Wiring, switch replacement, light & fan installation.",
     "image_url": "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"},
    {"name": "AC Repair", "slug": "ac-repair", "icon": "Wind",
     "description": "AC installation, gas refill, deep cleaning & servicing.",
     "image_url": "https://images.pexels.com/photos/33671149/pexels-photo-33671149.jpeg?auto=compress&cs=tinysrgb&h=650&w=940"},
    {"name": "Appliance Repair", "slug": "appliance", "icon": "Refrigerator",
     "description": "Fridge, washing machine, microwave & oven repair.",
     "image_url": "https://images.unsplash.com/photo-1585771724684-38269d6639fd?auto=format&fit=crop&w=940&q=80"},
    {"name": "Carpentry", "slug": "carpentry", "icon": "Hammer",
     "description": "Furniture repair, door locks, hinges & custom work.",
     "image_url": "https://images.unsplash.com/photo-1622045858893-a2c2b0f7c6b6?auto=format&fit=crop&w=940&q=80"},
    {"name": "Painting", "slug": "painting", "icon": "Paintbrush",
     "description": "Interior & exterior wall painting with premium finishes.",
     "image_url": "https://images.unsplash.com/photo-1562259949-e8e7689d7828?auto=format&fit=crop&w=940&q=80"},
    {"name": "Electronics Repair", "slug": "electronics", "icon": "Tv",
     "description": "TV, laptop, monitor & smart-device diagnostics.",
     "image_url": "https://images.unsplash.com/photo-1601524909162-ae8725290836?auto=format&fit=crop&w=940&q=80"},
    {"name": "Water Purifier", "slug": "water-purifier", "icon": "Droplet",
     "description": "RO installation, filter change & annual service.",
     "image_url": "https://images.unsplash.com/photo-1585687501004-615dfdfde7f1?auto=format&fit=crop&w=940&q=80"},
    {"name": "CCTV Installation", "slug": "cctv", "icon": "Camera",
     "description": "Home & office camera setup with remote monitoring.",
     "image_url": "https://images.unsplash.com/photo-1557187666-4fd70cf76254?auto=format&fit=crop&w=940&q=80"},
]

SERVICES_SEED = [
    ("Full Home Deep Cleaning", "cleaning", "Bedrooms, bathrooms & kitchen deep-cleaned with eco-friendly products.", 2499, 240),
    ("Kitchen Deep Cleaning", "cleaning", "Chimney, hob, tiles & sink degreased and sanitized.", 1499, 180),
    ("Bathroom Deep Cleaning", "cleaning", "Descaling of tiles, WC sanitization & mirror polish.", 999, 120),
    ("Sofa Cleaning (3-Seater)", "cleaning", "Foam shampoo & vacuum extraction for stain-free sofas.", 799, 90),

    ("Basin / Sink Leak Fix", "plumbing", "Fix leaks, replace faucets & clear blockages.", 399, 60),
    ("Toilet / Flush Repair", "plumbing", "Repair or replace flush tank & internal parts.", 499, 75),
    ("Water Tank Cleaning", "plumbing", "Complete overhead tank clean-out & sanitization.", 999, 120),

    ("Switch / Socket Replacement", "electrical", "Replace up to 5 switches or sockets with quality parts.", 349, 45),
    ("Fan Installation", "electrical", "Ceiling / exhaust fan installation with wiring check.", 499, 60),
    ("MCB / Fuse Repair", "electrical", "Diagnose and fix tripping circuits and MCB units.", 599, 60),
    ("Full Home Wiring Audit", "electrical", "Detailed inspection with issue report and quotation.", 799, 90),

    ("AC Service (Split)", "ac-repair", "Standard cleaning & gas-level check for one split AC.", 599, 60),
    ("AC Deep Clean (Jet)", "ac-repair", "Jet-water cleaning for split AC, removes deep dust.", 899, 90),
    ("AC Installation", "ac-repair", "Bracket, drainage & wiring for split AC install.", 1499, 120),
    ("Gas Refill (R32/R410)", "ac-repair", "Refrigerant gas top-up with leak check.", 2499, 90),

    ("Refrigerator Repair", "appliance", "Cooling issue diagnostics with spare replacement.", 499, 90),
    ("Washing Machine Repair", "appliance", "Front / top load washing machine diagnostics.", 499, 90),
    ("Microwave Repair", "appliance", "Heating and control panel fix for microwaves.", 449, 60),

    ("Furniture Repair", "carpentry", "Fix drawers, hinges, wobbling legs & polish.", 399, 60),
    ("Door Lock Replacement", "carpentry", "Lock repair or replacement with new bolt.", 349, 45),
    ("Custom Shelf Installation", "carpentry", "Wall mounted shelves with wall anchors & finish.", 799, 90),

    ("Interior Wall Painting", "painting", "1 BHK premium emulsion painting including labour.", 8999, 480),
    ("Wood Polishing", "painting", "Furniture wood polish with sanding & sealing.", 1499, 180),

    ("TV Repair", "electronics", "LED / LCD panel diagnostics and repair.", 599, 90),
    ("Laptop Repair", "electronics", "Software or hardware level diagnostics.", 699, 90),

    ("RO Service", "water-purifier", "Filter clean + TDS check + service.", 449, 60),
    ("RO Filter Replacement", "water-purifier", "Sediment + carbon filter replacement.", 899, 60),

    ("CCTV Camera Installation", "cctv", "Install up to 4 IP cameras with DVR setup.", 2999, 240),
]

CITIES_SEED = [
    {"name": "Bengaluru", "state": "Karnataka"},
    {"name": "Mumbai", "state": "Maharashtra"},
    {"name": "Delhi", "state": "Delhi"},
    {"name": "Hyderabad", "state": "Telangana"},
    {"name": "Chennai", "state": "Tamil Nadu"},
    {"name": "Pune", "state": "Maharashtra"},
    {"name": "Kolkata", "state": "West Bengal"},
    {"name": "Ahmedabad", "state": "Gujarat"},
]

COUPONS_SEED = [
    {"code": "WELCOME10", "discount_percent": 10, "max_discount": 300, "min_order": 300, "active": True},
    {"code": "MEGA20", "discount_percent": 20, "max_discount": 800, "min_order": 999, "active": True},
    {"code": "FIRSTBOOK", "discount_percent": 15, "max_discount": 500, "min_order": 500, "active": True},
]


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.categories.create_index("slug", unique=True)
    await db.categories.create_index("id", unique=True)
    await db.services.create_index("id", unique=True)
    await db.services.create_index("category_id")
    await db.services.create_index("name")
    await db.bookings.create_index("id", unique=True)
    await db.bookings.create_index("customer_id")
    await db.bookings.create_index("technician_id")
    await db.bookings.create_index("status")
    await db.reviews.create_index("id", unique=True)
    await db.reviews.create_index("service_id")
    await db.coupons.create_index("code", unique=True)
    await db.cities.create_index("name", unique=True)
    await db.payment_transactions.create_index("session_id", unique=True)
    await db.notifications.create_index("id", unique=True)

    # Seed admin
    if not await db.users.find_one({"email": ADMIN_EMAIL}):
        await db.users.insert_one({
            "id": new_id(), "email": ADMIN_EMAIL, "name": "Admin",
            "phone": None, "role": "admin",
            "password_hash": hash_pw(ADMIN_PASSWORD),
            "email_verified": True, "created_at": now_iso(),
            "address": None, "city": None, "bio": None, "avatar_url": None,
        })
        log.info(f"Seeded admin: {ADMIN_EMAIL}")

    # Seed sample customer + technician
    if not await db.users.find_one({"email": "customer@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "customer@homefix.pro", "name": "Aisha Kapoor",
            "phone": "+919000000001", "role": "customer",
            "password_hash": hash_pw("customer123"), "email_verified": True,
            "created_at": now_iso(),
            "address": "12, MG Road", "city": "Bengaluru",
            "bio": None, "avatar_url": None,
        })
    if not await db.users.find_one({"email": "tech@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "tech@homefix.pro", "name": "Ravi Kumar",
            "phone": "+919000000002", "role": "technician",
            "password_hash": hash_pw("tech123"), "email_verified": True,
            "created_at": now_iso(),
            "address": None, "city": "Bengaluru", "bio": "8 yrs experience in AC & electrical.",
            "avatar_url": None,
            "skills": ["AC Repair", "Electrical"],
            "is_available": True, "rating_avg": 4.8, "rating_count": 42,
        })
    # tech 2
    if not await db.users.find_one({"email": "tech2@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "tech2@homefix.pro", "name": "Sonia Verma",
            "phone": "+919000000003", "role": "technician",
            "password_hash": hash_pw("tech123"), "email_verified": True,
            "created_at": now_iso(),
            "address": None, "city": "Mumbai", "bio": "Cleaning specialist.",
            "avatar_url": None,
            "skills": ["Home Cleaning"],
            "is_available": True, "rating_avg": 4.6, "rating_count": 28,
        })

    # Seed cities
    for c in CITIES_SEED:
        if not await db.cities.find_one({"name": c["name"]}):
            await db.cities.insert_one({"id": new_id(), **c, "active": True})

    # Seed categories
    slug_to_id: Dict[str, str] = {}
    for c in CATEGORIES_SEED:
        existing = await db.categories.find_one({"slug": c["slug"]})
        if existing:
            slug_to_id[c["slug"]] = existing["id"]
        else:
            cid = new_id()
            await db.categories.insert_one({"id": cid, **c, "created_at": now_iso()})
            slug_to_id[c["slug"]] = cid

    # Seed services
    if await db.services.count_documents({}) < len(SERVICES_SEED):
        for name, slug, desc, price, dur in SERVICES_SEED:
            if await db.services.find_one({"name": name}):
                continue
            await db.services.insert_one({
                "id": new_id(), "name": name, "category_id": slug_to_id.get(slug),
                "description": desc, "price": float(price), "duration_minutes": dur,
                "image_url": next((cat["image_url"] for cat in CATEGORIES_SEED if cat["slug"] == slug), None),
                "features": ["Verified pros", "90-day service warranty", "Trained & background-checked"],
                "active": True, "rating_avg": round(4.4 + (hash(name) % 5) * 0.1, 1),
                "rating_count": 10 + (hash(name) % 90), "created_at": now_iso(),
            })

    # Seed coupons
    for c in COUPONS_SEED:
        if not await db.coupons.find_one({"code": c["code"]}):
            await db.coupons.insert_one({"id": new_id(), **c})

    log.info("Startup seed complete.")


@app.on_event("shutdown")
async def shutdown():
    client.close()
