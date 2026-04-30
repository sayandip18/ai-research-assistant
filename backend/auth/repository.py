from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Return the user with the given username, or None."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Return the user with the given UUID string, or None."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        return None
    result = await db.execute(select(User).where(User.id == uid))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, name: str, username: str, hashed_password: str
) -> User:
    """Insert a new user row and return it."""
    user = User(id=uuid.uuid4(), name=name, username=username, hashed_password=hashed_password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
