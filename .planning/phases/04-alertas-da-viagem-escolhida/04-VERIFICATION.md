---
phase: 04-alertas-da-viagem-escolhida
verified: 2026-11-16
status: passed
score: 6/6
behavior_unverified: 0
overrides_applied: 0
covered_files:
  - .planning/phases/04-alertas-da-viagem-escolhida/04-01-PLAN.md
  - .planning/phases/04-alertas-da-viagem-escolhida/04-01-SUMMARY.md
  - onibus/alertas.py
  - onibus/telegram_handlers.py
  - tests/test_alertas.py
  - tests/test_telegram_handlers.py
covered_digest: "v4:sha256:ae69b2e7a49104629bae3b780fb437ef5b868fbdde624d5845d2e2cadacc621b"
re_verification:
  previous_status: human_needed
  previous_score: 4/6
  gaps_closed:
    - Atalho vencido e agendamento do aviso final verificados pelo handler.
    - Substituição, titularidade e confirmação concorrente verificadas pelo handler.
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Abrir Notificar em consulta inline real, iniciar o chat privado, escolher uma saída e ativar o aviso."
    expected: "O chat privado apresenta os horários, confirma a linha e recebe contagens e aviso final."
    why_human: "O teste simula a API de callback, o cliente Telegram e a execução da fila."
  - test: "Escolher uma saída a menos de 10 minutos e conferir o alerta final."
    expected: "O bot avisa que está em cima da hora, oferece o aviso no horário da saída e envia somente esse alerta."
    why_human: "A interface e a entrega deste modo ainda aguardam aceite."
  - test: "Com alerta ativo, escolher outra saída e confirmar Substituir alerta."
    expected: "O alerta anterior permanece até a confirmação e a nova sequência passa a ser a única ativa."
    why_human: "Os testes de serviço e handler simulam o Telegram e a fila. Falta o aceite no aplicativo."
---

# Verificação da Fase 4 — Alertas da viagem escolhida

| Critério | Resultado | Evidência |
|---|---|---|
| Escolher uma saída apresentada pelo fluxo de Notificar | Verificado com API simulada | `test_notificar_abre_privado_e_agenda_avisos` percorre seleção, callback inline, /start, partida e antecedência. |
| Enviar aos 10 e 5 minutos para partida ao meio-dia | Verificado | O mesmo teste confere instantes, destino, textos e mensagem final. |
| Filtrar os quatro atalhos e oferecer somente saída quando nenhum cabe | Verificado | `test_atalhos_limites_e_sequencias` cobre limites em segundos, 0/15/20/30 e a fila. `test_notificar_substitui_com_confirmacao_e_revalida_atalho_expirado` aciona um atalho vencido e confirma que a nova opção agenda um único job após seleção. |
| Encerrar a sequência no horário da saída | Verificado | O teste integrado confere a entrega final. `test_falha_no_aviso_final_libera_vaga` confirma a liberação na falha de envio. |
| Isolar o estado dos passageiros durante navegação e entrega | Verificado | O teste de serviço comprova que a troca preserva o outro dono. O teste de handler rejeita tentativas de seleção e substituição por conta diferente. |
| Substituir mediante confirmação, preservando o alerta atual em falha | Verificado | O teste de serviço cobre falha parcial, preservação do alerta anterior e job obsoleto. O teste de handler aciona duas confirmações concorrentes e comprova que apenas uma troca é publicada. |

## Integração

- BOT-03 e ALERT-01. `build_application` registra `ponto_callback` e `start`. O ramo de próximos horários cria a referência a partir da consulta SQLite. O callback inline gera uma intenção de titularidade individual, e o /start privado fornece o chat de destino.
- BOT-07. `Alertas` armazena o alerta pelo usuário. A troca compara a identidade imediatamente antes de publicar os jobs em um trecho síncrono. A consulta revalida revisão, posição, data e horário publicado.
- ALERT-02, ALERT-03 e ALERT-04. `opcoes_antecedencia` seleciona os atalhos pelo relógio. `agendar` ancora os jobs na saída, e `_entregar` confere a identidade e entrega ao chat da viagem.

## Testes executados

- `.venv/Scripts/python.exe -m unittest discover -s tests -p test_alertas.py -v` — 3 aprovados.
- `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -k notific -v` — 2 aprovados.

O usuário confirmou no Telegram a entrega no privado com o atalho de 10 minutos, o retorno à escolha de horário após a correção de Voltar, o aviso final avulso e a substituição. A suíte de 74 testes passou após a correção.
