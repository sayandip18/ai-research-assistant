from dataclasses import dataclass
from typing import List
import tiktoken

@dataclass
class Chunk:
    content: str
    chunk_index: int
    token_count: int
    metadata: dict

class SmartChunker:
    """
    Recursive character splitting with overlap.
    Respects paragraph and sentence boundaries.
    """
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, metadata: dict = {}) -> List[Chunk]:
        chunks = self._split_recursive(text, self.separators)
        return [
            Chunk(
                content=c,
                chunk_index=i,
                token_count=len(self.encoder.encode(c)),
                metadata=metadata
            )
            for i, c in enumerate(chunks)
        ]

    def _split_recursive(self, text: str, separators: list) -> List[str]:
        if not separators:
            return [text]
        
        sep = separators[0]
        splits = text.split(sep) if sep else list(text)
        
        chunks, current = [], ""
        for split in splits:
            candidate = current + sep + split if current else split
            if len(self.encoder.encode(candidate)) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # If single split is too large, recurse
                if len(self.encoder.encode(split)) > self.chunk_size:
                    chunks.extend(self._split_recursive(split, separators[1:]))
                    current = ""
                else:
                    current = split
        
        if current:
            chunks.append(current)
        
        # Add overlap
        return self._add_overlap(chunks)

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        if len(chunks) <= 1:
            return chunks
        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tokens = self.encoder.encode(chunks[i-1])
            overlap_text = self.encoder.decode(prev_tokens[-self.overlap:])
            result.append(overlap_text + " " + chunks[i])
        return result