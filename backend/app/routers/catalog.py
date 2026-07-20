"""Catalog routes: categories, services, cities, coupons, technicians, contact."""
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException

from ..db import db, now_iso, new_id
from ..security import require_role
from ..models import CategoryIn, ServiceIn, CityIn, CouponIn, ContactIn

router = APIRouter(tags=["catalog"])


# Categories
@router.get("/categories")
async def list_categories():
    return await db.categories.find({}, {"_id": 0}).to_list(200)


@router.post("/categories")
async def create_category(body: CategoryIn, _: dict = Depends(require_role("admin"))):
    cat = {"id": new_id(), **body.model_dump(), "created_at": now_iso()}
    await db.categories.insert_one(cat)
    cat.pop("_id", None)
    return cat


@router.put("/categories/{cid}")
async def update_category(cid: str, body: CategoryIn, _: dict = Depends(require_role("admin"))):
    await db.categories.update_one({"id": cid}, {"$set": body.model_dump()})
    return await db.categories.find_one({"id": cid}, {"_id": 0})


@router.delete("/categories/{cid}")
async def delete_category(cid: str, _: dict = Depends(require_role("admin"))):
    await db.categories.delete_one({"id": cid})
    return {"ok": True}


# Services
@router.get("/services")
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


@router.get("/services/{sid}")
async def get_service(sid: str):
    s = await db.services.find_one({"id": sid}, {"_id": 0})
    if not s:
        raise HTTPException(404, "Service not found")
    cat = await db.categories.find_one({"id": s["category_id"]}, {"_id": 0})
    reviews = await db.reviews.find({"service_id": sid}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"service": s, "category": cat, "reviews": reviews}


@router.post("/services")
async def create_service(body: ServiceIn, _: dict = Depends(require_role("admin"))):
    s = {"id": new_id(), **body.model_dump(), "rating_avg": 0, "rating_count": 0, "created_at": now_iso()}
    await db.services.insert_one(s)
    s.pop("_id", None)
    return s


@router.put("/services/{sid}")
async def update_service(sid: str, body: ServiceIn, _: dict = Depends(require_role("admin"))):
    await db.services.update_one({"id": sid}, {"$set": body.model_dump()})
    return await db.services.find_one({"id": sid}, {"_id": 0})


@router.delete("/services/{sid}")
async def delete_service(sid: str, _: dict = Depends(require_role("admin"))):
    await db.services.delete_one({"id": sid})
    return {"ok": True}


# Cities
@router.get("/cities")
async def list_cities():
    return await db.cities.find({"active": True}, {"_id": 0}).to_list(500)


@router.post("/cities")
async def create_city(body: CityIn, _: dict = Depends(require_role("admin"))):
    c = {"id": new_id(), **body.model_dump()}
    await db.cities.insert_one(c)
    c.pop("_id", None)
    return c


@router.delete("/cities/{cid}")
async def delete_city(cid: str, _: dict = Depends(require_role("admin"))):
    await db.cities.delete_one({"id": cid})
    return {"ok": True}


# Coupons
@router.get("/coupons")
async def list_coupons(_: dict = Depends(require_role("admin"))):
    return await db.coupons.find({}, {"_id": 0}).to_list(200)


@router.post("/coupons")
async def create_coupon(body: CouponIn, _: dict = Depends(require_role("admin"))):
    c = {"id": new_id(), **body.model_dump(), "code": body.code.upper()}
    await db.coupons.insert_one(c)
    c.pop("_id", None)
    return c


@router.delete("/coupons/{cid}")
async def delete_coupon(cid: str, _: dict = Depends(require_role("admin"))):
    await db.coupons.delete_one({"id": cid})
    return {"ok": True}


@router.post("/coupons/validate")
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


# Technicians
@router.get("/technicians")
async def list_technicians():
    return await db.users.find({"role": "technician"}, {"password_hash": 0, "_id": 0}).to_list(500)


@router.get("/technicians/available")
async def available_technicians(_: dict = Depends(require_role("admin"))):
    return await db.users.find({"role": "technician", "is_available": True},
                               {"password_hash": 0, "_id": 0}).to_list(500)


# Contact
@router.post("/contact")
async def create_contact(body: ContactIn):
    c = {"id": new_id(), **body.model_dump(), "status": "new", "created_at": now_iso()}
    await db.contact_requests.insert_one(c)
    c.pop("_id", None)
    return c


# Notifications
@router.get("/notifications")
async def my_notifications(user: dict = Depends(require_role("customer", "technician", "admin"))):
    q = {"$or": [{"user_id": user["id"]}, {"role": user["role"], "user_id": None}]}
    return await db.notifications.find(q, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)


@router.post("/notifications/{nid}/read")
async def mark_read(nid: str, _: dict = Depends(require_role("customer", "technician", "admin"))):
    await db.notifications.update_one({"id": nid}, {"$set": {"read": True}})
    return {"ok": True}
