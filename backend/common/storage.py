from __future__ import annotations

import asyncio
import io

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from common.exceptions import ExternalServiceError
from config import settings


def _get_client():
    """Return a boto3 S3 client configured for MinIO / S3."""
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


async def upload_file(file_bytes: bytes, key: str, content_type: str) -> str:
    """Upload *file_bytes* to S3 under *key* and return the key."""
    client = _get_client()

    def _upload() -> None:
        client.upload_fileobj(
            io.BytesIO(file_bytes),
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )

    try:
        await asyncio.to_thread(_upload)
    except (BotoCoreError, ClientError) as exc:
        raise ExternalServiceError(f"S3 upload failed: {exc}") from exc
    return key


async def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    """Return a presigned GET URL for *key* valid for *expires_in* seconds."""
    client = _get_client()

    def _presign() -> str:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    try:
        return await asyncio.to_thread(_presign)
    except (BotoCoreError, ClientError) as exc:
        raise ExternalServiceError(f"S3 presign failed: {exc}") from exc
