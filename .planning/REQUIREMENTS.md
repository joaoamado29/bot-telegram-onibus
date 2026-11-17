# Requirements: Bot Telegram Ônibus

**Defined:** 2026-11-13
**Core Value:** Permitir que o passageiro consulte os próximos horários do ponto escolhido e receba avisos antes da saída selecionada, conforme o horário de Brasília e o calendário de operação.

## v1 Requirements

### Coleta e armazenamento

- [ ] **DATA-01**: Coletar endereços e horários das páginas referenciadas pelas linhas existentes no catálogo.
- [ ] **DATA-02**: Associar cada coleção de horários ao ponto e ao calendário publicados na página, descartando anúncios e itens sem horário válido.
- [ ] **DATA-03**: Manter tabela de horários com `numero`, `nome` e `horario_ponto1` até `horario_ponto5`, contendo listas independentes por ponto, separadas por tipo de dia.
- [ ] **DATA-04**: Impedir a gravação de um conjunto de horários quando as coleções de `horario_ponto1` ou `horario_ponto2` estiverem ausentes ou vazias, sem fabricar horários.
- [ ] **DATA-05**: Manter tabela de endereços com `numero`, `nome` e `ponto1` até `ponto5`, relacionada à tabela de horários por chave estrangeira cuja integridade seja aplicada no SQLite.
- [ ] **DATA-06**: Preservar a correspondência entre as posições dos endereços e das coleções de horários, sem inferir viagens comuns pela posição dos horários nas listas.

### Calendário e consulta

- [ ] **TIME-01**: Calcular a data e a hora da consulta no fuso `America/Sao_Paulo` (horário de Brasília).
- [ ] **TIME-02**: Selecionar automaticamente o calendário da data: dias úteis, sábados ou domingos/feriados, considerando feriados nacionais, do Ceará e de Fortaleza.
- [ ] **TIME-03**: Retornar os próximos três horários ainda disponíveis do ponto escolhido no dia consultado, em ordem crescente; retornar um ou dois quando houver menos de três.
- [ ] **TIME-04**: Distinguir dados/calendário indisponíveis de um calendário válido cujas saídas do dia já terminaram.
- [ ] **TIME-05**: Consultar os horários de amanhã usando a data e o calendário correspondentes, sem misturá-los às próximas saídas de hoje.

### Interação Telegram

- [ ] **BOT-01**: O usuário pode iniciar com `/start` e escolher uma linha do catálogo.
- [ ] **BOT-02**: Após escolher a linha, o usuário recebe e pode selecionar os endereços dos pontos daquela linha.
- [x] **BOT-03**: Após selecionar o endereço, o usuário recebe as próximas saídas de hoje e as opções Notificar, Ver horários e Voltar.
- [ ] **BOT-04**: O usuário pode usar Ver horários para consultar todos os horários do endereço escolhido no dia consultado.
- [ ] **BOT-05**: O usuário pode voltar à escolha do endereço da linha selecionada.
- [ ] **BOT-06**: Quando as saídas de hoje terminarem, o usuário recebe aviso e a opção Ver horários de amanhã.
- [x] **BOT-07**: As escolhas de linha, ponto e viagem de um usuário não alteram a navegação ou os alertas de outro usuário.

### Alertas

- [x] **ALERT-01**: O usuário pode escolher uma saída apresentada e ativar um alerta para aquela viagem. Se já houver alerta ativo, pode confirmar sua substituição.
- [x] **ALERT-02**: O usuário recebe o primeiro alerta na antecedência escolhida e os seguintes a cada cinco minutos enquanto a saída for futura, no formato `Faltam {minutos_faltantes} para o onibus!`.
- [x] **ALERT-03**: O bot apresenta os atalhos de 10, 15, 20 e 30 minutos cujo primeiro aviso ainda cabe. Se nenhum couber e a saída for futura, informa que está em cima da hora e oferece somente o aviso no horário da saída.
- [x] **ALERT-04**: No horário da saída, o usuário recebe `Está no horário do ônibus!` e os alertas daquela viagem são encerrados.
- [ ] **ALERT-05**: Após reinício do bot, alertas futuros persistidos são recuperados e avisos cujo horário passou são ignorados.
- [ ] **ALERT-06**: O usuário pode cancelar o acompanhamento de uma viagem por um botão, impedindo os próximos avisos desse alerta.

## v2 Requirements

Nenhum requisito adicional comprometido. Favoritos, recorrência diária e outras fontes/cidades dependem de nova definição de escopo.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rastreamento GPS e previsão em tempo real | O produto consulta horários publicados |
| Escolha inicial por endereço reunindo várias linhas | O fluxo aprovado escolhe primeiro a linha |
| Alertas recorrentes em outros dias | O acompanhamento termina na viagem escolhida |
| Alinhar horários entre pontos pelo índice | A origem publica listas de tamanhos diferentes e não estabelece essa correspondência |
| App separado ou Telegram Mini App | A interação aprovada ocorre na conversa com o bot |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DATA-01 | Phase 1 | Pending |
| DATA-02 | Phase 1 | Pending |
| DATA-03 | Phase 1 | Pending |
| DATA-04 | Phase 1 | Pending |
| DATA-05 | Phase 1 | Pending |
| DATA-06 | Phase 1 | Pending |
| TIME-01 | Phase 1 | Pending |
| TIME-02 | Phase 2 | Pending |
| TIME-03 | Phase 1 | Pending |
| TIME-04 | Phase 2 | Pending |
| TIME-05 | Phase 3 | Pending |
| BOT-01 | Phase 1 | Pending |
| BOT-02 | Phase 1 | Pending |
| BOT-03 | Phase 4 | Complete |
| BOT-04 | Phase 2 | Pending |
| BOT-05 | Phase 2 | Pending |
| BOT-06 | Phase 3 | Pending |
| BOT-07 | Phase 4 | Complete |
| ALERT-01 | Phase 4 | Complete |
| ALERT-02 | Phase 4 | Complete |
| ALERT-03 | Phase 4 | Complete |
| ALERT-04 | Phase 4 | Complete |
| ALERT-05 | Phase 5 | Pending |
| ALERT-06 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

## Acceptance Criteria

- Uma página com anúncios e listas de 26 e 27 horários mantém ambas as listas sem truncamento nem alinhamento artificial.
- Gravação com uma das duas primeiras coleções vazia é rejeitada; relações entre horários e endereços respeitam a chave estrangeira.
- Consulta às 11h de uma data de serviço seleciona o calendário correspondente e retorna até três horários futuros daquele ponto no mesmo dia.
- Consulta sem mais saídas avisa o término do dia e oferece amanhã; falta de calendário não é apresentada como término das saídas.
- Para saída às 12h e antecedência de 10 minutos, avisos às 11h50 e 11h55 precedem a mensagem final às 12h.
- Para saída às 12h consultada às 11h43, aparecem os atalhos de 10 e 15 minutos. Às 11h53, o bot oferece somente o aviso às 12h.
- Reinício recupera apenas os avisos futuros; cancelamento impede os próximos avisos da viagem cancelada.

---
*Requirements defined: 2026-11-13*
*Last updated: 2026-11-13 after roadmap traceability; all 24 v1 requirements remain user-approved, roadmap awaiting approval*
