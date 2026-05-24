from __future__ import annotations

from fastapi import APIRouter

from .routes import admin, auth, brand_profiles, context, fixtures, health, plugin_operations, quality, reports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(context.router)
api_router.include_router(fixtures.router)
api_router.include_router(admin.router)
api_router.include_router(brand_profiles.router)
api_router.include_router(plugin_operations.router)
api_router.include_router(plugin_operations.protected_router)
api_router.include_router(quality.router)
api_router.include_router(reports.router)

