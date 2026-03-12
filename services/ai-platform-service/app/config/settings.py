from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # AI Platform DB (postgres-ai)
    ai_db_name: str
    ai_db_host: str
    ai_db_port: int
    ai_db_user: str
    ai_db_password: str
    
    # AI Platform DB (postgres-ai) 
    ai_db_llm_call_max_calls_persisted: int = 15

    # Callback URL for Chat Service status updates
    chat_service_url: str

    # Ollama
    ollama_host: str
    ollama_port: int
    ollama_model: str
    ollama_timeout: int

    # OpenAI
    openai_api_key: str | None = None
    openai_model: str

    # Qdrant
    vector_db_url: str

    # RAG / embeddings
    rag_chunk_size: int
    rag_chunk_overlap: int
    rag_top_k: int
    rag_max_context_chars_on_prompt: int

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.ai_db_user}:{self.ai_db_password}"
            f"@{self.ai_db_host}:{self.ai_db_port}/{self.ai_db_name}"
        )

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"


settings = Settings()
