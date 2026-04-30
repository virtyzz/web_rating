from functools import lru_cache

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "YW Web Rating"
    gemini_api_key: str | None = Field(None, alias="GEMINI_API_KEY")
    database_url: str = Field(..., alias="DATABASE_URL")
    gemini_model: str = Field("gemini-2.5-flash", alias="GEMINI_MODEL")
    ai_provider: str = Field("gemini", alias="AI_PROVIDER")
    qwen_api_key: str | None = Field(None, alias="QWEN_API_KEY")
    qwen_base_url: str = Field(
        "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )
    qwen_model: str = Field("qwen3-vl-flash", alias="QWEN_MODEL")

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("DATABASE_URL must be a string.")

        if value.startswith("postgresql+psycopg://"):
            return value
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        return value

    @field_validator("ai_provider", mode="before")
    @classmethod
    def normalize_ai_provider(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("AI_PROVIDER must be a string.")
        return value.strip().lower()


@lru_cache
def get_settings() -> Settings:
    return Settings()
