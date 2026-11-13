---
phase: 01-primeiras-consultas-no-telegram
plan: "02"
subsystem: database-and-parsing
tags: [python, sqlite, beautifulsoup4, tdd, datetime]

# Dependency graph
requires:
  - phase: 01-01
    provides: Tracer ponta a ponta e schemas de pontos e horarios
provides:
  - Suporte completo e íntegro aos cinco pontos e múltiplos calendários
  - Validação estrita de horários HH:MM, descarte de anúncios e ordenação cronológica
  - Atomicidade de transações SQLite com rollback garantido e preservação last-good
affects: [01-03, 01-04]

actuals:
  tokens: 29000
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - Fixture HTML representativa com listas longas (26/27 horários) e anúncios (li.adInList)
    - Verificação estrita de limites temporais e fuso horário de Brasília
    - Testes de integridade transacional (FKs ativas, CHECKs de JSON array, rollback de revisão)

key-files:
  created:
    - tests/fixtures/horarios.html
    - tests/test_scraping.py
    - tests/test_schedules.py
    - tests/test_storage.py
  modified:
    - onibus/core.py

key-decisions:
  - "D-08: publicação válida substitui completamente pontos e horários antigos, removendo calendários obsoletos."
  - "D-09: se a primeira ou segunda coleção obrigatória estiver vazia/ausente, a atualização é rejeitada mantendo os dados anteriores íntegros."
  - "D-11: suporta até 5 posições de pontos com listas independentes e PK composta (numero, calendario)."
  - "D-12: listas com contagens independentes (26 e 27 horários) preservadas sem pareamento incorreto e com descarte de anúncios."
  - "D-13: consultas de saídas futuras respeitam limite estrito (saída de 12:00 expira em 12:00:00)."

patterns-established:
  - "Tratamento de status 'indisponivel' quando um ponto não opera em determinado calendário, distinguindo de 'encerrado'."
  - "Docstrings didáticas e acessíveis em todas as funções de domínio explicando o que faz e por que foi feito."

requirements-completed: [DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, TIME-01, TIME-03]

coverage:
  - id: D1
    description: "Parser HTML preserva múltiplos pontos e calendários, descarta anúncios e filtra HH:MM"
    requirement: "DATA-01"
    verification:
      - kind: unit
        ref: "tests/test_scraping.py#ScrapingParserTests.test_parse_fixture_preserva_pontos_e_descarta_anuncios"
        status: pass
    human_judgment: false
  - id: D2
    description: "Validações de integridade SQLite: FKs, CHECKs de arrays JSON e atomicidade com rollback"
    requirement: "DATA-03"
    verification:
      - kind: unit
        ref: "tests/test_storage.py#StorageIntegrityTests.test_checks_rejeitam_nulo_string_vazia_json_invalido_e_array_vazio"
        status: pass
    human_judgment: false
  - id: D3
    description: "Cálculo temporal das próximas saídas em Brasília com status disponivel, encerrado e indisponivel"
    requirement: "TIME-01"
    verification:
      - kind: unit
        ref: "tests/test_schedules.py#SchedulesTemporalTests.test_instante_estritamente_futuro_limite_12"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-11-13
status: complete
---

# Phase 1: Plan 01-02 Summary

**Expansão para 5 pontos, múltiplos calendários com integridade referencial, descarte de anúncios e limites temporais em Brasília comprovados**

## Performance

- **Duration:** 25 min
- **Started:** 2026-11-13T14:30:00Z
- **Completed:** 2026-11-13T14:32:00Z
- **Tasks:** 2 concluídas
- **Files modified:** 5

## Accomplishments
- Criada fixture representativa em `tests/fixtures/horarios.html` baseada nas linhas reais 004, 011 e 012 com marcadores de anúncio e listas de 26/27 horários.
- Implementada suíte `test_scraping.py` cobrindo extração de pontos, rejeição de menos de 2 ou mais de 5 pontos, descarte de publicidade e ordenação.
- Implementada suíte `test_schedules.py` validando os limites de relógio (11:59:59 vs 12:00:00), conversão segura de UTC para BRT e status `disponivel`/`encerrado`/`indisponivel`.
- Implementada suíte `test_storage.py` demonstrando atomicidade de transações, rollback diante de falhas, remoção de calendários obsoletos e bloqueios de integridade CHECK e FK no SQLite.
- Total de 21 testes automatizados em execução contínua com 100% de aprovação.

## Files Created/Modified
- `tests/fixtures/horarios.html` - HTML fixture com múltiplos pontos e calendários
- `tests/test_scraping.py` - testes unitários do parser HTML
- `tests/test_schedules.py` - testes unitários de regras temporais em Brasília
- `tests/test_storage.py` - testes unitários de integridade relacional e transacional no SQLite
- `onibus/core.py` - inclusão de comentários didáticos detalhados

## Decisions Made
- `proximas_saidas` define status `indisponivel` quando um ponto não possui horários cadastrados para aquele tipo de dia (ex: ponto secundário que não opera aos domingos), preservando a clareza para a fase 2.
- Adicionadas docstrings didáticas em todas as funções públicas e privadas de `onibus/core.py`.

## Next Phase Readiness
- Plan 01-02 concluído.
- Pronto para executar o plano `01-03-PLAN.md` (autocomplete inline, normalização de termos e paginação).
