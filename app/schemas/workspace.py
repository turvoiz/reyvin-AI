from pydantic import BaseModel


class WorkspaceSearchRequest(BaseModel):
    query: str
    project: str = "default"


class WorkspaceSearchResponse(BaseModel):
    found: bool
    symbol: dict | None


class WorkspaceAskRequest(BaseModel):
    question: str
    model: str = "qwen"
    thinking: bool = False
    project: str = "default"


class WorkspaceAskResponse(BaseModel):
    answer: str


class WorkspaceProjectRequest(BaseModel):
    project_id: str
    workspace: str


class WorkspaceExplainCodeRequest(BaseModel):
    code: str
    file: str = ""
    start_line: int = 0
    end_line: int = 0
    model: str = "qwen"
    thinking: bool = False
    project: str = "default"


class WorkspaceDiagnoseRequest(BaseModel):
    error: str
    file: str = ""
    model: str = "qwen"
    thinking: bool = False
    project: str = "default"


class WorkspaceApplyFixRequest(BaseModel):
    fix: dict
    project: str = "default"
    model: str = "qwen"
    thinking: bool = False
