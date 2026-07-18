"""Collector for official Pokémon GO Live blog posts via HTML scraping."""

from __future__ import annotations

import logging
from pathlib import Path

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

NEWS_URL = "https://pokemongolive.com/en/news/"
BASE_URL = "https://pokemongolive.com"


class PokemonGoLiveCollector(BaseCollector):
    """Extracts recent blog posts from Pokémon GO Live."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(data_dir)

    def parse_posts(self, html: str) -> list[dict]:
        """Parse blog post listings from the news page HTML.

        The selectors are intentionally broad to survive minor redesigns.
        """
        soup = BeautifulSoup(html, "html.parser")
        posts: list[dict] = []

        articles = soup.select("article, div.post-item, div.blog-item")
        for article in articles[:20]:
            title_tag = article.select_one("h3, h2, h4")
            link_tag = article.select_one("a[href]")
            time_tag = article.select_one("time[datetime], time, span.date")
            summary_tag = article.select_one("p")

            title = title_tag.get_text(strip=True) if title_tag else "Untitled"
            href = link_tag.get("href", "") if link_tag else ""
            url = href if href.startswith("http") else f"{BASE_URL}{href}"
            date = (
                time_tag.get("datetime", time_tag.get_text(strip=True))
                if time_tag
                else ""
            )
            summary = summary_tag.get_text(strip=True) if summary_tag else ""

            posts.append(
                {"name": title, "date": date, "url": url, "summary": summary}
            )

        logger.info("Parsed %d posts from Pokémon GO Live", len(posts))
        return posts

    async def collect(self) -> list[dict]:
        """Fetch and parse recent announcements."""
        try:
            html = await self.fetch_html(NEWS_URL)
            posts = self.parse_posts(html)
        except Exception:
            logger.warning(
                "Pokémon GO Live scraping failed. "
                "Site may require JS or be blocking requests.",
                exc_info=True,
            )
            posts = []

        if posts:
            self.save_markdown(posts, "announcements.md")
        return posts
