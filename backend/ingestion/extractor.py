from __future__ import annotations

import asyncio

import fitz  # PyMuPDF
from docx import Document


class TextExtractor:
    """Extract plain text from PDF, DOCX, Markdown, and plain-text files."""

    async def extract(self, file_path: str, file_type: str) -> str:
        """Return the plain-text content of *file_path* for the given *file_type*."""
        match file_type:
            case "pdf":
                return await asyncio.to_thread(self._extract_pdf, file_path)
            case "docx":
                return await asyncio.to_thread(self._extract_docx, file_path)
            case "txt" | "md":
                return await asyncio.to_thread(self._read_text, file_path)
            case _:
                raise ValueError(f"Unsupported file type: {file_type!r}")

    def _extract_pdf(self, path: str) -> str:
        """Extract text page-by-page from a PDF."""
        doc = fitz.open(path)
        return "\n\n".join(f"[Page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc))

    def _extract_docx(self, path: str) -> str:
        """Extract non-empty paragraphs from a DOCX file."""
        doc = Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _read_text(self, path: str) -> str:
        """Read a plain-text or Markdown file as-is."""
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
