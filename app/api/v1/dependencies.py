from fastapi import Header, HTTPException

from app.core.settings import settings
from app.workspace.project_registry import workspace_registry


def require_api_key(x_api_key: str = Header(default="")):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return x_api_key


def get_project_cache(project_id="default"):
    try:
        return workspace_registry.get(project_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
