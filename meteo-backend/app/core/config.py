from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MeteoFusion API"
    environment: str = "development"

    google_weather_api_key: Optional[str] = None
    weather_api_key: Optional[str] = None
    openweather_api_key: Optional[str] = None
    openmeteo_api_key: Optional[str] = None
    meteosource_api_key: Optional[str] = None
    xweather_client_id: Optional[str] = None
    xweather_client_secret: Optional[str] = None
    xweather_hourly_period_limit: int = 168

    http_timeout_seconds: float = 10.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
