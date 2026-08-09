from fastapi import APIRouter
from pydantic import BaseModel

from app.services.cascade_router import route_query

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str
    user_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    source: str


@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest) -> ChatResponse:
    result = await route_query(request.query)
    return ChatResponse(**result)
