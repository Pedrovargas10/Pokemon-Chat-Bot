import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.collectors.pokebattler import PokebattlerCollector


SAMPLE_API_RESPONSE = {
    "tiers": [
        {
            "tier": "RAID_LEVEL_5",
            "raidBosses": [
                {
                    "pokemon": "KYOGRE",
                    "pokemonId": 382,
                    "form": "NORMAL",
                },
                {
                    "pokemon": "SOLGALEO",
                    "pokemonId": 791,
                    "form": "NORMAL",
                },
            ],
        },
        {
            "tier": "RAID_LEVEL_MEGA",
            "raidBosses": [
                {
                    "pokemon": "SCEPTILE_MEGA",
                    "pokemonId": 254,
                    "form": "MEGA",
                },
            ],
        },
    ]
}


@pytest.mark.asyncio
async def test_pokebattler_parse():
    collector = PokebattlerCollector(data_dir=Path("/tmp/test_data"))
    bosses = collector.parse_raid_bosses(SAMPLE_API_RESPONSE)

    assert len(bosses) == 3

    kyogre = bosses[0]
    assert kyogre["pokemon"] == "Kyogre"
    assert kyogre["tier"] == "5"

    solgaleo = bosses[1]
    assert solgaleo["pokemon"] == "Solgaleo"
    assert solgaleo["tier"] == "5"

    sceptile = bosses[2]
    assert sceptile["pokemon"] == "Sceptile Mega"
    assert sceptile["tier"] == "Mega"


@pytest.mark.asyncio
async def test_pokebattler_collect_integration():
    collector = PokebattlerCollector(data_dir=Path("/tmp/test_data"))
    with patch.object(
        collector, "fetch_json", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = SAMPLE_API_RESPONSE
        bosses = await collector.collect()
        assert len(bosses) == 3
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_pokebattler_graceful_failure():
    collector = PokebattlerCollector(data_dir=Path("/tmp/test_data"))
    with patch.object(
        collector, "fetch_json", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.side_effect = Exception("API down")
        bosses = await collector.collect()
        assert bosses == []


@pytest.mark.asyncio
async def test_pokebattler_save_markdown(tmp_path):
    collector = PokebattlerCollector(data_dir=tmp_path)
    bosses = [
        {"name": "Kyogre", "pokemon": "Kyogre", "tier": "5", "form": "Normal"},
    ]
    path = collector.save_markdown(bosses, "tier_lists.md")
    content = path.read_text()
    assert "Kyogre" in content
