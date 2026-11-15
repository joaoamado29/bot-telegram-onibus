---
phase: 02-calend-rio-local-e-consulta-completa
verified: "2026-11-15T14:57:22Z"
status: human_needed
score: 8/8 must-haves verified
covered_files:
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-SUMMARY.md
  - README.md
  - onibus/core.py
  - onibus/holidays.py
  - onibus/telegram_handlers.py
  - tests/test_schedules.py
  - tests/test_telegram_handlers.py
covered_digest: "v4:sha256:79a85a1bd609a1dd15a066f4a58bd85e9ee51764dc1c5696af668f845e1602cf"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 7
  total: 7
  not_honored: []
human_verification:
  - test: "No Telegram real, escolher uma linha e ponto, abrir Ver horários e usar Voltar para escolher outro ponto."
    expected: "A mensagem inline mantém linha/endereço/data e tipo de dia; a lista completa inclui saídas passadas; Voltar apresenta os endereços da mesma linha e permite nova consulta sem /start."
    why_human: "Os testes simulam a API; entrega real, renderização dos botões e clareza da mensagem no cliente Telegram não foram observadas nesta fase."
  - test: "Em uma consulta com várias páginas, navegar Próxima e Anterior no Telegram real e retornar aos endereços."
    expected: "Páginas identificadas, sem erro de tamanho ou desaparecimento dos controles; Voltar continua disponível em todas as páginas."
    why_human: "O teste de 1440 horários prova conservação/limite no texto; a integração visual com o cliente Telegram requer observação humana."
---

# Fase 02: Calendário local e consulta completa — Verificação

**Objetivo:** O passageiro consulta os horários adequados à data local, incluindo feriados, vê a lista completa do ponto e navega de volta aos outros endereços da linha.

**Status:** human_needed. Implementação e comportamentos automatizados verificados; smoke no Telegram real pendente. Nenhum bloqueio funcional encontrado nesta verificação inicial.

## Cobertura do fluxo do passageiro

| Etapa | Resultado esperado | Evidência real | Estado |
|---|---|---|---|
| Escolher ponto | Até três saídas futuras da data de Brasília | `proximas_saidas`, `ponto_callback`; testes de limites e conversão UTC/BRT | VERIFIED |
| Consultar em feriado | Calendário domingos_feriados e nome/data | `feriados_em` precede weekday; metadados chegam ao cabeçalho | VERIFIED |
| Ver horários | Lista publicada integral, incluindo passados | `todos_horarios` recebe SELECT real; callback h preserva a data original | VERIFIED |
| Navegar páginas | Todos os horários, uma vez, até 4096 caracteres por mensagem | `_paginas_horarios` calcula orçamento; teste percorre 1440 valores e compara lista exata | VERIFIED |
| Voltar e trocar ponto | Endereços da mesma linha e nova seleção | `_voltar` revalida revisão e reutiliza `criar_artigo`; teste fluxo ponto1 → voltar → ponto2 | VERIFIED |

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

**Score:** 8/8 verdades verificadas; zero verdades presentes com comportamento não exercitado. Aparência/entrega real são verificações humanas adicionais, não alegadas como aprovadas.

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

## Verificações comportamentais executadas

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
| BOT-04 | 02-02 | Callback h com data, lista integral e páginas; prova exata de conservação | SATISFIED |
| BOT-05 | 02-02 | Callback b conserva linha e permite outra posição | SATISFIED |

Nenhum requisito órfão da fase. Consulta de amanhã e notificações pertencem às fases3–5, conforme ROADMAP; sua ausência não é lacuna desta entrega.

## Qualidade de testes e antipadrões

| Arquivo | Ativos | Desabilitados | Circularidade | Asserção mais forte | Parecer |
|---|---:|---:|---:|---|---|
| test_schedules.py | 14 | 0 | 0 | Valores/datas/status explícitos | Adequado |
| test_telegram_handlers.py | 16 | 0 | 0 | Fluxos multietapas e listas exatas | Adequado |

Nenhum marcador de dívida TBD/FIXME/XXX sem referência encontrado em produção/testes da fase. Tuplas vazias são defaults/estados indisponíveis e não stubs. O limite de identificação excessiva recebe alerta sem truncar o endereço; clientes reais ainda precisam do smoke abaixo.

## Decision Coverage

`check.decision-coverage-verify` retornou honored7/total7, not_honored vazio: “All trackable CONTEXT.md decisions are honored by shipped artifacts.”

## Verificação humana necessária

### 1. Consulta completa e retorno no Telegram real

**Teste:** escolher linha/ponto, abrir Ver horários, voltar e escolher outro endereço.
**Esperado:** identificação clara, todos os horários do calendário/data e retorno à mesma linha sem /start.
**Por que humano:** API é simulada nos testes; renderização, entrega e clareza no aplicativo não foram observadas.

### 2. Páginas no Telegram real

**Teste:** abrir uma lista extensa e navegar Próxima/Anterior, depois Voltar.
**Esperado:** mensagens aceitas, identificação e controles preservados, sem perda perceptível de horários.
**Por que humano:** o cálculo e conservação foram testados; a experiência do cliente externo requer observação.

## Registro final

O código do plano 02-02 foi registrado no commit `5fd45d7`, com resumo concluído. O fingerprint acima foi recomputado pela CLI após essa atualização de metadados; nenhuma alteração de produção ocorreu desde a verificação comportamental. Os dois testes humanos estão registrados em `02-UAT.md`.

Nenhuma lacuna funcional bloqueante encontrada; a fase permanece aguardando os dois testes humanos acima.
