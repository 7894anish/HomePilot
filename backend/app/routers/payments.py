"""Stripe Checkout, payment status polling, and webhook handling."""
import asyncio
import logging
import os

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request

from ..db import db, now_iso, new_id
from ..models import CheckoutIn
from ..security import get_current_user, require_role

log = logging.getLogger("homefix.payments")
router = APIRouter(tags=["payments"])

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")


def _configure_stripe() -> None:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Online payments are not configured")
    stripe.api_key = STRIPE_SECRET_KEY


@router.post("/payments/checkout")
async def create_checkout(body: CheckoutIn,
                          user: dict = Depends(require_role("customer"))):
    _configure_stripe()
    booking = await db.bookings.find_one({"id": body.booking_id})
    if not booking or booking["customer_id"] != user["id"]:
        raise HTTPException(404, "Booking not found")
    if booking.get("payment_status") == "paid":
        raise HTTPException(400, "Already paid")

    amount = float(booking["total"])
    origin = body.origin_url.rstrip("/")
    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "inr",
                    "unit_amount": int(round(amount * 100)),
                    "product_data": {"name": booking["service_name"]},
                },
                "quantity": 1,
            }],
            success_url=f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin}/payment/cancel?booking_id={booking['id']}",
            customer_email=user.get("email"),
            metadata={"booking_id": booking["id"], "user_id": user["id"]},
        )
    except stripe.StripeError as exc:
        log.warning("Stripe checkout creation failed: %s", exc)
        raise HTTPException(502, "Could not start online payment") from exc

    await db.payment_transactions.insert_one({
        "id": new_id(),
        "session_id": session.id,
        "booking_id": booking["id"],
        "user_id": user["id"],
        "amount": amount,
        "currency": "inr",
        "status": "initiated",
        "payment_status": "pending",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    })
    return {"checkout_url": session.url, "session_id": session.id}


async def _mark_paid(session_id: str) -> None:
    """Idempotently mark the transaction and booking as paid."""
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction or transaction.get("payment_status") == "paid":
        return

    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": "completed",
            "payment_status": "paid",
            "updated_at": now_iso(),
        }},
    )
    await db.bookings.update_one(
        {"id": transaction["booking_id"], "payment_status": {"$ne": "paid"}},
        {
            "$set": {
                "payment_status": "paid",
                "status": "confirmed",
                "updated_at": now_iso(),
            },
            "$push": {"status_history": {"status": "paid", "at": now_iso()}},
        },
    )

    booking = await db.bookings.find_one({"id": transaction["booking_id"]})
    user = await db.users.find_one({"id": transaction["user_id"]})
    if booking and user:
        try:
            from ..emailer import booking_email, send_email

            subject, title, html = booking_email(user["name"], booking)
            await send_email(user["email"], subject, title, html)
        except Exception:
            log.exception("Paid booking confirmation email failed")


@router.get("/payments/status/{session_id}")
async def payment_status(session_id: str,
                         user: dict = Depends(get_current_user)):
    transaction = await db.payment_transactions.find_one({"session_id": session_id})
    if not transaction or (
        user["role"] != "admin" and transaction["user_id"] != user["id"]
    ):
        raise HTTPException(404, "Payment not found")

    if transaction.get("payment_status") != "paid" and STRIPE_SECRET_KEY:
        _configure_stripe()
        try:
            session = await asyncio.to_thread(stripe.checkout.Session.retrieve, session_id)
            if session.payment_status == "paid":
                await _mark_paid(session_id)
                transaction = await db.payment_transactions.find_one({"session_id": session_id})
        except stripe.StripeError as exc:
            log.warning("Stripe payment status check failed: %s", exc)

    return {
        "session_id": transaction["session_id"],
        "status": transaction["status"],
        "payment_status": transaction["payment_status"],
        "booking_id": transaction.get("booking_id"),
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    _configure_stripe()
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503, "Stripe webhook is not configured")

    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(400, "Invalid Stripe webhook") from exc

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("payment_status") == "paid":
            await _mark_paid(session["id"])
    return {"ok": True}


@router.get("/payments/mine")
async def my_payments(user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]} if user["role"] != "admin" else {}
    return await db.payment_transactions.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
