from app.schemas.ai_schemas import MessageItem

def build_context_prompt(
    last_messages: list[MessageItem],
    summary_text: str | None,
    chunks: list[str],
    current_prompt: str,
) -> str:
    """Build the full prompt sent to the model.

    Five-layer structure:
        1. System prompt
        2. Conversation summary (if any)
        3. Relevant document chunks from RAG (if any)
        4. Recent conversation messages (if any)
        5. User question

    history items are dicts with keys: role ("user"|"assistant"), content (str).
    """
    
    parts = ["System:\nYou are a helpful AI assistant.\n"]

    if summary_text:
        parts.append(f"Conversation summary:\n{summary_text}\n")

    if chunks:
        parts.append("Relevant document context:\n")
        for i, chunk in enumerate(chunks, start=1):
            parts.append(f"[Chunk {i}]\n{chunk}\n")

    if last_messages:
        parts.append("Recent conversation:\n")
        for msg in last_messages:
            label = "User" if msg.role == "user" else "Assistant"
            parts.append(f"{label}: {msg.content}")
        parts.append("")  # blank line separator

    parts.append(f"User question:\n{current_prompt}")
    return "\n".join(parts)
