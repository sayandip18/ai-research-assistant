from __future__ import annotations

import hashlib
import json

import redis.asyncio as aioredis

from backend.config import settings


def _cache_key(text: str, model: str) -> str:
    digest = hashlib.sha256(f"{model}:{text}".encode()).hexdigest()
    return f"emb:{digest}"


async def get_cached_embedding(
    redis: aioredis.Redis, text: str, model: str
) -> list[float] | None:
    """Return a cached embedding vector, or None if not present."""
    raw = await redis.get(_cache_key(text, model))
    if raw is None:
        return None
    return json.loads(raw)


async def set_cached_embedding(
    redis: aioredis.Redis, text: str, model: str, embedding: list[float]
) -> None:
    """Store an embedding vector with the configured TTL."""
    await redis.set(
        _cache_key(text, model),
        json.dumps(embedding),
        ex=settings.embedding_cache_ttl,
    )
