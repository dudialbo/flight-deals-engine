import os
from unittest.mock import patch
from flight_deals_engine.config.settings import Settings

def test_settings_load_from_env():
    # We use _env_file=None to ignore local .env file
    with patch.dict(os.environ, {
        "SEARCH_BACKEND_BASE_URL": "https://api.example.com",
        "DEFAULT_ORIGIN": "JFK",
        "MONTHS_AHEAD": "12",
        "LOG_LEVEL": "DEBUG",
        "HOT_DEALS_SEARCH_HORIZON_DAYS": "120",
        "HOT_DEALS_NIGHTS_MIN": "3",
        "HOT_DEALS_NIGHTS_MAX": "7",
        "HOT_DEALS_LIMIT": "50",
    }):
        settings = Settings(_env_file=None)
        assert settings.SEARCH_BACKEND_BASE_URL == "https://api.example.com"
        assert settings.DEFAULT_ORIGIN == "JFK"
        assert settings.DEFAULT_MONTHS_AHEAD == 12
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.HOT_DEALS_SEARCH_HORIZON_DAYS == 120
        assert settings.HOT_DEALS_NIGHTS_MIN == 3
        assert settings.HOT_DEALS_NIGHTS_MAX == 7
        assert settings.HOT_DEALS_LIMIT == 50

def test_settings_defaults():
    # We use _env_file=None to ensure we test hardcoded defaults
    with patch.dict(os.environ, {
        "SEARCH_BACKEND_BASE_URL": "https://api.example.com"
    }):
        settings = Settings(_env_file=None)
        assert settings.DEFAULT_ORIGIN == "TLV"
        assert settings.DEFAULT_MONTHS_AHEAD == 6
        assert settings.LOG_LEVEL == "INFO"
        assert settings.HOT_DEALS_DESTINATIONS == ["LON", "PAR", "ATH", "ROM", "MAD", "BCN", "RHO", "HER"]
        assert settings.HOT_DEALS_SEARCH_HORIZON_DAYS == 90
        assert settings.HOT_DEALS_NIGHTS_MIN == 4
        assert settings.HOT_DEALS_NIGHTS_MAX == 5
        assert settings.HOT_DEALS_PASSENGERS == 1
        assert settings.HOT_DEALS_DIRECT_ONLY is True
        assert settings.HOT_DEALS_LIMIT == 20
