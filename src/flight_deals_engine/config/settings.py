from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Search Backend
    SEARCH_BACKEND_BASE_URL: str
    SEARCH_BACKEND_API_KEY: Optional[str] = None
    SEARCH_BACKEND_TIMEOUT_SECONDS: int = 20

    # Defaults
    DEFAULT_ORIGIN: str = "TLV"
    DEFAULT_MONTHS_AHEAD: int = Field(default=6, validation_alias="MONTHS_AHEAD")
    DEFAULT_CURRENCY: str = "USD"

    # Adapters
    STORAGE_ADAPTER: str = "null"  # Options: "null", "in_memory", "dynamodb", "json", "s3"
    S3_BUCKET_NAME: Optional[str] = None

    # Hot Deals Configuration
    HOT_DEALS_DESTINATIONS: List[str] = Field(
        default_factory=lambda: ["LON", "PAR", "ATH", "ROM", "MAD", "BCN", "RHO", "HER", "AMS", "BUD", "VIE", "LIS", "BER"]
    )
    HOT_DEALS_SEARCH_HORIZON_DAYS: int = 90
    HOT_DEALS_NIGHTS_MIN: int = 4
    HOT_DEALS_NIGHTS_MAX: int = 5
    HOT_DEALS_PASSENGERS: int = 1
    HOT_DEALS_DIRECT_ONLY: bool = True
    HOT_DEALS_LIMIT: int = 20

    # Last Minute Deals Configuration
    LAST_MINUTE_DESTINATIONS: List[str] = Field(
        default_factory=lambda: ["LON", "PAR", "ATH", "ROM", "MAD", "BCN", "RHO", "HER", "AMS", "BUD", "VIE", "LIS", "BER"]
    )
    LAST_MINUTE_HORIZON_DAYS: int = 14
    LAST_MINUTE_NIGHTS_MIN: int = 3
    LAST_MINUTE_NIGHTS_MAX: int = 5
    LAST_MINUTE_DIRECT_ONLY: bool = True
    LAST_MINUTE_LIMIT: int = 20

    # Observability
    LOG_LEVEL: str = "INFO"
