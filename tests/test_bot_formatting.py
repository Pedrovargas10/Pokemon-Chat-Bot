import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from telegram import Update, Message, User, Chat, CallbackQuery
from telegram.ext import ContextTypes

from src.bot import handle_tierlist

@pytest.fixture
def mock_context():
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    # Create bot_data with nothing needed because handle_tierlist reads from Path directly now
    return context

@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.edit_text = AsyncMock()
    update.callback_query = None
    return update

@pytest.mark.asyncio
async def test_all_tierlists_and_filters_no_markdown_crashes(mock_update, mock_context):
    expected_types = [
        "Normal", "Fire", "Water", "Electric", "Grass", "Ice",
        "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
        "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"
    ]
    
    filters_combos = [
        [],
        ["-nomegas"],
        ["-noshadows"],
        ["-puro"],
        ["-nomegas", "-noshadows", "-puro"]
    ]
    
    for t in expected_types:
        for filters in filters_combos:
            mock_context.args = [t.lower()] + filters
            mock_update.message.reply_text.reset_mock()
            
            await handle_tierlist(mock_update, mock_context)
            
            # Verify reply_text was called
            mock_update.message.reply_text.assert_called_once()
            args, kwargs = mock_update.message.reply_text.call_args
            text_out = args[0]
            
            # Check that it uses HTML mode
            assert kwargs.get("parse_mode") == "HTML", f"Failed on type {t} with filters {filters}"
            
            # Check for unescaped HTML characters that might break Telegram if it were Markdown
            # (In HTML, < and > need to be escaped, but pokemon names don't have them)
            assert "**" not in text_out, f"Markdown formatting found in HTML output: {text_out}"

@pytest.mark.asyncio
async def test_callbacks(mock_update, mock_context):
    mock_update.callback_query = MagicMock(spec=CallbackQuery)
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.message = mock_update.message
    
    # Simulate clicking "Electric" with filters enabled
    mock_update.callback_query.data = "tl|electric|1|1|1"
    
    await handle_tierlist(mock_update, mock_context)
    
    mock_update.message.edit_text.assert_called_once()
    args, kwargs = mock_update.message.edit_text.call_args
    assert kwargs.get("parse_mode") == "HTML"
    assert "**" not in args[0]
