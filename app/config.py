from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    default_user_id: str = "user_demo"
    default_account_id: str = "acct_demo_checking"

    # ADK `adk api_server` (see `app/services/agent_service.py`, `app/api/agents_routes.py`).
    adk_base_url: str = "http://127.0.0.1:8001"
    adk_app_name: str = "app"
    adk_timeout_seconds: float = 300.0


settings = Settings()
