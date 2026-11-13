# Plano 01-01 — checkpoint de execução

**Status:** aguardando configuração externa e smoke real; plano não concluído.
**Retomar:** tarefa 3 de `01-01-PLAN.md`; não refazer tarefas 1 e 2.

## Tarefas concluídas

1. Pacotes verificados e autorizados pelo usuário: “Pacotes verificados; pode instalar.” Instalados `python-telegram-bot[job-queue]==22.8` e `tzdata==2026.6`; `pip check` sem conflitos.
2. Tracer implementado e verificado: parser → SQLite real → resultado inline → callback sem mensagem → próximas saídas em Brasília.

## Commits

- `92d9382`: baseline explícito de `scraping.py`, `consulta.py`, `requirements.txt` e `README.md`.
- `249eb71`: testes RED e evidência validada como `RED_EVIDENCE_OK`.
- `ae0f89e`: implementação GREEN e cinco testes aprovados.

## Evidências

- `.venv/Scripts/python.exe -m unittest discover -s tests -p test_tracer.py -v`: 5 testes, OK.
- `.venv/Scripts/python.exe -m pip check`: No broken requirements found.
- `.venv/Scripts/python.exe bot.py --help`: CLI disponível.
- Coleta real da linha 011 publicada; catálogo mantém 379 linhas.
- Arrays por ponto da linha 011: úteis 33/33, sábados 26/26 e domingos/feriados 16/16.
- `TELEGRAM_BOT_TOKEN` ausente no ambiente do processo; valor nunca solicitado ou exibido.
- Polling e interação real não executados. Não marcar smoke aprovado ou plano completo.

## Próxima ação

Configurar o token localmente e habilitar `/setinline` no BotFather; nunca enviar token ao chat ou ao Git. Com o ambiente disponível, o executor inicia o bot e solicita a verificação `/start` → Buscar linha → selecionar 011 → escolher ponto → conferir saídas.

## Desvios

- Branch local `gsd/phase-01-primeiras-consultas-no-telegram` criada por autorização do orquestrador para respeitar a proteção de `master`.
- `.gitignore` acrescentado para excluir ambiente virtual, caches, segredos e SQLite de futuros commits.
- Um teste inicial precisou fechar explicitamente a conexão SQLite para a limpeza do banco temporário no Windows; os cinco testes passaram após o ajuste.

Nenhum SUMMARY completo foi emitido: o checkpoint humano da tarefa 3 continua pendente. A continuação deve conferir os commits acima e prosseguir a partir dele.
