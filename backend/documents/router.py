from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import User
from dependencies import get_current_user, get_db
from documents import service
from documents.schemas import DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    workspace_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Upload a document file to S3 and register it in the database."""
    return await service.upload_document(
        db, workspace_id=workspace_id, user_id=current_user.id, file=file
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    workspace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentResponse]:
    """List all documents in a workspace owned by the authenticated user."""
    return await service.list_workspace_documents(
        db, workspace_id=workspace_id, user_id=current_user.id
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Fetch a single document by ID."""
    return await service.get_document(db, document_id=document_id, user_id=current_user.id)
