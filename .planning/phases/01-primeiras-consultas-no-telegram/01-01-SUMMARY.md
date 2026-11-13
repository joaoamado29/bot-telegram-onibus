---
phase: 01-primeiras-consultas-no-telegram
plan: "01"
subsystem: telegram-bot
tags: [python, telegram, sqlite, beautifulsoup4, tdd]

# Dependency graph
requires: []
provides:
  - Caminho ponta a ponta (tracer) de consulta: HTML -> SQLite -> /start -> busca inline -> endereços -> próximas saídas de hoje em Brasília
affects: [01-02, 01-03, 01-04]

actuals:
  tokens: 44000
  tasks: 3
  commits: 4

tech-stack:
  added:
    - python-telegram-bot[job-queue]==22.8
    - tzdata==2026.6
  patterns:
    - Namespace package onibus (core, telegram_handlers)
    - SQLite com duas tabelas relacionais (pontos e horarios) com FK e CHECK constraints
    - Consultas temporais conscientes do fuso America/Sao_Paulo estritamente futuras

key-files:
  created:
    - onibus/core.py
    - onibus/telegram_handlers.py
    - bot.py
    - tests/test_tracer.py
  modified:
    - requirements.txt

key-decisions:
  - "D-02: /start oferece botão inline para busca imediata no chat sem exigir comandos adicionais."
  - "D-03: seleção do artigo abre opções diretas de endereços via botões de callback, compatíveis com inline_message_id sem depender de chosen_inline_result."
  - "D-11: tabelas pontos e horarios preservam posições e calendários com integridade referencial."
  - "D-13: consulta retorna até 3 saídas estritamente futuras do dia corrente no horário de Brasília."

patterns-established:
  - "Carregador nativo de .env no bot.py para manter segredos fora do repositório."
  - "Manipulação segura de callbacks inline sem dependência de message ou effective_chat."

requirements-completed: [DATA-01, DATA-03, DATA-04, DATA-05, DATA-06, TIME-01, TIME-03, BOT-01, BOT-02]

coverage:
  - id: D1
    description: "Parser, persistência e consulta temporal no SQLite compartilhados"
    requirement: "DATA-01"
    verification:
      - kind: unit
        ref: "tests/test_tracer.py#TracerTests.test_html_sqlite_inline_callback"
        status: pass
    human_judgment: false
  - id: D2
    description: "Handlers do Telegram compatíveis com mensagem inline e callback compacto"
    requirement: "BOT-01"
    verification:
      - kind: unit
        ref: "tests/test_tracer.py#TracerTests.test_start_and_application_registration"
        status: pass
    human_judgment: false
  - id: D3
    description: "Validação real no cliente Telegram: /start -> inline -> linha 011 -> ponto -> saídas"
    requirement: "BOT-02"
    verification: []
    human_judgment: true
    rationale: "Exige interação com cliente Telegram real e conta externa via BotFather"

duration: 35min
completed: 2026-11-13
status: complete
---

# Phase 1: Plan 01-01 Summary

**Tracer ponta a ponta implementado com SQLite real, fluxo inline no Telegram e validação de smoke comprovada pelo usuário**

## Performance

- **Duration:** 35 min
- **Started:** 2026-11-13T13:30:00Z
- **Completed:** 2026-11-13T14:28:00Z
- **Tasks:** 3 concluídas
- **Files modified:** 5

## Accomplishments
- Pacotes novos auditados e instalados (`python-telegram-bot` e `tzdata`).
- Módulos `onibus/core.py` e `onibus/telegram_handlers.py` implementados com TDD (5 testes automatizados aprovados).
- Executável `bot.py` criado com suporte a `--coletar-linha` e carregador seguro de `.env`.
- Smoke test interativo executado com sucesso no Telegram: `/start` -> busca inline -> seleção da linha 011 -> escolha de ponto -> saídas em tempo real calculadas no fuso de Brasília.

## Task Commits

1. **Baseline e dependências:** `92d9382` (chore(01-01): preserve existing product baseline)
2. **Testes RED do tracer:** `249eb71` (test(01-01): specify failing end-to-end timetable tracer)
3. **Implementação GREEN:** `ae0f89e` (feat(01-01): implement real timetable SQLite and inline tracer)
4. **Checkpoint e smoke:** `6d571d2` (docs(01-01): persist Telegram smoke checkpoint)

## Files Created/Modified
- `requirements.txt` - inclusão das bibliotecas do bot e timezone
- `onibus/core.py` - parsing, banco SQLite, tabelas `pontos` e `horarios`, consulta temporal
- `onibus/telegram_handlers.py` - handlers de `/start`, inline query e callback inline
- `bot.py` - entrypoint com suporte a `--coletar-linha`, `.env` local e polling
- `tests/test_tracer.py` - testes unitários ponta a ponta simulados

## Decisions Made
- `_carregar_env` adicionado a `bot.py` para injetar variáveis do arquivo `.env` ignorado pelo Git sem adicionar dependências extras.
- Callback inline usa formato compacto `p:numero:revisao:posicao` para caber no limite de 64 bytes do Telegram.

## Deviations from Plan
- Nenhuma alteração estrutural nas interfaces planejadas. Adicionado suporte a `.env` em `bot.py` para viabilizar execução em ambientes locais sem export manual de variáveis de ambiente.

## Next Phase Readiness
- Tracer 01-01 concluído e validado.
- Pronto para os planos paralelos da Onda 2:
  - `01-02-PLAN.md`: Expansão para os cinco pontos, calendários completos, integridade estrita e rollback.
  - `01-03-PLAN.md`: Autocomplete inline, busca com normalização e paginação.
