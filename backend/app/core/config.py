from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/holidays_hunter"

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    import_interval_minutes: int = 60


settings = Settings()
