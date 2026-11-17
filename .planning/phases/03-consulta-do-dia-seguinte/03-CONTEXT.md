# Fase 3 — Consulta do dia seguinte

**Discussão:** 2026-11-16  
**Status:** Pronta para planejamento

<domain>
## Escopo

Quando acabam as saídas de hoje para o ponto selecionado, o bot oferece a consulta de amanhã para a mesma linha e o mesmo endereço. A data e o calendário são determinados no horário de Brasília.
</domain>

<decisions>
## Decisões

- **D-01.** Quando houver horários publicados para amanhã, usar a mensagem “As saídas de hoje terminaram. A primeira saída de amanhã é às <horário>.” O número e o nome da linha aparecem apenas no título. O horário é a primeira saída de amanhã no ponto selecionado, conforme o calendário daquela data.
- **D-02.** Exibir o botão **Ver horários de amanhã** quando as saídas de hoje terminarem. Se a primeira saída de amanhã estiver indisponível, informar a indisponibilidade em vez de preencher o horário. A falta de dados de hoje recebe o aviso de indisponibilidade já previsto na Fase 2.
- **D-03.** Mostrar a lista completa de amanhã separadamente, identificando a data e o tipo de dia, com a paginação já usada em **Ver horários**.
- **D-04.** O botão **Voltar** na lista de amanhã abre a escolha de endereço da mesma linha.
</decisions>

<canonical_refs>
## Referências

- `.planning/ROADMAP.md`, Fase 3 — critérios de aceite, incluindo viradas de calendário.
- `.planning/REQUIREMENTS.md`, TIME-05 e BOT-06 — consulta por data e opção após o fim das saídas.
- `.planning/phases/02-calend-rio-local-e-consulta-completa/02-CONTEXT.md` — calendário e navegação existentes.
</canonical_refs>

<code_context>
## Código existente

- Reusar a apresentação paginada de **Ver horários**, a seleção de calendário por data e a navegação para a lista de endereços.
</code_context>

<deferred>
## Fases posteriores

- Alertas por viagem pertencem à Fase 4. A revisão geral das mensagens pertence à Fase 6.
</deferred>
