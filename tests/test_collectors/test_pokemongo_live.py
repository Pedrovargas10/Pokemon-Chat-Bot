import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from src.collectors.pokemongo_live import PokemonGoLiveCollector


SAMPLE_HTML = """
<html><body>
<section class="news-list">
  <article class="post-item">
    <a href="/en/news/2026-07-anniversary-event/">
      <h3 class="post-title">10th Anniversary Event Details</h3>
    </a>
    <time datetime="2026-07-10">July 10, 2026</time>
    <p class="post-summary">Celebrate Pokémon GO 10th anniversary with special bonuses!</p>
  </article>
  <article class="post-item">
    <a href="/en/news/2026-07-raid-rotation/">
      <h3 class="post-title">July Raid Rotation Update</h3>
    </a>
    <time datetime="2026-07-08">July 8, 2026</time>
    <p class="post-summary">New legendary raids are coming this month.</p>
  </article>
</section>
</body></html>
"""


@pytest.mark.asyncio
async def test_pokemongo_live_parse():
    collector = PokemonGoLiveCollector(data_dir=Path("/tmp/test_data"))
    posts = collector.parse_posts(SAMPLE_HTML)

    assert len(posts) == 2
    assert posts[0]["name"] == "10th Anniversary Event Details"
    assert "anniversary" in posts[0]["url"].lower()
    assert posts[0]["date"] == "2026-07-10"
    assert posts[0]["summary"] != ""
    assert posts[1]["name"] == "July Raid Rotation Update"


@pytest.mark.asyncio
async def test_pokemongo_live_collect_integration():
    collector = PokemonGoLiveCollector(data_dir=Path("/tmp/test_data"))
    with patch.object(
        collector, "fetch_html", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = SAMPLE_HTML
        posts = await collector.collect()
        assert len(posts) == 2
        mock_fetch.assert_called_once()


@pytest.mark.asyncio
async def test_pokemongo_live_save_markdown(tmp_path):
    collector = PokemonGoLiveCollector(data_dir=tmp_path)
    posts = [
        {
            "name": "10th Anniversary Event",
            "date": "2026-07-10",
            "url": "https://pokemongolive.com/en/news/2026-07-anniversary/",
            "summary": "Big event incoming!",
        }
    ]
    path = collector.save_markdown(posts, "announcements.md")
    content = path.read_text()
    assert "10th Anniversary Event" in content
