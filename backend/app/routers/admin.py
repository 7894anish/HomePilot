"""Admin-only routes + dashboards."""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends

from ..db import db, now_utc
from ..security import require_role

router = APIRouter(tags=["admin"])


@router.get("/admin/users")
async def list_users(role: Optional[str] = None, _: dict = Depends(require_role("admin"))):
    q = {"role": role} if role else {}
    return await db.users.find(q, {"password_hash": 0, "_id": 0}).to_list(1000)


@router.delete("/admin/users/{uid}")
async def delete_user(uid: str, _: dict = Depends(require_role("admin"))):
    await db.users.delete_one({"id": uid})
    return {"ok": True}


@router.get("/admin/bookings")
async def all_bookings(status: Optional[str] = None, _: dict = Depends(require_role("admin"))):
    from .bookings import _hydrate
    q = {"status": status} if status else {}
    items = await db.bookings.find(q).sort("created_at", -1).to_list(1000)
    return [await _hydrate(b) for b in items]


@router.get("/admin/reviews")
async def all_reviews(_: dict = Depends(require_role("admin"))):
    return await db.reviews.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)


@router.delete("/admin/reviews/{rid}")
async def delete_review(rid: str, _: dict = Depends(require_role("admin"))):
    await db.reviews.delete_one({"id": rid})
    return {"ok": True}


@router.get("/admin/contact")
async def list_contact(_: dict = Depends(require_role("admin"))):
    return await db.contact_requests.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)


# Dashboards
@router.get("/dashboard/admin")
async def admin_dash(_: dict = Depends(require_role("admin"))):
    total_bookings = await db.bookings.count_documents({})
    completed = await db.bookings.count_documents({"status": "completed"})
    pending = await db.bookings.count_documents({"status": {
        "$in": ["confirmed", "assigned", "in_progress", "accepted", "pending_payment"]
    }})
    customers = await db.users.count_documents({"role": "customer"})
    technicians = await db.users.count_documents({"role": "technician"})
    rev_pipe = await db.bookings.aggregate([
        {"$match": {"status": "completed"}},
        {"$group": {"_id": None, "sum": {"$sum": "$total"}}}
    ]).to_list(1)
    revenue = rev_pipe[0]["sum"] if rev_pipe else 0
    week_ago = (now_utc() - timedelta(days=7)).isoformat()
    weekly = await db.bookings.aggregate([
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": {"$substr": ["$created_at", 0, 10]},
                     "count": {"$sum": 1}, "revenue": {"$sum": "$total"}}},
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
                "customers": customers, "technicians": technicians,
                "revenue": round(revenue, 2)},
        "weekly": weekly, "by_status": by_status, "top_services": top_services,
    }


@router.get("/dashboard/customer")
async def customer_dash(user: dict = Depends(require_role("customer"))):
    total = await db.bookings.count_documents({"customer_id": user["id"]})
    completed = await db.bookings.count_documents({"customer_id": user["id"], "status": "completed"})
    pending = await db.bookings.count_documents({"customer_id": user["id"],
                                                 "status": {"$nin": ["completed", "cancelled", "rejected"]}})
    spend = await db.bookings.aggregate([
        {"$match": {"customer_id": user["id"], "payment_status": "paid"}},
        {"$group": {"_id": None, "s": {"$sum": "$total"}}}
    ]).to_list(1)
    return {"total": total, "completed": completed, "pending": pending,
            "total_spent": spend[0]["s"] if spend else 0}


@router.get("/dashboard/technician")
async def tech_dash(user: dict = Depends(require_role("technician"))):
    assigned = await db.bookings.count_documents({"technician_id": user["id"]})
    completed = await db.bookings.count_documents({"technician_id": user["id"], "status": "completed"})
    active = await db.bookings.count_documents({"technician_id": user["id"],
                                                "status": {"$in": ["assigned", "accepted", "in_progress"]}})
    earn = await db.bookings.aggregate([
        {"$match": {"technician_id": user["id"], "status": "completed"}},
        {"$group": {"_id": None, "s": {"$sum": "$total"}}}
    ]).to_list(1)
    rating_row = await db.users.find_one({"id": user["id"]},
                                         {"_id": 0, "rating_avg": 1, "rating_count": 1}) or {}
    return {"assigned": assigned, "completed": completed, "active": active,
            "earnings": round((earn[0]["s"] if earn else 0) * 0.7, 2),
            "rating": rating_row}
