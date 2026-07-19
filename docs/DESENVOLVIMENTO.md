# Desenvolvimento e Setup

Bot para Telegram focado em jogadores de Pokemon GO, com arquitetura hibrida (Python e Node.js).

---

## Pre-requisitos

| Ferramenta | Versao | Necessario para |
|-----------|--------|----------------|
| Python | 3.10+ | Executar o core do bot e scripts de coleta |
| Node.js | 20.x | Executar a ponte Javascript (DialgaDex engine) para calculos precisos de tier list |
| tmux | latest | Rodar o bot em background com gerenciamento facil de sessoes |
| Git | latest | Controle de versao e atualizacao do codigo |

> **Por que Node.js?** O calculo real de tier lists usa a engine original do DialgaDex. Usamos o Node.js como ponte (bridge) para executar a matematica nativa em JS, garantindo precisao absoluta nos resultados de PVE.

---

## Arquitetura de funcionamento

```text
┌──────────────────────────────┐   Polling       ┌──────────────────────────┐
│  API do Telegram             │ ◀────────────── │  Core do Bot (Python)    │
│  (Chatbot interface)         │                 │  src/bot.py              │
└──────────────────────────────┘                 └─────────▲────────────────┘
                                                           │ (Le .json)
┌──────────────────────────────┐   Executa JS    ┌─────────▼────────────────┐
│  Engine JS (Node.js)         │ ◀────────────── │  Coletores (APScheduler) │
│  DialgaDex Scripts           │ ──────────────▶ │  src/collectors/         │
└──────────────────────────────┘   Retorna JSON  └──────────────────────────┘
```

---

## Primeira vez? Setup unico

Da raiz do projeto, execute **uma unica vez**:

```bash
# 1. Crie o ambiente virtual e ative-o
python3 -m venv .venv
source .venv/bin/activate

# 2. Instale as dependencias Python
pip install -r requirements.txt

# 3. Configure a variavel de ambiente (Token do Telegram)
export BOT_TOKEN="seu_token_do_telegram_aqui"

# 4. Instale o Node.js (necessario para a JS Bridge)
curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo -E bash nodesource_setup.sh
sudo apt-get install -y nodejs
```

---

## Fluxo diario

### Rodando em foreground (debug)

```bash
export BOT_TOKEN="seu_token_do_telegram_aqui"
python3 main.py
```

### Rodando em background (producao)

```bash
# Inicia o bot em background via tmux
./start_bot.sh
```

| Comando tmux | Acao |
|-------|------|
| `tmux attach -t pokemon_bot` | Visualizar logs do bot ao vivo |
| `CTRL+B` e depois `D` | Desconectar da visualizacao |
| `tmux kill-session -t pokemon_bot` | Desligar o bot |

---

## Rodando os testes

A suite de testes valida as mensagens e formatacoes de modo a prevenir falhas na API do Telegram (por exemplo, erros de parse por underscores).

```bash
source .venv/bin/activate
pytest tests/test_bot_formatting.py -v
pytest tests/test_tierlists.py -v
```

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| `[Errno 2] No such file or directory: 'node'` | O pacote `nodejs` nao esta instalado no sistema. Siga o passo a passo do Setup Unico. |
| `BadRequest: Can't parse entities` | Erro do Telegram por caracteres reservados no Markdown. O bot atual utiliza parse HTML para prevencao (testes inclusos). |
| Bot nao responde | Pode ter havido crash silencioso ou token expirou. Entre na sessao `tmux` para ler o trace. |
