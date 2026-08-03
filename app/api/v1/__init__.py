from fastapi import APIRouter

from .chat import router as chat_router
from .developer import router as developer_router
from .health import router as health_router
from .workspace import router as workspace_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(chat_router)
api_router.include_router(developer_router)
api_router.include_router(workspace_router)
