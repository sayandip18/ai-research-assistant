from __future__ import annotations

import uuid

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import NotFoundError, ValidationError
from common.storage import upload_file
from documents import repository
from documents.schemas import DocumentResponse
from workspaces.repository import get_workspace_by_id

ALLOWED_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB


async def upload_document(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    file: UploadFile,
) -> DocumentResponse:
    """Validate the file, upload to S3, persist metadata, and return DocumentResponse."""
    ws = await get_workspace_by_id(db, workspace_id)
    if ws is None or ws.user_id != user_id:
        raise NotFoundError("Workspace not found")

    filename = file.filename or "upload"
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not allowed. Allowed types: {sorted(ALLOWED_EXTENSIONS)}"
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValidationError("File exceeds the 50 MB size limit")

    document_id = uuid.uuid4()
    s3_key = f"workspaces/{workspace_id}/documents/{document_id}/{filename}"
    content_type = file.content_type or "application/octet-stream"

    await upload_file(file_bytes, s3_key, content_type)

    doc = await repository.create_document(
        db,
        workspace_id=workspace_id,
        user_id=user_id,
        name=filename,
        s3_key=s3_key,
        content_type=content_type,
        size_bytes=len(file_bytes),
    )
    return DocumentResponse.model_validate(doc)


async def get_document(
    db: AsyncSession, document_id: uuid.UUID, user_id: uuid.UUID
) -> DocumentResponse:
    """Fetch a document, verifying the requester owns it."""
    doc = await repository.get_document_by_id(db, document_id)
    if doc is None or doc.user_id != user_id:
        raise NotFoundError("Document not found")
    return DocumentResponse.model_validate(doc)


async def list_workspace_documents(
    db: AsyncSession, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> list[DocumentResponse]:
    """List documents in a workspace, verifying workspace ownership."""
    ws = await get_workspace_by_id(db, workspace_id)
    if ws is None or ws.user_id != user_id:
        raise NotFoundError("Workspace not found")

    docs = await repository.list_documents_by_workspace(db, workspace_id)
    return [DocumentResponse.model_validate(d) for d in docs]
