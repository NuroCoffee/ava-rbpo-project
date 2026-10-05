from fastapi import APIRouter

from club_service.api.routes.auth import router as auth_router
from club_service.api.routes.health import router as health_router
from club_service.api.routes.memberships import router as memberships_router
from club_service.api.routes.plans import router as plans_router
from club_service.api.routes.users import router as users_router
from club_service.api.routes.visits import router as visits_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(plans_router)
api_router.include_router(memberships_router)
api_router.include_router(visits_router)
