import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.collectors.leekduck import LeekDuckCollector


SAMPLE_SCRAPED_DUCK = [
    {
        "name": "Kyogre in 5-Star Raid Battles",
        "eventType": "raid-battles",
        "heading": "Raid Battles",
        "link": "https://leekduck.com/events/kyogre-in-5-star-raid-battles-july-2026/",
        "start": "2026-07-15T06:00:00",
        "end": "2026-07-21T22:00:00",
        "extraData": {
            "pokemon": ["Kyogre"]
        },
    },
    {
        "name": "Eevee Spotlight Hour",
        "eventType": "pokémon-spotlight-hour",
        "heading": "Pokémon Spotlight Hour",
        "link": "https://leekduck.com/events/eevee-spotlight-hour/",
        "start": "2026-07-23T18:00:00",
        "end": "2026-07-23T19:00:00",
        "extraData": {
            "pokemon": ["Eevee"],
            "bonus": "2x Transfer Candy",
        },
    },
    {
        "name": "Community Day Classic: Beldum",
        "eventType": "community-day",
        "heading": "Community Day",
        "link": "https://leekduck.com/events/community-day-classic-beldum/",
        "start": "2026-07-26T14:00:00",
        "end": "2026-07-26T17:00:00",
        "extraData": {
            "pokemon": ["Beldum"],
            "bonus": "3x Catch XP",
        },
    },
]


@pytest.mark.asyncio
async def test_leekduck_parse_events():
    collector = LeekDuckCollector(data_dir=Path("/tmp/test_data"))
    events = collector.parse_events(SAMPLE_SCRAPED_DUCK)

    assert len(events) == 3

    raid = events[0]
    assert raid["name"] == "Kyogre in 5-Star Raid Battles"
    assert raid["type"] == "raid-battles"
    assert raid["start_date"] == "2026-07-15T06:00:00"
    assert raid["end_date"] == "2026-07-21T22:00:00"
    assert raid["url"] == "https://leekduck.com/events/kyogre-in-5-star-raid-battles-july-2026/"

    spotlight = events[1]
    assert spotlight["name"] == "Eevee Spotlight Hour"
    assert spotlight["type"] == "pokémon-spotlight-hour"
    assert spotlight["bonus"] == "2x Transfer Candy"


@pytest.mark.asyncio
async def test_leekduck_save_markdown(tmp_path):
    collector = LeekDuckCollector(data_dir=tmp_path)
    events = [
        {
            "name": "Kyogre in 5-Star Raid Battles",
            "type": "raid-battles",
            "start_date": "2026-07-15T06:00:00",
            "end_date": "2026-07-21T22:00:00",
            "url": "https://leekduck.com/events/kyogre/",
            "pokemon": ["Kyogre"],
            "bonus": "",
        },
    ]
    path = collector.save_markdown(events, "events.md")
    assert path.exists()
    content = path.read_text()
    assert "Kyogre in 5-Star Raid Battles" in content
    assert "raid-battles" in content
    assert "2026-07-21T22:00:00" in content


@pytest.mark.asyncio
async def test_leekduck_collect_integration():
    """Tests the full collect pipeline with mocked HTTP."""
    collector = LeekDuckCollector(data_dir=Path("/tmp/test_data"))
    with patch.object(
        collector, "fetch_json", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = SAMPLE_SCRAPED_DUCK
        events = await collector.collect()
        assert len(events) == 3
        assert events[0]["name"] == "Kyogre in 5-Star Raid Battles"
        mock_fetch.assert_called_once()
