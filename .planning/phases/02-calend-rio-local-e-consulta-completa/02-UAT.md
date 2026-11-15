---
status: testing
phase: 02-calend-rio-local-e-consulta-completa
source: [02-VERIFICATION.md]
started: 2026-11-15
updated: 2026-11-15
---

## Current Test

number: 1
name: Consultar lista completa e voltar aos pontos no Telegram
expected: |
  Escolha uma linha e um ponto no Telegram real. Abra Ver horários e use Voltar.
  Confira linha, endereço, data e calendário; a lista inclui horários passados.
  Voltar mostra os endereços da mesma linha e permite escolher outro ponto sem /start.
awaiting: user response

## Tests

### 1. Consultar lista completa e voltar aos pontos no Telegram
expected: A mensagem inline identifica linha/endereço/data/calendário, mostra todas as saídas e permite Voltar e escolher outro ponto da mesma linha.
result: [pending]

### 2. Navegar entre páginas no Telegram
expected: Em uma lista com várias páginas, Próxima e Anterior funcionam, os horários permanecem legíveis e Voltar está disponível em todas as páginas. Se os dados reais não gerarem várias páginas, registrar a limitação antes de considerar este item aprovado.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps

Nenhuma lacuna funcional identificada na verificação automatizada; observação real no Telegram pendente.
