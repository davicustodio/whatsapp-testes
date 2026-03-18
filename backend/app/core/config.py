from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "WhatsApp Testes API"
    app_env: str = "development"

    auth_password: str = Field(default="troque-essa-senha", alias="AUTH_PASSWORD")
    jwt_secret_key: str = Field(default="troque-por-uma-chave-secreta", alias="JWT_SECRET_KEY")
    jwt_expire_minutes: int = Field(default=1440, alias="JWT_EXPIRE_MINUTES")

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/whatsapp_testes",
        alias="DATABASE_URL",
    )

    whatsapp_provider: str = Field(default="evolution", alias="WHATSAPP_PROVIDER")

    evolution_api_url: str = Field(
        default="https://evolutionapi-joaocat.duckdns.org",
        alias="EVOLUTION_API_URL",
    )
    evolution_api_key: str = Field(default="", alias="EVOLUTION_API_KEY")
    evolution_messages_max_pages: int = Field(default=0, alias="EVOLUTION_MESSAGES_MAX_PAGES")

    meta_phone_number_id: str = Field(default="", alias="META_PHONE_NUMBER_ID")
    meta_access_token: str = Field(default="", alias="META_ACCESS_TOKEN")
    meta_business_account_id: str = Field(default="", alias="META_BUSINESS_ACCOUNT_ID")
    meta_webhook_verify_token: str = Field(default="", alias="META_WEBHOOK_VERIFY_TOKEN")

    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field(default="qwen/qwen3-coder-next", alias="OPENROUTER_MODEL")

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="EMBEDDING_MODEL",
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    embedding_max_per_sync: int = Field(default=300, alias="EMBEDDING_MAX_PER_SYNC")

    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
