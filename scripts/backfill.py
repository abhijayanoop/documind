from documind.ingest import backfill_embeddings

n = backfill_embeddings()
print(f"Backfilled {n} document embedding(s).")