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
    await update.message.reply_text(answer)


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
    await update.message.reply_text(answer)


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
    await update.message.reply_text(answer)


import json
from pathlib import Path

async def handle_tierlist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /tierlist <type> [filters]."""
    args = context.args
    if not args:
        await update.message.reply_text(
            "⚠️ Uso: /tierlist <tipo> [-nomegas] [-noshadows] [-puro] [-tudo]\n"
            "Ex: /tierlist eletrico -nomegas -noshadows"
        )
        return

    type_map = {
        "normal": "Normal", "fogo": "Fire", "fire": "Fire", "agua": "Water", "water": "Water",
        "eletrico": "Electric", "elétrico": "Electric", "electric": "Electric",
        "grama": "Grass", "planta": "Grass", "grass": "Grass", "gelo": "Ice", "ice": "Ice",
        "lutador": "Fighting", "fighting": "Fighting", "venenoso": "Poison", "poison": "Poison",
        "terra": "Ground", "ground": "Ground", "voador": "Flying", "flying": "Flying",
        "psiquico": "Psychic", "psíquico": "Psychic", "psychic": "Psychic",
        "inseto": "Bug", "bug": "Bug", "pedra": "Rock", "rock": "Rock",
        "fantasma": "Ghost", "ghost": "Ghost", "dragao": "Dragon", "dragão": "Dragon", "dragon": "Dragon",
        "sombrio": "Dark", "dark": "Dark", "metal": "Steel", "aco": "Steel", "aço": "Steel", "steel": "Steel",
        "fada": "Fairy", "fairy": "Fairy"
    }

    req_type = args[0].lower()
    if req_type not in type_map:
        await update.message.reply_text(f"❌ Tipo '{req_type}' desconhecido.")
        return
        
    target_type = type_map[req_type]
    
    # Load JSON
    gemini: GeminiClient = context.bot_data["gemini"]
    json_path = gemini.data_dir / "tier_list_raw.json"
    if not json_path.exists():
        await update.message.reply_text("❌ Tier list não gerada ainda.")
        return
        
    data = json.loads(json_path.read_text("utf-8"))
    if target_type not in data:
        await update.message.reply_text("❌ Sem dados para esse tipo.")
        return
        
    rankings = data[target_type]
    
    # Apply filters
    filters_text = []
    no_megas = "-nomegas" in args
    no_shadows = "-noshadows" in args
    pure_only = "-puro" in args or "-pure" in args
    show_all = "-tudo" in args or "-all" in args
    
    if no_megas: filters_text.append("Sem Megas")
    if no_shadows: filters_text.append("Sem Sombras")
    if pure_only: filters_text.append("Apenas Nativos do Tipo")
    if show_all: filters_text.append("Incluindo Não Lançados")
    else: filters_text.append("Apenas Lançados")

    filtered = []
    for r in rankings:
        if no_megas and r["is_mega"]: continue
        if no_shadows and r["is_shadow"]: continue
        if pure_only and not r["is_native"]: continue
        if not show_all and not r["is_released"]: continue
        filtered.append(r)
        
    if not filtered:
        await update.message.reply_text("❌ Nenhum Pokémon passou nos filtros.")
        return
        
    lines = [f"📊 **Top 10 Atacantes: {target_type}**"]
    if filters_text:
        lines.append(f"*(Filtros: {', '.join(filters_text)})*\n")
        
    for i, r in enumerate(filtered[:10]):
        # Format names like "Mega Mewtwo Y" -> "Mega Mewtwo Y"
        lines.append(f"**{i+1}. {r['name']}**")
        lines.append(f"⚔️ {r['fm']} + {r['cm']}")
        lines.append(f"📈 eDPS: {r['edps']}\n")
        
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

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
    await update.message.reply_text(answer)


def create_bot(token: str, gemini: GeminiClient) -> Application:
    """Build and configure the Telegram bot Application."""
    app = Application.builder().token(token).build()
    app.bot_data["gemini"] = gemini

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CommandHandler("help", handle_help))
    app.add_handler(CommandHandler("raids", handle_raids))
    app.add_handler(CommandHandler("events", handle_events))
    app.add_handler(CommandHandler("spotlight", handle_spotlight))
    app.add_handler(CommandHandler("tierlist", handle_tierlist))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    return app
