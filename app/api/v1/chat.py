from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import ai_service

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):

    result = ai_service.chat(
        model=request.model,
        message=request.message,
        thinking=request.thinking,
    )

    return ChatResponse(**result)
