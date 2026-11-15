---
phase: "02"
audited: "2026-11-15"
baseline: "Fluxo do Telegram; sem UI-SPEC"
screenshots: "not captured (interface renderizada pelo cliente Telegram)"
interaction_captures: "off (workflow.ui_interaction_capture is false)"
---

# Fase 02 — Revisão da interface

**Baseline:** Interface conversacional do Telegram; não há UI-SPEC nem frontend web no repositório.
**Screenshots:** Não capturadas. O bot não oferece página local para captura; cores, tipografia e espaçamento visual são renderizados pelo cliente Telegram.
**Interaction captures:** off (workflow.ui_interaction_capture is false). A navegação foi exercitada pelo usuário no Telegram durante o UAT.

## Pontuação dos pilares

| Pilar | Nota | Achado principal |
|---|---:|---|
| 1. Texto | 2/4 | A indicação “Página 1/1” é redundante quando a lista cabe em uma página; revisão já prevista na Fase 6. |
| 2. Hierarquia | 3/4 | A mensagem ordena linha, ponto, data e horários; a apresentação visual final depende do Telegram. |
| 3. Cor | 3/4 | A implementação usa os controles padrão do Telegram; a aplicação não define paleta própria. |
| 4. Tipografia | 3/4 | O texto separa cabeçalho e conteúdo, mas fonte e pesos são controlados pelo cliente Telegram. |
| 5. Espaçamento | 3/4 | Botões de seleção aparecem em linhas separadas e os controles de navegação ficam agrupados; o espaçamento visual é do cliente Telegram. |
| 6. Experiência | 4/4 | Voltar, buscar outra linha, navegação entre páginas e tratamento de página inválida estão conectados e exercitados. |

**Total: 18/24**

As notas dos pilares visuais registram os limites de avaliação do canal Telegram; a ausência de layout web ou de tokens visuais próprios não é tratada como defeito do produto.

## Prioridades

1. Remover “Página 1/1” em listas sem paginação, conforme escopo da Fase 6 — reduz informação redundante.
2. Revisar os textos dos botões em conjunto na Fase 6 — mantém nomes e orientação consistentes.
3. Preservar a validação real no cliente Telegram quando houver mudança de teclado ou apresentação — os testes locais não reproduzem o renderizador do cliente.

## Achados detalhados

### Pilar 1: Texto (2/4)

- `onibus/telegram_handlers.py:137-166`: `_paginas_horarios` sempre inclui “Página {n}/{total}”, inclusive `Página 1/1`. A observação do usuário foi registrada para a Fase 6; não impede consulta nem navegação.
- `onibus/telegram_handlers.py:38-54, 129-134`: `/start`, seleção e navegação usam ações em português, com “Buscar linha”, “Buscar outra linha”, “Ver horários” e “Voltar”.
- `onibus/telegram_handlers.py:111-126, 201-240`: mensagens distinguem indisponibilidade, encerramento, seleção expirada e dados inválidos.

### Pilar 2: Hierarquia (3/4)

- `onibus/telegram_handlers.py:111-126, 137-145`: linha, ponto, data e calendário precedem os horários; não há estilo visual explícito na mensagem.
- `onibus/telegram_handlers.py:57-77, 129-134`: ações são agrupadas em botões inline do Telegram. A hierarquia visual exata não pode ser verificada sem o cliente.

### Pilar 3: Cor (3/4)

- O código entrega texto e `InlineKeyboardMarkup`, sem cores hard-coded nem tokens de cor (`onibus/telegram_handlers.py:57-77, 129-134, 174-198`). O cliente Telegram aplica sua própria paleta.

### Pilar 4: Tipografia (3/4)

- As mensagens usam texto simples, com a linha no cabeçalho e horários em linhas próprias (`onibus/telegram_handlers.py:111-126, 137-145`). Fonte, tamanho e peso são definidos pelo Telegram.

### Pilar 5: Espaçamento (3/4)

- A estrutura separa seleção de pontos, navegação e retorno em linhas distintas; Anterior/Próxima compartilham uma linha (`onibus/telegram_handlers.py:66-77, 129-134, 174-198`). O espaço visual entre controles é do cliente Telegram.

### Pilar 6: Experiência (4/4)

- `onibus/telegram_handlers.py:129-134, 137-166, 201-240`: consulta oferece Ver horários, Voltar e Buscar outra linha; páginas oferecem Anterior/Próxima quando aplicável, além de Voltar e Buscar outra linha.
- `tests/test_telegram_handlers.py:58-76, 89-116`: fluxo de busca em diferentes estados e percurso limitado pelas 52 páginas do conjunto de 1.440 horários; cada página afirma no máximo 28 horários e a sequência integral.
- O usuário confirmou no Telegram o funcionamento da navegação multipágina com a linha 051; registro em `02-UAT.md`.

## Arquivos auditados

- `onibus/telegram_handlers.py`
- `tests/test_telegram_handlers.py`
- `02-01-PLAN.md`, `02-02-PLAN.md`, `02-03-PLAN.md`
- `02-01-SUMMARY.md`, `02-02-SUMMARY.md`, `02-03-SUMMARY.md`
- `02-UAT.md`
