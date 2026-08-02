from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.workspace.cache import workspace_cache


@asynccontextmanager
async def lifespan(app: FastAPI):

    workspace_cache.load(".")

    print(f"Workspace indexed: {len(workspace_cache.symbols())} symbols")

    yield


app = FastAPI(
    title="Reyvin API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(
    api_router,
    prefix="/api/v1",
)


@app.get("/")
async def root():
    return {"message": "Welcome to Reyvin API 🚀"}
