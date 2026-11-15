---
phase: 02-calend-rio-local-e-consulta-completa
plan: "03"
subsystem: telegram
tags: [python, telegram, navigation, gap-closure]
status: complete
gap_closure: true
gap_ids: [G-02-2]
requires:
  - phase: 02-02
    provides: Consulta completa, páginas e retorno aos pontos
provides:
  - Ação Buscar outra linha nos pontos, consulta e páginas completas
affects: [06-melhorar-clareza-das-respostas-do-bot]
tech-stack:
  added: []
  patterns: [reutilização da busca inline no chat atual]
key-files:
  created:
    - .planning/phases/02-calend-rio-local-e-consulta-completa/02-03-red-evidence.json
  modified:
    - onibus/telegram_handlers.py
    - tests/test_telegram_handlers.py
requirements-completed: [BOT-04, BOT-05]
key-decisions:
  - Buscar outra linha usa switch_inline_query_current_chat vazio, como a busca inicial, sem novo callback.
  - Voltar continua dirigido aos pontos da mesma linha; Página 1/1 permanece nesta correção.
duration: 3min
completed: 2026-11-15
coverage:
  - id: G-02-2
    description: Buscar outra linha disponível nos estados da consulta sem remover Voltar
    requirement: BOT-05
    verification:
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_buscar_outra_linha_em_pontos_consultas_e_retorno
        status: pass
      - kind: integration
        ref: tests/test_telegram_handlers.py#test_lista_extensa_pagina_sem_perdas
        status: pass
    human_judgment: false
---

# Phase 02 Plan 03: Buscar outra linha na navegação

**Busca inline de outra linha disponível na escolha de pontos, próximas saídas, estados sem horários e todas as páginas integrais.**

## Accomplishments

- Um helper cria a ação Buscar outra linha com `switch_inline_query_current_chat=""`, reutilizando o mecanismo de `/start` e `inline_query`.
- `criar_artigo`, `_teclado_consulta` e o teclado das páginas incluem a ação adicional; `_voltar` reaproveita o artigo e recebe a ação automaticamente.
- Os callbacks de ponto, revisão, data, página e Voltar não foram alterados.
- Testes verificam ação única com consulta inline vazia e ausência de callback, inclusive em indisponibilidade e dia encerrado. O teste de 1.440 horários confere a ação e Voltar em cada página.

## Verification

- RED antes da alteração de produção: 17 handlers executados, 15 passaram e 2 falharam por ausência de Buscar outra linha (assertion `0 != 1`). Registro: `02-03-red-evidence.json`.
- GREEN focado: 17 testes em `test_telegram_handlers.py`, 0.731s, exit 0.
- Suíte completa: 65 testes, 3.215s, exit 0.
- A assinatura local instalada de `InlineKeyboardButton` confirma o parâmetro reutilizado `switch_inline_query_current_chat`.

## Task Commits

| Tarefa | Commit | Resultado |
|---|---|---|
| 1 | `4a9fda2` | Busca de outra linha em todos os estados da navegação, com testes |

Commit registrado pelo orquestrador após revisão independente sem novos achados.

## Deviations from Plan

- Registro de commits transferido ao orquestrador para evitar chamadas de aprovação Git pendentes. Houve RED e GREEN observados, porém não foi criado commit RED separado.
- Nenhuma alteração de coleta, banco ou calendário da linha 004: o usuário confirmou seu funcionamento somente em dias úteis.

## Known Limitations

- A ação abre a busca inline do Telegram; a interação real do cliente precisa ser confirmada no UAT.
- A navegação multipágina real segue não exercitada pelo usuário, que observou apenas Página 1/1. O teste automatizado percorreu todas as páginas sem perda de horários.
- A apresentação de Página 1/1 permanece para a fase 6, conforme escopo.

## Threat Mitigations

- T-02-05: reutiliza busca inline existente sem introduzir callback, estado mutável ou novo acesso ao banco. Testes preservam Voltar e as revisões já validadas.
- T-02-SC: nenhuma dependência nova.

## Self-Check: PASSED

Arquivos de implementação, testes e evidência existem; 65 testes passaram e commit `4a9fda2` confirmado. Atualização de STATE/ROADMAP/UAT pertence ao orquestrador. Nenhum dado de produção ou alteração anterior foi descartado.
