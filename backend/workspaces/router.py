from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from dependencies import get_current_user, get_db
from workspaces import service
from workspaces.schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    """Create a new workspace for the authenticated user."""
    return await service.create_workspace(db, user_id=current_user.id, payload=payload)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceResponse]:
    """Return all workspaces owned by the authenticated user."""
    return await service.list_user_workspaces(db, user_id=current_user.id)
