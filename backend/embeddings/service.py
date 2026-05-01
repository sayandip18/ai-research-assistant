from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import openai
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.common.redis import get_redis
from backend.config import settings
from backend.embeddings.cache import get_cached_embedding, set_cached_embedding

if TYPE_CHECKING:
    pass

log = structlog.get_logger(__name__)

_BATCH_SIZE = 500
_EMBEDDING_DIMENSIONS = 1536  # text-embedding-3-small


class EmbeddingService:
    """Wraps the OpenAI embeddings API with batching and Redis caching."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string, using the cache when possible."""
        redis = get_redis()
        cached = await get_cached_embedding(redis, text, self._model)
        if cached is not None:
            log.debug("embedding.cache_hit", model=self._model)
            return cached

        vector = await self._embed_single(text)
        await set_cached_embedding(redis, text, self._model, vector)
        return vector

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of document chunks, batching and caching automatically.

        Returns a list of vectors in the same order as the input texts.
        """
        if not texts:
            return []

        redis = get_redis()
        results: list[list[float] | None] = [None] * len(texts)

        # Resolve cache hits first
        uncached_indices: list[int] = []
        for i, text in enumerate(texts):
            vector = await get_cached_embedding(redis, text, self._model)
            if vector is not None:
                results[i] = vector
            else:
                uncached_indices.append(i)

        log.info(
            "embedding.batch_start",
            total=len(texts),
            cache_hits=len(texts) - len(uncached_indices),
            to_embed=len(uncached_indices),
        )

        # Embed uncached texts in batches of _BATCH_SIZE
        for batch_start in range(0, len(uncached_indices), _BATCH_SIZE):
            batch_indices = uncached_indices[batch_start : batch_start + _BATCH_SIZE]
            batch_texts = [texts[i] for i in batch_indices]

            vectors = await self._embed_batch(batch_texts)

            # Store results and populate cache
            cache_tasks = []
            for idx, vector in zip(batch_indices, vectors):
                results[idx] = vector
                cache_tasks.append(
                    set_cached_embedding(redis, texts[idx], self._model, vector)
                )
            await asyncio.gather(*cache_tasks)

        # All slots must be filled at this point
        return [v for v in results if v is not None]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(openai.RateLimitError),
    )
    async def _embed_single(self, text: str) -> list[float]:
        """Call the OpenAI API for one text string."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=text,
            dimensions=_EMBEDDING_DIMENSIONS,
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(openai.RateLimitError),
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Call the OpenAI API for a batch of texts (≤ _BATCH_SIZE)."""
        response = await self._client.embeddings.create(
            model=self._model,
            input=texts,
            dimensions=_EMBEDDING_DIMENSIONS,
        )
        # The API guarantees results are returned in the same order as input
        return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]


embedding_service = EmbeddingService()
