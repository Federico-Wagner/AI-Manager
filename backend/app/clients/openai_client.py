from openai import OpenAI

from app.config.settings import settings


def generate(prompt: str) -> str:
    """Send a prompt to OpenAI and return the completion text."""
    client = OpenAI(api_key=settings.openai_api_key)
    completion = client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return completion.choices[0].message.content or ""
