import os
import importlib
import pytest
from unittest.mock import patch


def _fresh_settings():
    """Import Settings fresh to avoid caching."""
    import src.config as mod
    importlib.reload(mod)
    return mod.Settings


def test_settings_loads_from_env():
    env = {
        "TELEGRAM_TOKEN": "test-tg-token",
        "GEMINI_API_KEY": "test-gemini-key",
        "SCRAPE_INTERVAL_MINUTES": "60",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env, clear=True):
        Settings = _fresh_settings()
        s = Settings()
        assert s.telegram_token == "test-tg-token"
        assert s.gemini_api_key == "test-gemini-key"
        assert s.scrape_interval_minutes == 60
        assert s.gemini_model == "gemini-2.5-flash"
        assert s.log_level == "DEBUG"


def test_settings_defaults():
    env = {
        "TELEGRAM_TOKEN": "tok",
        "GEMINI_API_KEY": "key",
    }
    with patch.dict(os.environ, env, clear=True):
        Settings = _fresh_settings()
        s = Settings()
        assert s.scrape_interval_minutes == 120
        assert s.gemini_model == "gemini-2.5-flash"
        assert s.log_level == "INFO"
        assert s.data_dir.name == "data"


def test_settings_missing_token_raises():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}, clear=True):
        Settings = _fresh_settings()
        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            Settings()


def test_settings_missing_gemini_key_raises():
    with patch.dict(os.environ, {"TELEGRAM_TOKEN": "tok"}, clear=True):
        Settings = _fresh_settings()
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            Settings()
