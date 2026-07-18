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
