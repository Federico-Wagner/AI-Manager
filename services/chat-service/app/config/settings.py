from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Chat Service DB (postgres-chat)
    chat_db_name: str
    chat_db_host: str
    chat_db_port: int
    chat_db_user: str
    chat_db_password: str

    # AI Platform Service URL
    ai_platform_url: str
    ai_platform_timeout: int

    # Conversation settings
    chat_context_window: int
    summary_trigger_messages: int
    summary_max_tokens: int

    # File uploads
    uploads_dir: str = "/data/uploads"

    # CORS
    cors_origins: list[str] = ["http://localhost:4200"]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.chat_db_user}:{self.chat_db_password}"
            f"@{self.chat_db_host}:{self.chat_db_port}/{self.chat_db_name}"
        )


settings = Settings()
