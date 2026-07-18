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
