# HomeFix Pro — Product Requirements Document

## Problem Statement (original)
Build a production-ready Urban Company-style home services platform for Plumbing, Electrical, Electronics Repair, AC Repair, Appliance Repair, Carpentry, Painting, Home Cleaning, Water Purifier Service, CCTV Installation and other home services. Full customer/technician/admin flows with charts, ratings, coupons, live status, payments and multi-role auth.

## Tech Choices (user-confirmed)
- **Stack:** React + FastAPI + MongoDB + Shadcn/Tailwind (blue #0d6efd / orange #fd7e14)
- **Auth:** JWT httpOnly cookies (bcrypt), roles: admin / customer / technician
- **Payments:** Stripe Flow B via `emergentintegrations` (`sk_test_emergent`) + Cash on service
- **Emails:** Console log for MVP (Resend integration deferred)

## User Personas
- **Customer** — books services, tracks bookings, pays online/cash, leaves reviews
- **Technician** — accepts/rejects jobs, updates status, uploads work photos, earns commissions
- **Admin** — manages catalog, users, bookings, assigns technicians, monitors analytics

## Implemented (2026-02, iteration 2)
- ✅ **Modularized backend**: server.py 1077→60 lines. Routers split into `app/routers/{auth,catalog,bookings,payments,admin,uploads}.py`; shared `app/{db,security,models,emailer,storage,seed}.py`.
- ✅ **Resend emails** wired via `emergentintegrations` proxy for welcome, booking confirmation & password reset — falls back to logs when `EMERGENT_EMAIL_KEY` is empty (platform-provisioned).
- ✅ **File upload** endpoint `POST /api/upload` + serve at `GET /api/files/{id}` using Emergent object storage; 5MB limit + MIME whitelist. Booking wizard now has a real file picker (was URL input).
- ✅ **Debounced search** on /services (350 ms) — no more Enter needed.
- Test coverage: **56/56 backend** (38 regression + 18 new), full E2E in Playwright.

## Implemented (2026-02, iteration 1)
- ✅ Public: Home (hero, categories, popular services, why-us, process, testimonials, FAQ, CTA, footer, WhatsApp+call FAB), About, Services (search/filter/pagination), Service Detail, Contact
- ✅ Auth: register (customer/technician), login, logout, /me, refresh, forgot/reset password, change password, brute-force lockout, admin seeded
- ✅ Customer dashboard: overview KPIs, My Bookings, Booking detail (cancel + pay), Payments, Reviews, Notifications
- ✅ Booking flow: 4-step wizard (date → time → address → details → payment) with coupon validation, discount applied, cash or Stripe online
- ✅ Technician dashboard: overview, Assigned Jobs, Accept/Reject/Start/Complete flow, Earnings, Reviews, Notifications
- ✅ Admin dashboard: KPIs, weekly bookings+revenue line chart, status pie, top services bar chart, Bookings list w/ Assign, Customers/Technicians/Services/Categories/Coupons/Cities/Reviews/Contact CRUD
- ✅ Reviews with automatic rating aggregation on service + technician
- ✅ Stripe online payment with polling, session lookup, webhook idempotency
- ✅ Seed data: 3 users, 8 cities, 10 categories, 28 services, 3 coupons

## Test Coverage
- Backend: 38/38 pytest passing
- Frontend: full booking → assignment → completion → review cycle verified E2E

## Backlog (P1/P2)
- **P1**: Real image upload (currently URL input) — plug in object storage playbook
- **P1**: Email notifications (booking confirmation, password reset, tech assignment) via Resend
- **P1**: Live search debounce on /services
- **P2**: Razorpay integration (India-native)
- **P2**: Dark mode toggle
- **P2**: PDF invoice generation
- **P2**: Multi-language (i18n)
- **P2**: Push notifications + real-time booking status via WebSockets
- **P2**: Google Maps for address picking + nearby technician
- **P2**: Modularize server.py into routers (auth, bookings, admin, payments)
