import re
from dataclasses import dataclass


@dataclass
class Chunk:
    index: int
    text: str


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[Chunk]:
    """Split text into overlapping, sentence-aware chunks.

    chunk_size / overlap are in *words* here for simplicity (token-based is a
    refinement). Splits on sentence boundaries, packing sentences into chunks
    up to chunk_size words, carrying `overlap` words into the next chunk.
    """
    # Rough sentence split — good enough; a real system might use a tokenizer.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[Chunk] = []
    current: list[str] = []
    current_len = 0
    idx = 0

    for sent in sentences:
        words = sent.split()
        if current_len + len(words) > chunk_size and current:
            chunks.append(Chunk(index=idx, text=" ".join(current)))
            idx += 1
            # carry overlap words into the next chunk
            carry = current[-overlap:] if overlap else []
            current = carry + words
            current_len = len(current)
        else:
            current += words
            current_len += len(words)

    if current:
        chunks.append(Chunk(index=idx, text=" ".join(current)))

    return chunks
