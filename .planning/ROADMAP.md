# Roadmap: Bot Telegram Ônibus

## Overview

A primeira entrega conecta a coleta detalhada ao Telegram para escolher uma linha, selecionar um ponto e consultar próximas saídas. As entregas seguintes completam o calendário local e a navegação, a consulta de amanhã, os alertas por viagem e a continuidade desses alertas após reinício. Cada fase inclui dados, regras, interação e verificações necessários à capacidade que entrega; não há fases isoladas de banco, parser ou interface. O escopo é composto pelos 24 requisitos aprovados em `.planning/REQUIREMENTS.md`.

Este roadmap foi aprovado pelo usuário; nenhum plano de implementação foi executado.

## Phases

- [ ] **Phase 1: Primeiras consultas no Telegram** - Escolher linha e ponto e consultar próximas saídas usando horários coletados e persistidos.
- [ ] **Phase 2: Calendário local e consulta completa** - Consultar o calendário correto em feriados, ver todos os horários e voltar entre os pontos.
- [ ] **Phase 3: Consulta do dia seguinte** - Receber aviso de fim das saídas e consultar amanhã separadamente.
- [ ] **Phase 4: Alertas da viagem escolhida** - Escolher uma saída, informar antecedência e receber contagens e aviso final.
- [ ] **Phase 5: Continuidade e cancelamento dos alertas** - Manter alertas futuros após reinício e cancelar acompanhamentos pelo Telegram.

## Phase Details

### Phase 1: Primeiras consultas no Telegram
**Goal:** O passageiro inicia o bot, escolhe uma linha e um endereço e recebe até três próximas saídas do ponto no horário de Brasília, a partir dos dados reais coletados.
**Mode:** mvp
**Depends on:** Nenhuma (primeira fase).
**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, TIME-01, TIME-03, BOT-01, BOT-02
**Success Criteria:**
1. O usuário envia `/start`, escolhe uma linha do catálogo e recebe os endereços daquela linha para selecionar um ponto.
2. Ao escolher o endereço em um dia cujo calendário esteja disponível, o usuário recebe até três saídas futuras de hoje em ordem crescente, calculadas em `America/Sao_Paulo`; se restarem uma ou duas, recebe apenas essas saídas.
3. Os horários apresentados pertencem ao endereço e ao calendário publicados: uma página com listas de 26 e 27 horários preserva ambas integralmente, sem parear viagens pelo índice nem incorporar anúncios.
4. O responsável pela coleta consegue consultar, após reabrir o banco, os endereços e listas independentes das cinco posições nas duas tabelas solicitadas; uma relação sem registro correspondente é rejeitada pela chave estrangeira.
5. Uma coleta com a primeira ou segunda coleção obrigatória vazia não grava um conjunto inválido nem substitui horários por valores inventados.
**Plans:** TBD
**UI hint:** yes

Escopo incremental: a consulta inicial reconhece os tipos de dia publicados e o dia da semana; a seleção completa por feriados locais pertence à Phase 2. A primeira entrega não promete calendário de feriados nem notificações antes dessas capacidades serem concluídas. Modelo de identidade, formato das coleções e política de rejeição devem ser definidos ao planejar esta fase, respeitando a representação aprovada.

### Phase 2: Calendário local e consulta completa
**Goal:** O passageiro consulta os horários adequados à data local, incluindo feriados, vê a lista completa do ponto e navega de volta aos outros endereços da linha.
**Mode:** mvp
**Depends on:** Phase 1.
**Requirements:** TIME-02, TIME-04, BOT-04, BOT-05
**Success Criteria:**
1. Em datas verificáveis de dia útil, sábado, domingo e feriado nacional, do Ceará ou de Fortaleza, a consulta seleciona automaticamente o calendário correspondente à data de Brasília.
2. O usuário usa Ver horários e recebe todos os horários do endereço escolhido no dia consultado, preservando a identificação do ponto e do tipo de dia.
3. O usuário usa Voltar e pode escolher outro endereço da mesma linha sem reiniciar a conversa.
4. O usuário recebe mensagens distintas quando faltam dados/calendário e quando um calendário válido já não possui saídas futuras; ausência de tabela não vira uma afirmação de encerramento das saídas.
**Plans:** TBD
**UI hint:** yes

A fonte verificável e a manutenção dos feriados serão definidas no planejamento desta fase. Não presumir que ponto facultativo seja feriado nem inventar calendário ausente na origem.

### Phase 3: Consulta do dia seguinte
**Goal:** Quando as saídas de hoje acabam, o passageiro consegue consultar os horários de amanhã, com a data e o calendário corretos.
**Mode:** mvp
**Depends on:** Phase 2.
**Requirements:** TIME-05, BOT-06
**Success Criteria:**
1. Quando um ponto não tem mais saídas hoje, o usuário recebe aviso de que os horários de hoje terminaram e a opção Ver horários de amanhã.
2. Ao selecionar amanhã, o usuário recebe os horários daquela data, inclusive na passagem de sexta para sábado, de sábado para domingo e na véspera de um feriado abrangido pelo calendário.
3. A resposta identifica amanhã como outra data e não completa as próximas saídas de hoje com horários do dia seguinte; calendário indisponível continua sendo informado como indisponível.
**Plans:** TBD
**UI hint:** yes

### Phase 4: Alertas da viagem escolhida
**Goal:** O passageiro escolhe uma saída e recebe avisos com a antecedência desejada, a cada cinco minutos, até a mensagem final daquela viagem.
**Mode:** mvp
**Depends on:** Phase 3.
**Requirements:** BOT-03, BOT-07, ALERT-01, ALERT-02, ALERT-03, ALERT-04
**Success Criteria:**
1. Após escolher o endereço, o usuário recebe próximas saídas e as opções Notificar, Ver horários e Voltar; em Notificar, escolhe uma saída apresentada e informa a antecedência em minutos.
2. Para saída às 12h e antecedência de 10 minutos, o usuário recebe `Faltam 10 para o onibus!` às 11h50 e `Faltam 5 para o onibus!` às 11h55, no formato aprovado `Faltam {minutos_faltantes} para o onibus!`.
3. Para saída às 12h e antecedência de 12 minutos, o usuário recebe contagens de 12, 7 e 2 minutos às 11h48, 11h53 e 11h58, respectivamente.
4. Às 12h, o usuário recebe `Está no horário do ônibus!`; nenhuma nova contagem é enviada para a viagem encerrada.
5. Dois usuários escolhem linhas, pontos e saídas diferentes sem alterar as escolhas nem os alertas um do outro; navegar após agendar não muda a viagem acompanhada.
**Plans:** TBD
**UI hint:** yes

Definir no planejamento a validação de minutos e a ativação quando o primeiro instante solicitado já tiver passado, preservando a antecedência livre aprovada. Esta fase verifica o fluxo com o processo em funcionamento; a recuperação de reinícios é entregue na Phase 5.

### Phase 5: Continuidade e cancelamento dos alertas
**Goal:** O passageiro mantém o acompanhamento de viagens futuras após reinício do bot e pode interrompê-lo por um botão.
**Mode:** mvp
**Depends on:** Phase 4.
**Requirements:** ALERT-05, ALERT-06
**Success Criteria:**
1. Após um reinício entre duas contagens, o passageiro continua recebendo os avisos futuros e a mensagem final da viagem persistida, sem receber novamente avisos cujo horário já passou.
2. O usuário cancela um alerta por um botão e deixa de receber os próximos avisos e a mensagem final daquele acompanhamento.
3. Reiniciar o bot após cancelar não reativa o alerta; cancelar um acompanhamento não interrompe os alertas de outro usuário.
**Plans:** TBD
**UI hint:** yes

## Progress

**Execution Order:** 1 → 2 → 3 → 4 → 5. Dentro de cada fase, planos independentes podem executar em paralelo conforme `.planning/config.json`; dependências funcionais entre fases permanecem obrigatórias.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Primeiras consultas no Telegram | 0/TBD | Not started | - |
| 2. Calendário local e consulta completa | 0/TBD | Not started | - |
| 3. Consulta do dia seguinte | 0/TBD | Not started | - |
| 4. Alertas da viagem escolhida | 0/TBD | Not started | - |
| 5. Continuidade e cancelamento dos alertas | 0/TBD | Not started | - |

## Requirement Coverage

- Phase 1: 10 requisitos.
- Phase 2: 4 requisitos.
- Phase 3: 2 requisitos.
- Phase 4: 6 requisitos.
- Phase 5: 2 requisitos.
- Total: 24/24 requisitos mapeados, cada um em exatamente uma fase; nenhum órfão.

---
*Created: 2026-11-13; roadmap em modo MVP aprovado pelo usuário.*
