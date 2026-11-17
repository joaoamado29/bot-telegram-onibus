---
status: testing
phase: 04-alertas-da-viagem-escolhida
source: [04-01-SUMMARY.md, 04-VERIFICATION.md]
started: 2026-11-16
updated: 2026-11-17
---

## Current Test

number: 2
name: Aviso no horário da saída
expected: |
  Com menos de 10 minutos, Voltar reabre a escolha de horário.
  Só no horário da saída agenda apenas a mensagem final no privado.
awaiting: user response

## Tests

### 1. Ativar e receber alertas no privado
expected: O botão Notificar abre a configuração no privado. O atalho de 10 minutos gera a confirmação, dois avisos e a mensagem final no horário da saída.
result: pass

### 2. Aviso no horário da saída
expected: Com menos de 10 minutos e uma saída futura, o bot avisa que está em cima da hora, permite voltar à escolha de horário ou receber apenas o aviso final.
result: pending
note: O usuário apontou a ausência de Voltar. O botão foi adicionado e está pendente de conferência no Telegram.

### 3. Substituir alerta
expected: Com um alerta ativo, o bot oferece Substituir alerta. A sequência da nova viagem passa a valer após a confirmação.
result: pending

## Summary

total: 3
passed: 1
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps

Nenhuma registrada.
