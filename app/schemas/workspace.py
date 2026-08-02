from pydantic import BaseModel


class WorkspaceSearchRequest(BaseModel):
    query: str


class WorkspaceSearchResponse(BaseModel):
    found: bool
    symbol: dict | None


class WorkspaceAskRequest(BaseModel):
    question: str
    model: str = "qwen"
    thinking: bool = False


class WorkspaceAskResponse(BaseModel):
    answer: str
