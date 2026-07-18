"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    """Reads configuration from environment variables on instantiation."""

    def __init__(self) -> None:
        self.telegram_token = self._require("TELEGRAM_TOKEN")
        self.gemini_api_key = self._require("GEMINI_API_KEY")
        self.scrape_interval_minutes = int(
            os.getenv("SCRAPE_INTERVAL_MINUTES", "120")
        )
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.data_dir = _PROJECT_ROOT / "data"

    @staticmethod
    def _require(key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise ValueError(
                f"{key} environment variable is required but not set."
            )
        return value
