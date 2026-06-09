from pydantic_settings import BaseSettings, SettingsConfigDict;

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    embedding_dimension: int = 1536
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"  
    llm_temperature: float = 0.1
    openai_api_key: str = ""
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

settings = Settings()