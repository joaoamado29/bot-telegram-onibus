---
phase: 02-calend-rio-local-e-consulta-completa
verified: "2026-11-15T16:48:43Z"
status: human_needed
score: 9/9 must-haves verified
covered_files:
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-03-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-03-SUMMARY.md
  - README.md
  - onibus/core.py
  - onibus/holidays.py
  - onibus/telegram_handlers.py
  - tests/test_schedules.py
  - tests/test_telegram_handlers.py
covered_digest: "v4:sha256:50a46fb089e886d882ab09bd2fa713ad164e0b479cc03012df29653fe2bd0579"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 8/8
  gaps_closed: [G-02-2]
  gaps_remaining: []
  regressions: []
decision_coverage:
  honored: 7
  total: 7
  not_honored: []
human_verification:
  - test: "Após a correção, tocar Buscar outra linha na lista de pontos, próximas saídas e Ver horários no Telegram real."
    expected: "A busca inline abre no chat atual e permite escolher outra linha sem /start; Voltar continua retornando aos pontos da linha atual."
    why_human: "A propriedade e os teclados foram testados; abertura real da busca no cliente Telegram ainda não foi observada. Corresponde ao teste 3 pendente do UAT."
  - test: "Em uma consulta com várias páginas, navegar Próxima e Anterior no Telegram real e retornar aos endereços."
    expected: "Páginas identificadas, sem erro de tamanho ou desaparecimento dos controles; Voltar continua disponível em todas as páginas."
    why_human: "O teste de 1440 horários prova conservação/limite no texto; no UAT real foram observadas apenas listas Página 1/1. Teste 2 bloqueado por falta de lista multipágina real, sem falha comprovada."
---

# Fase 02: Calendário local e consulta completa — Verificação

**Objetivo:** O passageiro consulta os horários adequados à data local, incluindo feriados, vê a lista completa do ponto e navega de volta aos outros endereços da linha.

**Status:** human_needed. Reverificação após o plano 02-03: implementação e comportamentos automatizados verificados; abertura real de Buscar outra linha e smoke multipágina pendentes. Nenhum bloqueio funcional encontrado. A evidência da verificação anterior permanece abaixo, identificada como histórica quando apropriado.

## Cobertura do fluxo do passageiro

| Etapa | Resultado esperado | Evidência real | Estado |
|---|---|---|---|
| Escolher ponto | Até três saídas futuras da data de Brasília | `proximas_saidas`, `ponto_callback`; testes de limites e conversão UTC/BRT | VERIFIED |
| Consultar em feriado | Calendário domingos_feriados e nome/data | `feriados_em` precede weekday; metadados chegam ao cabeçalho | VERIFIED |
| Ver horários | Lista publicada integral, incluindo passados | `todos_horarios` recebe SELECT real; callback h preserva a data original | VERIFIED |
| Navegar páginas | Todos os horários, uma vez, até 4096 caracteres por mensagem | `_paginas_horarios` calcula orçamento; teste percorre 1440 valores e compara lista exata | VERIFIED |
| Voltar e trocar ponto | Endereços da mesma linha e nova seleção | `_voltar` revalida revisão e reutiliza `criar_artigo`; teste fluxo ponto1 → voltar → ponto2 | VERIFIED |
| Buscar outra linha | Busca inline no chat atual em todos os teclados | `_botao_buscar_outra_linha` em `criar_artigo`, `_teclado_consulta` e páginas; teste nomeado executado nesta reverificação | VERIFIED |

## Objetivo e verdades observáveis

| # | Verdade (contrato ROADMAP e detalhes adicionais dos planos) | Estado | Evidência |
|---|---|---|---|
| 1 | Dia útil, sábado, domingo e feriados selecionam calendário da data BRT | VERIFIED | `core.py:225` converte fuso antes de classificar; feriados precedem weekday. Testes de Data Magna, Assunção no sábado e conversão UTC passaram. |
| 2 | Ver horários mostra todas as saídas do endereço/calendário/data, incluindo passadas | VERIFIED | SELECT vinculado por numero/calendario e coluna fechada; `todos_horarios` distinto de `horarios`. Teste após meia-noite mantém 13/11 e os três valores publicados. |
| 3 | Voltar permite outro endereço da mesma linha sem reiniciar | VERIFIED | Callback b conserva numero/revisao e recompõe teclado de posições existentes. Teste multietapas executado e aprovado. |
| 4 | Dados/calendário indisponíveis são distintos de lista válida esgotada | VERIFIED | Ausência de linha/endereço/calendário/lista e vazio geram indisponivel; só lista não vazia sem futuros gera encerrado. Testes de vazio/ausente/0 futuras passaram. |
| 5 | Ponto facultativo excluído, exceção anual restrita e nomes coincidentes preservados | VERIFIED | Catálogo puro com regras fixas/móveis e `_EXCECOES_ANUAIS`; seis testes de catálogo executados, incluindo 13/04 somente 2026 e colisão 2079. |
| 6 | Feriado mostra nome e data local | VERIFIED | `ConsultaSaidas.feriados` flui para `formato_saidas` e `_paginas_horarios`; teste Telegram verifica nome e dia; código não substitui o calendário ausente. |
| 7 | Paginação conserva horários e respeita limite por página | VERIFIED | Orçamento deriva do cabeçalho/rótulo efetivamente emitidos; teste de 1440 horários comprova igualdade da concatenação e <=4096. |
| 8 | Callbacks inválidos/obsoletos não consultam outra posição/revisão | VERIFIED | fullmatch, posição 1..5, data válida, página no intervalo, revisão/endereço em snapshot BEGIN; teste concorrente WAL executado preserva endereço/horários da revisão1 durante publicação da revisão2. |
| 9 | Buscar outra linha é oferecido nos pontos, consultas e páginas sem remover Voltar | VERIFIED | Helper em três construtores com `switch_inline_query_current_chat=""`; teste multietapas e teste de 1440 horários executados novamente e aprovados. |

**Score:** 9/9 verdades verificadas no contrato automatizado; zero verdades presentes com transição não exercitada. A abertura da busca e a aparência/entrega no cliente real são verificações humanas adicionais, não alegadas como aprovadas.

## Artefatos — existência, substância e conexão

| Artefato | Conteúdo real | Conexão e dados | Estado |
|---|---|---|---|
| `onibus/holidays.py` | Metadados imutáveis, catálogo nacional/CE/Fortaleza, cálculo da Páscoa e exceção2026 | `core.py` importa e chama feriados_em sobre local.date() | VERIFIED |
| `onibus/core.py` | Classificação temporal e SELECT dos horários | Retorna ConsultaSaidas consumida pelos handlers com lista integral e futura separadas | VERIFIED |
| `onibus/telegram_handlers.py` | Callbacks, transação de leitura, paginação e retorno | build_application registra CallbackQueryHandler(ponto_callback); asyncio.to_thread chama funções SQLite reais | VERIFIED |
| `tests/test_schedules.py` | 14 testes ativos, valores/datas explícitos e bancos temporários | Exercitam catálogo e core, sem rede ou circularidade de expected values | VERIFIED |
| `tests/test_telegram_handlers.py` | 16 testes ativos com AsyncMock da API e SQLite real | Fluxos completos conferem texto/teclado, paginação e revisão | VERIFIED |

As duas consultas `verify.artifacts` retornaram 3/3 cada. `verify.key-links` retornou 0/3 por plano com “Target not referenced in source”: a heurística procura paths literais/direção, mas os vínculos foram verificados manualmente por imports e chamadas Python e pelos testes abaixo. Não se tomou a heurística por evidência de ligação ausente.

## Ligações e rastreamento dos dados

| Origem → destino | Ligação comprovada | Estado |
|---|---|---|
| holidays → core | `from onibus.holidays import feriados_em`; chamada antes do weekday | WIRED |
| core → resposta Telegram | import ConsultaSaidas/proximas_saidas; retorno de `_consultar` alimenta formato/páginas | WIRED |
| Telegram → SQLite | ponto_callback aguarda to_thread(_consultar/_voltar); número/revisão/ponto vêm do callback validado | WIRED |
| SQLite → mensagem integral | SELECT horarios → JSON publicado → todos_horarios → grupos → edit_message_text | FLOWING |
| SQLite → retorno | SELECT pontos → revisão validada → criar_artigo → texto e teclado | FLOWING |

Não há retorno estático substituindo horários reais. Literais de teste fornecem entradas independentes da implementação.

## Verificações comportamentais da rodada anterior

Comando: `.venv/Scripts/python.exe -c` com unittest.loadTestsFromNames para `HolidaysCatalogTests`, `SchedulesTemporalTests` e os quatro testes nomeados abaixo. **18 testes, 0.373s, exit0.** Não foi repetida a suíte completa.

| Teste/conjunto | Resultado |
|---|---|
| HolidaysCatalogTests (6) | PASS — fixos/móveis, colisão, facultativo, exceção e ano |
| SchedulesTemporalTests (8) | PASS — fuso, limites, calendário, falta/vazio e fim |
| test_ver_horarios_inclui_passados_e_preserva_data | PASS — data preservada após meia-noite |
| test_lista_extensa_pagina_sem_perdas | PASS — 1440 valores iguais, sem duplicação/perda |
| test_voltar_reconstroi_enderecos_e_permite_outro_ponto | PASS — fluxo multietapas |
| test_consulta_mantem_snapshot_durante_publicacao | PASS — publicação intercalada não mistura revisões |

Probes externos: não declarados pelos planos; não aplicável. Não foram iniciados serviços, feitas consultas de passageiro na rede ou alterado o banco de produção.

## Cobertura de requisitos

| Requisito | Plano | Evidência | Estado |
|---|---|---|---|
| TIME-02 | 02-01 | Catálogo offline e precedência legal sobre weekday; testes de datas explícitas | SATISFIED |
| TIME-04 | 02-01 | Estados indisponivel/encerrado distintos em core e resposta | SATISFIED |
| BOT-04 | 02-02, 02-03 | Callback h com data, lista integral e páginas; prova exata de conservação e novo botão preservados | SATISFIED |
| BOT-05 | 02-02, 02-03 | Callback b conserva linha e permite outra posição; busca adicional de linha reutiliza mecanismo existente | SATISFIED |

Nenhum requisito órfão da fase. Consulta de amanhã e notificações pertencem às fases3–5, conforme ROADMAP; sua ausência não é lacuna desta entrega.

## Qualidade de testes e antipadrões

| Arquivo | Ativos | Desabilitados | Circularidade | Asserção mais forte | Parecer |
|---|---:|---:|---:|---|---|
| test_schedules.py | 14 | 0 | 0 | Valores/datas/status explícitos | Adequado |
| test_telegram_handlers.py | 17 | 0 | 0 | Fluxos multietapas, parâmetros explícitos dos botões e listas exatas | Adequado |

Nenhum marcador de dívida TBD/FIXME/XXX sem referência encontrado em produção/testes da fase. Tuplas vazias são defaults/estados indisponíveis e não stubs. O limite de identificação excessiva recebe alerta sem truncar o endereço; clientes reais ainda precisam do smoke abaixo.

## Decision Coverage

`check.decision-coverage-verify` retornou honored7/total7, not_honored vazio: “All trackable CONTEXT.md decisions are honored by shipped artifacts.”

## Verificação humana necessária

### 1. Buscar outra linha após a correção

**Teste:** tocar Buscar outra linha na lista de pontos, na consulta e em Ver horários, selecionar outra linha; depois conferir Voltar.
**Esperado:** busca inline no chat atual, escolha de outra linha sem /start e Voltar preservando os pontos da linha atual.
**Por que humano:** os testes provam propriedades do botão e montagem do teclado; a interação do cliente externo exige observação. Teste 3 do UAT está pendente.

### 2. Páginas no Telegram real

**Teste:** abrir uma lista extensa e navegar Próxima/Anterior, depois Voltar.
**Esperado:** mensagens aceitas, identificação e controles preservados, sem perda perceptível de horários.
**Por que humano:** o cálculo e conservação foram testados; a experiência do cliente externo requer observação.

**Estado do UAT:** bloqueado; o usuário observou apenas Página 1/1. Não é evidência de defeito nem aprovação da navegação multipágina.

## Registro final

O código do plano 02-02 foi registrado no commit `5fd45d7`; o fechamento G-02-2 está no commit `4a9fda2`, com resumo concluído. O fingerprint foi recomputado pela CLI incluindo os três planos/resumos. O UAT preserva o relato histórico do teste 1, registra G-02-2 resolvido pelo plano 02-03 e adiciona o teste 3 humano pendente.

O usuário confirmou que a linha 004 opera somente em dias úteis; a indisponibilidade em domingo/feriado corresponde ao calendário publicado e não é tratada como falha. A clareza das mensagens e Página 1/1 estão previstas na fase 6.

Nenhuma lacuna funcional bloqueante encontrada; a fase permanece aguardando os dois testes humanos acima.

## Reverificação incremental 02-03 — evidência executada

Leitura direta confirmou o helper com consulta vazia, sem callback novo, em `criar_artigo`, `_teclado_consulta` e no teclado de cada página. `_voltar` reutiliza `criar_artigo`. `build_application` registra `InlineQueryHandler(inline_query)`, cuja leitura SQLite via `_artigos` produz sugestões reais; não há lista estática substituindo os dados.

Comando executado: `.venv/Scripts/python.exe -c` carregando pelo nome os quatro testes abaixo com `unittest.defaultTestLoader.loadTestsFromNames`. **4 testes, 0.208s, exit 0.** A suíte completa não foi repetida nesta reverificação.

| Teste | Resultado |
|---|---|
| test_buscar_outra_linha_em_pontos_consultas_e_retorno | PASS — botão único, consulta inline vazia, sem callback em pontos, consulta, indisponibilidade, encerramento e retorno |
| test_lista_extensa_pagina_sem_perdas | PASS — 1440 horários conservados, até 4096 caracteres, Busca e Voltar em todas as páginas |
| test_voltar_reconstroi_enderecos_e_permite_outro_ponto | PASS — troca de ponto da mesma linha preservada |
| test_consulta_mantem_snapshot_durante_publicacao | PASS — revisão/endereço/horários consistentes sob publicação intercalada |

`verify.artifacts` do plano 02-03 retornou 2/2. `verify.key-links` retornou 0/1 pela heurística de path literal; o vínculo real é o import `buscar_sugestoes` de `onibus.search`, usado em `_artigos` pelo handler inline registrado. Essa ligação foi conferida diretamente; o resultado heurístico não foi contado como prova de falha.

Decision coverage executada novamente: honored 7/total 7; nenhum item não honrado. Scan de dívida e testes desabilitados nos arquivos de produção/testes verificados: nenhum marcador encontrado. O novo teste usa expectativas explícitas do contrato (`""`, ausência de callback, presença única e fluxo multietapas), sem gerar expected values pela implementação.

### Advisory (New Scope, Unevidenced)

Nenhum achado adicional. Não foram alterados produção, banco, UAT, STATE ou ROADMAP nesta reverificação.
