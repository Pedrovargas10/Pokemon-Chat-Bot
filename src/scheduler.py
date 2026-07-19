"""Periodic data collection scheduler using APScheduler."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.collectors.leekduck import LeekDuckCollector
from src.collectors.pokebattler import PokebattlerCollector
from src.collectors.pokemongo_live import PokemonGoLiveCollector
from src.collectors.dialgadex import DialgadexCollector

if TYPE_CHECKING:
    from src.collectors.base import BaseCollector
    from src.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


async def run_all_collectors(
    collectors: list[BaseCollector], gemini: GeminiClient
) -> None:
    """Run all collectors concurrently and refresh the Gemini context."""
    logger.info("Starting scheduled collection run...")
    results = await asyncio.gather(
        *(c.collect() for c in collectors),
        return_exceptions=True,
    )
    for collector, result in zip(collectors, results):
        name = type(collector).__name__
        if isinstance(result, Exception):
            logger.error("Collector %s failed: %s", name, result)
        else:
            logger.info("Collector %s returned %d items", name, len(result))

    gemini.refresh_context()
    logger.info("Collection run complete. Context refreshed.")


def setup_scheduler(
    collectors: list[BaseCollector],
    gemini: GeminiClient,
    interval_minutes: int,
) -> AsyncIOScheduler:
    """Create an APScheduler that runs collectors periodically.

    The scheduler is returned but NOT started — the caller must
    call ``scheduler.start()`` when the event loop is running.
    """
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all_collectors,
        trigger="interval",
        minutes=interval_minutes,
        args=[collectors, gemini],
        id="collection_job",
        name="Periodic data collection",
        replace_existing=True,
    )
    logger.info(
        "Scheduler configured: collecting every %d minutes", interval_minutes
    )
    return scheduler
