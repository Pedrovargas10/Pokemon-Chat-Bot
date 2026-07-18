"""Collector for LeekDuck Pokémon GO events via ScrapedDuck JSON feed."""

from __future__ import annotations

import logging
from pathlib import Path

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# ScrapedDuck community JSON feed — structured LeekDuck data on GitHub
SCRAPED_DUCK_URL = (
    "https://raw.githubusercontent.com/bigfoott/ScrapedDuck/"
    "data/events.min.json"
)


class LeekDuckCollector(BaseCollector):
    """Fetches current/upcoming events from the ScrapedDuck JSON feed."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir)

    def parse_events(self, raw_events: list[dict]) -> list[dict]:
        """Normalize raw ScrapedDuck JSON into a clean list of event dicts."""
        events: list[dict] = []

        for raw in raw_events:
            extra = raw.get("extraData") or {}
            pokemon = extra.get("pokemon", [])
            bonus = extra.get("bonus", "")

            events.append(
                {
                    "name": raw.get("name", "Unknown Event"),
                    "type": raw.get("eventType", "unknown"),
                    "heading": raw.get("heading", ""),
                    "start_date": raw.get("start", ""),
                    "end_date": raw.get("end", ""),
                    "url": raw.get("link", ""),
                    "pokemon": pokemon,
                    "bonus": bonus if isinstance(bonus, str) else str(bonus),
                }
            )

        logger.info("Parsed %d events from ScrapedDuck", len(events))
        return events

    async def collect(self) -> list[dict]:
        """Fetch ScrapedDuck JSON and parse all events."""
        raw = await self.fetch_json(SCRAPED_DUCK_URL)
        if not isinstance(raw, list):
            raw = raw.get("events", []) if isinstance(raw, dict) else []
        events = self.parse_events(raw)
        self.save_markdown(events, "events.md")
        return events
