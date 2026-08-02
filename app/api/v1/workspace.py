from fastapi import APIRouter

from app.workspace.cache import workspace_cache
from app.workspace.indexer import indexer
from app.services.workspace_service import workspace_service
from app.schemas.workspace import *

router = APIRouter(
    prefix="/workspace",
    tags=["Workspace"],
)


@router.get("/scan")
def scan():
    return indexer.index(".")


@router.post("/reload")
def reload_workspace():

    workspace_cache.reload()

    return {
        "message": "Workspace reloaded",
        "symbols": len(workspace_cache.symbols()),
    }






@router.get("/calls")
def calls():

    return workspace_cache.calls()


@router.get("/resolver")
def resolver():

    return workspace_cache.resolver()


@router.get("/references")
def references():

    return workspace_cache.references()


@router.get("/graph")
def graph():

    return workspace_cache.graph()


@router.post("/search")
def search(request: WorkspaceSearchRequest):

    symbol = workspace_service.search(request.query)

    return WorkspaceSearchResponse(
        found=symbol is not None,
        symbol=symbol,
    )


@router.post("/ask")
def ask(request: WorkspaceAskRequest):

    answer = workspace_service.ask(
        question=request.question,
        model=request.model,
        thinking=request.thinking,
    )

    return WorkspaceAskResponse(
        answer=answer,
    )


from app.workspace.tracer import trace_engine






@router.get("/knowledge/{symbol}")
def knowledge(symbol: str):

    return workspace_cache.knowledge(symbol)


@router.get("/deadcode")
def deadcode():

    return workspace_cache.deadcode()


@router.get("/impact/{symbol}")
def impact(symbol: str):

    return workspace_cache.impact(symbol)


@router.get("/trace/{symbol}")
def trace(symbol: str):

    return trace_engine.trace(
        workspace_cache.calls(),
        symbol,
    )
