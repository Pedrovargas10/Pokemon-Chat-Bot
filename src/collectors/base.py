"""Abstract base collector with shared HTTP and persistence logic."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PokemonGOBot/1.0; "
        "+https://github.com/chatbotpokemon)"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseCollector(ABC):
    """Base class for all data collectors."""

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def fetch_json(self, url: str) -> dict | list:
        """Fetch a URL and parse the response as JSON."""
        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS, timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def fetch_html(self, url: str) -> str:
        """Fetch a URL and return its HTML body as a string."""
        async with httpx.AsyncClient(
            headers=_DEFAULT_HEADERS, timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text

    @abstractmethod
    async def collect(self) -> list[dict]:
        """Run the collector and return structured data."""
        ...

    def save_markdown(self, data: list[dict], filename: str) -> Path:
        """Persist *data* as a human-readable Markdown file."""
        path = self.data_dir / filename
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        title = filename.replace(".md", "").replace("_", " ").title()
        lines = [f"# {title}", ""]
        lines.append(f"> Última atualização: {now}")
        lines.append("")

        for item in data:
            lines.append(f"## {item.get('name', 'Sem título')}")
            for key, value in item.items():
                if key == "name":
                    continue
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                lines.append(f"- **{key}:** {value}")
            lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        logger.info("Saved %d items to %s", len(data), path)
        return path
