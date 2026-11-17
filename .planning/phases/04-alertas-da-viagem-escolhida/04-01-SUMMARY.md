---
phase: 04-alertas-da-viagem-escolhida
plan: "01"
subsystem: telegram
tags: [telegram, jobqueue, alertas, horario-de-brasilia]
requires:
  - phase: 03-consulta-do-dia-seguinte
    provides: consulta paginada e navegação por callbacks
provides:
  - configuração privada e agendamento de alertas por viagem
  - substituição explícita de um alerta ativo por passageiro
affects: [continuidade-e-cancelamento-dos-alertas]
tech-stack:
  added: []
  patterns: [tokens opacos de curta duração, JobQueue, troca por identidade]
key-files:
  created: [onibus/alertas.py, tests/test_alertas.py]
  modified: [onibus/telegram_handlers.py, tests/test_telegram_handlers.py]
key-decisions:
  - "O destino é o chat privado observado ao abrir o link de Notificar."
  - "A substituição publica a nova identidade somente após criar todos os jobs."
requirements-completed: [BOT-03, BOT-07, ALERT-01, ALERT-02, ALERT-03, ALERT-04]
completed: 2026-11-16
status: complete
commits: 2
plan_head_before: 72edb4ebb532ffc9181ab249d1b76384c1649950
plan_head_after: a555b74fe504c178eae3cceeb52736b0fb51c205
actuals:
  tokens: 6717
  tasks: 3
  commits: 2
---

# Resumo do plano 04-01 — Alertas da viagem escolhida

O botão **Notificar** abre a configuração privada da viagem selecionada. O bot mostra as antecedências ainda válidas, envia avisos em intervalos de cinco minutos e libera a vaga ao emitir a mensagem final. Uma nova viagem só substitui a atual após confirmação e agendamento bem-sucedido.

## Verificação

- O teste de integração percorreu o callback da consulta inline, o link privado, a escolha da saída e as três entregas no chat privado.
- Os testes do serviço cobriram limites dos atalhos, agendamento apenas no horário da saída, falha parcial da fila, substituição, isolamento e liberação da vaga quando o envio final falha.
- O teste adicional em `a555b74` valida no handler a revalidação de um atalho vencido, o agendamento de somente um aviso final, o botão Substituir alerta, a rejeição de outro usuário e duas confirmações concorrentes com um único sucesso.
- A suíte completa aprovou 74 testes. O aceite no aplicativo Telegram permanece pendente.

## Desvios

- Os prefixos de alerta são encaminhados pelo callback já registrado, que continua responsável pela navegação existente. Isso preserva os três handlers do grupo original.
- A implementação e a cobertura das três tarefas foram registradas juntas no commit `988a88f`. O histórico contém uma verificação verde do tracer e da suíte, com os testes produzidos depois da primeira edição do código.

## Self-Check: PASSED

Os quatro arquivos declarados existem e os dois commits de execução constam na branch atual.
