"""Stripe checkout + polling + webhook (Flow B via emergentintegrations)."""
import os
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

from ..db import db, now_iso, new_id
from ..security import get_current_user, require_role
from ..models import CheckoutIn

log = logging.getLogger("homefix.payments")
router = APIRouter(tags=["payments"])
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")


def _client(request: Request) -> StripeCheckout:
    webhook_url = f"{str(request.base_url).rstrip('/')}/api/webhook/stripe"
    return StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)


@router.post("/payments/checkout")
async def create_checkout(body: CheckoutIn, request: Request,
                          user: dict = Depends(require_role("customer"))):
    b = await db.bookings.find_one({"id": body.booking_id})
    if not b or b["customer_id"] != user["id"]:
        raise HTTPException(404, "Booking not found")
    if b.get("payment_status") == "paid":
        raise HTTPException(400, "Already paid")
    amount = float(b["total"])
    origin = body.origin_url.rstrip("/")
    checkout = _client(request)
    req = CheckoutSessionRequest(
        amount=amount, currency="inr",
        success_url=f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{origin}/payment/cancel?booking_id={b['id']}",
        metadata={"booking_id": b["id"], "user_id": user["id"]},
    )
    session = await checkout.create_checkout_session(req)
    await db.payment_transactions.insert_one({
        "id": new_id(), "session_id": session.session_id,
        "booking_id": b["id"], "user_id": user["id"],
        "amount": amount, "currency": "inr",
        "status": "initiated", "payment_status": "pending",
        "created_at": now_iso(), "updated_at": now_iso(),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}


async def _mark_paid(session_id: str) -> None:
    """Idempotent: mark tx + booking as paid + email confirmation."""
    tx = await db.payment_transactions.find_one({"session_id": session_id})
    if not tx or tx.get("payment_status") == "paid":
        return
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {"status": "completed", "payment_status": "paid", "updated_at": now_iso()}},
    )
    await db.bookings.update_one(
        {"id": tx["booking_id"], "payment_status": {"$ne": "paid"}},
        {"$set": {"payment_status": "paid", "status": "confirmed", "updated_at": now_iso()},
         "$push": {"status_history": {"status": "paid", "at": now_iso()}}},
    )
    b = await db.bookings.find_one({"id": tx["booking_id"]})
    user = await db.users.find_one({"id": tx["user_id"]})
    if b and user:
        try:
            from ..emailer import send_email, booking_email
            subj, title, html = booking_email(user["name"], b)
            await send_email(user["email"], subj, title, html)
        except Exception as e:
            log.warning(f"paid confirmation mail failed: {e}")


@router.get("/payments/status/{session_id}")
async def payment_status(session_id: str, request: Request):
    rec = await db.payment_transactions.find_one({"session_id": session_id})
    if not rec:
        raise HTTPException(404, "Not found")
    if rec.get("payment_status") != "paid":
        try:
            s = await _client(request).get_checkout_status(session_id)
            if s.payment_status == "paid" or s.status == "complete":
                await _mark_paid(session_id)
                rec = await db.payment_transactions.find_one({"session_id": session_id})
        except Exception as e:
            log.warning(f"poll error: {e}")
    return {"session_id": rec["session_id"], "status": rec["status"],
            "payment_status": rec["payment_status"], "booking_id": rec.get("booking_id")}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    checkout = _client(request)
    body_bytes = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        resp = await checkout.handle_webhook(body_bytes, signature)
    except Exception as e:
        raise HTTPException(400, f"Webhook error: {e}")
    if resp.payment_status == "paid":
        await _mark_paid(resp.session_id)
    return {"ok": True}


@router.get("/payments/mine")
async def my_payments(user: dict = Depends(get_current_user)):
    q = {"user_id": user["id"]} if user["role"] != "admin" else {}
    return await db.payment_transactions.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
