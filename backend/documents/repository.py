from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from documents.models import Document


async def create_document(
    db: AsyncSession,
    *,
    id: uuid.UUID | None = None,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    name: str,
    s3_key: str,
    content_type: str,
    size_bytes: int,
) -> Document:
    """Insert a document record and return it."""
    doc = Document(
        id=id or uuid.uuid4(),
        workspace_id=workspace_id,
        user_id=user_id,
        name=name,
        s3_key=s3_key,
        content_type=content_type,
        size_bytes=size_bytes,
        status="pending",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def update_document_status(db: AsyncSession, document_id: uuid.UUID, status: str) -> None:
    """Update only the status column of a document row."""
    await db.execute(
        update(Document).where(Document.id == document_id).values(status=status)
    )
    await db.commit()


async def get_document_by_id(db: AsyncSession, document_id: uuid.UUID) -> Document | None:
    """Fetch a document by primary key."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    return result.scalar_one_or_none()


async def list_documents_by_workspace(
    db: AsyncSession, workspace_id: uuid.UUID
) -> list[Document]:
    """Return all documents in a workspace, newest first."""
    result = await db.execute(
        select(Document)
        .where(Document.workspace_id == workspace_id)
        .order_by(Document.created_at.desc())
    )
    return list(result.scalars().all())
