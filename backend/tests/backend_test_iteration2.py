"""HomeFix Pro — iteration 2 tests.

Covers new/modified surface:
- POST /api/upload (multipart, auth-required, size/MIME validation)
- GET /api/files/{id} (returns binary + correct Content-Type)
- POST /api/auth/forgot-password → returns reset_token + logs mock email
- POST /api/auth/reset-password with token updates the password
- Welcome email is logged on registration
- Booking-confirmation email is logged on cash booking creation
- Debounced live search on /services still returns filtered results
- Regression: root, categories, services, admin dashboard, coupons/validate
"""
import io
import os
import uuid
import time
import struct
import zlib
import subprocess
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"
BACKEND_LOG = "/var/log/supervisor/backend.err.log"

ADMIN = ("admin@homefix.pro", "admin123")
CUST = ("customer@homefix.pro", "customer123")


def _sess():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(session, email, password):
    r = session.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email} -> {r.status_code} {r.text}"
    return r.json()


def _tail_backend_log(n=2000) -> str:
    """Read tail of backend log (both err+out); tolerate rotation."""
    out = ""
    for path in ("/var/log/supervisor/backend.err.log", "/var/log/supervisor/backend.out.log"):
        try:
            r = subprocess.run(["tail", "-n", str(n), path], capture_output=True, text=True, timeout=5)
            out += r.stdout + "\n"
        except Exception:
            pass
    return out


def _grep_backend_log(pattern: str) -> str:
    """Grep both backend logs for a pattern — more reliable across log volume."""
    out = ""
    for path in ("/var/log/supervisor/backend.err.log", "/var/log/supervisor/backend.out.log"):
        try:
            r = subprocess.run(["grep", "-F", pattern, path], capture_output=True, text=True, timeout=5)
            out += r.stdout
        except Exception:
            pass
    return out


def _tiny_png() -> bytes:
    """Build a minimal valid 1x1 PNG (transparent) without pillow dep."""
    # signature + IHDR + IDAT + IEND
    sig = b"\x89PNG\r\n\x1a\n"
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    raw = b"\x00\x00\x00\x00\x00"  # 1 scanline: filter byte + RGBA
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ---------- fixtures ----------
@pytest.fixture(scope="module")
def admin_s():
    s = _sess()
    _login(s, *ADMIN)
    return s


@pytest.fixture(scope="module")
def cust_s():
    s = _sess()
    _login(s, *CUST)
    return s


# ---------- regression ----------
class TestRegression:
    def test_root(self):
        r = requests.get(f"{BASE}/")
        assert r.status_code == 200 and r.json()["status"] == "ok"

    def test_categories(self):
        r = requests.get(f"{BASE}/categories")
        assert r.status_code == 200 and len(r.json()) >= 5

    def test_services_list(self):
        r = requests.get(f"{BASE}/services")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] > 0 and len(d["items"]) > 0

    def test_admin_dashboard(self, admin_s):
        r = admin_s.get(f"{BASE}/dashboard/admin")
        assert r.status_code == 200
        d = r.json()
        for k in ("kpi", "weekly", "top_services"):
            assert k in d

    def test_coupon_validate(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "WELCOME10", "amount": 1000})
        assert r.status_code == 200 and r.json()["discount"] == 100.0

    def test_notifications(self, cust_s):
        r = cust_s.get(f"{BASE}/notifications")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_contact(self):
        subj = f"TEST_it2_{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{BASE}/contact", json={
            "name": "T", "email": "t@x.io", "subject": subj, "message": "hi"
        })
        assert r.status_code == 200


# ---------- Debounced/live services search backend ----------
class TestSearch:
    def test_services_search_ac(self):
        r = requests.get(f"{BASE}/services", params={"q": "AC"})
        assert r.status_code == 200
        items = r.json()["items"]
        assert any("AC" in it["name"] for it in items)

    def test_services_search_no_match(self):
        r = requests.get(f"{BASE}/services", params={"q": "zzzzzzz"})
        assert r.status_code == 200
        assert r.json()["total"] == 0


# ---------- File upload / download ----------
class TestUpload:
    def test_upload_requires_auth(self):
        # anonymous → 401
        png = _tiny_png()
        r = requests.post(f"{BASE}/upload",
                          files={"file": ("t.png", png, "image/png")})
        assert r.status_code in (401, 403), r.text

    def test_upload_success_and_download(self, cust_s):
        png = _tiny_png()
        r = cust_s.post(f"{BASE}/upload",
                        files={"file": ("test.png", png, "image/png")})
        # requests session inherits Content-Type=json header; override via files kw uses multipart
        # but we've set json content-type on the session. requests's files= replaces content-type.
        # Remove header if it interferes
        if r.status_code == 422:
            # retry without json header
            s2 = requests.Session()
            s2.cookies.update(cust_s.cookies)
            r = s2.post(f"{BASE}/upload",
                        files={"file": ("test.png", png, "image/png")})
        assert r.status_code == 200, r.text
        d = r.json()
        assert "id" in d and "path" in d and "url" in d and "size" in d
        assert d["size"] == len(png)
        assert d["url"].startswith("/api/files/")
        # GET download
        rd = requests.get(BASE.rsplit("/api", 1)[0] + d["url"])
        assert rd.status_code == 200
        assert rd.headers.get("Content-Type", "").startswith("image/png")
        assert rd.content == png

    def test_upload_rejects_non_image(self, cust_s):
        s2 = requests.Session()
        s2.cookies.update(cust_s.cookies)
        r = s2.post(f"{BASE}/upload",
                    files={"file": ("bad.txt", b"hello", "text/plain")})
        assert r.status_code == 400, r.text
        assert "jpg" in r.text.lower() or "png" in r.text.lower() or "allowed" in r.text.lower()

    def test_upload_rejects_oversize(self, cust_s):
        s2 = requests.Session()
        s2.cookies.update(cust_s.cookies)
        big = b"\x89PNG\r\n\x1a\n" + b"a" * (5 * 1024 * 1024 + 10)
        r = s2.post(f"{BASE}/upload",
                    files={"file": ("big.png", big, "image/png")})
        assert r.status_code == 400, r.text
        assert "large" in r.text.lower() or "5" in r.text

    def test_download_nonexistent(self):
        r = requests.get(f"{BASE}/files/{uuid.uuid4()}")
        assert r.status_code == 404


# ---------- Password reset ----------
class TestPasswordReset:
    def test_forgot_and_reset_flow(self):
        # register a throwaway user
        s = _sess()
        email = f"TEST_reset_{uuid.uuid4().hex[:6]}@homefix.pro"
        r = s.post(f"{BASE}/auth/register", json={
            "name": "Reset User", "email": email, "password": "originalpw"
        })
        assert r.status_code == 200
        # forgot-password
        r2 = requests.post(f"{BASE}/auth/forgot-password", json={"email": email})
        assert r2.status_code == 200
        body = r2.json()
        assert body.get("ok") is True
        token = body.get("reset_token")
        assert token and len(token) > 10
        # reset
        r3 = requests.post(f"{BASE}/auth/reset-password", json={
            "token": token, "password": "newpassword123"
        })
        assert r3.status_code == 200 and r3.json()["ok"] is True
        # login with new password
        s2 = _sess()
        r4 = s2.post(f"{BASE}/auth/login", json={"email": email, "password": "newpassword123"})
        assert r4.status_code == 200
        # old password rejected
        s3 = _sess()
        r5 = s3.post(f"{BASE}/auth/login", json={"email": email, "password": "originalpw"})
        assert r5.status_code == 401
        # token cannot be reused
        r6 = requests.post(f"{BASE}/auth/reset-password", json={
            "token": token, "password": "another"
        })
        assert r6.status_code == 400

    def test_forgot_unknown_email_returns_ok(self):
        # Should not reveal whether email exists
        r = requests.post(f"{BASE}/auth/forgot-password",
                          json={"email": "nobody-xyz@example.io"})
        assert r.status_code == 200


# ---------- Email logging (mock mode) ----------
class TestEmailLogs:
    def test_welcome_email_logged_on_register(self):
        s = _sess()
        email = f"TEST_wel_{uuid.uuid4().hex[:6]}@homefix.pro"
        r = s.post(f"{BASE}/auth/register", json={
            "name": "Welcome Tester", "email": email, "password": "test1234"
        })
        assert r.status_code == 200
        time.sleep(1.0)
        # backend lowercases email on register — search accordingly
        matches = _grep_backend_log(email.lower())
        assert "email:mock" in matches, (
            f"Expected mock welcome email log for {email}, got: {matches!r}\n"
            f"Recent log tail: {_tail_backend_log(200)[-800:]}"
        )
        assert "Welcome to HomeFix Pro" in matches

    def test_booking_confirmation_email_logged(self, cust_s):
        # pick a service
        svc = requests.get(f"{BASE}/services", params={"size": 1}).json()["items"][0]
        marker = f"TEST it2 email {uuid.uuid4().hex[:6]}"
        payload = {
            "service_id": svc["id"],
            "scheduled_date": "2026-12-30",
            "scheduled_time": "12:00",
            "address": marker,
            "city": "Bengaluru",
            "problem_description": "TEST for email log",
            "payment_method": "cash",
        }
        r = cust_s.post(f"{BASE}/bookings", json=payload)
        assert r.status_code == 200, r.text
        booking_id = r.json()["id"]
        time.sleep(1.0)
        # Booking-confirmation email must have been logged as "email:mock"
        # with subject "Booking confirmed" and destination customer@homefix.pro
        conf = _grep_backend_log("Booking confirmed")
        assert "email:mock" in conf, f"No booking-confirmed email log. Got: {conf!r}"
        # Ensure at least one such line is for the customer used here
        assert "customer@homefix.pro" in conf
