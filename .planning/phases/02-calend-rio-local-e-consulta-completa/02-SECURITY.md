---
phase: "02"
slug: calend-rio-local-e-consulta-completa
status: verified
threats_open: 0
asvs_level: 1
created: "2026-11-15"
---

# Fase 02 ? Seguran?a

## Trust Boundaries

| Fronteira | Controle |
|---|---|
| Cat?logo legal ? calend?rio ? SQLite ? Telegram | Cat?logo local rastre?vel; calend?rio fechado; estados distintos |
| Callback Telegram ? revis?o/ponto ? mensagem | Fullmatch, intervalo, snapshot SQLite e pagina??o limitada |

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|---|---|---|---|---|---|---|
| T-02-01 | Tampering | holidays.py | medium | mitigate | Metadados imut?veis e fontes legais; exce??es separadas; testes de datas | closed |
| T-02-02 | Tampering | core.py | medium | mitigate | Feriado precede weekday; aus?ncia/vazio distinto de encerramento; testes determin?sticos | closed |
| T-02-03 | Tampering | telegram_handlers.py | medium | mitigate | Fullmatch, revis?o/endere?o em snapshot, valida??o de data/p?gina, alertas seguros; teste concorrente WAL | closed |
| T-02-04 | Denial of Service | pagina??o | low | mitigate | Or?amento real de 4096 caracteres por p?gina; 1440 hor?rios testados sem perdas | closed |
| T-02-SC | Tampering | depend?ncias | low | accept | Bibliotecas existentes; nenhuma depend?ncia nova nesta fase | closed |

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---|---|---|---|---|
| R-02-SC | T-02-SC | Nenhuma depend?ncia nova; uso das bibliotecas existentes aprovadas | Planos 02-01 e 02-02 aprovados | 2026-11-13 |

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|---|---|---|---|---|
| 2026-11-15 | 5 | 5 | 0 | gsd-security-auditor + registro pelo orquestrador |

Auditor verificou T-02-01..04 em c?digo/testes; T-02-SC foi encerrada ao persistir a aceita??o j? declarada nos planos. N?o foi criada nova aceita??o de risco.

## Sign-Off

- [x] Todas as amea?as t?m disposi??o.
- [x] Risco aceito documentado.
- [x] threats_open: 0, limiar high.
- [x] status: verified.
