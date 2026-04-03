from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.users import router as users_router
from app.api.v1.websocket import router as websocket_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(sessions_router)
api_router.include_router(tickets_router)
api_router.include_router(users_router)
api_router.include_router(websocket_router)
