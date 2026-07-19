# Pokemon Chat Bot

Bot para Telegram focado em jogadores de Pokemon GO, oferecendo informacoes atualizadas sobre eventos, raids, horas de holofote e rankeamentos detalhados de atacantes para PVE baseados em calculos avancados de dano por segundo.

> Projeto open-source desenvolvido para auxiliar treinadores a montarem as melhores equipes para raids no Pokemon GO.

---

## Pre-requisitos

| Ferramenta | Versao | Necessario para |
|-----------|--------|----------------|
| Python | 3.10+ | Executar o core do bot e scripts de coleta |
| Node.js | 20.x | Executar a ponte Javascript (DialgaDex engine) para calculos precisos de tier list |
| tmux | latest | Rodar o bot em background com gerenciamento facil de sessoes |
| Git | latest | Controle de versao e atualizacao do codigo |

> **Por que Node.js?** O calculo real de tier lists usa a engine original do DialgaDex (repositorio anexado). Usamos o Node.js como ponte (bridge) para executar a matematica nativa em JS, garantindo 100% de precisao nos resultados.

---

## Arquitetura de funcionamento

O projeto eh composto por um sistema hibrido de polling (Telegram) e rotinas agendadas (Scraping), rodando integralmente na mesma maquina virtual.

```text
┌──────────────────────────────┐   Polling       ┌──────────────────────────┐
│  API do Telegram             │ ◀────────────── │  Core do Bot (Python)    │
│  (Chatbot interface)         │                 │  src/bot.py              │
└──────────────────────────────┘                 └─────────▲────────────────┘
                                                           │ (Le arquivos .json)
┌──────────────────────────────┐   Executa JS    ┌─────────▼────────────────┐
│  Engine JS (Node.js)         │ ◀────────────── │  Coletores (APScheduler) │
│  DialgaDex Scripts           │ ──────────────▶ │  src/collectors/         │
└──────────────────────────────┘   Retorna JSON  └──────────────────────────┘
```

| Modulo | Funcao principal |
|---|---|
| **Telegram Bot** | Escuta mensagens e envia respostas baseadas em dados armazenados em JSON. |
| **Schedulers** | Baixa informacoes do LeekDuck, Pokebattler e Pokemon GO Live a cada 2 horas. |
| **JS Bridge** | Processa 18 tipos de atacantes com regras complexas (Type Affinity) usando a engine original. |

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
# (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
sudo -E bash nodesource_setup.sh
sudo apt-get install -y nodejs
```

Apos esses 4 passos, o projeto estara pronto para execucao.

---

## Fluxo diario - como rodar o projeto

### Rodando em foreground (para debug e testes)

```bash
# Da raiz do projeto, com o venv ativado
export BOT_TOKEN="seu_token_do_telegram_aqui"
python3 main.py
```

### Rodando em background (Producao)

Para manter o bot online independentemente da sessao SSH, utilize o script nativo providenciado usando `tmux`.

```bash
# Inicia o bot em background via tmux
./start_bot.sh
```

**Opcoes no terminal tmux:**

| Comando | Acao |
|-------|------|
| `tmux attach -t pokemon_bot` | Visualizar logs do bot ao vivo |
| `CTRL+B` e depois `D` | Desconectar da visualizacao (o bot continua rodando) |
| `tmux kill-session -t pokemon_bot` | Desligar o bot completamente |

---

## Rodando os testes

A suite de testes valida as mensagens e formatações de modo a prevenir falhas na API do Telegram por parse incorreto de caracteres.

```bash
# Ative o venv
source .venv/bin/activate

# Execute a suite principal de formatacao e geracao de dados
pytest tests/test_bot_formatting.py -v
pytest tests/test_tierlists.py -v
```

---

## Estrutura do projeto

```text
.
├── src/                        # Logica principal do bot e coletores
│   ├── collectors/             # Scripts de scraping
│   │   ├── dialgadex.py        # Coletor Python para tier lists
│   │   ├── dialgadex_bridge.js # Ponte Node.js para engine DialgaDex
│   │   ├── leekduck.py         # Coletor de eventos e spotlight
│   │   └── pokebattler.py      # Coletor de raids
│   ├── bot.py                  # Handlers do Telegram (comandos)
│   ├── scheduler.py            # Orquestrador de tarefas (APScheduler)
│   └── context_builder.py      # Formatador de respostas
├── dialgadex/                  # Modulo do DialgaDex clonado (Engine Original)
├── tests/                      # Suite de testes em pytest
├── data/                       # Arquivos JSON salvos pelos coletores
├── main.py                     # Entrypoint do sistema
├── start_bot.sh                # Script para daemonizar via tmux
└── requirements.txt            # Dependencias Python
```

---

## Comandos disponiveis para os usuarios

No Telegram, os usuarios podem acessar o bot atraves dos seguintes comandos:

| Comando | Descricao |
|--------|-----------|
| `/start` | Mensagem de boas-vindas |
| `/help` | Listar todos os comandos disponiveis |
| `/tierlist` | Visualizar os top 10 atacantes (por tipo) usando regras PVE detalhadas. Aceita botões interativos para filtros |
| `/raids` | Consultar chefes de reides atuais e seus principais counters |
| `/events` | Visualizar eventos atuais e os que irao comecar nos proximos dias |
| `/spotlight` | Ver quais sao os proximos Pokemon da hora do holofote e os bonus aplicados |

---

## Troubleshooting

| Problema | Solucao |
|----------|---------|
| `Collector DialgadexCollector failed: [Errno 2] No such file or directory: 'node'` | O pacote `nodejs` nao esta instalado no sistema. Instale-o utilizando as instrucoes do setup inicial. |
| `telegram.error.BadRequest: Can't parse entities` | Retorno da API do Telegram reclamando de caracteres reservados mal formatados (ex: underscore nao finalizado em parse Markdown). O bot atualmente utiliza parse HTML para prevencao. |
| Bot nao responde aos comandos | O bot pode ter caido ou o token expirou. Conecte no `tmux` para inspecionar o Traceback no `main.py`. |
| Arquivos `.json` na pasta `/data/` estao vazios | A execucao inicial dos Schedulers falhou. Verifique acesso a internet do servidor ou se a API externa sofreu reestruturacao. |
