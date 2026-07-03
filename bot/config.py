from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    zulip_email: str
    zulip_api_key: str
    zulip_site: str
    zulip_bot_name: str = "linear"

    linear_api_key: str
    linear_team_id: str
    linear_team_key: str = ""

    log_level: str = "INFO"


def load_settings() -> Settings:
    return Settings()
