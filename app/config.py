from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    default_user_id: str = "user_demo"
    default_account_id: str = "acct_demo_checking"
    max_file_upload_mb: int = Field(default=20, ge=1, le=512)

    # ADK `adk api_server` (see `app/services/agent_service.py`, `app/api/agents_routes.py`).
    adk_base_url: str = "http://127.0.0.1:8001"
    adk_app_name: str = "app"
    adk_timeout_seconds: float = 300.0

    @property
    def max_file_upload_bytes(self) -> int:
        return self.max_file_upload_mb * 1024 * 1024


settings = Settings()
