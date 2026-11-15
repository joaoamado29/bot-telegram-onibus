---
status: diagnosed
phase: 02-calend-rio-local-e-consulta-completa
source: [02-VERIFICATION.md]
started: 2026-11-15
updated: 2026-11-15
---

## Current Test

[testing paused — paginação real sem dados suficientes; ajustes diagnosticados]

## Tests

### 1. Consultar lista completa e voltar aos pontos no Telegram
expected: A mensagem inline identifica linha/endereço/data/calendário, mostra todas as saídas e permite Voltar e escolher outro ponto da mesma linha.
result: issue
reported: "Linha 004 / Terminal do Papicu mostra horários indisponíveis em 15/11/2026 (Proclamação da República). Linhas 011 e 012 estão normais, mas só é possível voltar para a seleção de ponto; falta voltar para a seleção de linha."
severity: minor
clarification: "Usuário confirmou: a linha 004 está correta, realmente ele roda apenas em dias uteis. Falha mantida apenas para a navegação à seleção de linha."

### 2. Navegar entre páginas no Telegram
expected: Em uma lista com várias páginas, Próxima e Anterior funcionam, os horários permanecem legíveis e Voltar está disponível em todas as páginas. Se os dados reais não gerarem várias páginas, registrar a limitação antes de considerar este item aprovado.
result: blocked
blocked_by: prior-phase
reason: "Usuário: Não. Porém aparece um principio de paginação (\"Página 1/1\"). As listas observadas couberam em uma página; navegação Próxima/Anterior não exercitada. Não é uma falha comprovada de paginação."

## Summary

total: 2
passed: 0
issues: 1
pending: 0
skipped: 0
blocked: 1

## Gaps

- gap_id: G-02-2
  truth: "O passageiro consegue retornar à seleção de linha pela navegação do bot."
  status: failed
  reason: "Usuário informou que Voltar só permite selecionar outro ponto, sem botão para escolher outra linha. Ampliação solicitada do comportamento D-06, que originalmente previa retornar apenas aos pontos."
  severity: minor
  test: 1
  root_cause: "A navegação implementa D-06 original: Voltar reconstrói os pontos da mesma linha; não há botão de busca de outra linha nesse teclado."
  artifacts:
    - path: onibus/telegram_handlers.py
      issue: "Teclados de consulta e pontos não oferecem retorno à busca de linha."
  missing:
    - "Adicionar ação explícita para escolher outra linha preservando Voltar aos pontos."

## Observações confirmadas

- G-02-1 retirado das falhas após esclarecimento do usuário: a linha 004 opera somente em dias úteis. A indisponibilidade em domingo/feriado é correta. Não houve correção do banco ou do coletor.
- A apresentação de mensagens e do rótulo Página 1/1 será discutida na fase 6, adicionada a pedido do usuário.
