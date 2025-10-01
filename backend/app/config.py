"""
Application configuration using Pydantic Settings.
"""
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file="../.env",  # .env is in project root
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(None, validation_alias="ANTHROPIC_API_KEY")
    brave_api_key: str | None = Field(None, validation_alias="BRAVE_API_KEY")

    # Clerk Authentication
    clerk_secret_key: str = Field(..., validation_alias="CLERK_SECRET_KEY")
    clerk_publishable_key: str = Field(
        ..., validation_alias="NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    )

    # Supabase Database
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_anon_key: str = Field(..., validation_alias="SUPABASE_ANON_KEY")
    supabase_service_key: str | None = Field(
        None, validation_alias="SUPABASE_SERVICE_KEY"
    )

    # Upstash Redis (uses HTTPS REST API, not standard Redis protocol)
    upstash_redis_url: str = Field(..., validation_alias="UPSTASH_REDIS_REST_URL")
    upstash_redis_token: str = Field(..., validation_alias="UPSTASH_REDIS_REST_TOKEN")

    # Cloudflare R2
    r2_account_id: str = Field(..., validation_alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(..., validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(..., validation_alias="R2_SECRET_ACCESS_KEY")
    r2_bucket_name: str = Field(..., validation_alias="R2_BUCKET_NAME")
    r2_endpoint: str = Field(..., validation_alias="R2_ENDPOINT")

    # Application Settings
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    cors_origins: list[str] = ["http://localhost:3000"]

    # LLM Settings
    default_llm_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4"

    # Cache TTL (in seconds)
    company_cache_ttl: int = 86400  # 24 hours


settings = Settings()
