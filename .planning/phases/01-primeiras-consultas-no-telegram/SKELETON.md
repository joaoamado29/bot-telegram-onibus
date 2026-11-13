# Walking Skeleton — Bot Telegram Ônibus

**Phase:** 1
**Generated:** 2026-11-13
**Status:** Contrato de planejamento; nenhuma capacidade foi implementada ou verificada nesta geração.

## Capability Proven End-to-End

Capacidade a comprovar no plano01: uma linha coletada da origem é gravada em SQLite, encontrada por busca inline no Telegram e seu endereço selecionado retorna até três próximas saídas de hoje.

## Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Python existente + python-telegram-bot22.8 com job-queue | Preservar coletor e servir interação inline pesquisada |
| Data layer | sqlite3; catálogo linhas preservado; tabelas pontos/horarios amplas | Contrato aprovado com arrays JSON independentes e FK |
| Auth | Token de serviço em TELEGRAM_BOT_TOKEN; sem login de passageiro | Telegram fornece identidade de cliente e horários são públicos |
| Deployment target | Processo local de desenvolvimento com polling | Exercita stack completo sem escolher provedor de produção |
| Directory layout | bot.py; namespace onibus com core.py, telegram_handlers.py, search.py, refresh.py | Fronteiras suficientes sem fragmentação artificial da entrega inicial |
| Time | ZoneInfo America/Sao_Paulo + tzdata no Windows | Data/hora de consulta e agenda semanal explícitas |
| Schedules | pontos(numero PK/FK linhas) e horarios(numero,calendario PK/FK pontos) | Identidade estável por linha atual; cada ponto guarda lista independente |

O modelo conserva numero/nome e cinco colunas solicitadas nas duas tabelas. Incluir outra cidade/fonte/variante exige nova decisão de identidade; não usar nome como chave. Reversibilidade do esquema é costly: futuras alterações demandam migração; não altera schema preexistente de linhas.

## Stack Touched in Phase 1

- [ ] Scaffold: dependências do bot, entrada, configuração por ambiente e unittest.
- [ ] Routing: /start, inline queries e callbacks de ponto registrados.
- [ ] Database: escrita e leitura reais com FK e transação por linha.
- [ ] UI: resultado inline com endereços e botões que consultam SQLite.
- [ ] Deployment: comando local `.venv/Scripts/python.exe bot.py --coletar-linha NUMERO` e depois execução normal com coleta automática.

## Out of Scope (Deferred to Later Slices)

- Feriados completos e navegação Ver horários/Voltar: fase2.
- Consulta de amanhã: fase3.
- Alertas: fase4; recuperação/cancelamento: fase5.
- GPS, várias cidades e recorrência diária não pertencem ao escopo aprovado.

## Subsequent Slice Plan

- Fase2: estender resolução de calendário e handlers, preservando identidades de linha/ponto.
- Fase3: consultar outra data explicitamente.
- Fase4: adicionar alertas por viagem sem derivar chat_id de mensagem inline.
- Fase5: persistir intenções de alerta e cancelamento.

## Multi-Source Coverage Audit

| SOURCE | ID | Feature/Requirement | Plan | Status | Notes |
|--------|----|---------------------|------|--------|-------|
| GOAL | Phase1 | Linha→ponto→até três saídas reais | 01,02,03,04 | COVERED | Tracer validado antes de expansão |
| REQ | DATA-01 | Páginas detalhadas | 01,02,04 | COVERED | Coleta manual de linha e automática completa |
| REQ | DATA-02 | Anúncios/ponto/calendário | 02 | COVERED | Fixtures e parsing estrito |
| REQ | DATA-03 | Cinco arrays independentes | 01,02 | COVERED | Roundtrip JSON |
| REQ | DATA-04 | Primeiras duas obrigatórias | 01,02,04 | COVERED | SQL+Python; rejeição last-good |
| REQ | DATA-05 | FK entre tabelas | 01,02 | COVERED | Enforcement real SQLite |
| REQ | DATA-06 | Correspondência de posições | 01,02,04 | COVERED | Sem parear viagens |
| REQ | TIME-01 | Brasília | 01,02 | COVERED | ZoneInfo/clock |
| REQ | TIME-03 | Até três saídas de hoje | 01,02 | COVERED | Limites de data/instante |
| REQ | BOT-01 | /start e linha | 01,03,04 | COVERED | Inline+paginação |
| REQ | BOT-02 | Endereços selecionáveis | 01,03,04 | COVERED | Artigo+callback inline |
| CONTEXT | D-01 | Número/nome e formato | 03 | COVERED | Nome original |
| CONTEXT | D-02 | Autocomplete inline | 01,03 | COVERED | Sem chosen result obrigatório |
| CONTEXT | D-03 | Endereços diretos | 01,03 | COVERED | Teclado no artigo |
| CONTEXT | D-04 | Ignorar caixa/acentos | 03 | COVERED | Unicode |
| CONTEXT | D-05 | Dez e rolar mais | 03 | COVERED | Offset limitado |
| CONTEXT | D-06 | Domingo01 BRT | 04 | COVERED | days0 PTB |
| CONTEXT | D-07 | Retry e last-good | 04 | COVERED | Três retries/ciclo |
| CONTEXT | D-08 | Substituição válida | 02,04 | COVERED | Transação por linha |
| CONTEXT | D-09 | Incompleto não apaga | 02,04 | COVERED | Continua demais linhas |
| CONTEXT | D-10 | Coleta inicial | 04 | COVERED | Job inicial sem bloquear polling |
| CONTEXT | D-11 | Duas tabelas/cinco pontos | 01,02 | COVERED | FK e listas independentes |
| CONTEXT | D-12 | 26/27 e anúncios | 02 | COVERED | Não truncar |
| CONTEXT | D-13 | Hoje, até três | 01,02 | COVERED | Sem completar amanhã |
| RESEARCH | Inline | Callback sem message | 01,03 | COVERED | inline_message_id |
| RESEARCH | Storage | Atomicidade/constraints | 01,02 | COVERED | Banco real temporário |
| RESEARCH | Refresh | Worker/lock/retries | 04 | COVERED | Um dono da agenda |
| RESEARCH | Operations | Token/BotFather/dev run | 01,04 | COVERED | Checkpoints reais |
| RESEARCH | Packages | Novos pacotes auditados | 01 | COVERED | Checkpoint explícito antes de instalar |
| RESEARCH | Validation | Fixtures/mocks/clock/zero-test detection | 01..04 | COVERED | VALIDATION mapeada |
| RESEARCH | Baseline | Produto existente não rastreado | 01 | COVERED | Commit explícito antes de alterar |

## Probe Dispositions

As dez linhas de 01-EDGE-PROBE.json permanecem flagged unclassified/unresolved; não foram reclassificadas por invenção. Distribuição: DATA-01..06/TIME-01/TIME-03 no02 (e tracer01); BOT-01/02 no03. Testes conhecidos não substituem inspeção das demais bordas pelo verificador.

Prohibition recall executado sobre os dez requisitos: integridade de listas, mistura de datas, anúncios, SQL, token e scraping por tecla são engenharia/segurança canônica e ficam nos testes/threat_model, não geram proibições adicionais. Nenhuma proibição bespoke sobre valores/ética sobreviveu ao filtro; não foram criados descriptors ou aprovações fictícias.

## Dependency Graph

Wave1:01 tracer e pré-requisitos externos. Wave2:02 core/dados e03 busca/adaptador em paralelo, interfaces01 estáveis e nenhum arquivo compartilhado. Wave3:04 runtime/agenda e smoke completo, dependente de02 e03.
