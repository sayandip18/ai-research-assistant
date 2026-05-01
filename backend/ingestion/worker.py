from __future__ import annotations

import asyncio
import io
import uuid

import fitz  # PyMuPDF
import redis.asyncio as aioredis
import structlog
from docx import Document as DocxDocument

from common.db import AsyncSessionFactory
from common.exceptions import IngestionError
from common.storage import download_file
from config import settings
from documents import repository
from ingestion.chunker import SmartChunker
from workers.celery_app import celery_app

log = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# In-memory parsers — keyed by file extension
# ---------------------------------------------------------------------------

def _parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes, prefixing each page number."""
    doc = fitz.open(stream=io.BytesIO(file_bytes), filetype="pdf")
    return "\n\n".join(f"[Page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc))


def _parse_docx(file_bytes: bytes) -> str:
    """Extract non-empty paragraphs from a DOCX file."""
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())


_BLOCKING_PARSERS: dict[str, object] = {
    "pdf": _parse_pdf,
    "docx": _parse_docx,
}


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="ingestion.ingest_document",
    max_retries=3,
    default_retry_delay=60,
)
def ingest_document(self, document_id: str) -> None:
    """Celery entry point — synchronously drives the async ingestion pipeline."""
    try:
        asyncio.run(_ingest_async(document_id))
    except IngestionError as exc:
        log.error("ingestion.failed", document_id=document_id, error=str(exc))
        self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Async pipeline
# ---------------------------------------------------------------------------

async def _ingest_async(document_id: str) -> None:
    """Full pipeline: S3 fetch → parse → chunk → embed → store → status update."""
    doc_uuid = uuid.UUID(document_id)
    idempotency_key = f"ingest_result:{document_id}"
    redis = aioredis.Redis.from_url(settings.redis_url, decode_responses=False)

    try:
        # Short-circuit if this document was already successfully ingested.
        if await redis.get(idempotency_key) == b"success":
            log.info("ingestion.already_completed", document_id=document_id)
            return

        async with AsyncSessionFactory() as db:
            doc = await repository.get_document_by_id(db, doc_uuid)
            if doc is None:
                raise IngestionError(f"Document {document_id} not found in database")

            await repository.update_document_status(db, doc_uuid, "processing")
            log.info("ingestion.started", document_id=document_id, s3_key=doc.s3_key)

            try:
                # 1. Fetch raw bytes from object storage.
                file_bytes = await download_file(doc.s3_key)

                # 2. Dispatch to the correct parser by file extension.
                ext = doc.name.rsplit(".", 1)[-1].lower() if "." in doc.name else ""
                if ext in _BLOCKING_PARSERS:
                    # CPU-bound / blocking libs — run in a thread pool.
                    text = await asyncio.to_thread(_BLOCKING_PARSERS[ext], file_bytes)
                elif ext in ("txt", "md"):
                    text = file_bytes.decode("utf-8", errors="replace")
                else:
                    raise IngestionError(f"No parser registered for extension '{ext}'")

                log.info("ingestion.parsed", document_id=document_id, ext=ext, chars=len(text))

                # 3. Run text through the chunking strategy.
                chunker = SmartChunker(
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap,
                )
                chunks = await asyncio.to_thread(
                    chunker.chunk,
                    text,
                    {"document_id": document_id, "workspace_id": str(doc.workspace_id)},
                )
                log.info("ingestion.chunked", document_id=document_id, chunk_count=len(chunks))

                # 4. Embed chunks and upsert into the vector store.
                # Uncomment once embeddings/service.py and vectorstore/repository.py are implemented:
                # embedder = EmbeddingService()
                # embeddings = await embedder.embed_documents([c.content for c in chunks])
                # vs = VectorStoreRepository(db)
                # await vs.upsert(document_id=doc_uuid, chunks=chunks, embeddings=embeddings)

                await repository.update_document_status(db, doc_uuid, "ready")
                # TTL of 24 h — long enough to de-duplicate retries, short enough to allow re-ingestion.
                await redis.setex(idempotency_key, 86400, "success")
                log.info("ingestion.completed", document_id=document_id, chunk_count=len(chunks))

            except IngestionError:
                raise
            except Exception as exc:
                await repository.update_document_status(db, doc_uuid, "failed")
                raise IngestionError(str(exc)) from exc
    finally:
        await redis.aclose()
