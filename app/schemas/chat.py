from typing import Literal

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    model: Literal["auto", "qwen", "deepseek"] = "auto"
    thinking: bool = False


class ChatResponse(BaseModel):
    response: str
    model: str
    thinking: bool
    elapsed_ms: int
