from documind.retrieval import RetrievedDoc

ABSTENTION = "I don't have information about that in the documents available to you."

SYSTEM_PROMPT = (
    "You are DocuMind, an assistant that answers questions using ONLY the "
    "documents provided in the user message. Follow these rules strictly:\n"
    "1. Base your answer solely on the provided documents. Do not use outside "
    "knowledge.\n"
    "2. If the documents do not contain the answer, reply with exactly: "
    f'"{ABSTENTION}"\n'
    "3. Do not speculate, estimate, or invent facts, figures, or policies.\n"
    "4. When you use a fact, you may reference the document title it came from.\n"
    "5. Be concise and direct."
)


def build_context_block(docs: list[RetrievedDoc]) -> str:
    if not docs:
        return "(no documents available)"
    parts = []
    for i, d in enumerate(docs, start=1):
        parts.append(f"[Document {i}] {d.title}\n{d.content}")
    return "\n\n".join(parts)


def build_messages(question: str, docs: list[RetrievedDoc]) -> list[dict]:
    context = build_context_block(docs)
    user_content = (
        f"Documents:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the documents above."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]