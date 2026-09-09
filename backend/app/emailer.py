"""Transactional email helper using the standard Resend HTTP API.

When RESEND_API_KEY or EMAIL_FROM is not configured, messages are logged so
local development remains fully functional.
"""
import logging
import os

import httpx

log = logging.getLogger("homefix.email")

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "HomeFix Pro")


def _wrap(title: str, body_html: str) -> str:
    """Basic responsive HTML email shell with the brand colors."""
    return f"""
<html>
  <body style="margin:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:40px 0;">
      <tr><td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(15,23,42,0.06);">
          <tr><td style="background:#0d6efd;padding:24px 32px;color:#ffffff;">
            <div style="font-size:20px;font-weight:800;">HomeFix<span style="color:#fd7e14;">.</span>Pro</div>
            <div style="font-size:12px;opacity:0.8;letter-spacing:2px;text-transform:uppercase;">Home services, on demand</div>
          </td></tr>
          <tr><td style="padding:32px;">
            <h1 style="margin:0 0 16px 0;font-size:24px;color:#0f172a;">{title}</h1>
            <div style="color:#334155;font-size:15px;line-height:1.6;">{body_html}</div>
          </td></tr>
          <tr><td style="padding:20px 32px;background:#f8fafc;color:#94a3b8;font-size:12px;text-align:center;">
            © HomeFix Pro · Need help? Reply to this email.
          </td></tr>
        </table>
      </td></tr>
    </table>
  </body>
</html>
""".strip()


async def send_email(to: str, subject: str, title: str, body_html: str,
                     reply_to: str | None = None) -> None:
    """Send an email without allowing delivery errors to break app requests."""
    html = _wrap(title, body_html)
    if not RESEND_API_KEY or not EMAIL_FROM:
        log.info(
            "[email:mock] to=%s subject=%r — set RESEND_API_KEY and EMAIL_FROM to send",
            to,
            subject,
        )
        log.debug(html)
        return

    payload = {
        "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>",
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if reply_to:
        payload["reply_to"] = reply_to

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "User-Agent": "HomeFix-Pro/1.0",
                },
                json=payload,
            )
            response.raise_for_status()
            log.info(
                "[email] sent to=%s subject=%r id=%s",
                to,
                subject,
                response.json().get("id"),
            )
    except httpx.HTTPStatusError as exc:
        log.error("[email] failed %s: %s", exc.response.status_code, exc.response.text[:200])
    except Exception:
        log.exception("[email] delivery error")


def welcome_email(name: str) -> tuple[str, str, str]:
    return (
        "Welcome to HomeFix Pro!",
        "You're all set!",
        f"""
        <p>Hi <b>{name}</b>,</p>
        <p>Welcome to HomeFix Pro — India's fastest way to book verified home-services pros.</p>
        <p>Use coupon <b style="background:#fff3e0;padding:4px 10px;border-radius:6px;color:#fd7e14;">WELCOME10</b> for 10% off your first booking.</p>
        <p><a href="#" style="display:inline-block;background:#0d6efd;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Browse services</a></p>
        """,
    )


def booking_email(name: str, booking: dict) -> tuple[str, str, str]:
    return (
        f"Booking confirmed — {booking['service_name']}",
        "Your booking is confirmed",
        f"""
        <p>Hi <b>{name}</b>, thanks for booking with HomeFix Pro. Here are your details:</p>
        <table cellpadding="8" style="width:100%;font-size:14px;border:1px solid #e2e8f0;border-radius:8px;">
          <tr><td style="color:#64748b;">Service</td><td><b>{booking['service_name']}</b></td></tr>
          <tr style="background:#f8fafc;"><td style="color:#64748b;">Date &amp; Time</td><td>{booking['scheduled_date']} · {booking['scheduled_time']}</td></tr>
          <tr><td style="color:#64748b;">Address</td><td>{booking['address']}</td></tr>
          <tr style="background:#f8fafc;"><td style="color:#64748b;">Total</td><td><b>₹{booking['total']}</b></td></tr>
          <tr><td style="color:#64748b;">Booking ID</td><td>#{booking['id'][:8].upper()}</td></tr>
        </table>
        <p style="margin-top:16px;">A verified professional will be assigned soon. You can track live status in your dashboard.</p>
        """,
    )


def reset_email(name: str, token: str, origin: str) -> tuple[str, str, str]:
    link = f"{origin}/reset-password?token={token}"
    return (
        "Reset your HomeFix Pro password",
        "Reset your password",
        f"""
        <p>Hi <b>{name}</b>,</p>
        <p>Someone (hopefully you) requested a password reset. Click the button below to set a new password. The link expires in 1 hour.</p>
        <p><a href="{link}" style="display:inline-block;background:#0d6efd;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">Reset password</a></p>
        <p style="font-size:12px;color:#94a3b8;">If you didn't request this, ignore this email.</p>
        """,
    )
