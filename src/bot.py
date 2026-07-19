"""Telegram bot handlers and application factory."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
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
        "/tierlist — Tier lists de atacantes (PvE)\n"
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


from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import json
from pathlib import Path

async def handle_tierlist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /tierlist <type> [filters]."""
    if update.callback_query:
        # Came from a button click
        query = update.callback_query
        await query.answer()
        data = query.data.split("|")
        # Format: tl|type|no_megas|no_shadows|pure_only
        req_type = data[1]
        no_megas = data[2] == "1"
        no_shadows = data[3] == "1"
        pure_only = data[4] == "1"
        # Since it's a callback, we reply by editing the message
        message = query.message
        is_callback = True
    else:
        args = context.args
        if not args:
            await update.message.reply_text(
                "⚠️ Uso: /tierlist <tipo> [-nomegas] [-noshadows] [-puro] [-tudo]\n"
                "Ex: /tierlist eletrico\n\n"
                "Tipos: normal, fogo, agua, eletrico, grama, gelo, lutador, venenoso, terra, voador, psiquico, inseto, pedra, fantasma, dragao, sombrio, metal, fada"
            )
            return

        req_type = args[0].lower()
        no_megas = "-nomegas" in args
        no_shadows = "-noshadows" in args
        pure_only = "-puro" in args or "-pure" in args
        message = update.message
        is_callback = False

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
        "fada": "Fairy", "fairy": "Fairy",
        # English fallbacks from buttons
        "electric": "Electric", "grass": "Grass", "fire": "Fire", "water": "Water", "ice": "Ice",
        "fighting": "Fighting", "poison": "Poison", "ground": "Ground", "flying": "Flying",
        "psychic": "Psychic", "bug": "Bug", "rock": "Rock", "ghost": "Ghost", "dragon": "Dragon",
        "dark": "Dark", "steel": "Steel", "fairy": "Fairy", "normal": "Normal"
    }

    if req_type not in type_map:
        if not is_callback:
            await message.reply_text(f"❌ Tipo '{req_type}' desconhecido.")
        return
        
    target_type = type_map[req_type]
    
    # Fix: use hardcoded Path instead of gemini.data_dir which doesn't exist
    json_path = Path("data/tier_list_raw.json")
    if not json_path.exists():
        text = "❌ Tier list não gerada ainda. O scheduler ainda não baixou os dados."
        if is_callback: await message.edit_text(text)
        else: await message.reply_text(text)
        return
        
    data_json = json.loads(json_path.read_text("utf-8"))
    if target_type not in data_json:
        text = "❌ Sem dados para esse tipo."
        if is_callback: await message.edit_text(text)
        else: await message.reply_text(text)
        return
        
    rankings = data_json[target_type]
    
    # Apply filters
    filters_text = []
    no_megas = "-nomegas" in args
    no_shadows = "-noshadows" in args
    pure_only = "-puro" in args or "-pure" in args
    show_all = "-tudo" in args or "-all" in args
    
    if no_megas: filters_text.append("Sem Megas")
    if no_shadows: filters_text.append("Sem Sombras")
    if pure_only: filters_text.append("Apenas Nativos do Tipo")

    filtered = []
    for r in rankings:
        if no_megas and r["is_mega"]: continue
        if no_shadows and r["is_shadow"]: continue
        if pure_only and not r["is_native"]: continue
        filtered.append(r)
        
    if not filtered:
        await update.message.reply_text("❌ Nenhum Pokémon passou nos filtros.")
        return
        
    lines = [f"📊 **Top 10 Atacantes: {target_type}**"]
    if filters_text:
        lines.append(f"*(Filtros: {', '.join(filters_text)})*\n")
    else:
        lines.append("\n")
        
    for i, r in enumerate(filtered[:10]):
        lines.append(f"**{i+1}. {r['name']}**")
        lines.append(f"⚔️ {r['fm']} + {r['cm']}")
        lines.append(f"📈 eDPS: {r['edps']}\n")
        
    text_out = "\n".join(lines)
    
    # Generate Interactive Buttons
    def make_btn_data(m: bool, s: bool, p: bool) -> str:
        return f"tl|{target_type.lower()}|{'1' if m else '0'}|{'1' if s else '0'}|{'1' if p else '0'}"

    # Buttons to toggle filters
    btn_mega = InlineKeyboardButton(f"{'🟢' if not no_megas else '🔴'} Megas", callback_data=make_btn_data(not no_megas, no_shadows, pure_only))
    btn_shadow = InlineKeyboardButton(f"{'🟢' if not no_shadows else '🔴'} Sombras", callback_data=make_btn_data(no_megas, not no_shadows, pure_only))
    btn_pure = InlineKeyboardButton(f"{'🟢' if pure_only else '🔴'} Só Nativos", callback_data=make_btn_data(no_megas, no_shadows, not pure_only))
    
    reply_markup = InlineKeyboardMarkup([
        [btn_mega, btn_shadow, btn_pure]
    ])
        
    if is_callback:
        try:
            await message.edit_text(text_out, parse_mode="Markdown", reply_markup=reply_markup)
        except Exception:
            pass # Ignore "message is not modified" errors
    else:
        await message.reply_text(text_out, parse_mode="Markdown", reply_markup=reply_markup)

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
    app.add_handler(CallbackQueryHandler(handle_tierlist, pattern="^tl\\|"))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    return app
