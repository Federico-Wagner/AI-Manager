from fastapi import HTTPException

from app.clients import ollama_client, openai_client


def route(prompt: str, model: str) -> str:
    """Route the prompt to the appropriate AI model client."""
    if model == "local":
        return ollama_client.generate(prompt)
    elif model == "openai":
        return openai_client.generate(prompt)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported model '{model}'. Use 'local' or 'openai'.",
        )
