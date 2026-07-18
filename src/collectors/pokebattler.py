"""Collector for Pokebattler raid boss data via REST API."""

from __future__ import annotations

import logging
from pathlib import Path

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

# Pokebattler public REST API endpoint for current raid bosses
RAIDS_API_URL = "https://fight.pokebattler.com/raids"


def _format_pokemon_name(raw: str) -> str:
    """Convert API name like 'KYOGRE' or 'SCEPTILE_MEGA' to readable form."""
    parts = raw.replace("_", " ").title().split()
    return " ".join(parts)


def _format_tier(raw: str) -> str:
    """Convert tier names like 'RAID_LEVEL_5' to '5', 'RAID_LEVEL_MEGA' to 'Mega'."""
    raw = raw.upper()
    if "MEGA" in raw:
        return "Mega"
    for suffix in ("5", "3", "1"):
        if raw.endswith(suffix):
            return suffix
    return raw.replace("RAID_LEVEL_", "")


class PokebattlerCollector(BaseCollector):
    """Fetches current raid bosses from Pokebattler's API."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir)

    def parse_raid_bosses(self, api_response: dict) -> list[dict]:
        """Parse the /raids API response into a flat list of boss dicts."""
        bosses: list[dict] = []
        tiers = api_response.get("tiers", [])

        for tier_group in tiers:
            tier_name = _format_tier(tier_group.get("tier", ""))
            for boss in tier_group.get("raidBosses", []):
                raw_name = boss.get("pokemon", "UNKNOWN")
                bosses.append(
                    {
                        "name": _format_pokemon_name(raw_name),
                        "pokemon": _format_pokemon_name(raw_name),
                        "tier": tier_name,
                        "form": boss.get("form", "Normal").replace("_", " ").title(),
                    }
                )

        logger.info("Parsed %d raid bosses from Pokebattler", len(bosses))
        return bosses

    async def collect(self) -> list[dict]:
        """Fetch and parse current raid boss data."""
        try:
            data = await self.fetch_json(RAIDS_API_URL)
            bosses = self.parse_raid_bosses(data)
        except Exception:
            logger.warning(
                "Pokebattler API call failed. Using empty boss list.",
                exc_info=True,
            )
            bosses = []

        if bosses:
            self.save_markdown(bosses, "tier_lists.md")
        return bosses
