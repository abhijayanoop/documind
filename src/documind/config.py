from pydantic_settings import BaseSettings, SettingsConfigDict;

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    embedding_dimension: int = 1536
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""

settings = Settings()