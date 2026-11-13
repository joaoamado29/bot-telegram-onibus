---
phase: 01-primeiras-consultas-no-telegram
plan: "03"
subsystem: search-and-inline-query
tags: [python, telegram, unicode, sqlite, pagination]

# Dependency graph
requires:
  - phase: 01-01
    provides: Adaptador telegram_handlers e catálogo de linhas publicado
provides:
  - Busca textual com normalização Unicode NFKD (sem acentos e case-insensitive)
  - Paginação controlada de 10 em 10 itens com next_offset estável
  - Validação estrita de callbacks inline com expiração de revisões obsoletas
affects: [01-04]

actuals:
  tokens: 25000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Normalização Unicode NFKD registrada diretamente no SQLite via conn.create_function
    - Paginação baseada em limit+1 para detecção limpa de fim de catálogo
    - Tratamento de mensagens exclusivamente inline no Telegram via inline_message_id

key-files:
  created:
    - onibus/search.py
    - tests/test_search.py
    - tests/test_telegram_handlers.py
  modified:
    - onibus/telegram_handlers.py

key-decisions:
  - "D-01: busca por número ou nome parcial apresenta sugestões no formato numero - nome original."
  - "D-02: busca integrada via InlineQuery no chat atual sem necessidade de envio de comandos."
  - "D-03: seleção exibe os endereços da linha com botões compactos vinculados à revisão."
  - "D-04: busca sem acentos e case-insensitive (joao encontra São João)."
  - "D-05: paginação de 10 em 10 resultados com next_offset para rolagem contínua."

patterns-established:
  - "Rejeição segura de callbacks com revisões divergentes com aviso amigável de expiração."
  - "Docstrings didáticas e código modular em conformidade com as regras da equipe."

requirements-completed: [BOT-01, BOT-02]

coverage:
  - id: D1
    description: "Busca textual com normalização de acentos e ordenação estável por número"
    requirement: "BOT-01"
    verification:
      - kind: unit
        ref: "tests/test_search.py#SearchTests.test_busca_por_nome_sem_acentos_e_case_insensitive"
        status: pass
    human_judgment: false
  - id: D2
    description: "Paginação de sugestões inline de 10 em 10 itens com next_offset vazio no término"
    requirement: "BOT-01"
    verification:
      - kind: unit
        ref: "tests/test_search.py#SearchTests.test_paginacao_dez_por_pagina_com_next_offset"
        status: pass
    human_judgment: false
  - id: D3
    description: "Manipulação de callbacks inline sem message e rejeição de revisões desatualizadas"
    requirement: "BOT-02"
    verification:
      - kind: unit
        ref: "tests/test_telegram_handlers.py#TelegramHandlersTests.test_ponto_callback_inline_sem_message_retorna_saidas"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-11-13
status: complete
---

# Phase 1: Plan 01-03 Summary

**Busca inline com normalização de acentos, paginação de 10 itens e tratamento resiliente de callbacks inline implementados**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-13T14:33:00Z
- **Completed:** 2026-11-13T14:35:00Z
- **Tasks:** 2 concluídas
- **Files modified:** 4

## Accomplishments
- Criado o módulo `onibus/search.py` com `normalizar_busca` e `buscar_sugestoes`, integrando função customizada de normalização no SQLite.
- Garantido que apenas linhas com pontos publicados apareçam nos resultados inline, preservando acentos originais na exibição.
- Implementada paginação com `limit+1` entregando exatamente 10 itens por lote e informando `next_offset` vazio no fim da lista (testado com 25 linhas em lotes de 10, 10 e 5).
- Atualizado `onibus/telegram_handlers.py` para usar `buscar_sugestoes` e lidar defensivamente com offsets maliciosos, callbacks corrompidos ou revisões desatualizadas sem tracebacks.
- Suíte completa de 33 testes automatizados aprovada com 100% de sucesso.

## Files Created/Modified
- `onibus/search.py` - normalização Unicode NFKD e busca paginada
- `onibus/telegram_handlers.py` - integração com o serviço de busca e tratamento de callbacks inline
- `tests/test_search.py` - testes unitários de busca, normalização e paginação
- `tests/test_telegram_handlers.py` - testes unitários de /start, inline_query e callbacks inline

## Decisions Made
- O termo vazio retorna as primeiras linhas disponíveis com pontos publicados, permitindo explorar opções logo ao abrir o autocomplete.
- A função customizada `normalizar_texto` no SQLite evita ter que carregar todo o banco para a memória Python para fazer buscas case/accent-insensitive.

## Next Phase Readiness
- Plan 01-03 concluído.
- Pronto para executar o plano final da Fase 1: `01-04-PLAN.md` (agendamento semanal de coleta, tentativas automáticas com retry, e smoke test final).
