from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from workspaces.models import Workspace


async def create_workspace(
    db: AsyncSession, user_id: uuid.UUID, name: str, description: str | None
) -> Workspace:
    """Insert a new workspace row and return it."""
    ws = Workspace(user_id=user_id, name=name, description=description)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ws


async def get_workspace_by_id(db: AsyncSession, workspace_id: uuid.UUID) -> Workspace | None:
    """Fetch a single workspace by primary key."""
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    return result.scalar_one_or_none()


async def list_workspaces_for_user(
    db: AsyncSession, user_id: uuid.UUID
) -> list[Workspace]:
    """Return all workspaces owned by *user_id*, newest first."""
    result = await db.execute(
        select(Workspace)
        .where(Workspace.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    return list(result.scalars().all())
