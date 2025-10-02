"""API routes for project management."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Deliverable, Project
from app.middleware.auth import CurrentUser

router = APIRouter(prefix="/projects", tags=["projects"])


# Request/Response Models
class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    target_company: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_company: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    firm_id: str
    name: str
    description: str | None
    target_company: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliverableResponse(BaseModel):
    id: str
    project_id: str
    deliverable_type: str
    status: str
    file_url: str | None
    deliverable_metadata: str | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Create a new project for the user's firm."""
    from app.db.models import Firm, User

    # Use org_id if available, otherwise fall back to user_id for development
    firm_id = current_user.get("org_id") or current_user["user_id"]
    user_id = current_user["user_id"]

    # Note: User and firm are auto-provisioned by auth middleware on first request
    project = Project(
        id=uuid.uuid4(),
        firm_id=firm_id,
        owner_id=user_id,
        name=project_data.name,
        description=project_data.description,
        target_company=project_data.target_company,
        status="draft",
    )

    db.add(project)
    await db.commit()
    await db.refresh(project)

    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[Project]:
    """List all projects for the user's firm."""
    # Use org_id if available, otherwise fall back to user_id for personal accounts
    firm_id = current_user.get("org_id") or current_user["user_id"]

    result = await db.execute(
        select(Project)
        .where(Project.firm_id == firm_id)
        .order_by(Project.created_at.desc())
    )

    projects = result.scalars().all()
    return list(projects)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Get a specific project by ID."""
    result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify user has access to this project
    firm_id = current_user.get("org_id") or current_user["user_id"]
    if project.firm_id != firm_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """Update a project."""
    result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify user has access
    if project.firm_id != current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project."""
    result = await db.execute(select(Project).where(Project.id == uuid.UUID(project_id)))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Verify user has access
    if project.firm_id != current_user.get("org_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    await db.delete(project)
    await db.commit()


@router.get("/{project_id}/deliverables", response_model=list[DeliverableResponse])
async def list_project_deliverables(
    project_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[Deliverable]:
    """List all deliverables for a project."""
    # First verify project access
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

    # Get deliverables
    result = await db.execute(
        select(Deliverable)
        .where(Deliverable.project_id == uuid.UUID(project_id))
        .order_by(Deliverable.created_at.desc())
    )

    deliverables = result.scalars().all()
    return list(deliverables)
