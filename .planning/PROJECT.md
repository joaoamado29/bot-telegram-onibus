# Bot Telegram Ônibus

## What This Is

Um bot de Telegram para consultar horários de ônibus a partir dos dados do Tonoponto. O usuário inicia com `/start`, escolhe a linha e depois um endereço de ponto daquela linha para consultar as próximas três saídas e receber lembretes.

## Core Value

Permitir que o passageiro encontre os próximos horários do ponto escolhido e receba avisos antes da saída selecionada, conforme o horário de Brasília e o calendário de operação.

## Requirements

### Validated

- ✓ Coletar número, nome e link das linhas no Tonoponto — existente em `scraping.py`.
- ✓ Persistir as linhas em SQLite, evitando inserções duplicadas por número — existente em `scraping.py`.
- ✓ Consultar as linhas armazenadas pelo terminal — existente em `consulta.py`.

### Active

- [ ] Percorrer os links armazenados para extrair horários, normalmente em tags `li`, e endereços de pontos, normalmente em tags `h2`.
- [ ] Criar tabela de horários com `numero`, `nome`, `horario_ponto1`, `horario_ponto2`, `horario_ponto3`, `horario_ponto4` e `horario_ponto5`; os dois primeiros horários são obrigatórios.
- [ ] Criar tabela de endereços com `numero`, `nome`, `ponto1`, `ponto2`, `ponto3`, `ponto4` e `ponto5`, relacionada à tabela de horários por chave estrangeira comum.
- [ ] Preservar a correspondência entre cada horário e seu endereço de ponto e a separação dos calendários de operação.
- [ ] Iniciar o bot com `/start`, permitir escolher a linha e apresentar os endereços daquela linha.
- [ ] Mostrar os próximos três horários do ponto selecionado com base no horário de Brasília e no calendário correspondente ao dia.
- [ ] Selecionar automaticamente horários de dias úteis, sábados e domingos/feriados.
- [ ] Disponibilizar opções de notificar, ver todos os horários do endereço e voltar à escolha do endereço.
- [ ] Permitir escolher uma saída e um atalho disponível de antecedência, com um alerta ativo por passageiro e opção de substituição.
- [ ] Enviar alertas a cada cinco minutos a partir da antecedência escolhida: "Faltam {minutos_faltantes} para o onibus!".
- [ ] Enviar "Está no horário do ônibus!" no horário da saída e encerrar os alertas daquela viagem.
- [ ] Avisar quando os horários de hoje terminarem e oferecer consulta dos horários do dia seguinte.

### Out of Scope

- Rastreamento GPS e previsão de chegada em tempo real — o escopo confirmado utiliza horários publicados.
- Consulta inicial agregando todas as linhas por endereço — o fluxo confirmado começa pela escolha da linha.
- Alertas recorrentes em outros dias — o escopo confirmado encerra os alertas na saída selecionada.

## Context

- Aplicação existente em Python, com `requests`, Beautiful Soup e SQLite; mapa em `.planning/codebase/`.
- `scraping.py` coleta o catálogo de linhas; `consulta.py` lista os dados persistidos. Ainda não há implementação de bot ou coleta detalhada dos horários nos links.
- O usuário descreve horários entre as informações existentes; a implementação mapeada persiste número, nome, link e `created_at`. A extração estruturada dos horários das páginas detalhadas integra o novo escopo.
- Os seletores `li` e `h2` são indicações do usuário; a estrutura real das páginas deve ser validada antes de definir o parser.
- Links existentes omitem o esquema; o novo coletor precisará reconstruir URLs válidas com validação do domínio de origem.
- O banco atual usa inserção sem atualização; a estratégia de atualização dos novos horários deve ser definida no planejamento.
- Cada coluna `horario_pontoN` guarda uma coleção independente de horários por calendário; não alinhar horários de pontos diferentes pelo índice. As coleções dos pontos 1 e 2 são obrigatórias.
- Considerar feriados nacionais, estaduais do Ceará e municipais de Fortaleza; a fonte verificável do calendário será definida no planejamento.
- Mostrar uma ou duas saídas quando não houver três disponíveis, sem completar a lista com outro dia.
- Atalhos de 10, 15, 20 e 30 minutos conforme o tempo disponível. Se nenhum couber, oferecer aviso no horário da saída.
- Persistir alertas futuros para recuperar após reinício, pular avisos vencidos e oferecer cancelamento.
- Ainda precisam ser definidos no planejamento: identidade/cardinalidade das tabelas, fonte verificável de feriados e tratamento de páginas que não atendem à obrigatoriedade das duas primeiras coleções.
- Exemplo confirmado: saída às 12h e antecedência de 10 minutos gera avisos às 11h50 e 11h55 e mensagem final às 12h.

## Constraints

- **Base existente**: Evoluir o coletor Python e o banco SQLite preservando as linhas já armazenadas.
- **Integridade**: `horario_ponto1` e `horario_ponto2` não podem ficar vazios; as tabelas de horários e endereços devem ter relação por chave estrangeira.
- **Tempo**: Consultas e alertas devem usar o horário de Brasília, com calendário automático por data.
- **Origem dos dados**: Endereços e horários devem vir das páginas referenciadas pelas linhas coletadas.
- **Interface**: A interação do passageiro ocorre pelo Telegram em português, começando pela linha e depois pelo endereço.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Escolher linha antes do endereço | Fluxo explicitamente escolhido pelo usuário | Confirmado |
| Selecionar calendário automaticamente | Evitar que o passageiro escolha manualmente o tipo de dia | Confirmado |
| Consultar próximas três saídas | Dar alternativas próximas ao momento da consulta | Confirmado |
| Alertas a cada cinco minutos e mensagem final | Acompanhar o tempo restante até a viagem selecionada | Confirmado |
| Oferecer amanhã quando hoje terminar | Informar ausência de novas saídas sem misturar datas | Confirmado |
| Duas tabelas relacionadas, com até cinco pontos | Estrutura solicitada pelo usuário | Confirmado; detalhes relacionais pendentes |
| Coleções independentes por ponto e calendário | Páginas reais possuem quantidades diferentes por ponto | Confirmado |
| Feriados nacionais, Ceará e Fortaleza | Calendário automático correspondente à operação local | Confirmado |
| Mostrar menos de três saídas quando necessário | Preservar a data consultada sem inventar horários | Confirmado |
| Atalhos de antecedência e contagem a cada cinco minutos | 10, 15, 20 e 30 minutos conforme o tempo disponível | Confirmado |
| Um alerta ativo por passageiro | O passageiro pode confirmar a substituição de uma viagem acompanhada | Confirmado |
| Recuperar alertas futuros e descartar avisos vencidos | Manter o acompanhamento após reinício sem inundar o usuário | Confirmado |
| Cancelamento de alertas | Permitir interromper o acompanhamento da viagem | Confirmado |

## Evolution

Este documento evolui nas transições de fase e nos marcos do projeto.

Após cada fase: mover requisitos validados para Validated; registrar novos requisitos, exclusões justificadas e decisões; revisar a descrição do produto quando necessário.

Após cada marco: revisar todas as seções, confirmar o valor central, reavaliar exclusões e atualizar o contexto com o estado real do projeto.

---
*Last updated: 2026-11-13 after initialization*
