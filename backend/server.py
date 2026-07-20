"""HomeFix Pro — FastAPI app entrypoint."""
import logging

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from app import BASE_DIR  # noqa: F401 — triggers .env load
from app.db import client
from app.seed import run_seed
from app.storage import init_storage
from app.routers.auth import router as auth_router, profile_router
from app.routers.catalog import router as catalog_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.routers.admin import router as admin_router
from app.routers.uploads import router as uploads_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("homefix")

app = FastAPI(title="HomeFix Pro API")

# All routers mount under /api
api = APIRouter(prefix="/api")
api.include_router(auth_router)
api.include_router(profile_router)
api.include_router(catalog_router)
api.include_router(bookings_router)
api.include_router(payments_router)
api.include_router(admin_router)
api.include_router(uploads_router)


@api.get("/")
async def root():
    return {"service": "HomeFix Pro", "status": "ok"}


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await run_seed()
    init_storage()


@app.on_event("shutdown")
async def shutdown():
    client.close()
