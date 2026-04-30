from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    s3_key: str
    content_type: str
    size_bytes: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
