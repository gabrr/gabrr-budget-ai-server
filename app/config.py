from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    default_user_id: str = "user_demo"
    default_account_id: str = "acct_demo_checking"


settings = Settings()
