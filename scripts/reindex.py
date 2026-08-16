import sys
from pathlib import Path

from documind.config import settings
from documind.database import get_connection
from documind.chunking import chunk_text
from documind.ingest import ingest_documents, DocumentInput

CORPUS_DIR = Path(__file__).parent.parent / "corpus"

CORPUS = [
    ("cred", "doc_001", "CRED Engineering Interview Guide", "public", "cred_doc_001.txt"),
    ("cred", "doc_002", "CRED ML Engineer Compensation Bands", "salary_tier", "cred_doc_002.txt"),
    ("razorpay", "doc_001", "Razorpay Technical Interview Overview", "public", "razorpay_doc_001.txt"),
]


def _sync_embedding_dimension(conn) -> None:
    dim = settings.embedding_dimension
    with conn.cursor() as cur:
        cur.execute(f"ALTER TABLE documents ALTER COLUMN embedding TYPE vector({dim})")
    conn.commit()


def reindex(chunk_size: int, overlap: int) -> None:
    print(f"embedding_model={settings.embedding_model!r} embedding_dimension={settings.embedding_dimension}")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE documents RESTART IDENTITY")
        conn.commit()
        _sync_embedding_dimension(conn)

    docs: list[DocumentInput] = []
    for tenant_id, base_id, title, access, filename in CORPUS:
        text = (CORPUS_DIR / filename).read_text(encoding="utf-8")
        for c in chunk_text(text, chunk_size=chunk_size, overlap=overlap):
            docs.append(DocumentInput(
                tenant_id=tenant_id,
                document_id=f"{base_id}::chunk_{c.index}",
                title=f"{title} (part {c.index + 1})",
                content=c.text,
                access_level=access,
            ))

    n = ingest_documents(docs)
    print(f"reindexed {n} chunks at chunk_size={chunk_size} overlap={overlap}")


if __name__ == "__main__":
    reindex(int(sys.argv[1]), int(sys.argv[2]))
