from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from workspaces import repository
from workspaces.schemas import WorkspaceCreate, WorkspaceResponse


async def create_workspace(
    db: AsyncSession, user_id: uuid.UUID, payload: WorkspaceCreate
) -> WorkspaceResponse:
    """Create a workspace owned by *user_id*."""
    ws = await repository.create_workspace(
        db, user_id=user_id, name=payload.name, description=payload.description
    )
    return WorkspaceResponse.model_validate(ws)


async def list_user_workspaces(
    db: AsyncSession, user_id: uuid.UUID
) -> list[WorkspaceResponse]:
    """Return all workspaces belonging to *user_id*."""
    workspaces = await repository.list_workspaces_for_user(db, user_id)
    return [WorkspaceResponse.model_validate(ws) for ws in workspaces]
