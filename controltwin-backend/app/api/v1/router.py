"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.collectors import router as collectors_router
from app.api.v1.endpoints.datapoints import router as datapoints_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.sites import router as sites_router
from app.api.v1.endpoints.settings import router as settings_router
from app.api.v1.endpoints.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(sites_router)
api_router.include_router(assets_router)
api_router.include_router(datapoints_router)
api_router.include_router(alerts_router)
api_router.include_router(collectors_router)
api_router.include_router(settings_router)
api_router.include_router(health_router)
