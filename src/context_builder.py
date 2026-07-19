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

    The returned string is used as ``system_instruction`` for the Gemini API.
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

## Regras CRÍTICAS:
1. Responda SEMPRE em português brasileiro, de forma clara e amigável.
2. Inicie sua resposta diretamente com o texto. NUNCA comece com caracteres soltos, parênteses ou pontuação quebrada.
3. Use APENAS os dados fornecidos abaixo para responder. Não invente informações de cabeça.
5. SEJA EXTREMAMENTE CONCISO. O Telegram tem limite de caracteres. Nunca liste dezenas de eventos. Escolha apenas os 3 a 5 mais importantes/próximos.
6. PROIBIDO USAR MARKDOWN: NÃO use asteriscos (**) nem hashtags (#) no texto. O usuário acha estranho. Formate a estrutura apenas com quebras de linha e emojis.
7. PADRÃO DE RESPOSTA: Sempre que listar eventos ou raids, use um formato limpo. Exemplo: "🛑 Kyogre (5 Estrelas) — Disponível até 21 de julho às 22:00".
8. Cruze informações entre eventos, raids e tier lists SOMENTE se você tiver os dados.

## Dados Atualizados do Pokémon GO:
{data_block}"""
