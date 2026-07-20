"""Booking + review routes."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from ..db import db, now_iso, new_id
from ..security import get_current_user, require_role
from ..models import BookingCreate, BookingStatusIn, AssignTechIn, ReviewIn
from ..emailer import send_email, booking_email

log = logging.getLogger("homefix.bookings")
router = APIRouter(tags=["bookings"])


async def _hydrate(b: dict) -> dict:
    b.pop("_id", None)
    b["service"] = await db.services.find_one({"id": b["service_id"]}, {"_id": 0})
    if b.get("customer_id"):
        b["customer"] = await db.users.find_one({"id": b["customer_id"]}, {"_id": 0, "password_hash": 0})
    if b.get("technician_id"):
        b["technician"] = await db.users.find_one({"id": b["technician_id"]}, {"_id": 0, "password_hash": 0})
    return b


@router.post("/bookings")
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
        "id": new_id(), "customer_id": user["id"], "technician_id": None,
        "service_id": body.service_id, "service_name": service["name"],
        "scheduled_date": body.scheduled_date, "scheduled_time": body.scheduled_time,
        "address": body.address, "city": body.city,
        "problem_description": body.problem_description,
        "images": body.images, "coupon_code": body.coupon_code,
        "amount": amount, "discount": discount, "total": total,
        "payment_method": body.payment_method,
        "payment_status": "pending",
        "status": "pending_payment" if body.payment_method == "online" else "confirmed",
        "work_images": [], "created_at": now_iso(), "updated_at": now_iso(),
        "status_history": [{"status": "created", "at": now_iso()}],
    }
    await db.bookings.insert_one(booking)
    await db.notifications.insert_one({
        "id": new_id(), "user_id": None, "role": "admin",
        "title": "New booking", "message": f"{user['name']} booked {service['name']}",
        "booking_id": booking["id"], "read": False, "created_at": now_iso(),
    })
    if body.payment_method == "cash":
        subj, title, html = booking_email(user["name"], booking)
        try:
            await send_email(user["email"], subj, title, html)
        except Exception as e:
            log.warning(f"booking mail failed: {e}")
    return await _hydrate(booking)


@router.get("/bookings/mine")
async def my_bookings(user: dict = Depends(get_current_user)):
    if user["role"] == "customer":
        q = {"customer_id": user["id"]}
    elif user["role"] == "technician":
        q = {"technician_id": user["id"]}
    else:
        q = {}
    items = await db.bookings.find(q).sort("created_at", -1).to_list(500)
    return [await _hydrate(b) for b in items]


@router.get("/bookings/{bid}")
async def get_booking(bid: str, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"id": bid})
    if not b:
        raise HTTPException(404, "Not found")
    if user["role"] == "customer" and b["customer_id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if user["role"] == "technician" and b.get("technician_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    return await _hydrate(b)


@router.post("/bookings/{bid}/status")
async def update_status(bid: str, body: BookingStatusIn, user: dict = Depends(get_current_user)):
    b = await db.bookings.find_one({"id": bid})
    if not b:
        raise HTTPException(404, "Not found")
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
    upd = {"status": body.status, "updated_at": now_iso()}
    if body.status == "rejected":
        upd["technician_id"] = None
    await db.bookings.update_one({"id": bid}, {
        "$set": upd,
        "$push": {"status_history": {"status": body.status, "at": now_iso(), "note": body.note}},
    })
    await db.notifications.insert_one({
        "id": new_id(), "user_id": b["customer_id"], "role": "customer",
        "title": f"Booking {body.status}",
        "message": body.note or f"Your booking is now {body.status}",
        "booking_id": bid, "read": False, "created_at": now_iso(),
    })
    return await _hydrate(await db.bookings.find_one({"id": bid}))


@router.post("/bookings/{bid}/work-images")
async def upload_work_images(bid: str, payload: dict, user: dict = Depends(require_role("technician"))):
    b = await db.bookings.find_one({"id": bid})
    if not b or b.get("technician_id") != user["id"]:
        raise HTTPException(403, "Forbidden")
    imgs = payload.get("images", [])
    await db.bookings.update_one({"id": bid}, {
        "$push": {"work_images": {"$each": imgs}},
        "$set": {"updated_at": now_iso()},
    })
    return {"ok": True}


# Admin assign
@router.post("/admin/bookings/{bid}/assign")
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
    return await _hydrate(b)


# Reviews
@router.post("/reviews")
async def create_review(body: ReviewIn, user: dict = Depends(require_role("customer"))):
    b = await db.bookings.find_one({"id": body.booking_id})
    if not b or b["customer_id"] != user["id"]:
        raise HTTPException(403, "Forbidden")
    if b["status"] != "completed":
        raise HTTPException(400, "Can only review completed bookings")
    if await db.reviews.find_one({"booking_id": body.booking_id}):
        raise HTTPException(400, "Already reviewed")
    rev = {
        "id": new_id(), "booking_id": body.booking_id,
        "service_id": b["service_id"], "technician_id": b.get("technician_id"),
        "customer_id": user["id"], "customer_name": user["name"],
        "rating": body.rating, "comment": body.comment, "created_at": now_iso(),
    }
    await db.reviews.insert_one(rev)
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


@router.get("/reviews/mine")
async def my_reviews(user: dict = Depends(get_current_user)):
    q: dict = {}
    if user["role"] == "customer":
        q = {"customer_id": user["id"]}
    elif user["role"] == "technician":
        q = {"technician_id": user["id"]}
    return await db.reviews.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
