"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_env: str = "local"
    max_upload_mb: int = 10
    openrouter_api_key: str = ""

    @property
    def max_upload_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.max_upload_mb * 1024 * 1024

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
