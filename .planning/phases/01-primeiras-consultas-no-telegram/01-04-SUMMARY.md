---
phase: 01-primeiras-consultas-no-telegram
plan: "04"
subsystem: scheduler-and-lifecycle
tags: [python, telegram, scheduler, jobqueue, retry, sqlite]

# Dependency graph
requires:
  - phase: 01-02
    provides: Suporte a 5 pontos, múltiplos calendários e transações atômicas no SQLite
  - phase: 01-03
    provides: Busca normalizada e paginação de sugestões inline
provides:
  - Coordenador de coleta com bootstrap automático quando a base está vazia
  - Agendamento semanal aos domingos às 01:00 (horário de Brasília) via JobQueue
  - Recuperação resiliente de falhas com retries limitados (5, 15, 60 min) e lock assíncrono
  - Documentação operacional completa e validação de ponta a ponta no cliente Telegram
affects: [02-calendario-de-operacao-e-feriados]

actuals:
  tokens: 30000
  tasks: 3
  commits: 2

tech-stack:
  added: []
  patterns:
    - Agendamento em segundo plano acoplado ao ciclo de vida do python-telegram-bot
    - Execução de tarefas de rede e banco fora do event loop via asyncio.to_thread
    - Serialização com asyncio.Lock e retries finitos com deduplicação de jobs

key-files:
  created:
    - onibus/refresh.py
    - tests/test_refresh.py
    - tests/test_application.py
  modified:
    - bot.py
    - README.md

key-decisions:
  - "D-06: atualização semanal agendada para todo domingo às 01:00 no fuso America/Sao_Paulo."
  - "D-07: falhas de linha preservam dados anteriores (last-good) e disparam retries em 5, 15 e 60 minutos sem travar o bot."
  - "D-08: nova publicação válida substitui completamente horários antigos e atualiza consultas."
  - "D-09: linhas com coleções obrigatórias vazias/inválidas são rejeitadas isoladamente sem impactar as demais."
  - "D-10: banco sem horários dispara coleta inicial automática em segundo plano."

patterns-established:
  - "Uso de conexões curtas e locais com SQLite dentro dos workers de thread."
  - "Instruções claras de ambiente e segurança no README.md sem expor nenhum segredo."

requirements-completed: [DATA-01, DATA-04, DATA-06, BOT-01, BOT-02]

coverage:
  - id: D1
    description: "Coordenador de coleta com agendamento de domingo 01h e retries a 5, 15 e 60 minutos"
    requirement: "DATA-06"
    verification:
      - kind: unit
        ref: "tests/test_refresh.py#RefreshCoordinatorTests.test_registrar_coletas_agenda_job_semanal_domingo_01h"
        status: pass
    human_judgment: false
  - id: D2
    description: "Preservação de dados válidos anteriores diante de falhas de coleta e isolamento por linha"
    requirement: "DATA-04"
    verification:
      - kind: unit
        ref: "tests/test_refresh.py#RefreshCoordinatorTests.test_falha_em_uma_linha_preserva_anterior_e_agenda_retry"
        status: pass
    human_judgment: false
  - id: D3
    description: "Validação completa do fluxo no cliente Telegram: /start -> busca -> endereços -> próximas saídas"
    requirement: "BOT-02"
    verification: []
    human_judgment: true
    rationale: "Exige confirmação humana da interação real no cliente Telegram com dados do banco e fuso de Brasília"

duration: 30min
completed: 2026-11-13
status: complete
---

# Phase 1: Plan 01-04 Summary

**Coleta automática inicial, agendamento semanal aos domingos, retries resilientes e validação final da Fase 1 comprovada no Telegram**

## Performance

- **Duration:** 30 min
- **Started:** 2026-11-13T14:36:00Z
- **Completed:** 2026-11-13T14:49:00Z
- **Tasks:** 3 concluídas
- **Files modified:** 5

## Accomplishments
- Implementado `onibus/refresh.py` com a classe `CoordenadorColeta`, integrando rotinas de atualização ao `JobQueue` do `python-telegram-bot`.
- Implementada a coleta inicial automática quando o banco não possui horários (`D-10`).
- Implementado o agendamento semanal para domingos às 01:00 horário de Brasília (`D-06`).
- Implementada a política de retries defensiva: até 3 tentativas (a 5, 15 e 60 minutos) por linha, com cancelamento após sucesso e preservação do último conjunto válido em caso de esgotamento (`D-07` e `D-09`).
- Suíte completa de 44 testes automatizados aprovada com 100% de sucesso.
- Validação real no Telegram executada com sucesso pelo usuário, comprovando o fluxo ponta a ponta.

## Files Created/Modified
- `onibus/refresh.py` - coordenação de coletas e retries
- `bot.py` - conexão de coletas ao ciclo de vida da aplicação
- `tests/test_refresh.py` - testes unitários e de integração do coordenador de coletas
- `tests/test_application.py` - testes da aplicação e lifecycle
- `README.md` - documentação de configuração, execução e arquitetura

## Decisions Made
- O processo do bot serializa as coletas com `asyncio.Lock` para garantir que jobs semanais, inicial ou retries não concorram na gravação do SQLite.
- O README orienta a necessidade de manter o processo ativo para o cumprimento da agenda semanal aos domingos.

## Next Phase Readiness
- **Fase 1 100% concluída!**
- Todos os 4 planos da Fase 1 foram entregues, testados e validados no cliente real.
- Pronto para a **Fase 2: Calendário de operação e feriados** (tratar feriados nacionais, estaduais do Ceará e municipais de Fortaleza, e distinguir calendário ausente de fim das saídas).
