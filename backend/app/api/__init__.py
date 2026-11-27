"""Router aggregation: every router the application exposes is mounted from here."""

from fastapi import APIRouter

from . import admin, health, listings, orders, sets

api_router = APIRouter()
api_router.include_router(admin.public_router)
api_router.include_router(admin.router)
api_router.include_router(health.router)
api_router.include_router(listings.router)
api_router.include_router(orders.router)
api_router.include_router(sets.router)
