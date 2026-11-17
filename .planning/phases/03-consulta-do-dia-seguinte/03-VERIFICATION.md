---
phase: 03-consulta-do-dia-seguinte
verified: 2026-11-16T20:25:54Z
status: passed
score: 4/4
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 4
  total: 4
  not_honored: []
covered_files:
  - .planning/phases/03-consulta-do-dia-seguinte/03-01-PLAN.md
  - .planning/phases/03-consulta-do-dia-seguinte/03-01-SUMMARY.md
  - onibus/telegram_handlers.py
  - tests/test_telegram_handlers.py
covered_digest: "v4:sha256:91c1147822eec310096c2553dcf0147dfcc2b5b5352bad7282c43380e1992e05"
human_verification: []
---

# Verificação da Fase 3 — Consulta do dia seguinte

O fluxo foi verificado no handler com dados persistidos em SQLite e aprovado pelo usuário no Telegram.

## Cobertura do fluxo

| Etapa | Evidência | Resultado |
|---|---|---|
| Selecionar um ponto após a última saída | `test_fim_da_sexta_abre_horarios_de_sabado` confirma o aviso com a primeira saída daquele ponto e o callback de sábado. | Verificado |
| Abrir os horários de amanhã | `test_amanha_usa_calendario_de_domingo_ou_feriado` confirma domingo e feriado, incluindo a primeira saída às 00:00. | Verificado |
| Navegar e voltar aos endereços | `test_lista_de_amanha_preserva_data_e_pagina_apos_meia_noite` usa os botões retornados pelo handler, verifica a data após a meia-noite, a paginação e o retorno à linha. | Verificado |
| Distinguir calendários indisponíveis | `test_amanha_indisponivel_so_e_oferecido_quando_hoje_encerra` verifica os estados de operação, encerramento e indisponibilidade. | Verificado |

Os quatro testes acima foram executados por nome com `unittest` e passaram.

## Integração e requisitos

- **BOT-06, D-01 e D-02.** O callback de seleção lê hoje e amanhã no mesmo snapshot SQLite após validar ponto e revisão. A mensagem usa o primeiro valor da lista completa de amanhã. Se ele estiver indisponível, o aviso oferece a consulta da data e informa a indisponibilidade.
- **TIME-05 e D-03.** A data de Brasília vem de `proximas_saidas` em `onibus/core.py`. O callback de amanhã carrega a data absoluta e a rota de horários completos conserva essa data durante a paginação. O teste usa horários distintos das duas datas.
- **D-04.** O callback de retorno reutiliza a navegação para os pontos da mesma linha. `build_application` registra `ponto_callback`, que é exercitado diretamente pelos testes de integração de handler.

Os dois arquivos de implementação e teste existem e estão conectados pelo handler. A busca por marcadores de implementação pendente não encontrou bloqueios nos arquivos alterados.

## Aceite no Telegram

O usuário confirmou o aviso, a lista de amanhã e o retorno aos endereços. Depois do aceite, pediu que o número e o nome da linha aparecessem apenas no título. O ajuste de texto foi verificado na suíte de 69 testes.
