"""Entrypoint — boots collectors, scheduler, and Telegram bot."""

from __future__ import annotations

import asyncio
import logging
import sys

from src.config import Settings
from src.gemini_client import GeminiClient
from src.collectors import (
    LeekDuckCollector,
    PokemonGoLiveCollector,
    PokebattlerCollector,
    DialgadexCollector,
)
from src.scheduler import run_all_collectors, setup_scheduler
from src.bot import create_bot


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main() -> None:
    settings = Settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    logger.info("🚀 Starting PokéGuia Bot...")

    # 1. Initialize collectors
    collectors = [
        LeekDuckCollector(data_dir=settings.data_dir),
        PokemonGoLiveCollector(data_dir=settings.data_dir),
        PokebattlerCollector(data_dir=settings.data_dir),
        DialgadexCollector(data_dir=settings.data_dir),
    ]

    # 2. Initialize Gemini client
    gemini = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        data_dir=settings.data_dir,
    )

    # 3. Run initial collection so the bot has context on first message
    logger.info("Running initial data collection...")
    asyncio.run(run_all_collectors(collectors, gemini))

    # 4. Create bot and scheduler
    app = create_bot(token=settings.telegram_token, gemini=gemini)
    scheduler = setup_scheduler(
        collectors=collectors,
        gemini=gemini,
        interval_minutes=settings.scrape_interval_minutes,
    )

    # 5. Start scheduler after the event loop is running
    async def post_init(application) -> None:
        scheduler.start()
        logger.info("✅ Scheduler started. Bot is ready!")

    app.post_init = post_init
    logger.info("🤖 Bot is starting polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
