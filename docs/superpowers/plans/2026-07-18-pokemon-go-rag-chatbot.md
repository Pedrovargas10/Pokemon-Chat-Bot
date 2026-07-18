# Pokémon GO RAG Chatbot — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar um assistente virtual no Telegram que responde dúvidas de jogadores de Pokémon GO sobre eventos, raids, spotlight hours e tier lists, usando dados extraídos automaticamente da web como contexto para o Gemini (RAG).

**Architecture:** O sistema é dividido em 3 subsistemas: (1) coletores de dados que extraem informações de ScrapedDuck (JSON via GitHub), Pokebattler (API REST) e Pokémon GO Live (HTML scraping) e salvam em Markdown; (2) um módulo de integração com o Gemini que monta o contexto RAG a partir dos Markdowns; (3) um bot Telegram que recebe perguntas, consulta o Gemini com o contexto e retorna respostas estratégicas. Um scheduler roda os coletores periodicamente.

**Tech Stack:** Python 3.11+ · httpx (HTTP async) + BeautifulSoup4 (parsing HTML fallback) · google-genai (Gemini API, free tier) · python-telegram-bot v22+ (interface) · APScheduler (agendamento) · python-dotenv (configuração)

## Global Constraints

- Custo: R$ 0,00 — apenas free tier do Gemini e libs open-source
- Gemini model: verificar modelo disponível no AI Studio (ex: `gemini-2.5-flash`). **Gemini 2.0 Flash foi descontinuado em junho/2026.** Usar o modelo Flash mais recente disponível na free tier
- Python ≥ 3.11
- Sem banco de dados — contexto armazenado em arquivos `.md` em `data/`
- Respostas em português brasileiro
- Todos os horários em fuso local (America/Sao_Paulo) quando exibidos ao usuário
- Sem Playwright/Selenium — apenas HTTP requests + parsing (HTML ou JSON)
- Variáveis sensíveis (tokens, API keys) em `.env`, nunca hardcoded
- LeekDuck: usar **ScrapedDuck** (https://github.com/bigfoott/ScrapedDuck) — feed JSON comunitário, sem scraping HTML
- Pokebattler: usar API REST pública (`fight.pokebattler.com`), respeitar Cache-Control e não paralelizar requests
- Pokémon GO Live: scraping HTML básico da página de notícias (fallback gracioso se falhar)
- Créditos: mencionar LeekDuck, ScrapedDuck e Pokebattler conforme suas regras

---

## File Structure

```
chatbotpokemon/
├── docs/superpowers/plans/
│   └── 2026-07-18-pokemon-go-rag-chatbot.md   # Este plano
├── src/
│   ├── __init__.py
│   ├── config.py              # Carrega .env, define constantes
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base.py            # Classe base async collector
│   │   ├── leekduck.py        # Collector de eventos via ScrapedDuck JSON
│   │   ├── pokemongo_live.py  # Collector de anúncios oficiais (HTML)
│   │   └── pokebattler.py     # Collector de tier lists via API REST
│   ├── gemini_client.py       # Wrapper do Gemini com RAG
│   ├── context_builder.py     # Monta contexto MD para o Gemini
│   ├── bot.py                 # Bot Telegram (handlers)
│   └── scheduler.py           # Agenda coleta periódica
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures compartilhadas
│   ├── test_config.py
│   ├── test_collectors/
│   │   ├── __init__.py
│   │   ├── test_leekduck.py
│   │   ├── test_pokemongo_live.py
│   │   └── test_pokebattler.py
│   ├── test_context_builder.py
│   ├── test_gemini_client.py
│   └── test_bot.py
├── data/                      # Dados coletados (gitignored)
│   ├── events.md
│   ├── raids.md
│   ├── announcements.md
│   └── tier_lists.md
├── main.py                    # Entrypoint
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

### Task 1: Project Scaffolding & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `src/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`

**Interfaces:**
- Consumes: nada (primeira task)
- Produces:
  - `src.config.Settings` — class with attributes:
    - `telegram_token: str` (required)
    - `gemini_api_key: str` (required)
    - `data_dir: Path` (default: `PROJECT_ROOT / "data"`)
    - `scrape_interval_minutes: int` (default: `120`)
    - `gemini_model: str` (default: `gemini-2.5-flash`)
    - `log_level: str` (default: `INFO`)

- [ ] **Step 1: Create requirements.txt**

```
httpx>=0.27,<1.0
beautifulsoup4>=4.12,<5.0
google-genai>=1.0,<2.0
python-telegram-bot>=22.0,<23.0
python-dotenv>=1.0,<2.0
apscheduler>=3.10,<4.0
pytest>=8.0,<9.0
pytest-asyncio>=0.23,<1.0
```

- [ ] **Step 2: Create .env.example**

```
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
SCRAPE_INTERVAL_MINUTES=120
GEMINI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
```

- [ ] **Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
data/
.venv/
venv/
*.egg-info/
dist/
build/
.pytest_cache/
```

- [ ] **Step 4: Create empty init files**

```python
# src/__init__.py — empty
```

```python
# tests/__init__.py — empty
```

```python
# tests/conftest.py
"""Shared test fixtures."""
import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolate_env():
    """Prevent tests from reading the real .env file."""
    with patch.dict(os.environ, {}, clear=False):
        yield
```

- [ ] **Step 5: Write the failing test for config**

```python
# tests/test_config.py
import os
import importlib
import pytest
from unittest.mock import patch


def _fresh_settings():
    """Import Settings fresh to avoid caching."""
    import src.config as mod
    importlib.reload(mod)
    return mod.Settings


def test_settings_loads_from_env():
    env = {
        "TELEGRAM_TOKEN": "test-tg-token",
        "GEMINI_API_KEY": "test-gemini-key",
        "SCRAPE_INTERVAL_MINUTES": "60",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, env, clear=True):
        Settings = _fresh_settings()
        s = Settings()
        assert s.telegram_token == "test-tg-token"
        assert s.gemini_api_key == "test-gemini-key"
        assert s.scrape_interval_minutes == 60
        assert s.gemini_model == "gemini-2.5-flash"
        assert s.log_level == "DEBUG"


def test_settings_defaults():
    env = {
        "TELEGRAM_TOKEN": "tok",
        "GEMINI_API_KEY": "key",
    }
    with patch.dict(os.environ, env, clear=True):
        Settings = _fresh_settings()
        s = Settings()
        assert s.scrape_interval_minutes == 120
        assert s.gemini_model == "gemini-2.5-flash"
        assert s.log_level == "INFO"
        assert s.data_dir.name == "data"


def test_settings_missing_token_raises():
    with patch.dict(os.environ, {"GEMINI_API_KEY": "key"}, clear=True):
        Settings = _fresh_settings()
        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            Settings()


def test_settings_missing_gemini_key_raises():
    with patch.dict(os.environ, {"TELEGRAM_TOKEN": "tok"}, clear=True):
        Settings = _fresh_settings()
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            Settings()
```

- [ ] **Step 6: Run test to verify it fails**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src'`

- [ ] **Step 7: Implement src/config.py**

```python
# src/config.py
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
```

- [ ] **Step 8: Run test to verify it passes**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 9: Install dependencies and commit**

```bash
cd /home/pedro/chatbotpokemon
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git init
git add .
git commit -m "feat: project scaffolding and config module"
```

---

### Task 2: Base Collector & LeekDuck Events (ScrapedDuck JSON)

**Files:**
- Create: `src/collectors/__init__.py`
- Create: `src/collectors/base.py`
- Create: `src/collectors/leekduck.py`
- Create: `tests/test_collectors/__init__.py`
- Create: `tests/test_collectors/test_leekduck.py`

**Interfaces:**
- Consumes: `Settings.data_dir` (Path)
- Produces:
  - `src.collectors.base.BaseCollector` — abstract class with:
    - `__init__(data_dir: Path)`
    - `async fetch_json(url: str) -> dict | list`
    - `async fetch_html(url: str) -> str`
    - `abstract async collect() -> list[dict]`
    - `save_markdown(data: list[dict], filename: str) -> Path`
  - `src.collectors.leekduck.LeekDuckCollector(BaseCollector)`:
    - `async collect() -> list[dict]` — fetches ScrapedDuck JSON from GitHub, returns list of event dicts with keys: `name: str`, `type: str`, `start_date: str`, `end_date: str`, `url: str`
    - Saves to `data/events.md`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_collectors/__init__.py — empty
```

```python
# tests/test_collectors/test_leekduck.py
import json
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
        }
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
            "bonus": "2x Transfer Candy"
        }
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
            "bonus": "3x Catch XP"
        }
    }
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_collectors/test_leekduck.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.collectors'`

- [ ] **Step 3: Implement src/collectors/base.py**

```python
# src/collectors/base.py
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
```

- [ ] **Step 4: Implement src/collectors/leekduck.py**

```python
# src/collectors/leekduck.py
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
```

```python
# src/collectors/__init__.py
from src.collectors.leekduck import LeekDuckCollector

__all__ = ["LeekDuckCollector"]
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_collectors/test_leekduck.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/collectors/ tests/test_collectors/
git commit -m "feat: base collector and LeekDuck events via ScrapedDuck"
```

---

### Task 3: Pokémon GO Live & Pokebattler Collectors

**Files:**
- Create: `src/collectors/pokemongo_live.py`
- Create: `src/collectors/pokebattler.py`
- Modify: `src/collectors/__init__.py`
- Create: `tests/test_collectors/test_pokemongo_live.py`
- Create: `tests/test_collectors/test_pokebattler.py`

**Interfaces:**
- Consumes: `src.collectors.base.BaseCollector`
- Produces:
  - `PokemonGoLiveCollector.collect() -> list[dict]` — dicts with keys: `name: str`, `date: str`, `url: str`, `summary: str`; saves to `data/announcements.md`
  - `PokebattlerCollector.collect() -> list[dict]` — dicts with keys: `pokemon: str`, `tier: str`, `type: str`, `counters: list[str]`; saves to `data/tier_lists.md`

- [ ] **Step 1: Write the failing tests for Pokémon GO Live**

```python
# tests/test_collectors/test_pokemongo_live.py
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
```

- [ ] **Step 2: Write the failing tests for Pokebattler**

```python
# tests/test_collectors/test_pokebattler.py
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
            ]
        },
        {
            "tier": "RAID_LEVEL_MEGA",
            "raidBosses": [
                {
                    "pokemon": "SCEPTILE_MEGA",
                    "pokemonId": 254,
                    "form": "MEGA",
                },
            ]
        }
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_collectors/test_pokemongo_live.py tests/test_collectors/test_pokebattler.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Implement src/collectors/pokemongo_live.py**

```python
# src/collectors/pokemongo_live.py
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
```

- [ ] **Step 5: Implement src/collectors/pokebattler.py**

```python
# src/collectors/pokebattler.py
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
```

Update `src/collectors/__init__.py`:

```python
# src/collectors/__init__.py
from src.collectors.leekduck import LeekDuckCollector
from src.collectors.pokemongo_live import PokemonGoLiveCollector
from src.collectors.pokebattler import PokebattlerCollector

__all__ = ["LeekDuckCollector", "PokemonGoLiveCollector", "PokebattlerCollector"]
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_collectors/ -v`
Expected: ALL passed (7+ tests)

- [ ] **Step 7: Commit**

```bash
git add src/collectors/ tests/test_collectors/
git commit -m "feat: Pokémon GO Live and Pokebattler collectors"
```

---

### Task 4: Context Builder (RAG Assembly)

**Files:**
- Create: `src/context_builder.py`
- Create: `tests/test_context_builder.py`

**Interfaces:**
- Consumes: `Settings.data_dir` (Path), Markdown files in `data/`
- Produces:
  - `build_context(data_dir: Path) -> str` — reads all `.md` files from `data/` and concatenates them with separators
  - `get_system_prompt(context: str) -> str` — wraps the context in the bot's persona and strategic instructions; returns complete system_instruction string for Gemini

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_context_builder.py
import pytest
from pathlib import Path

from src.context_builder import build_context, get_system_prompt


def test_build_context_reads_all_md_files(tmp_path):
    (tmp_path / "events.md").write_text("# Events\n\n## Kyogre Raids\n- type: raid")
    (tmp_path / "announcements.md").write_text(
        "# Announcements\n\n## Anniversary\n- Big event"
    )
    (tmp_path / "not_md.txt").write_text("should be ignored")

    context = build_context(tmp_path)

    assert "Kyogre Raids" in context
    assert "Anniversary" in context
    assert "should be ignored" not in context


def test_build_context_empty_dir(tmp_path):
    context = build_context(tmp_path)
    assert context == ""


def test_build_context_nonexistent_dir():
    context = build_context(Path("/nonexistent/dir"))
    assert context == ""


def test_get_system_prompt_includes_persona():
    context = "## Kyogre Raids\n- type: raid"
    prompt = get_system_prompt(context)

    assert "Pokémon GO" in prompt
    assert context in prompt
    assert "português" in prompt.lower() or "brasileiro" in prompt.lower()


def test_get_system_prompt_handles_empty_context():
    prompt = get_system_prompt("")
    assert "Pokémon GO" in prompt
    assert "indisponível" in prompt.lower() or "indisponíveis" in prompt.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_context_builder.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/context_builder.py**

```python
# src/context_builder.py
"""Assembles scraped Markdown files into a single RAG context string."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SECTION_SEPARATOR = "\n\n---\n\n"


def build_context(data_dir: Path) -> str:
    """Read all .md files from *data_dir* and concatenate them.

    Returns an empty string if no files are found or the directory
    does not exist.
    """
    if not data_dir.exists():
        return ""

    md_files = sorted(data_dir.glob("*.md"))
    if not md_files:
        return ""

    sections: list[str] = []
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8").strip()
        if content:
            sections.append(content)

    combined = _SECTION_SEPARATOR.join(sections)
    logger.info(
        "Built context from %d files (%d chars)", len(sections), len(combined)
    )
    return combined


def get_system_prompt(context: str) -> str:
    """Wrap the scraped context in the bot's persona and instructions.

    The returned string is used as `system_instruction` for the Gemini API.
    """
    if not context.strip():
        data_block = (
            "\n\n[DADOS INDISPONÍVEIS — os coletores ainda não rodaram. "
            "Informe ao usuário que os dados estão sendo carregados.]\n"
        )
    else:
        data_block = f"\n\n{context}\n"

    return f"""Você é o **PokéGuia**, um assistente virtual especialista em Pokémon GO.
Sua função é ajudar jogadores respondendo dúvidas sobre eventos, raids, spotlight hours,
tier lists de atacantes e estratégias do jogo.

## Regras:
1. Responda SEMPRE em português brasileiro, de forma clara e amigável.
2. Use APENAS os dados fornecidos abaixo para responder. Não invente informações.
3. Se a informação não estiver nos dados, diga honestamente que não tem essa informação no momento.
4. Quando relevante, dê conselhos estratégicos (ex: "guarde seus passes de reide para o próximo mês", "aproveite o spotlight hour para farmear candies").
5. Formate respostas com emojis e listas quando apropriado para facilitar a leitura no Telegram.
6. Ao mencionar datas, converta para formato legível (ex: "terça-feira, 21 de julho").
7. Cruze informações entre eventos, raids e tier lists para dar respostas completas.
8. Dados coletados de LeekDuck/ScrapedDuck e Pokebattler. Créditos a essas fontes quando solicitado.

## Dados Atualizados do Pokémon GO:
{data_block}"""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_context_builder.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/context_builder.py tests/test_context_builder.py
git commit -m "feat: context builder for RAG assembly"
```

---

### Task 5: Gemini Client (LLM Integration)

**Files:**
- Create: `src/gemini_client.py`
- Create: `tests/test_gemini_client.py`

**Interfaces:**
- Consumes: `Settings.gemini_api_key: str`, `Settings.gemini_model: str`, `Settings.data_dir: Path`, `build_context(Path) -> str`, `get_system_prompt(str) -> str`
- Produces:
  - `GeminiClient`:
    - `__init__(api_key: str, model: str, data_dir: Path)`
    - `async ask(question: str) -> str` — sends question to Gemini with RAG context, returns response text
    - `refresh_context() -> None` — re-reads Markdown files and updates `_system_prompt`
    - `model: str` — the model name
    - `_system_prompt: str` — current system prompt (for testing)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_gemini_client.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

from src.gemini_client import GeminiClient


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "events.md").write_text(
        "# Events\n\n## Kyogre Raids\n- ends: 2026-07-21"
    )
    return tmp_path


def test_gemini_client_init(data_dir):
    with patch("src.gemini_client.genai") as mock_genai:
        mock_genai.Client.return_value = MagicMock()
        client = GeminiClient(
            api_key="fake-key",
            model="gemini-2.5-flash",
            data_dir=data_dir,
        )
        assert client.model == "gemini-2.5-flash"
        assert "Kyogre" in client._system_prompt


def test_gemini_client_refresh_context(data_dir):
    with patch("src.gemini_client.genai") as mock_genai:
        mock_genai.Client.return_value = MagicMock()
        client = GeminiClient(
            api_key="fake-key",
            model="gemini-2.5-flash",
            data_dir=data_dir,
        )
        assert "Kyogre" in client._system_prompt

        (data_dir / "events.md").write_text(
            "# Events\n\n## Mewtwo Raids\n- ends: 2026-08-01"
        )
        client.refresh_context()

        assert "Mewtwo" in client._system_prompt
        assert "Kyogre" not in client._system_prompt


@pytest.mark.asyncio
async def test_gemini_client_ask(data_dir):
    with patch("src.gemini_client.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "Kyogre está nas raids até 21 de julho!"
        mock_client.models.generate_content.return_value = mock_response

        client = GeminiClient(
            api_key="fake-key",
            model="gemini-2.5-flash",
            data_dir=data_dir,
        )
        answer = await client.ask("Quais raids estão rolando?")

        assert "Kyogre" in answer
        mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_client_ask_handles_error(data_dir):
    with patch("src.gemini_client.genai") as mock_genai:
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_client.models.generate_content.side_effect = Exception("API Error")

        client = GeminiClient(
            api_key="fake-key",
            model="gemini-2.5-flash",
            data_dir=data_dir,
        )
        answer = await client.ask("Teste")

        assert "erro" in answer.lower() or "desculpe" in answer.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_gemini_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/gemini_client.py**

```python
# src/gemini_client.py
"""Wrapper around the Google Gemini API for RAG-based Q&A."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from google import genai
from google.genai import types as genai_types

from src.context_builder import build_context, get_system_prompt

logger = logging.getLogger(__name__)


class GeminiClient:
    """Sends user questions to Gemini with scraped context as system prompt."""

    def __init__(self, api_key: str, model: str, data_dir: Path) -> None:
        self.model = model
        self._data_dir = data_dir
        self._client = genai.Client(api_key=api_key)
        self._system_prompt = ""
        self.refresh_context()

    def refresh_context(self) -> None:
        """Re-read Markdown files and rebuild the system prompt."""
        context = build_context(self._data_dir)
        self._system_prompt = get_system_prompt(context)
        logger.info(
            "Context refreshed (%d chars)", len(self._system_prompt)
        )

    async def ask(self, question: str) -> str:
        """Send a question to Gemini and return the response text.

        Uses ``asyncio.to_thread`` because the google-genai SDK
        ``generate_content`` call is synchronous.
        """
        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self.model,
                config=genai_types.GenerateContentConfig(
                    system_instruction=self._system_prompt,
                    temperature=0.7,
                    max_output_tokens=2048,
                ),
                contents=question,
            )
            return response.text or "Não consegui gerar uma resposta."
        except Exception:
            logger.exception("Gemini API call failed")
            return (
                "🤖 Desculpe, ocorreu um erro ao consultar a IA. "
                "Tente novamente em alguns instantes."
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_gemini_client.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/gemini_client.py tests/test_gemini_client.py
git commit -m "feat: Gemini client with RAG context injection"
```

---

### Task 6: Telegram Bot (Interface Layer)

**Files:**
- Create: `src/bot.py`
- Create: `tests/test_bot.py`

**Interfaces:**
- Consumes: `GeminiClient.ask(question: str) -> str`, `Settings.telegram_token: str`
- Produces:
  - `handle_start(update, context) -> None`
  - `handle_help(update, context) -> None`
  - `handle_raids(update, context) -> None`
  - `handle_events(update, context) -> None`
  - `handle_spotlight(update, context) -> None`
  - `handle_message(update, context) -> None` — freeform text handler, reads `context.bot_data["gemini"]`
  - `create_bot(token: str, gemini: GeminiClient) -> Application`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_bot.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.bot import handle_start, handle_help, handle_message


@pytest.fixture
def mock_update():
    update = MagicMock()
    update.effective_user.first_name = "Ash"
    update.message.reply_text = AsyncMock()
    update.message.text = "Quais raids estão rolando?"
    return update


@pytest.fixture
def mock_context():
    context = MagicMock()
    context.bot_data = {}
    return context


@pytest.mark.asyncio
async def test_handle_start(mock_update, mock_context):
    await handle_start(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "Ash" in call_text


@pytest.mark.asyncio
async def test_handle_help(mock_update, mock_context):
    await handle_help(mock_update, mock_context)
    mock_update.message.reply_text.assert_called_once()
    call_text = mock_update.message.reply_text.call_args[0][0]
    assert "/raids" in call_text


@pytest.mark.asyncio
async def test_handle_message_calls_gemini(mock_update, mock_context):
    mock_gemini = AsyncMock()
    mock_gemini.ask.return_value = "Kyogre está nas raids tier 5!"
    mock_context.bot_data["gemini"] = mock_gemini

    await handle_message(mock_update, mock_context)

    mock_gemini.ask.assert_called_once_with("Quais raids estão rolando?")
    mock_update.message.reply_text.assert_called_once()
    response_text = mock_update.message.reply_text.call_args[0][0]
    assert "Kyogre" in response_text


@pytest.mark.asyncio
async def test_handle_message_empty_text(mock_update, mock_context):
    mock_update.message.text = ""
    mock_gemini = AsyncMock()
    mock_context.bot_data["gemini"] = mock_gemini

    await handle_message(mock_update, mock_context)

    mock_gemini.ask.assert_not_called()
    mock_update.message.reply_text.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_bot.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement src/bot.py**

```python
# src/bot.py
"""Telegram bot handlers and application factory."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


async def handle_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Send a welcome message when /start is issued."""
    name = update.effective_user.first_name or "Treinador"
    await update.message.reply_text(
        f"👋 Olá, {name}! Eu sou o **PokéGuia**, seu assistente de Pokémon GO!\n\n"
        "Pode me perguntar qualquer coisa sobre:\n"
        "🎯 Eventos atuais e futuros\n"
        "⚔️ Raids e melhores contadores\n"
        "✨ Spotlight Hours e bônus\n"
        "📊 Tier lists de atacantes\n\n"
        "Envie sua pergunta ou use /help para ver os comandos!",
        parse_mode="Markdown",
    )


async def handle_help(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """List available commands."""
    await update.message.reply_text(
        "📖 **Comandos disponíveis:**\n\n"
        "/start — Iniciar o bot\n"
        "/help — Ver esta ajuda\n"
        "/raids — Raids atuais + contadores\n"
        "/events — Eventos atuais e futuros\n"
        "/spotlight — Próximos Spotlight Hours\n\n"
        "Ou simplesmente envie sua pergunta em texto livre! 💬",
        parse_mode="Markdown",
    )


async def handle_raids(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Shortcut to ask about current raids."""
    gemini: GeminiClient = context.bot_data["gemini"]
    await update.message.reply_text("🔍 Consultando raids atuais...")
    answer = await gemini.ask(
        "Quais são as raids atuais e próximas? "
        "Inclua os tier levels e, se disponível, os melhores contadores."
    )
    await update.message.reply_text(answer, parse_mode="Markdown")


async def handle_events(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Shortcut to ask about current and upcoming events."""
    gemini: GeminiClient = context.bot_data["gemini"]
    await update.message.reply_text("🔍 Consultando eventos...")
    answer = await gemini.ask(
        "Quais eventos estão acontecendo agora e quais são os próximos? "
        "Dê conselhos estratégicos sobre como aproveitar cada um."
    )
    await update.message.reply_text(answer, parse_mode="Markdown")


async def handle_spotlight(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Shortcut to ask about Spotlight Hours."""
    gemini: GeminiClient = context.bot_data["gemini"]
    await update.message.reply_text("🔍 Consultando Spotlight Hours...")
    answer = await gemini.ask(
        "Quais são os próximos Pokémon Spotlight Hours? "
        "Quais valem a pena participar e por quê?"
    )
    await update.message.reply_text(answer, parse_mode="Markdown")


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle freeform text questions from the user."""
    question = update.message.text

    if not question or not question.strip():
        await update.message.reply_text(
            "🤔 Não entendi. Tente enviar uma pergunta sobre Pokémon GO!"
        )
        return

    gemini: GeminiClient = context.bot_data["gemini"]
    logger.info(
        "Question from %s: %s", update.effective_user.first_name, question
    )
    answer = await gemini.ask(question)
    await update.message.reply_text(answer, parse_mode="Markdown")


def create_bot(token: str, gemini: GeminiClient) -> Application:
    """Build and configure the Telegram bot Application."""
    app = Application.builder().token(token).build()
    app.bot_data["gemini"] = gemini

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("raids", handle_raids))
    app.add_handler(CommandHandler("events", handle_events))
    app.add_handler(CommandHandler("spotlight", handle_spotlight))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    return app
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/test_bot.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/bot.py tests/test_bot.py
git commit -m "feat: Telegram bot with command and message handlers"
```

---

### Task 7: Scheduler & Main Entrypoint

**Files:**
- Create: `src/scheduler.py`
- Create: `main.py`

**Interfaces:**
- Consumes:
  - `LeekDuckCollector.collect()`, `PokemonGoLiveCollector.collect()`, `PokebattlerCollector.collect()` — all `async () -> list[dict]`
  - `GeminiClient.refresh_context()` — `() -> None`
  - `create_bot(token: str, gemini: GeminiClient) -> Application`
  - `Settings` — all fields
- Produces:
  - `run_all_collectors(collectors: list[BaseCollector], gemini: GeminiClient) -> None` — runs all collectors concurrently and refreshes context
  - `setup_scheduler(collectors, gemini, interval_minutes) -> AsyncIOScheduler`
  - `main.py:main()` — boots everything

- [ ] **Step 1: Implement src/scheduler.py**

```python
# src/scheduler.py
"""Periodic data collection scheduler using APScheduler."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
```

- [ ] **Step 2: Implement main.py**

```python
# main.py
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
```

- [ ] **Step 3: Verify imports work**

Run: `cd /home/pedro/chatbotpokemon && python -c "from src.scheduler import setup_scheduler, run_all_collectors; print('scheduler OK')"`
Expected: `scheduler OK`

Run: `cd /home/pedro/chatbotpokemon && python -c "import main; print('main OK')"`
Expected: `main OK` (may warn about missing .env, but import should succeed)

- [ ] **Step 4: Commit**

```bash
git add src/scheduler.py main.py
git commit -m "feat: scheduler and main entrypoint"
```

---

### Task 8: README & Full Test Suite Verification

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: tudo (task final)
- Produces: documentação de uso completa

- [ ] **Step 1: Create README.md**

```markdown
# 🤖 PokéGuia — Chatbot Pokémon GO (RAG)

Assistente virtual no Telegram que responde dúvidas sobre Pokémon GO usando
dados coletados automaticamente da web + IA do Google Gemini.

## ✨ Funcionalidades

- 📅 **Eventos atuais e futuros** — via ScrapedDuck/LeekDuck
- ⚔️ **Raids e bosses atuais** — via API Pokebattler
- ✨ **Spotlight Hours e bônus**
- 📊 **Tier lists de atacantes**
- 🧠 **Conselhos estratégicos** (ex: "guarde passes para o próximo mês")
- 📰 **Anúncios oficiais** — via Pokémon GO Live

## 🛠️ Setup

### Pré-requisitos

- Python 3.11+
- Token do Telegram Bot — via [@BotFather](https://t.me/BotFather)
- API Key do Gemini — via [Google AI Studio](https://aistudio.google.com/apikey)

### Instalação

```bash
git clone https://github.com/seu-usuario/chatbotpokemon.git
cd chatbotpokemon
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edite .env com seu TELEGRAM_TOKEN e GEMINI_API_KEY
```

### Executando

```bash
python main.py
```

O bot vai:
1. Coletar dados dos 3 fontes (ScrapedDuck, Pokebattler, PoGO Live)
2. Montar o contexto RAG para o Gemini
3. Iniciar o bot no Telegram
4. Re-coletar dados a cada 2 horas (configurável)

## 📱 Comandos do Bot

| Comando      | Descrição                    |
|------------- |------------------------------|
| `/start`     | Mensagem de boas-vindas      |
| `/help`      | Lista de comandos            |
| `/raids`     | Raids atuais + contadores    |
| `/events`    | Eventos atuais e futuros     |
| `/spotlight` | Próximos Spotlight Hours     |
| Texto livre  | Qualquer pergunta sobre PoGO |

## ⚙️ Configuração (.env)

| Variável                   | Obrigatória | Default           | Descrição                   |
|--------------------------- |-------------|-------------------|-----------------------------|
| `TELEGRAM_TOKEN`           | ✅          | —                 | Token do BotFather          |
| `GEMINI_API_KEY`           | ✅          | —                 | API key do Google AI Studio |
| `SCRAPE_INTERVAL_MINUTES`  | ❌          | `120`             | Intervalo de coleta (min)   |
| `GEMINI_MODEL`             | ❌          | `gemini-2.5-flash`| Modelo do Gemini            |
| `LOG_LEVEL`                | ❌          | `INFO`            | Nível de log                |

## 🧪 Testes

```bash
python -m pytest tests/ -v
```

## 🏗️ Arquitetura

```
User (Telegram) → Bot → Gemini (com contexto RAG)
                           ↑
                    Context Builder ← Markdown files ← Collectors
                                                        ↑
                                      ScrapedDuck | PoGO Live | Pokebattler API
```

## 📋 Créditos

- [LeekDuck](https://leekduck.com) — fonte dos dados de eventos
- [ScrapedDuck](https://github.com/bigfoott/ScrapedDuck) — feed JSON dos dados LeekDuck
- [Pokebattler](https://www.pokebattler.com) — tier lists e dados de raids

## 💰 Custo

**R$ 0,00** — usa apenas free tier do Gemini e bibliotecas open-source.
```

- [ ] **Step 2: Run the full test suite**

Run: `cd /home/pedro/chatbotpokemon && python -m pytest tests/ -v --tb=short`
Expected: ALL tests pass (17+ tests)

- [ ] **Step 3: Final commit**

```bash
git add README.md
git commit -m "docs: add README with setup instructions and credits"
```

---

## Self-Review ✅

**1. Spec coverage:**
- ✅ Python como linguagem
- ✅ Gemini Flash (via google-genai SDK, free tier) — modelo atualizado para `gemini-2.5-flash`
- ✅ Coleta de dados: ScrapedDuck JSON (LeekDuck), Pokebattler API, Pokémon GO Live HTML — tudo gratuito e fácil
- ✅ Fontes: LeekDuck (via ScrapedDuck), Pokémon GO Live, Pokebattler
- ✅ Interface: Bot Telegram (mais prático para jogadores mobile)
- ✅ Custo: R$ 0,00
- ✅ Coleta periódica salvando em Markdown
- ✅ Gemini usa texto extraído como contexto do sistema (system_instruction)
- ✅ Conselhos estratégicos no system prompt
- ✅ Cruzamento de informações entre fontes

**2. Placeholder scan:** Nenhum "TBD", "TODO", ou "implementar depois" encontrado. Todos os steps têm código completo.

**3. Type consistency:**
- `Settings` — mesmos atributos referenciados em todas as tasks
- `BaseCollector.collect() -> list[dict]` — consistente em todos os collectors
- `GeminiClient.ask(str) -> str` — usado corretamente no bot
- `GeminiClient.refresh_context() -> None` — usado no scheduler e nos testes
- `build_context(Path) -> str` e `get_system_prompt(str) -> str` — assinaturas consistentes
- `create_bot(str, GeminiClient) -> Application` — consistente com main.py
- `run_all_collectors(list[BaseCollector], GeminiClient) -> None` — consistente entre scheduler.py e main.py
