---
phase: "04"
slug: alertas-da-viagem-escolhida
status: complete
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-16"
---

# Fase 4 — Estratégia de validação

## Infraestrutura

Usar unittest no venv, SQLite temporário, relógio injetado e JobQueue simulada. Os testes seguem os callbacks emitidos pelos handlers, inspecionam os instantes e executam os callbacks agendados sem esperar a passagem do tempo.

- Comando rápido `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v`
- Suíte completa `.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py -v`

Execute o comando rápido após o tracer e a suíte completa após cada expansão. Saída diferente de zero ou nenhum teste coletado indica falha.

## Mapa de verificação

| Tarefa | Onda | Requisitos | Ameaças | Comando | Evidência automatizada |
|--------|------|------------|---------|---------|-------------------|
| 04-01-01 | 1 | BOT-03, BOT-07, ALERT-01, ALERT-02, ALERT-04 | T-04-01, T-04-02, T-04-03 | Rápido | Fluxo inline para privado, destino correto, 11h50, 11h55 e 12h. |
| 04-01-02 | 1 | ALERT-02, ALERT-03, ALERT-04 | T-04-02, T-04-03 | Suíte completa | Elegibilidade com segundos, atalho vencido, todos os intervalos e final avulso. |
| 04-01-03 | 1 | BOT-07, ALERT-01, ALERT-04 | T-04-01, T-04-02, T-04-03 | Suíte completa | Titularidade, dois usuários, confirmações concorrentes, falha parcial e jobs obsoletos. |

## Aceite no Telegram

1. Abra uma consulta inline para uma linha e um ponto com próxima saída. Toque em Notificar e confira se a configuração abre no chat privado após iniciar a conversa.
2. Escolha uma viagem, ative um atalho disponível ou o aviso final e confira o texto de confirmação e a entrega no privado. Os horários e a cadência combinados também têm testes automatizados com relógio controlado.
3. Com uma viagem ativa, escolha outra e confira se aparece Substituir alerta. Confirme e acompanhe a nova viagem. A recuperação após falha parcial e os cliques simultâneos são exercitados na suíte.

## Conclusão

- [x] Registrar evidência dos testes por tarefa. A suíte de handlers passou com 23 testes e a suíte completa com 74 testes após `a555b74`.
- [ ] Confirmar o aceite no aplicativo.
