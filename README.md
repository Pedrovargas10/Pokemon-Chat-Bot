<p align="center">
  <img src="https://img.shields.io/badge/Pokemon_Chat_Bot-1a2744?style=for-the-badge&logo=telegram&logoColor=white" alt="Pokemon Chat Bot">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-ativo-1d7a4a?style=flat-square" alt="Ativo">
  <img src="https://img.shields.io/badge/plataforma-Telegram-1a2744?style=flat-square" alt="Telegram">
  <img src="https://img.shields.io/badge/linguagem-Python%20%C2%B7%20Node.js-d4813a?style=flat-square" alt="Python e Node.js">
</p>

---

<h3 align="center">Seu assistente definitivo para PVE no Pokemon GO.</h3>

<p align="center">
  Montar equipes de raids perfeitas exige conhecimento profundo de mecanicas, multiplicadores de dano e status ocultos.<br>
  O <strong>PokeGuia Bot</strong> simplifica tudo isso direto no seu Telegram: ele utiliza a engine matematica original do <strong>DialgaDex</strong><br>
  (executada via Node.js em background) para entregar <strong>tier lists de altissima precisao</strong>, alem de eventos e chefes de reides.
</p>

<br>

## O que da para fazer

<table>
<tr>
<td width="50%" valign="top">

### Para treinadores casuais

- **Acompanhar eventos** — lista completa e atualizada dos eventos correntes.
- **Consultar raids ativas** — veja quem sao os chefes disponiveis no momento.
- **Horas do holofote** — saiba exatamente qual o Pokemon destaque e o bonus do dia.
- **Interacao facil** — interface conversacional fluida no aplicativo que voce ja usa.

</td>
<td width="50%" valign="top">

### Para treinadores hardcore

- **Tier lists precisas (eDPS)** — classificacao baseada em equacoes matematicas reais do jogo.
- **Filtros interativos** — oculte megas ou sombras direto por botoes no chat.
- **Type Affinity** — calculo avancado que leva em conta os chefes de raid atuais.
- **Respostas instataneas** — toda a base de dados de atributos guardada em memoria local.

</td>
</tr>
</table>

> **Engine de precisao absoluta.** Diferente de bots comuns, as nossas metricas rodam utilizando JavaScript nativamente em um ambiente orquestrado, o que assegura que o dano e a velocidade de cada ataque sejam calculados no limite do frame.

<br>

## Como acessar

<table>
<tr>
<td width="50%" align="center">
<h4>Acessar o Bot</h4>
<a href="https://t.me/">Abrir no Telegram</a><br>
<sub>Busque e inicie a conversa</sub>
</td>
<td width="50%" align="center">
<h4>Codigo Fonte</h4>
<a href="https://github.com/Pedrovargas10/Pokemon-Chat-Bot">Repositorio Github</a><br>
<sub>Codigo aberto para melhorias</sub>
</td>
</tr>
</table>

<br>

## Comandos do assistente

No aplicativo do Telegram, os comandos suportados nativamente sao:

- `/start` — Inicia o assistente e exibe a introducao.
- `/help` — Apresenta todos os comandos listados e suas descricoes.
- `/tierlist <tipo>` — Gera o top 10 atacantes para um tipo especifico utilizando calculos avancados.
- `/raids` — Exibe os chefes que estao nos ginasios agora mesmo.
- `/events` — Resume eventos correntes e programados no jogo.
- `/spotlight` — Informa os detalhes da hora do holofote as tercas-feiras.

## Para desenvolvedores

Rodar o projeto localmente, visualizar arquitetura dos coletores e resolucao de problemas (troubleshooting): **[`docs/DESENVOLVIMENTO.md`](docs/DESENVOLVIMENTO.md)**.
