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
