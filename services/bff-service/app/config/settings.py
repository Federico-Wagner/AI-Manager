from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Downstream service
    chat_service_url: str = "http://chat-service:8000"
    chat_service_timeout: int = 300  # generous — covers full LLM call latency

    # Public CORS
    cors_origins: list[str] = ["http://localhost:4200"]


settings = Settings()
