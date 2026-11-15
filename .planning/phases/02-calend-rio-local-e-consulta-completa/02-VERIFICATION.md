---
phase: 02-calend-rio-local-e-consulta-completa
verified: 2026-11-15T20:50:51Z
status: passed
score: 9/9
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 7
  total: 7
  not_honored: []
re_verification:
  previous_status: human_needed
  previous_score: 9/9
  gaps_closed: ["UAT da busca de outra linha e paginação real aprovado", "Meta MVP validada e evidência atualizada"]
  gaps_remaining: []
  regressions: []
advisory:
  - finding: "WR-05: roadmap do README diverge da organização aprovada"
    category: other
    reason: "Deriva documental fora do escopo funcional; registrada na disposição da revisão, sem alterar README."
    evidence_status: "README.md:128-132 comparado ao ROADMAP aprovado"
human_verification: []
covered_files:
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-01-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-02-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-03-PLAN.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-03-SUMMARY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-REVIEW-DISPOSITION.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-REVIEW.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-SECURITY.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-UAT.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-UI-REVIEW.md
  - .planning/phases/02-calend-rio-local-e-consulta-completa/02-VALIDATION.md
  - README.md
  - onibus/core.py
  - onibus/holidays.py
  - onibus/search.py
  - onibus/telegram_handlers.py
  - tests/test_schedules.py
  - tests/test_telegram_handlers.py
covered_digest: "v4:sha256:d820ac6ecd5eef1f89f8e464082c5de02d28040357a4012516685f9ae384064e"
---

# Fase 02 — Verificação da meta

## User Flow Coverage

**História validada:** As a passageiro que consulta horários de ônibus pelo Telegram, I want to consultar os horários do ponto conforme a data e os feriados, ver a lista completa e voltar à escolha de endereço, so that eu possa planejar minha viagem com os horários corretos do dia e escolher o ponto mais conveniente.

| Passo | Esperado | Evidência | Estado |
|---|---|---|---|
| Escolher linha/ponto | Endereços reais e consulta do ponto escolhido | inline_query → buscar_sugestoes/SQLite → criar_artigo; teste de fluxo inline e UAT | VERIFIED |
| Consultar data/feriado | Calendário automático de Brasília | proximas_saidas converte BRT antes de feriados_em/weekday; testes de UTC, Data Magna e feriado no sábado | VERIFIED |
| Ver horários | Lista integral identificada, inclusive passados | Callback h preserva data e revisão; teste atravessa meia-noite mantendo 13/11 | VERIFIED |
| Navegar páginas | Até 28 horários e 4096 caracteres; sem perdas | Teste compara 1440 valores; UAT teste 2 aprovado com linha 051 | VERIFIED |
| Voltar e escolher endereço | Pontos da mesma linha, sem reiniciar | _voltar reutiliza criar_artigo; teste multietapas muda Terminal A para B | VERIFIED |
| Resultado | Planejar com horários do dia e escolher ponto conveniente | Dados de calendário/ponto reais, lista integral e retorno comprovados; busca de outra linha aprovada no UAT teste 3 | VERIFIED |

## Verdades observáveis

| # | Contrato | Evidência atual | Estado |
|---|---|---|---|
| 1 | SC1: calendário correto em dia útil, sábado, domingo e feriado nacional/CE/Fortaleza | Catálogo fixo/móvel/exceção anual; classificação BRT precede weekday; 14 testes temporais/catálogo aprovados | VERIFIED |
| 2 | SC2/D-05: lista completa do ponto/data/calendário | SELECT por numero/calendario, coluna validada 1..5; todos_horarios separado dos futuros; teste de data preservada | VERIFIED |
| 3 | SC3/D-06: Voltar aos endereços da mesma linha | Callback b valida revisão e recompõe artigos; fluxo de outro ponto exercitado | VERIFIED |
| 4 | SC4/D-04/D-07: indisponibilidade distinta de encerramento | Ausência/vazio retorna indisponivel; lista válida sem futuro retorna encerrado; testes de ambos estados | VERIFIED |
| 5 | D-01: facultativo excluído, colisões preservadas, exceções restritas ao ano | Seis testes HolidaysCatalogTests com expectativas explícitas, inclusive 2027 e colisão 2079 | VERIFIED |
| 6 | D-03: feriado informa nome/data | ConsultaSaidas.feriados alimenta formato_saidas e páginas; teste callback_em_feriado_mostra_nome_e_data | VERIFIED |
| 7 | D-05: paginação integral e limitada | _HORARIOS_POR_PAGINA=28 e orçamento calculado; teste de 1440 valores sem perda/duplicação | VERIFIED |
| 8 | Callback inválido/obsoleto não lê outra posição/revisão | fullmatch, intervalos/data/página e BEGIN antes da leitura; teste WAL publica revisão concorrente sem misturar snapshot | VERIFIED |
| 9 | Buscar outra linha em todos os teclados preserva Voltar | Helper com switch_inline_query_current_chat vazio em pontos, consulta e páginas; teste específico e UAT teste 3 | VERIFIED |

**Score: 9/9; behavior_unverified: 0.** Nenhuma verdade aprovada apenas pela presença de símbolos.

## Artefatos e ligações

`verify.artifacts` passou 3/3 no plano 01, 3/3 no plano 02 e 2/2 no plano 03. Os arquivos são substantivos e consumidos pela aplicação.

| Ligação | Evidência concreta | Estado |
|---|---|---|
| holidays → core | import feriados_em e chamada sobre local.date antes de weekday | WIRED |
| core → Telegram | ConsultaSaidas/proximas_saidas importados; retorno alimenta texto e teclados | WIRED |
| Callback → SQLite | ponto_callback aguarda asyncio.to_thread(_consultar/_voltar); conexões locais fechadas | WIRED |
| SQLite → lista integral | SELECT parametrizado → JSON publicado → todos_horarios → páginas → edit_message_text | FLOWING |
| Buscar outra linha → sugestões | Botão abre inline_query, que usa _artigos e buscar_sugestoes com consulta SQLite | FLOWING |

`verify.key-links` retornou 0/3, 0/3 e 0/1 com “Target not referenced in source”: a heurística busca paths literais/direção. As ligações acima foram verificadas nos imports/chamadas e exercitadas pelos testes. Não há retorno estático substituindo dados de passageiros.

## Verificação comportamental executada

Comando: `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py' -v`.

**65 testes, 3.675s, exit 0, OK.** Uma única execução da suíte completa nesta rodada. Bancos temporários e API Telegram simulada; nenhum serviço iniciado, requisição real ou alteração no banco de produção.

Casos decisivos: data_magna_em_dia_util; feriado_em_sabado; relogio_utc; lista_publicada_vazia; ver_horarios_inclui_passados_e_preserva_data; lista_extensa_pagina_sem_perdas; voltar_reconstroi_enderecos; consulta_mantem_snapshot_durante_publicacao; buscar_outra_linha_em_pontos_consultas_e_retorno. Todos passaram na execução acima.

Probes externos: não declarados nos planos; não aplicável.

## Cobertura de requisitos

| Requisito | Planos | Prova | Estado |
|---|---|---|---|
| TIME-02 | 02-01 | Catálogo offline e seleção por data BRT com precedência de feriados | SATISFIED |
| TIME-04 | 02-01 | Estados indisponivel/encerrado distintos nos testes e mensagens | SATISFIED |
| BOT-04 | 02-02, 02-03 | Lista integral, data, páginas e navegação comprovadas | SATISFIED |
| BOT-05 | 02-02, 02-03 | Retorno e escolha de outro ponto sem /start | SATISFIED |

Quatro requisitos mapeados, nenhum órfão. Consulta de amanhã pertence à Fase 3; avisos às Fases 4 e 5, conforme decisão explícita do usuário. A rotina anual de manutenção do catálogo está documentada no README; esta rodada verifica a implementação versionada e não reivindica nova pesquisa legislativa.

## Qualidade dos testes e antipadrões

| Arquivo | Ativos | Ignorados | Circularidade | Asserção mais forte |
|---|---:|---:|---:|---|
| tests/test_schedules.py | 14 | 0 | 0 | Datas, nomes, calendários e valores explícitos |
| tests/test_telegram_handlers.py | 17 | 0 | 0 | Fluxos multietapas, revisão concorrente e concatenação exata |

Nenhum marcador TBD/FIXME/XXX ou teste desabilitado encontrado nos arquivos de produção/teste da fase. Valores de expectativa vêm de datas/listas explícitas; não são gerados pela função sob teste. Nenhuma proibição formal declarada nos must_haves exige resolução adicional.

## Decision Coverage

Consulta `check.decision-coverage-verify`: **honored 7 / total 7**, not_honored vazio. All trackable CONTEXT.md decisions are honored by shipped artifacts.

## Revisões e UAT

- Nyquist: todos quatro requisitos cobertos, zero lacunas; VALIDATION atualizado com a execução atual.
- Segurança: registro elaborado nos planos, ASVS L1, seis ameaças fechadas e threats_open: 0. As mitigações de callback/SQL/snapshot/limite foram relidas e exercitadas. Nenhum risco novo aceito nesta rodada.
- Interface: revisão existente preservada (18/24); avaliação limitada ao canal Telegram, sem capturas novas. Texto “Página 1/1” continua previsto na Fase 6.
- Código: revisão independente de seis arquivos, zero novos defeitos funcionais, um WARNING documental WR-05; disposição explícita no artefato irmão.
- UAT: teste 1 conserva relato histórico e resolução válida pelo plano 02-03 com SUMMARY; testes 2 e 3 aprovados. `phase uat-passed 2 --uat-only` retornou passed:true sem blockers. A linha 004 é somente de dias úteis, conforme confirmação do usuário.

## Advisory — fora do escopo funcional

WR-05: o roadmap do README ainda descreve organização antiga. A correção documental foi sugerida e registrada, sem alterar README nem ampliar esta fase. Isso não contradiz os quatro requisitos funcionais verificados.

## Verificação humana pendente

Nenhuma. Os itens humanos anteriores foram satisfeitos pelas respostas reais preservadas em 02-UAT.md; esta rodada não reivindica ter observado o cliente Telegram novamente.

## Resultado

Meta MVP válida e alcançada; nenhuma lacuna funcional ou transição sem evidência. Fingerprint gerado pelo CLI após finalizar os artefatos técnicos, incluindo automaticamente os três planos e resumos. A transição da fase pertence ao orquestrador.
