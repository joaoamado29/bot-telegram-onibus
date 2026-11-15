---
phase: "02"
slug: "calend-rio-local-e-consulta-completa"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-11-15"
---

# Fase 02 — Estratégia de validação

Auditoria independente dos requisitos TIME-02, TIME-04, BOT-04 e BOT-05. Os testes existentes foram lidos e executados; não foi necessário criar testes duplicados.

## Test Infrastructure

| Propriedade | Valor |
|-------------|-------|
| Framework | Python unittest, unittest.IsolatedAsyncioTestCase e unittest.mock |
| Configuração | Descoberta padrão de unittest em tests/; bancos SQLite temporários |
| Comando rápido | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` |
| Suíte completa | `.venv/Scripts/python.exe -m unittest discover -s tests -p 'test_*.py' -v` |
| Resultado auditado | 65 testes aprovados em 3.675s; exit code 0 (2026-11-15, reverificação da meta MVP) |
| Relógio e rede | Datas fixas; callbacks simulados; sem Telegram ou rede para os testes |

## Sampling Rate

- Após cada tarefa: executar o arquivo de teste correspondente abaixo.
- Após cada onda e antes do UAT: executar a suíte completa.
- Latência observada da suíte completa: aproximadamente 3 segundos; nenhum comando usa watch.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | TIME-02 | T-02-01 | Feriado precede weekday no calendário de Brasília | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` | sim | green |
| 02-01-01 | 01 | 1 | TIME-04 | T-02-02 | Dados ausentes/vazios não são apresentados como encerramento | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` | sim | green |
| 02-01-02 | 01 | 1 | TIME-02 | T-02-01 | Datas fixas/móveis, colisões e exceção anual não inventam feriado | unit | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` | sim | green |
| 02-02-01 | 02 | 2 | BOT-04 | T-02-04 | Lista integral conserva passados/data/calendário; páginas não perdem valores | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` | sim | green |
| 02-02-02 | 02 | 2 | BOT-05 | T-02-03 | Voltar conserva linha; seleção expirada/inválida não lê outra revisão | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` | sim | green |
| 02-03-01 | 03 | 3 | BOT-04, BOT-05 | T-02-05 | Buscar outra linha abre a busca existente em todos os teclados sem remover Voltar | integration | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` | sim | green |

## Evidência comportamental por requisito

| Requisito | Testes representativos | Classificação |
|-----------|-----------------------|---------------|
| TIME-02 | HolidaysCatalogTests: seis testes para datas fixas, móveis, colisões, exceção só em 2026, ponto facultativo e mudança de ano; SchedulesTemporalTests.test_data_magna_em_dia_util_seleciona_domingo_feriado, test_feriado_em_sabado_prevalece_sobre_calendario_de_sabados e test_relogio_utc_converte_corretamente_para_brt | COVERED |
| TIME-04 | SchedulesTemporalTests.test_ponto_sem_calendario_retorna_indisponivel, test_lista_publicada_vazia_e_indisponivel_nao_encerrada e test_quantidade_de_saidas_retorna_ate_tres; TelegramHandlersTests.test_ver_horarios_feriado_e_indisponibilidade | COVERED |
| BOT-04 | TelegramHandlersTests.test_ver_horarios_inclui_passados_e_preserva_data, test_lista_extensa_pagina_sem_perdas, test_cabecalho_longo_que_cabe_abre_lista e test_identificacao_excessiva_informa_erro | COVERED |
| BOT-05 | TelegramHandlersTests.test_voltar_reconstroi_enderecos_e_permite_outro_ponto, test_navegacao_obsoleta_nao_exibe_horarios_ou_enderecos, test_callbacks_navegacao_invalidos_nao_editam, test_data_e_pagina_invalidas_explicam_erro e test_consulta_mantem_snapshot_durante_publicacao | COVERED |

A lista extensa compara os 1.440 valores publicados com a concatenação das páginas, em ordem e sem duplicação, e confere o teto de 4096 caracteres. A troca de dia do relógio ocorre entre o clique inicial e Ver horários. O teste concorrente intercala publicação de revisão nova no banco WAL e exige dados consistentes da revisão já validada.

## Wave 0 Requirements

A infraestrutura existente cobre todos os requisitos da fase. Nenhuma dependência ou fixture adicional foi necessária nesta auditoria.

## Manual-Only Verifications

Reverificação da meta MVP: 65 testes verdes (3.675s), incluindo 17 testes de handlers e comparação integral de 1440 horários com até 28 por página. Nenhuma lacuna automatizável encontrada. Abertura real da busca e navegação multipágina foram aprovadas pelo usuário em `02-UAT.md`; a issue histórica do teste 1 está resolvida pelo plano 02-03 executado.

Não há lacuna automatizável nos quatro requisitos. O smoke visual no Telegram real continua recomendado para conferir renderização e usabilidade dos botões; esta auditoria usa mocks da API e não afirma ter executado esse smoke.

## Validation Sign-Off

- [x] Todas as tarefas têm comando automatizado executável.
- [x] Nenhuma sequência de três tarefas fica sem verificação automatizada.
- [x] Não há referência de teste ausente nem necessidade de Wave 0.
- [x] Comandos sem watch e suíte completa verde.
- [x] Latência medida inferior a 5 segundos nesta execução.
- [x] `nyquist_compliant: true` corresponde à cobertura comportamental executada.

**Aprovação automatizada:** 2026-11-15 — auditoria Nyquist atualizada, 65/65 testes. Commits e conclusão do plano 02-02 permanecem sob responsabilidade do orquestrador; conformidade de cobertura não implica alegação de sequência TDD integral.

## Validation Audit 2026-11-15

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
