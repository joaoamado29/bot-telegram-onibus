---
phase: "02"
slug: calend-rio-local-e-consulta-completa
status: verified
threats_open: 0
asvs_level: 1
created: "2026-11-15"
---

# Fase 02 — Segurança

## Trust Boundaries

| Fronteira | Controle |
|---|---|
| Catálogo legal → calendário → SQLite → Telegram | Catálogo local rastreável; calendário fechado; estados distintos |
| Callback Telegram → revisão/ponto → mensagem | Fullmatch, intervalo, snapshot SQLite e paginação limitada |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|---|---|---|---|---|---|---|
| T-02-01 | Tampering | holidays.py | medium | mitigate | Metadados imutáveis e fontes legais; exceções separadas; testes de datas | closed |
| T-02-02 | Tampering | core.py | medium | mitigate | Feriado precede weekday; ausência/vazio distinto de encerramento; testes determinísticos | closed |
| T-02-03 | Tampering | telegram_handlers.py | medium | mitigate | Fullmatch, revisão/endereço em snapshot, validação de data/página, alertas seguros; teste concorrente WAL | closed |
| T-02-04 | Denial of Service | paginação | low | mitigate | Orçamento real de 4096 caracteres por página; 1440 horários testados sem perdas | closed |
| T-02-05 | Tampering | navegação de linha | medium | mitigate | Busca inline existente com switch_inline_query_current_chat vazio; sem novo callback ou estado; revisão independente e 17 testes de handlers verdes | closed |
| T-02-SC | Tampering | dependências | low | accept | Bibliotecas existentes; nenhuma dependência nova nesta fase | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| R-02-SC | T-02-SC | Nenhuma dependência nova; uso das bibliotecas existentes aprovadas | Planos 02-01, 02-02 e 02-03 aprovados | 2026-11-13 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---|---|---|---|
| 2026-11-15 | 5 | 5 | 0 | gsd-security-auditor + registro pelo orquestrador |
| 2026-11-15 | 6 | 6 | 0 | Revisão incremental 02-03, T-02-05 confirmada |

Auditor verificou T-02-01..04 em código/testes; T-02-SC foi encerrada ao persistir a aceitação já declarada nos planos. Não foi criada nova aceitação de risco. T-02-05 verificada na revisão incremental sem mudança das fronteiras de confiança.

## Sign-Off

- [x] Todas as ameaças têm disposição.
- [x] Risco aceito documentado.
- [x] threats_open: 0, limiar high.
- [x] status: verified.
