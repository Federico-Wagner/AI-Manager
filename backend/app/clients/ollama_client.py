import httpx

from app.config.settings import settings


def generate(prompt: str) -> str:
    """Send a prompt to Ollama and return the generated text.

    Calls the Ollama /api/generate endpoint with stream=False to get a
    single complete response.
    """
    with httpx.Client(timeout=settings.ollama_timeout) as client:
        response = client.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]
