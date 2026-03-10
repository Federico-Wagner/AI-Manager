from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/ai_chat"
    openai_api_key: str = ""
    ollama_host: str = "ollama"
    ollama_port: int = "11434"
    ollama_model: str = "llama3"
    openai_model: str = "gpt-4o-mini"

    @property
    def ollama_base_url(self) -> str:
        """Constructs the Ollama base URL from host and port."""
        return f"http://{self.ollama_host}:{self.ollama_port}"


settings = Settings()
