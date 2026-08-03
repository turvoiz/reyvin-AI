from fastapi import APIRouter, HTTPException

from app.api.v1.dependencies import get_project_cache
from app.schemas.workspace import *
from app.services.explain_service import explain_service
from app.services.insight_service import insight_service
from app.services.review_service import review_service
from app.services.workspace_service import workspace_service
from app.workspace.indexer import indexer
from app.workspace.project_registry import workspace_registry
from app.workspace.search.symbol_search import symbol_search

router = APIRouter(
    prefix="/workspace",
    tags=["Workspace"],
)


@router.get("/projects")
def list_projects():
    return workspace_registry.list()


@router.post("/projects")
def register_project(request: WorkspaceProjectRequest):
    try:
        return workspace_registry.register(
            request.project_id,
            request.workspace,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/projects/{project_id}/reload")
def reload_project(project_id: str):
    cache = get_project_cache(project_id)
    cache.reload()
    return workspace_registry.describe(project_id)


@router.get("/scan")
def scan(project: str = "default"):
    return indexer.index(get_project_cache(project).workspace)


@router.post("/reload")
def reload_workspace(project: str = "default"):

    cache = get_project_cache(project)
    cache.reload()

    return {
        "message": "Workspace reloaded",
        "symbols": len(cache.symbols()),
    }


@router.get("/calls")
def calls(project: str = "default"):

    return get_project_cache(project).calls()


@router.get("/resolver")
def resolver(project: str = "default"):

    return get_project_cache(project).resolver()


@router.get("/references")
def references(project: str = "default"):

    return get_project_cache(project).references()


@router.get("/graph")
def graph(project: str = "default"):

    return get_project_cache(project).graph()


@router.post("/search")
def search(request: WorkspaceSearchRequest):

    symbol = workspace_service.search(
        request.query,
        get_project_cache(request.project),
    )

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
        cache=get_project_cache(request.project),
    )

    return WorkspaceAskResponse(
        answer=answer,
    )


from app.workspace.tracer import trace_engine


@router.get("/knowledge/{symbol}")
def knowledge(symbol: str, project: str = "default"):

    return get_project_cache(project).knowledge(symbol)


@router.get("/deadcode")
def deadcode(project: str = "default"):

    return get_project_cache(project).deadcode()


@router.get("/impact/{symbol}")
def impact(symbol: str, project: str = "default"):

    return get_project_cache(project).impact(symbol)


@router.get("/trace/{symbol}")
def trace(symbol: str, project: str = "default"):

    return trace_engine.trace(
        get_project_cache(project).calls(),
        symbol,
    )


@router.get("/explain/{symbol}")
def explain(
    symbol: str,
    model: str = "qwen",
    thinking: bool = False,
    project: str = "default",
):
    return explain_service.explain(
        symbol,
        model,
        thinking,
        get_project_cache(project),
    )


@router.get("/review/{symbol}")
def review(
    symbol: str,
    model: str = "qwen",
    thinking: bool = False,
    project: str = "default",
):
    return review_service.review(
        symbol,
        model,
        thinking,
        get_project_cache(project),
    )


@router.get("/stats")
def stats(project: str = "default"):

    cache = get_project_cache(project)

    return {
        "symbols": len(cache.symbols()),
        "knowledge_cache": len(cache._knowledge),
    }


@router.get("/insight/{symbol}")
def insight(
    symbol: str,
    model: str = "auto",
    thinking: bool = False,
    project: str = "default",
):
    return insight_service.insight(
        symbol,
        model,
        thinking,
        get_project_cache(project),
    )


@router.post("/rebuild")
def rebuild(project: str = "default"):

    return get_project_cache(project).rebuild()


@router.get("/changed")
def changed(project: str = "default"):

    return get_project_cache(project).changed_files()


@router.post("/accept")
def accept(project: str = "default"):

    return get_project_cache(project).accept_changes()


@router.get("/search")
def search_symbol(
    q: str,
    limit: int = 20,
    project: str = "default",
):

    return symbol_search.search(
        get_project_cache(project),
        q,
        limit,
    )
