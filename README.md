<p align="center">
  <img src="docs/assets/logopokeguia.jpg" alt="Pokemon Chat Bot — Seu assistente definitivo para PVE no Pokemon GO" width="200" style="border-radius: 50%;">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-ativo-1d7a4a?style=flat-square" alt="Ativo">
  <img src="https://img.shields.io/badge/plataforma-Telegram-1a2744?style=flat-square" alt="Telegram">
  <img src="https://img.shields.io/badge/linguagem-Python%20%C2%B7%20Node.js-d4813a?style=flat-square" alt="Python e Node.js">
</p>

---

<h3 align="center">O conhecimento de um Mestre Pokémon diretamente no seu Telegram.</h3>

<p align="center">
  O <strong>PokéGuia Bot</strong> nasceu para resolver um problema real de quem joga Pokémon GO: a constante busca por informações espalhadas pela internet. Chega de abrir dezenas de abas para saber qual o evento da semana, quem é o chefe da reide ou qual Pokémon usar para dar o maior dano possível. Tudo o que você precisa agora está a um comando de distância, respondido de forma instantânea na palma da sua mão.
</p>

<br>

## Principais Funcionalidades

O bot não apenas coleta informações, mas utiliza regras e lógicas rigorosas para apresentar dados úteis para jogadores de qualquer nível — de novatos a treinadores veteranos:

* **Tier Lists de Altíssima Precisão (eDPS):**  
  Usamos a consagrada *Engine Matemática do DialgaDex* (processada via ponte nativa em Node.js) para calcular o dano real dos atacantes no jogo. Isso significa que as nossas tier lists consideram as reides ativas no momento (Type Affinity), defesa, HP e a velocidade de cada animação de ataque. Você terá a resposta cirúrgica sobre quais são os melhores Pokémon para cada tipo.
  
* **Filtros Dinâmicos e Interativos:**  
  Não quer usar Megas ou Pokémon Sombrosos? Sem problema. O bot traz botões iterativos diretamente no chat do Telegram, permitindo filtrar a tier list em tempo real com apenas um toque, sem a necessidade de digitar comandos complexos.

* **Eventos e Horas do Holofote:**  
  Mantenha-se por dentro do calendário do jogo. O PokéGuia resume de forma elegante os eventos atuais e futuros (coletados de fontes como LeekDuck) e avisa sobre o Pokémon em destaque na terça-feira.

* **Chefes de Reides Atuais:**  
  Saiba exatamente quais chefes estão dominando os ginásios hoje e veja uma lista rápida dos melhores tipos e *counters* para enfrentá-los com eficiência.

<br>

## Como Acessar

A experiência é totalmente focada no Telegram, sem necessidade de baixar novos aplicativos ou se cadastrar em sites.

<table align="center">
  <tr>
    <td align="center">
      <h4>Converse com o Bot</h4>
      <a href="https://t.me/pokeguia_pedro_bot"><strong>t.me/pokeguia_pedro_bot</strong></a><br>
      <sub>Clique para abrir o Telegram</sub>
    </td>
  </tr>
</table>

<br>

## Comandos do Assistente

Ao iniciar uma conversa, os seguintes comandos já estarão à sua disposição:

* `/start` — Inicia o assistente e exibe a mensagem de boas-vindas.
* `/help` — Apresenta todos os comandos listados e suas descrições.
* `/tierlist <tipo>` — Gera o top 10 atacantes para um tipo específico. Aceita filtros avançados via botões no chat.
* `/raids` — Exibe os chefes que estão nos ginásios no momento atual.
* `/events` — Lista os eventos correntes e os próximos que irão começar.
* `/spotlight` — Informa o Pokémon da próxima Hora do Holofote e o bônus semanal.

<br>

## Para Desenvolvedores

O PokéGuia Bot foi construído com Python 3.10+, utilizando um orquestrador agendado (APScheduler) e uma ponte JavaScript para cálculos. 

Se você deseja rodar o projeto localmente, entender a arquitetura dos coletores de dados ou ver o guia de solução de problemas (Troubleshooting), acesse nossa documentação técnica: 
**[`docs/DESENVOLVIMENTO.md`](docs/DESENVOLVIMENTO.md)**
