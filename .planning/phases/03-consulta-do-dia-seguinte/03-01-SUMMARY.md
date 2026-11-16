---
phase: 03-consulta-do-dia-seguinte
plan: "01"
subsystem: telegram
tags: [telegram, sqlite, calendario, navegacao]
requires:
  - phase: 02-calend-rio-local-e-consulta-completa
    provides: seleção por calendário, lista datada e paginação
provides:
  - consulta dos horários do dia seguinte no mesmo ponto
affects: [alertas-da-viagem-escolhida]
tech-stack:
  added: []
  patterns: [reutilização do callback datado, snapshot SQLite]
key-files:
  created: []
  modified: [onibus/telegram_handlers.py, tests/test_telegram_handlers.py]
key-decisions:
  - "A primeira partida usa a lista completa, que inclui 00:00."
  - "O botão carrega a data civil absoluta e abre a lista paginada existente."
requirements-completed: [TIME-05, BOT-06]
completed: 2026-11-16
status: complete
commits: 2
plan_head_before: 78575e7ef6438136a45d311f6ebd4ce7d073f4b6
plan_head_after: 95668608db964ee157c746c2c73cb92de4170740
actuals:
  tokens: 3335
  tasks: 2
  commits: 2
---

# Resumo do plano 03-01 — Consulta do dia seguinte

Ao acabar o serviço de hoje no ponto selecionado, o Telegram informa a primeira saída publicada para amanhã e oferece a lista completa para a data correta. Hoje e amanhã são consultados na mesma leitura do SQLite. Quando faltam dados para amanhã, a mensagem informa a indisponibilidade. O botão **Voltar** reabre os endereços da linha.

## Execução

1. `50f543f` — Aviso de encerramento, botão datado e teste de sexta para sábado.
2. `9566860` — Cobertura de domingo, feriado, saída às 00:00, relógio em UTC, clique após a meia-noite, paginação, indisponibilidade e retorno.

## Verificação

- O teste de sexta para sábado falhou diante do aviso anterior e passou após a implementação. A suíte de handlers passou com 18 testes após a primeira tarefa.
- Os testes da segunda tarefa foram adicionados antes de qualquer ajuste de produção nessa tarefa e passaram com o tracer completo. A suíte completa passou com 69 testes.
- O aceite manual no Telegram permanece pendente.

## Self-Check: PASSED

Os arquivos de produção e teste estão presentes e os dois commits constam no histórico da branch.
