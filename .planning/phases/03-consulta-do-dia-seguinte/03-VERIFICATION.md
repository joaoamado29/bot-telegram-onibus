---
phase: 03-consulta-do-dia-seguinte
verified: 2026-11-16T20:25:54Z
status: human_needed
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
covered_digest: "v4:sha256:5311339cdafd4574b31fee09f236754980652fb6ece4139ab4129d1a248d803c"
human_verification:
  - test: "No Telegram, selecionar uma linha e um ponto após a última saída do dia, abrir Ver horários de amanhã, avançar se houver mais páginas e tocar em Voltar."
    expected: "O aviso anuncia a primeira saída publicada para amanhã naquele ponto. A lista mostra a data e o calendário de amanhã. Voltar exibe os endereços da mesma linha."
    why_human: "Os testes executam o handler com chamadas do Telegram simuladas. A interação no aplicativo ainda precisa de aceite."
---

# Verificação da Fase 3 — Consulta do dia seguinte

O fluxo foi verificado no handler com dados persistidos em SQLite. O aceite no aplicativo Telegram está pendente.

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

Após a última saída de um ponto, verifique o aviso no aplicativo e abra **Ver horários de amanhã**. Confira a data, o calendário e a primeira saída. Se houver mais de uma página, navegue pela lista. **Voltar** deve abrir os endereços da mesma linha.
