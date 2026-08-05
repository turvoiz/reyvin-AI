from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import get_project_cache, require_api_key
from app.schemas.workspace import (
    WorkspaceApplyFixRequest,
    WorkspaceDiagnoseRequest,
    WorkspaceExplainCodeRequest,
    WorkspaceProjectRequest,
)
from app.services.architecture_service import architecture_service
from app.services.code_service import code_service
from app.services.diagnose_service import diagnose_service
from app.services.explain_service import explain_service
from app.services.fix_service import fix_service
from app.services.review_service import review_service
from app.workspace.project_registry import workspace_registry
from app.workspace.search.symbol_search import symbol_search

router = APIRouter(tags=["Developer API"])


@router.post("/analyze")
def analyze(request: WorkspaceProjectRequest, _: str = Depends(require_api_key)):
    try:
        return workspace_registry.register(
            request.project_id,
            request.workspace,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/symbol/{name}")
def symbol(name: str, project: str = "default", _: str = Depends(require_api_key)):
    result = get_project_cache(project).get(name)

    if result is None:
        raise HTTPException(status_code=404, detail="Symbol not found")

    return result


@router.get("/explain/{symbol}")
def explain(
    symbol: str,
    model: str = "qwen",
    thinking: bool = False,
    project: str = "default",
    _: str = Depends(require_api_key),
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
    _: str = Depends(require_api_key),
):
    return review_service.review(
        symbol,
        model,
        thinking,
        get_project_cache(project),
    )


@router.get("/impact/{symbol}")
def impact(symbol: str, project: str = "default", _: str = Depends(require_api_key)):
    return get_project_cache(project).impact(symbol)


@router.post("/explain-code")
def explain_code(
    request: WorkspaceExplainCodeRequest,
    _: str = Depends(require_api_key),
):
    return code_service.explain(
        request.code,
        request.file,
        request.start_line,
        request.end_line,
        request.model,
        request.thinking,
        get_project_cache(request.project),
    )


@router.post("/diagnose-error")
def diagnose_error(
    request: WorkspaceDiagnoseRequest,
    _: str = Depends(require_api_key),
):
    return diagnose_service.diagnose(
        request.error,
        request.file,
        request.model,
        request.thinking,
        get_project_cache(request.project),
        [turn.model_dump() for turn in request.history],
    )


@router.get("/knowledge/{symbol}")
def knowledge(symbol: str, project: str = "default", _: str = Depends(require_api_key)):
    return get_project_cache(project).knowledge(symbol)


@router.get("/search")
def search(
    q: str,
    limit: int = 20,
    project: str = "default",
    _: str = Depends(require_api_key),
):
    return symbol_search.search(
        get_project_cache(project),
        q,
        limit,
    )


@router.get("/architecture")
def architecture(
    model: str = "qwen",
    thinking: bool = False,
    project: str = "default",
    _: str = Depends(require_api_key),
):
    return architecture_service.explain(
        model,
        thinking,
        get_project_cache(project),
    )


@router.post("/apply-fix")
def apply_fix(
    request: WorkspaceApplyFixRequest,
    _: str = Depends(require_api_key),
):
    try:
        return fix_service.apply(
            request.fix,
            request.project,
            request.model,
            request.thinking,
            request.error,
            request.confirm,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/revert-fix")
def revert_fix(
    project: str = "default",
    _: str = Depends(require_api_key),
):
    try:
        return fix_service.revert(project)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
