from fastapi import APIRouter
from apps.api.src.api.v1.endpoints import health, draws, statistics, generator

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(draws.router, tags=["draws"])
router.include_router(statistics.router, tags=["statistics"])
router.include_router(generator.router, tags=["generator"])
