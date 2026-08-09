from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    telegram_bot_token: str
    backend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = BotSettings()
