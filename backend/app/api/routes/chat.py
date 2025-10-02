"""API routes for chat functionality."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import ChatMessage, Project
from app.middleware.auth import CurrentUser
from app.services.llm_client import llm_client

router = APIRouter(prefix="/chat", tags=["chat"])


# Request/Response Models
class ChatMessageCreate(BaseModel):
    project_id: str
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    content: str
    message_metadata: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCompletionRequest(BaseModel):
    project_id: str
    message: str
    stream: bool = False


class ChatCompletionResponse(BaseModel):
    message_id: str
    content: str


@router.post("/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: ChatMessageCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ChatMessage:
    """Create a new chat message."""
    # Verify project exists and user has access
    result = await db.execute(
        select(Project).where(Project.id == uuid.UUID(message_data.project_id))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.firm_id != current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Create message
    message = ChatMessage(
        id=uuid.uuid4(),
        project_id=uuid.UUID(message_data.project_id),
        user_id=current_user["user_id"],
        role="user",
        content=message_data.content,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message


@router.get("/messages/{project_id}", response_model=list[ChatMessageResponse])
async def list_messages(
    project_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> list[ChatMessage]:
    """List chat messages for a project."""
    # Verify project access
    result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.firm_id != current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == uuid.UUID(project_id))
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )

    messages = result.scalars().all()
    return list(messages)


@router.post("/completion", response_model=ChatCompletionResponse)
async def chat_completion(
    request_data: ChatCompletionRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Generate a chat completion response.

    This endpoint:
    1. Saves the user message
    2. Retrieves conversation history
    3. Generates AI response
    4. Saves the AI response
    5. Returns the response
    """
    # Verify project access
    result = await db.execute(
        select(Project).where(Project.id == uuid.UUID(request_data.project_id))
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if project.firm_id != current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Save user message
    user_message = ChatMessage(
        id=uuid.uuid4(),
        project_id=uuid.UUID(request_data.project_id),
        user_id=current_user["user_id"],
        role="user",
        content=request_data.message,
    )
    db.add(user_message)
    await db.flush()

    # Get recent conversation history
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.project_id == uuid.UUID(request_data.project_id))
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
    )
    history = result.scalars().all()

    # Build messages for LLM
    messages = [
        {
            "role": "system",
            "content": (
                f"You are an AI assistant for investment banking analysts. "
                f"You help with research, company analysis, and creating deliverables. "
                f"Project: {project.name}. "
                f"Target companies: {', '.join(project.target_companies or [])}."
            ),
        }
    ]

    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Generate AI response
    if request_data.stream:
        # TODO: Implement streaming response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Streaming not yet implemented",
        )

    ai_response = await llm_client.chat_completion(messages=messages)

    # Save AI message
    ai_message = ChatMessage(
        id=uuid.uuid4(),
        project_id=uuid.UUID(request_data.project_id),
        user_id=current_user["user_id"],
        role="assistant",
        content=ai_response,
    )
    db.add(ai_message)

    await db.commit()

    return {
        "message_id": str(ai_message.id),
        "content": ai_response,
    }
