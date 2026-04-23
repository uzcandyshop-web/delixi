"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "DELIXI"
    log_level: str = "INFO"

    bot_token: str = Field(..., alias="BOT_TOKEN")
    webapp_url: str = Field(..., alias="WEBAPP_URL")
    qr_secret: str = Field(..., alias="QR_SECRET")
    database_url: str = Field(..., alias="DATABASE_URL")
    admin_tg_ids: str = Field(default="", alias="ADMIN_TG_IDS")

    @property
    def admin_tg_id_set(self) -> set[int]:
        if not self.admin_tg_ids.strip():
            return set()
        return {int(x.strip()) for x in self.admin_tg_ids.split(",") if x.strip()}

    @property
    def sqlalchemy_url(self) -> str:
        # Render sometimes supplies postgres:// — SQLAlchemy wants postgresql+psycopg2://
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
