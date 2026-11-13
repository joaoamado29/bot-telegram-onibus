---
phase: "01"
slug: "primeiras-consultas-no-telegram"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-11-13"
---

# Phase 01 — Validation Strategy

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | Python unittest, IsolatedAsyncioTestCase e AsyncMock |
| Config file | Nenhum; infraestrutura do produto será criada na execução |
| Quick run command | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` |
| Full suite command | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py -v` |
| Estimated runtime | Alvo de 30 segundos; não medido |

## Sampling Rate

- Após cada tarefa: suíte focal do contrato alterado; verificar código de saída e que pelo menos um teste executou.
- Após cada wave: suíte completa do produto, sem rede real e sem escrever no banco de produção.
- Antes de verificar a fase: suíte completa verde e smoke real no Telegram.
- Latência máxima pretendida: 30 segundos por suíte automatizada; ainda não medida.

## Per-Task Verification Map

IDs abaixo correspondem aos planos gerados. Todos os testes ainda precisam ser criados; nenhuma execução foi declarada.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-02 | 01 | 1 | DATA-01,DATA-03..06,TIME-01,TIME-03,BOT-01,BOT-02 | T-01-01..03 | Caminho completo com banco real e callback validado | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_tracer.py -v` | Não — criada na própria tarefa | pending |
| 01-02-01 | 02 | 2 | DATA-01, DATA-02, DATA-06 | T-01-04 | Descartar anúncios e preservar ponto/calendário | unit | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_scraping.py -v` | Não — criada na própria tarefa | pending |
| 01-02-02 | 02 | 2 | DATA-03, DATA-04, DATA-05 | T-01-05 | Coleções não vazias e FK aplicada | SQLite integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_storage.py -v` | Não — criada na própria tarefa | pending |
| 01-02-01 | 02 | 2 | DATA-06, TIME-01, TIME-03 | T-01-04 | Listas independentes e relógio explícito | unit/integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` | Não — criada na própria tarefa | pending |
| 01-03-01 | 03 | 2 | BOT-01; D-01,D-04 | T-01-06 | Busca normalizada e parametrizada | unit | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_search.py -v` | Não — criada na própria tarefa | pending |
| 01-03-02 | 03 | 2 | BOT-01, BOT-02; D-02,D-03,D-05 | T-01-06,T-01-07 | Callback validado sem depender de chat_id | async adapter | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` | Não — criada na própria tarefa | pending |
| 01-04-01/02 | 04 | 3 | D-06 a D-10 | T-01-08,T-01-09 | Falha não destrói last-good; retries limitados | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_refresh.py -v` | Não — criada na própria tarefa | pending |
| 01-04-02 | 04 | 3 | BOT-01,BOT-02 | T-01-10 | Runtime e configuração sem segredos | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_application.py -v` | Não — criada na própria tarefa | pending |

## Wave 0 Requirements

- [ ] Criar infraestrutura unittest e fixtures representativas de páginas reais.
- [ ] Cobrir publicidade, calendários por ponto e listas desiguais 26/27.
- [ ] Usar bancos temporários, transporte HTTP simulado e relógio injetável.
- [ ] Criar os módulos de teste indicados com testes comportamentais efetivos, sem stubs que passam vazios.
- [ ] Verificar que discovery não executa zero testes.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Autocomplete inline real e seleção de ponto | BOT-01, BOT-02; D-01 a D-05 | Cliente Telegram, BotFather e token externo | Em bot de desenvolvimento habilitar inline, iniciar `/start`, abrir busca, digitar `12`/`papicu`/`joao`, rolar, escolher linha, conferir endereços e consultar ponto |

## Validation Sign-Off

- [ ] Toda tarefa tem verificação automatizada ou dependência explícita da infraestrutura inicial.
- [ ] Nenhuma sequência de três tarefas sem verificação automatizada.
- [ ] Referências ausentes são criadas antes dos comandos que as executam.
- [ ] Comandos sem watch e com `<fails_when>` observável nos planos.
- [ ] Plano de validação atualizado com IDs reais de tarefas, waves e ameaças.
- [ ] Suíte completa verde e smoke humano registrado na execução.

**Approval:** pending execution validation; este documento não declara conformidade nem testes executados.
