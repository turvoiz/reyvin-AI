from fastapi import APIRouter

from app.schemas.workspace import *
from app.services.explain_service import explain_service
from app.services.insight_service import insight_service
from app.services.review_service import review_service
from app.services.workspace_service import workspace_service
from app.workspace.cache import workspace_cache
from app.workspace.indexer import indexer
from app.workspace.search.symbol_search import symbol_search

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


@router.get("/explain/{symbol}")
def explain(
    symbol: str,
    model: str = "qwen",
    thinking: bool = False,
):
    return explain_service.explain(
        symbol,
        model,
        thinking,
    )


@router.get("/review/{symbol}")
def review(
    symbol: str,
    model: str = "qwen",
    thinking: bool = False,
):
    return review_service.review(
        symbol,
        model,
        thinking,
    )


@router.get("/stats")
def stats():

    return {
        "symbols": len(workspace_cache.symbols()),
        "knowledge_cache": len(workspace_cache._knowledge),
    }


@router.get("/insight/{symbol}")
def insight(
    symbol: str,
    model: str = "auto",
    thinking: bool = False,
):
    return insight_service.insight(
        symbol,
        model,
        thinking,
    )


@router.post("/rebuild")
def rebuild():

    return workspace_cache.rebuild()


@router.get("/changed")
def changed():

    return workspace_cache.changed_files()


@router.post("/accept")
def accept():

    return workspace_cache.accept_changes()


@router.get("/search")
def search_symbol(
    q: str,
    limit: int = 20,
):

    return symbol_search.search(
        workspace_cache,
        q,
        limit,
    )
