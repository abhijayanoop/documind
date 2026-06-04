from pydantic_settings import BaseSettings, SettingsConfigDict;

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    embedding_dimension: int = 1536

settings = Settings()