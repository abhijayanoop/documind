# DocuMind + EvalKit

DocuMind is a multi-tenant, RBAC-secured RAG backend: retrieval-layer access control, hybrid (dense + BM25) search, grounded generation with abstention, JWT auth, and file ingestion with sentence-aware chunking. EvalKit is its companion eval harness: RAGAS faithfulness/relevance, deterministic retrieval precision/recall, an instructor-based hallucination judge, and regression detection against a promoted baseline, gated in CI on every pull request.

## Running locally

```bash
docker compose up -d
uv run python -m documind.migrate
uv run python scripts/seed.py
uv run python scripts/backfill.py
uv run uvicorn documind.api:app --reload
```

Run the test suite with `uv run pytest`. Run an eval with `uv run python -m evalkit.cli` (add `--promote` to accept the result as the new baseline).

Note: `scripts/reindex.py` (used for the chunking/embedding experiments below) `TRUNCATE`s the `documents` table and re-ingests a fixed experiment corpus from `corpus/*.txt`. If you've run an experiment and want the original seeded dataset back for the general test suite, re-run `scripts/seed.py` after truncating (`scripts/seed.py` upserts by `(tenant_id, document_id)` and won't remove leftover chunk rows on its own, so truncate first if the table isn't already clean).

## Optimizing DocuMind with EvalKit — Results

Starting from a working RAG baseline (`chunk_size=512, overlap=64`, `text-embedding-3-small`, `gpt-4o-mini`), I used EvalKit to run controlled, one-variable-at-a-time experiments over a 4-case interview-prep test set, gated against regression in CI on every change.

### Headline

- Chunk size 256 (over-fragmenting a ~500-1050 word corpus into 15 chunks) **regressed** answer relevance by −0.035 — rejected.
- `text-embedding-3-large` showed **no measurable retrieval gain** over `text-embedding-3-small` on this corpus (precision/recall already at ceiling) while costing ~6.5× per token — rejected.
- `gpt-4o` scored **worse** than `gpt-4o-mini` on both faithfulness (−0.037, a real regression) and relevance, while costing ~19× more per query — rejected outright, no trade-off to weigh.
- Final accepted configuration: **`chunk_size=512, overlap=64`, `text-embedding-3-small`, `gpt-4o-mini`** — the original baseline, validated rather than replaced. Every proposed upgrade was measured and rejected on evidence.

### Full results table

| Experiment | Variable changed | Faithfulness | Relevance | Hallucination rate | Retrieval P/R | Cost/query | Decision |
|---|---|---:|---:|---:|---|---:|---|
| Chunking (baseline) | `chunk_size=512, overlap=64` | 1.00 | 0.9176 | 0.00 | not comparable across chunk settings | ~$0.00032 | ✅ baseline |
| Chunking (smaller) | `chunk_size=256, overlap=32` | 1.00 | 0.8826 (🔴 −0.035) | 0.00 | not comparable across chunk settings | ~$0.00027 | ❌ reject — fragmented context |
| Chunking (larger) | `chunk_size=1024, overlap=128` | 1.00 | 0.9005 (−0.017, flat) | 0.00 | not comparable across chunk settings | ~$0.00030 | ❌ reject — no better than baseline |
| Embedding | `text-embedding-3-small → -large` | 1.00 | 0.9141 (−0.0035, flat) | 0.00 | identical to baseline (1.0/0.5/1.0/—) | ~6.5× embedding cost, same query cost | ❌ reject — no measurable gain |
| Model | `gpt-4o-mini → gpt-4o` | 0.963 (🔴 −0.037) | 0.9047 (−0.013) | 0.00 | unchanged (chunks/embeddings fixed) | ~$0.00603 (~19×) | ❌ reject — worse quality, far higher cost |

*Reranking was scoped as an optional experiment but skipped — retrieval precision/recall were already at ceiling on this corpus, leaving little room for a reranker to show a measurable gain, and it was deprioritized in favor of finishing the required legs.*

Cost/query computed as `(mean_prompt_tokens × input_price + mean_completion_tokens × output_price) / 1,000,000` using published OpenAI per-token rates (`gpt-4o-mini`: $0.15 / $0.60 per 1M input/output tokens; `gpt-4o`: $2.50 / $10.00; `text-embedding-3-small`: $0.02/1M tokens; `text-embedding-3-large`: $0.13/1M tokens).

### What I changed and why

1. **Chunking:** tested 256/512/1024-word chunks (sentence-aware, with overlap) against the accepted 512/64 baseline. Smaller chunks measurably hurt relevance by fragmenting per-chunk context; larger chunks were statistically flat but strictly no better, so the original default was already well-chosen for this corpus.
2. **Embeddings:** `text-embedding-3-large` produced *identical* retrieval precision/recall to `-small` — the corpus is small enough that retrieval was already at ceiling, so there was no headroom for a better embedding model to show a gain, and it isn't worth ~6.5× the indexing cost here.
3. **Generation model:** evaluated `gpt-4o` expecting a quality/cost trade-off to weigh, but it actually *regressed* faithfulness (more verbose answers, ~2× completion tokens, and one case dropped from 1.00 to 0.89 faithfulness) while costing ~19× more per query — a clean reject with no trade-off involved.

### How I know these are real

Every change was measured against a promoted baseline (`eval_runs/baseline.json`) using EvalKit's regression detector, and any drop in a quality metric beyond tolerance is flagged and would fail CI (`.github/workflows/eval.yml` runs the same check on every pull request, using a committed comparison baseline and blocking the merge on a non-zero exit code). The two experiments that showed real regressions (256-word chunking, `gpt-4o`) were caught by exactly this mechanism, not by eyeballing the numbers.
