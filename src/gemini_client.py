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
