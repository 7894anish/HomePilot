"""Startup DB indexes + seed data."""
import logging
import os

from .db import db, now_iso, new_id
from .security import hash_pw

log = logging.getLogger("homefix.seed")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@homefix.pro")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

CATEGORIES = [
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

SERVICES = [
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

CITIES = [
    {"name": "Bengaluru", "state": "Karnataka"}, {"name": "Mumbai", "state": "Maharashtra"},
    {"name": "Delhi", "state": "Delhi"}, {"name": "Hyderabad", "state": "Telangana"},
    {"name": "Chennai", "state": "Tamil Nadu"}, {"name": "Pune", "state": "Maharashtra"},
    {"name": "Kolkata", "state": "West Bengal"}, {"name": "Ahmedabad", "state": "Gujarat"},
]

COUPONS = [
    {"code": "WELCOME10", "discount_percent": 10, "max_discount": 300, "min_order": 300, "active": True},
    {"code": "MEGA20", "discount_percent": 20, "max_discount": 800, "min_order": 999, "active": True},
    {"code": "FIRSTBOOK", "discount_percent": 15, "max_discount": 500, "min_order": 500, "active": True},
]


async def run_seed() -> None:
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
    await db.files.create_index("id", unique=True)

    if not await db.users.find_one({"email": ADMIN_EMAIL}):
        await db.users.insert_one({
            "id": new_id(), "email": ADMIN_EMAIL, "name": "Admin",
            "phone": None, "role": "admin",
            "password_hash": hash_pw(ADMIN_PASSWORD),
            "email_verified": True, "created_at": now_iso(),
            "address": None, "city": None, "bio": None, "avatar_url": None,
        })
        log.info(f"Seeded admin: {ADMIN_EMAIL}")

    if not await db.users.find_one({"email": "customer@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "customer@homefix.pro", "name": "Aisha Kapoor",
            "phone": "+919000000001", "role": "customer",
            "password_hash": hash_pw("customer123"), "email_verified": True,
            "created_at": now_iso(), "address": "12, MG Road", "city": "Bengaluru",
            "bio": None, "avatar_url": None,
        })
    if not await db.users.find_one({"email": "tech@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "tech@homefix.pro", "name": "Ravi Kumar",
            "phone": "+919000000002", "role": "technician",
            "password_hash": hash_pw("tech123"), "email_verified": True,
            "created_at": now_iso(), "address": None, "city": "Bengaluru",
            "bio": "8 yrs experience in AC & electrical.", "avatar_url": None,
            "skills": ["AC Repair", "Electrical"], "is_available": True,
            "rating_avg": 4.8, "rating_count": 42,
        })
    if not await db.users.find_one({"email": "tech2@homefix.pro"}):
        await db.users.insert_one({
            "id": new_id(), "email": "tech2@homefix.pro", "name": "Sonia Verma",
            "phone": "+919000000003", "role": "technician",
            "password_hash": hash_pw("tech123"), "email_verified": True,
            "created_at": now_iso(), "address": None, "city": "Mumbai",
            "bio": "Cleaning specialist.", "avatar_url": None,
            "skills": ["Home Cleaning"], "is_available": True,
            "rating_avg": 4.6, "rating_count": 28,
        })

    for c in CITIES:
        if not await db.cities.find_one({"name": c["name"]}):
            await db.cities.insert_one({"id": new_id(), **c, "active": True})

    slug_to_id: dict = {}
    for c in CATEGORIES:
        existing = await db.categories.find_one({"slug": c["slug"]})
        if existing:
            slug_to_id[c["slug"]] = existing["id"]
        else:
            cid = new_id()
            await db.categories.insert_one({"id": cid, **c, "created_at": now_iso()})
            slug_to_id[c["slug"]] = cid

    if await db.services.count_documents({}) < len(SERVICES):
        for name, slug, desc, price, dur in SERVICES:
            if await db.services.find_one({"name": name}):
                continue
            await db.services.insert_one({
                "id": new_id(), "name": name, "category_id": slug_to_id.get(slug),
                "description": desc, "price": float(price), "duration_minutes": dur,
                "image_url": next((cat["image_url"] for cat in CATEGORIES if cat["slug"] == slug), None),
                "features": ["Verified pros", "90-day service warranty", "Trained & background-checked"],
                "active": True,
                "rating_avg": round(4.4 + (hash(name) % 5) * 0.1, 1),
                "rating_count": 10 + (hash(name) % 90),
                "created_at": now_iso(),
            })

    for c in COUPONS:
        if not await db.coupons.find_one({"code": c["code"]}):
            await db.coupons.insert_one({"id": new_id(), **c})

    log.info("Startup seed complete.")
