"""Application settings, sourced from the environment (12-factor)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="WF_", extra="ignore")

    app_name: str = "Nagare Workflow"
    environment: str = "local"
    database_url: str = "sqlite:///./workflow.db"

    secret_key: str = "local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "nagare-workflow"
    access_token_expire_minutes: int = 60 * 12
    password_hash_iterations: int = 260_000

    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


settings = Settings()
