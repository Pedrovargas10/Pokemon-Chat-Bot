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
