---
phase: "03"
slug: consulta-do-dia-seguinte
status: complete
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-16"
---

# Fase 3 — Estratégia de validação

## Infraestrutura

Use unittest, SQLite temporário, relógio injetado e mocks assíncronos de callbacks. A pesquisa registrou 65 testes aprovados na linha de base. O arquivo `tests/test_telegram_handlers.py` já fornece a infraestrutura para os novos casos.

- Comando rápido `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v`
- Suíte completa `.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py -v`

## Frequência

Execute o comando rápido após a tarefa 1. Execute a suíte completa após a tarefa 2 e antes do aceite.

## Mapa de verificação por tarefa

| Tarefa | Onda | Requisito | Referência | Comando | Estado |
|--------|------|-----------|------------|---------|--------|
| 03-01-01 | 1 | BOT-06, TIME-05 | T-03-01, T-03-02 | Rápido | 18 testes aprovados no commit `50f543f`. |
| 03-01-02 | 1 | TIME-05, BOT-06 | T-03-01, T-03-02 | Suíte completa | 69 testes aprovados no commit `9566860`. |

## Aceite no Telegram

Confirme a apresentação do aviso e dos botões em uma conversa real. A automação permanece responsável pelas datas de corte, cenários com dados ausentes e integridade da paginação.

## Conclusão

- [x] Registrar evidência do comando rápido e da suíte completa.
- [x] Confirmar a cobertura automatizada dos requisitos.
