---
phase: 02-calend-rio-local-e-consulta-completa
plan: "01"
subsystem: calendar
tags: [python, holidays, sqlite, telegram, offline]
requires:
  - phase: 01-primeiras-consultas-no-telegram
    provides: Consulta temporal e apresentação Telegram
provides:
  - Catálogo offline de feriados nacionais, Ceará e Fortaleza com fontes oficiais
  - Precedência dos feriados no calendário e identificação na resposta Telegram
  - Distinção entre calendário indisponível e saídas encerradas
affects: [02-02, consulta-do-dia-seguinte, alertas]
tech-stack:
  added: []
  patterns: [catálogo imutável local, cálculo gregoriano da Páscoa, exceções anuais separadas]
key-files:
  created: [onibus/holidays.py]
  modified: [onibus/core.py, onibus/telegram_handlers.py, tests/test_schedules.py, tests/test_telegram_handlers.py, README.md]
key-decisions:
  - Feriado prevalece sobre weekday e conserva todos os nomes coincidentes.
  - Exceção de 13/04/2026 não se propaga para outros anos.
  - Revisão anual cabe ao mantenedor antes do novo ano civil.
requirements-completed: [TIME-02, TIME-04]
coverage:
  - id: D1
    description: Feriados reconhecidos selecionam domingos_feriados em Brasília
    requirement: TIME-02
    verification:
      - kind: integration
        ref: tests/test_schedules.py
        status: pass
    human_judgment: false
  - id: D2
    description: Resposta identifica feriado e distingue dados ausentes de dia encerrado
    requirement: TIME-04
    verification:
      - kind: integration
        ref: tests/test_schedules.py
        status: pass
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_callback_em_feriado_mostra_nome_e_data
        status: pass
    human_judgment: false
actuals:
  tokens: 4370
  tasks: 2
  commits: 4
plan_head_before: 1618de4c1817668698902a510aec2dcf540bb90b
plan_head_after: 49c9efc9fba45e1222a2219df8d95cd8a29248be
duration: 8min
completed: 2026-11-15
status: complete
---

# Phase 2 Plan 1: Calendário local de feriados Summary

**Consulta em Brasília usa feriados locais com regras offline, datas móveis e exceção municipal anual rastreável.**

## Accomplishments

- Nove datas nacionais, Data Magna e quatro feriados religiosos municipais reconhecidos sem rede durante a consulta.
- Sexta-feira da Paixão e Corpus Christi calculados a partir da Páscoa gregoriana; colisões preservam todos os nomes.
- Horários ausentes/vazios permanecem indisponíveis; somente uma lista publicada esgotada informa encerramento.
- README registra fontes e revisão anual pelo mantenedor.

## Task Commits

| Tarefa | Commit | Resultado |
|---|---|---|
| 1 — integração inicial (sessão anterior) | beebfae | Data Magna, precedência e resposta Telegram |
| 2 — RED | 371977c | Casos fixos, móveis, colisões, exceção anual e sábado |
| 2 — GREEN | 49c9efc | Catálogo completo, mudança de ano e documentação |

Contagem medida por `git rev-list --count 1618de4..49c9efc`: 4; inclui o commit de pausa `ac0471e` entre sessões. Tokens medidos por caracteres/4 do diff dos seis arquivos de produto/testes/documentação deste plano.

## Verification

- `python -m unittest discover -s tests -p test_schedules.py -v`: 14 testes aprovados.
- `python -m unittest discover -s tests -p test_telegram_handlers.py -v`: 6 testes aprovados.
- `git diff --check -- onibus/holidays.py tests/test_schedules.py README.md`: aprovado.
- RED original: catálogo retornava apenas Data Magna; o alvo `test_feriados_moveis_calculados_offline` executou e falhou em `assertIn`, sem falha de importação/fixture. Evidência existente validada com `check tdd-red-evidence`: `RED_EVIDENCE_OK`. Execução local confirmou as falhas planejadas antes da implementação.

## Official Source Review

- [Lei 662/1949 consolidada, redação Lei 10.607/2002](https://www2.camara.leg.br/legin/fed/lei/1940-1949/lei-662-6-abril-1949-347136-normaatualizada-pl.html).
- [Lei 14.759/2023](https://normas.leg.br/?urn=urn%3Alex%3Abr%3Afederal%3Alei%3A2023-12-21%3B14759).
- [EC estadual 73/2011](https://www2.al.ce.gov.br/legislativo/tramit2011/ec73.htm).
- [Lei municipal 8.796/2003](https://legislacao.pgm.fortaleza.ce.gov.br/images/6/6d/Lei8796-03.pdf).
- [Lei municipal 11.649/2026 e texto original](https://sapl.fortaleza.ce.leg.br/norma/14390): feriado exclusivo de 13/04/2026.
- [Calendário oficial TRE-CE atualizado em 2026](https://www.tre-ce.jus.br/legislacao/compilada/portaria-conjunta/2026/portaria-conjunta-no-3-de-9-de-abril-de-2026): conferência cruzada dos feriados municipais e respectivas bases normativas, sem importar recessos judiciais ou pontos facultativos.

## Deviations from Plan

Nenhuma alteração de escopo. Recuperação manual autorizada preservou a tarefa 1 concluída; estado e roadmap serão atualizados pelo orquestrador.

## Issues Encountered

Git exigiu execução escalada para gravar o índice; commits realizados após autorização da ferramenta. `git diff --check` global encontrou espaço final preexistente em `bot.py:75`, fora do escopo e preservado. Verificação dos arquivos do plano passou.

## Known Stubs

Nenhum stub que impeça o objetivo deste plano.

## Next Phase Readiness

Plano 02-02 pode usar metadados de feriados e estados existentes. Nenhum bloqueio conhecido. Catálogo requer revisão anual conforme README; nenhuma atualização remota acontece durante consulta de passageiro.

## Self-Check: PASSED

Arquivos do plano existem, commits beebfae/371977c/49c9efc estão na ancestralidade de HEAD e ambas as verificações planejadas passaram. Mudanças anteriores de bot.py e onibus/refresh.py foram preservadas.
