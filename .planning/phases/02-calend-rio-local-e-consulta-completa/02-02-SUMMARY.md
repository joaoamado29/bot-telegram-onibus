---
phase: 02-calend-rio-local-e-consulta-completa
plan: "02"
subsystem: telegram
tags: [python, sqlite, telegram, pagination]
status: complete
requires:
  - phase: 02-01
    provides: Calendário local e metadados de feriado
provides:
  - Lista integral por ponto, calendário e data preservada entre callbacks
  - Paginação em mensagens de até 4096 caracteres
  - Retorno aos endereços da mesma linha
affects: [03-consulta-do-dia-seguinte]
tech-stack:
  added: []
  patterns: [callbacks com data explícita, SQLite em asyncio.to_thread]
key-files:
  created: []
  modified:
    - onibus/core.py
    - onibus/telegram_handlers.py
    - tests/test_telegram_handlers.py
requirements-completed: [BOT-04, BOT-05]
key-decisions:
  - A data YYYYMMDD acompanha o callback da lista integral para preservar o calendário após meia-noite.
  - Voltar reconstrói o mesmo artigo de endereços usando a revisão atual validada no SQLite.
duration: 25min
completed: 2026-11-15
coverage:
  - id: D1
    description: Lista integral preserva passados, feriado, calendário e data
    requirement: BOT-04
    verification:
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_ver_horarios_inclui_passados_e_preserva_data
        status: pass
    human_judgment: false
  - id: D2
    description: Paginação preserva 1440 horários sem duplicar ou truncar
    requirement: BOT-04
    verification:
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_lista_extensa_pagina_sem_perdas
        status: pass
    human_judgment: false
  - id: D3
    description: Voltar mantém linha e permite escolher outro endereço
    requirement: BOT-05
    verification:
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_voltar_reconstroi_enderecos_e_permite_outro_ponto
        status: pass
    human_judgment: false
---

# Phase 02 Plan 02: Consulta completa e retorno aos pontos

**Lista integral identificada por ponto/data/calendário, páginas sem perda de horários e retorno aos endereços da mesma linha.**

## Accomplishments

- `ConsultaSaidas.todos_horarios` preserva a lista publicada; `horarios` mantém até três saídas futuras.
- Botões Ver horários/Voltar na consulta inicial; páginas completas repetem identificação e mantêm navegação inline.
- Callbacks usam fullmatch, campos limitados, posição 1..5, data válida, página no intervalo e revisão validada no banco.
- Banco acessado e conexão fechada dentro das funções síncronas chamadas via `asyncio.to_thread`.

## Verification

- `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py' -v`: **64 testes passaram**, última execução 3.027s.
- 16 testes de handlers cobrem fluxo completo, 1440 horários, volta/outro ponto, data preservada após meia-noite, feriado, indisponibilidade e callbacks inválidos/obsoletos, snapshot concorrente, alertas claros e limites reais de mensagem.
- RED real preservado em `02-02-list-red.json`; classifier retornou `RED_EVIDENCE_OK`: 8 testes, 6 pass, 2 fail pela ausência do botão Ver horários.

## Task Commits

| Tarefas | Commit | Resultado |
|---|---|---|
| 1 e 2, incluindo correções da revisão | `5fd45d7` | Lista completa, paginação, retorno e callbacks consistentes |

O orquestrador registrou as duas tarefas juntas após concluir e revisar as correções. Não houve commit RED separado nem separação de commits por tarefa; o desvio é registrado abaixo.

## Deviations from Plan

- Commits transferidos ao orquestrador por instrução explícita; RED/GREEN observado, porém commit RED separado não produzido devido à aprovação pendente. `tdd_mode=false` conforme init; desvio de registro deve permanecer visível.
- Testes de Voltar foram escritos após implementação inicial do retorno; validam comportamento, mas não tiveram RED próprio. Não declarar sequência TDD integral para tarefa 2.

## Correções da revisão

- CR-01: `BEGIN` explícito antes da validação da revisão mantém os SELECTs de revisão, pontos e horários no mesmo snapshot. Teste determinístico em WAL publica revisão 2 entre validação e consulta e confirma endereço/horários da revisão 1.
- WR-01: data impossível e página fora do intervalo respondem uma única vez com alerta em português; nenhuma edição indevida.
- WR-02: orçamento calculado com cabeçalho e rótulo da página efetivamente emitidos. Endereço de 3950 caracteres abre a lista completa; identificação realmente excessiva produz alerta claro preservando mensagem/Voltar existentes.
- RED antes das correções: 16 testes de handlers, quatro assertions falharam pelos achados previstos. GREEN final: 64/64 testes.

## Known Limitations

- Se a identificação e um único horário não couberem em 4096 caracteres, a lista integral mantém a mensagem existente e informa a limitação por alerta, sem truncar o endereço.
- Validação visual no Telegram real permanece a cargo da verificação da fase.

## Self-Check: PASSED

Arquivos de produção e testes existem; 64 testes verdes, revisão independente clean com três achados corrigidos e commit `5fd45d7` confirmado. Validação visual real no Telegram continua pendente. STATE/ROADMAP/REQUIREMENTS são mantidos pelo orquestrador.
