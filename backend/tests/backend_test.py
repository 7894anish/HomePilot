"""HomeFix Pro backend API test suite (pytest).

Covers: auth (register/login/me/change-pw), categories/services/cities,
coupon validation, booking creation with coupon+cash, admin assign,
technician accept→in_progress→complete, review creation, contact,
Stripe payment checkout URL creation, dashboards, notifications.
"""
import os
import time
import uuid
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") + "/api"

ADMIN = ("admin@homefix.pro", "admin123")
CUST = ("customer@homefix.pro", "customer123")
TECH = ("tech@homefix.pro", "tech123")


# ---------- session helpers ----------
def _sess():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _login(session, email, password):
    r = session.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login {email} -> {r.status_code} {r.text}"
    return r.json()


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


@pytest.fixture(scope="module")
def tech_s():
    s = _sess()
    _login(s, *TECH)
    return s


# ---------- basic ----------
class TestHealth:
    def test_root(self):
        r = requests.get(f"{BASE}/")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ---------- auth ----------
class TestAuth:
    def test_login_admin(self):
        s = _sess()
        u = _login(s, *ADMIN)
        assert u["role"] == "admin"
        assert u["email"] == ADMIN[0]
        # cookie set
        assert "access_token" in s.cookies

    def test_login_wrong_password(self):
        s = _sess()
        r = s.post(f"{BASE}/auth/login", json={"email": "customer@homefix.pro", "password": "wrong"})
        assert r.status_code == 401

    def test_me(self, cust_s):
        r = cust_s.get(f"{BASE}/auth/me")
        assert r.status_code == 200
        assert r.json()["role"] == "customer"

    def test_register_new(self):
        s = _sess()
        email = f"test_{uuid.uuid4().hex[:8]}@homefix.pro"
        r = s.post(f"{BASE}/auth/register", json={
            "name": "Test User", "email": email, "password": "test1234",
            "phone": "+911234500000", "role": "customer",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["email"] == email
        assert data["role"] == "customer"
        assert "access_token" in s.cookies
        # me works
        r2 = s.get(f"{BASE}/auth/me")
        assert r2.status_code == 200 and r2.json()["email"] == email

    def test_register_duplicate(self):
        s = _sess()
        r = s.post(f"{BASE}/auth/register", json={
            "name": "Dup", "email": "customer@homefix.pro", "password": "customer123",
        })
        assert r.status_code == 400

    def test_change_password_and_revert(self):
        s = _sess()
        _login(s, *CUST)
        r = s.post(f"{BASE}/auth/change-password", json={
            "current_password": "customer123", "new_password": "customer1234"
        })
        assert r.status_code == 200
        # revert
        r2 = s.post(f"{BASE}/auth/change-password", json={
            "current_password": "customer1234", "new_password": "customer123"
        })
        assert r2.status_code == 200


# ---------- catalog ----------
class TestCatalog:
    def test_categories(self):
        r = requests.get(f"{BASE}/categories")
        assert r.status_code == 200
        cats = r.json()
        assert len(cats) >= 5
        assert all("id" in c and "slug" in c for c in cats)

    def test_services_list(self):
        r = requests.get(f"{BASE}/services")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] > 0
        assert len(d["items"]) > 0

    def test_services_search(self):
        r = requests.get(f"{BASE}/services", params={"q": "AC"})
        assert r.status_code == 200
        items = r.json()["items"]
        assert any("AC" in it["name"] for it in items)

    def test_services_filter_by_category(self):
        cats = requests.get(f"{BASE}/categories").json()
        cid = next(c["id"] for c in cats if c["slug"] == "cleaning")
        r = requests.get(f"{BASE}/services", params={"category_id": cid})
        d = r.json()
        assert d["total"] > 0
        assert all(it["category_id"] == cid for it in d["items"])

    def test_service_detail(self):
        items = requests.get(f"{BASE}/services").json()["items"]
        sid = items[0]["id"]
        r = requests.get(f"{BASE}/services/{sid}")
        assert r.status_code == 200
        d = r.json()
        assert d["service"]["id"] == sid
        assert "category" in d
        assert isinstance(d["reviews"], list)

    def test_cities(self):
        r = requests.get(f"{BASE}/cities")
        assert r.status_code == 200
        assert len(r.json()) >= 5


# ---------- coupons ----------
class TestCoupons:
    def test_invalid_code(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "NOPE123", "amount": 1000})
        assert r.status_code == 404

    def test_welcome10(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "WELCOME10", "amount": 1000})
        assert r.status_code == 200
        d = r.json()
        assert d["discount"] == 100.0  # 10% of 1000

    def test_welcome10_max_cap(self):
        # 10% of 5000 = 500, but capped at 300
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "WELCOME10", "amount": 5000})
        assert r.status_code == 200
        assert r.json()["discount"] == 300.0

    def test_welcome10_min_order(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "WELCOME10", "amount": 100})
        assert r.status_code == 400

    def test_mega20(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "MEGA20", "amount": 2000})
        assert r.status_code == 200
        assert r.json()["discount"] == 400.0

    def test_firstbook(self):
        r = requests.post(f"{BASE}/coupons/validate", json={"code": "FIRSTBOOK", "amount": 1000})
        assert r.status_code == 200
        assert r.json()["discount"] == 150.0


# ---------- Full booking cycle ----------
@pytest.fixture(scope="module")
def sample_service():
    items = requests.get(f"{BASE}/services").json()["items"]
    # pick a service priced >= 300 to use WELCOME10
    return next(it for it in items if it["price"] >= 500)


@pytest.fixture(scope="module")
def created_booking(cust_s, sample_service):
    payload = {
        "service_id": sample_service["id"],
        "scheduled_date": "2026-12-15",
        "scheduled_time": "10:00",
        "address": "TEST 42, MG Road",
        "city": "Bengaluru",
        "problem_description": "AC not cooling",
        "coupon_code": "WELCOME10",
        "payment_method": "cash",
    }
    r = cust_s.post(f"{BASE}/bookings", json=payload)
    assert r.status_code == 200, r.text
    b = r.json()
    return b


class TestBookingFlow:
    def test_create_booking_cash_with_coupon(self, created_booking, sample_service):
        b = created_booking
        assert b["status"] == "confirmed"
        assert b["payment_method"] == "cash"
        price = sample_service["price"]
        expected_disc = min(price * 0.10, 300.0)
        assert abs(b["discount"] - round(expected_disc, 2)) < 0.01
        assert abs(b["total"] - round(price - expected_disc, 2)) < 0.01

    def test_my_bookings(self, cust_s, created_booking):
        r = cust_s.get(f"{BASE}/bookings/mine")
        assert r.status_code == 200
        ids = [b["id"] for b in r.json()]
        assert created_booking["id"] in ids

    def test_get_booking_detail(self, cust_s, created_booking):
        r = cust_s.get(f"{BASE}/bookings/{created_booking['id']}")
        assert r.status_code == 200
        d = r.json()
        assert d["id"] == created_booking["id"]
        assert d["service"]["id"] == created_booking["service_id"]

    def test_customer_cannot_view_other_booking(self, created_booking):
        # login as a fresh new customer
        s = _sess()
        email = f"TEST_{uuid.uuid4().hex[:6]}@homefix.pro"
        s.post(f"{BASE}/auth/register", json={
            "name": "Other Cust", "email": email, "password": "test1234"
        })
        r = s.get(f"{BASE}/bookings/{created_booking['id']}")
        assert r.status_code == 403

    def test_admin_list_all_bookings(self, admin_s, created_booking):
        r = admin_s.get(f"{BASE}/admin/bookings")
        assert r.status_code == 200
        ids = [b["id"] for b in r.json()]
        assert created_booking["id"] in ids

    def test_admin_assign_technician(self, admin_s, created_booking):
        techs = requests.get(f"{BASE}/technicians").json()
        tech_id = next(t["id"] for t in techs if t["email"] == "tech@homefix.pro")
        r = admin_s.post(f"{BASE}/admin/bookings/{created_booking['id']}/assign",
                          json={"technician_id": tech_id})
        assert r.status_code == 200, r.text
        b = r.json()
        assert b["technician_id"] == tech_id
        assert b["status"] == "assigned"

    def test_tech_accept(self, tech_s, created_booking):
        r = tech_s.post(f"{BASE}/bookings/{created_booking['id']}/status",
                        json={"status": "accepted"})
        assert r.status_code == 200
        assert r.json()["status"] == "accepted"

    def test_tech_in_progress(self, tech_s, created_booking):
        r = tech_s.post(f"{BASE}/bookings/{created_booking['id']}/status",
                        json={"status": "in_progress"})
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    def test_tech_complete(self, tech_s, created_booking):
        r = tech_s.post(f"{BASE}/bookings/{created_booking['id']}/status",
                        json={"status": "completed"})
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_customer_review(self, cust_s, created_booking):
        r = cust_s.post(f"{BASE}/reviews", json={
            "booking_id": created_booking["id"],
            "rating": 5, "comment": "Excellent service"
        })
        assert r.status_code == 200, r.text
        rev = r.json()
        assert rev["rating"] == 5
        # review shows on service detail
        sid = created_booking["service_id"]
        detail = requests.get(f"{BASE}/services/{sid}").json()
        assert any(rv["id"] == rev["id"] for rv in detail["reviews"])

    def test_review_duplicate_blocked(self, cust_s, created_booking):
        r = cust_s.post(f"{BASE}/reviews", json={
            "booking_id": created_booking["id"], "rating": 4
        })
        assert r.status_code == 400


# ---------- Stripe checkout URL ----------
class TestPayment:
    def test_online_booking_checkout_url(self, cust_s, sample_service):
        # create an online booking
        payload = {
            "service_id": sample_service["id"],
            "scheduled_date": "2026-12-20",
            "scheduled_time": "11:00",
            "address": "TEST online",
            "city": "Bengaluru",
            "problem_description": "TEST online payment",
            "payment_method": "online",
        }
        r = cust_s.post(f"{BASE}/bookings", json=payload)
        assert r.status_code == 200
        b = r.json()
        assert b["status"] == "pending_payment"

        # checkout
        r2 = cust_s.post(f"{BASE}/payments/checkout", json={
            "booking_id": b["id"],
            "origin_url": os.environ["REACT_APP_BACKEND_URL"].rstrip("/"),
        })
        assert r2.status_code == 200, r2.text
        d = r2.json()
        assert "checkout_url" in d and d["checkout_url"].startswith("http")
        assert "session_id" in d


# ---------- Contact + notifications + dashboards ----------
class TestMisc:
    def test_contact_submit(self, admin_s):
        subj = f"TEST_{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{BASE}/contact", json={
            "name": "Test", "email": "test@example.com",
            "subject": subj, "message": "Hello"
        })
        assert r.status_code == 200
        r2 = admin_s.get(f"{BASE}/admin/contact")
        assert r2.status_code == 200
        assert any(c["subject"] == subj for c in r2.json())

    def test_notifications_customer(self, cust_s):
        r = cust_s.get(f"{BASE}/notifications")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_notifications_admin(self, admin_s):
        r = admin_s.get(f"{BASE}/notifications")
        assert r.status_code == 200

    def test_admin_dashboard(self, admin_s):
        r = admin_s.get(f"{BASE}/dashboard/admin")
        assert r.status_code == 200
        d = r.json()
        assert "kpi" in d and "weekly" in d and "top_services" in d

    def test_customer_dashboard(self, cust_s):
        r = cust_s.get(f"{BASE}/dashboard/customer")
        assert r.status_code == 200
        assert "total" in r.json()

    def test_tech_dashboard(self, tech_s):
        r = tech_s.get(f"{BASE}/dashboard/technician")
        assert r.status_code == 200
        assert "assigned" in r.json()

    def test_role_forbidden(self, cust_s):
        r = cust_s.get(f"{BASE}/admin/bookings")
        assert r.status_code == 403
