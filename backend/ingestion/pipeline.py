from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ingestion.chunker import SmartChunker
from ingestion.extractor import TextExtractor

# from embeddings.service import EmbeddingService          # wire once implemented
# from vectorstore.repository import VectorStoreRepository  # wire once implemented

log = structlog.get_logger(__name__)


class IngestionPipeline:
    """Orchestrates the full ingestion flow: extract → chunk → embed → store."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.extractor = TextExtractor()
        self.chunker = SmartChunker(chunk_size=512, overlap=64)

    async def run(self, document_id: str, file_path: str, file_type: str) -> None:
        """Run the full ingestion pipeline for the document at *file_path*."""
        try:
            text = await self.extractor.extract(file_path, file_type)
            chunks = self.chunker.chunk(text, metadata={"document_id": document_id})
            # TODO: embed chunks and upsert into vector store once those modules land.
            log.info("ingestion.completed", document_id=document_id, chunk_count=len(chunks))
        except Exception as exc:
            log.error("ingestion.failed", document_id=document_id, error=str(exc))
            raise
