---
phase: 02-calend-rio-local-e-consulta-completa
reviewed: "2026-11-15T17:35:50Z"
depth: standard
files_reviewed: 2
files_reviewed_list:
  - onibus/telegram_handlers.py
  - tests/test_telegram_handlers.py
incremental_plan: "02-03"
historical_scope: "A revisÃ£o inicial cobriu holidays.py, core.py, telegram_handlers.py, test_schedules.py, test_telegram_handlers.py e README.md; achados resolvidos preservados abaixo."
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
  necessity: 0
resolved_findings: [CR-01, WR-01, WR-02, WR-03, WR-04]
resolved_count: 5
status: clean
---

# Fase 02: revisÃ£o de cÃ³digo

## Summary

Revisao incremental apos o ajuste dos testes da paginacao de 28 horarios. A implementacao mantem os limites de quantidade e de 4096 caracteres. O teste agora afirma no maximo 28 horarios por pagina, percorre todas as paginas esperadas e verifica a lista integral; os achados WR-03 e WR-04 estao resolvidos.

## Narrative Findings (AI reviewer)

### Revisao incremental do limite de 28 horarios

#### Warnings

### WR-03: Teste de paginacao nao verifica o limite de 28 horarios
**Resolution:** fixed; `test_lista_extensa_pagina_sem_perdas` now asserts at most 28 times on each page.

**Classification:** WARNING
**File:** `tests/test_telegram_handlers.py:102-112`
**Issue:** O teste percorre os 1440 horarios e verifica o limite de 4096 caracteres, mas nao conta os horarios em cada pagina. Uma regressao que removesse `_HORARIOS_POR_PAGINA` ainda poderia passar: o limite de caracteres quebraria a lista em paginas maiores que 28, preservando todos os valores e mantendo cada texto abaixo de 4096.
**Fix:** Para cada texto de pagina, extraia os horarios e afirme que a contagem e menor ou igual a 28; mantenha tambem a comparacao da sequencia completa para detectar perda e duplicacao.

### WR-04: Percurso de paginas do teste nao tem limite de iteracoes
**Resolution:** fixed; traversal is bounded to the expected number of pages, and the final full-list equality assertion fails if schedules remain or callbacks repeat.

**Classification:** WARNING
**File:** `tests/test_telegram_handlers.py:99`
**Issue:** `while True` depende exclusivamente da resposta do botao `Proxima` para terminar. Se uma regressao produzir um ciclo de callbacks que nunca alcance a ultima pagina, o teste fica executando sem fim em vez de falhar com diagnostico localizado.
**Fix:** Limite as iteracoes ao numero esperado de paginas (ou a um limite derivado da quantidade de horarios) e falhe explicitamente se ainda houver `Proxima` apos esse limite.

### RevisÃ£o incremental do plano 02-03

Nenhum novo achado comprovado no diff de `onibus/telegram_handlers.py` e `tests/test_telegram_handlers.py`. O helper `_botao_buscar_outra_linha` em `telegram_handlers.py:52` constrÃ³i uma aÃ§Ã£o inline com consulta vazia; os trÃªs pontos de construÃ§Ã£o do teclado a reutilizam, sem acrescentar callback nem estado mutÃ¡vel. `_voltar` reaproveita o artigo, portanto tambÃ©m recebe a aÃ§Ã£o. O comportamento do parÃ¢metro vazio foi conferido na documentaÃ§Ã£o da biblioteca instalada. A busca continua entrando por `inline_query` e `buscar_sugestoes`, com validaÃ§Ãµes e parÃ¢metros SQL existentes.

Foram executados os 17 testes dos handlers nesta revisÃ£o (0.783s, exit 0), incluindo aÃ§Ã£o Ãºnica nos pontos, retorno, prÃ³ximas saÃ­das, indisponibilidade, encerramento e cada pÃ¡gina dos 1.440 horÃ¡rios. As asserÃ§Ãµes conferem consulta vazia e ausÃªncia de `callback_data`; o ciclo Voltar e a preservaÃ§Ã£o de data continuam exercitados. NÃ£o foram introduzidos novos achados de necessidade.

**T-02-05:** mitigaÃ§Ã£o presente: busca inline existente reutilizada, sem nova entrada de callback nem acesso ao banco. **BOT-04/BOT-05:** cobertura preservada e ampliada pelo teste `test_buscar_outra_linha_em_pontos_consultas_e_retorno` e pelas asserÃ§Ãµes em `test_lista_extensa_pagina_sem_perdas`. A interaÃ§Ã£o real do cliente Telegram ainda requer confirmaÃ§Ã£o humana; esta revisÃ£o nÃ£o a declara executada.

Os trÃªs achados histÃ³ricos a seguir continuam resolvidos e nÃ£o representam achados abertos do plano 02-03.

## Critical Issues

### CR-01: ValidaÃ§Ã£o da revisÃ£o e leitura de horÃ¡rios nÃ£o compartilham um snapshot

**Classification:** BLOCKER
**Resolution:** fixed â€” `BEGIN` antes de ler a revisÃ£o preserva o snapshot atÃ© fechar a conexÃ£o. Confirmado por `test_consulta_mantem_snapshot_durante_publicacao`, com publicaÃ§Ã£o concorrente em WAL sem trocar Terminal A pelos novos dados.
**File:** `onibus/telegram_handlers.py:176-179`
**Issue:** `_consultar` lÃª a revisÃ£o em um SELECT e depois chama `proximas_saidas`, que lÃª novamente os pontos e horÃ¡rios. A conexÃ£o nÃ£o inicia uma transaÃ§Ã£o de leitura; no sqlite3 utilizado, o SELECT isolado nÃ£o mantÃ©m um snapshot entre esses comandos. A atualizaÃ§Ã£o semanal pode publicar uma nova revisÃ£o entre a validaÃ§Ã£o e a consulta, fazendo um botÃ£o antigo mostrar outro endereÃ§o e horÃ¡rios. A nova aÃ§Ã£o `h` reutiliza essa fronteira sem proteÃ§Ã£o, contrariando a garantia de rejeitar revisÃ£o obsoleta antes de exibir dados. ReproduÃ§Ã£o determinÃ­stica, sem alterar arquivos: publicar revisÃ£o 1 com Terminal A/12:00; intercalar publicaÃ§Ã£o da revisÃ£o 2 com Terminal NOVO/13:00 imediatamente antes da chamada real a `proximas_saidas`; `_consultar(db,11,1,1,agora)` retorna Terminal NOVO e 13:00 em vez de recusar ou manter a revisÃ£o 1.
**Fix:** Iniciar explicitamente uma transaÃ§Ã£o de leitura antes do primeiro SELECT e manter a validaÃ§Ã£o de revisÃ£o, pontos e horÃ¡rios dentro do mesmo snapshot, fechando-a antes de editar a mensagem. Alternativamente, carregar revisÃ£o/endereÃ§o/coleÃ§Ã£o por uma Ãºnica consulta SQL e validar a revisÃ£o do prÃ³prio resultado. Acrescentar teste determinÃ­stico com publicaÃ§Ã£o intercalada.

## Warnings

### WR-01: Datas e pÃ¡ginas invÃ¡lidas sÃ£o confirmadas sem mensagem de erro

**Classification:** WARNING
**Resolution:** fixed â€” os caminhos de data/pÃ¡gina invÃ¡lida retornam alerta em portuguÃªs sem confirmaÃ§Ã£o vazia prÃ©via. Confirmado por `test_data_e_pagina_invalidas_explicam_erro`.
**File:** `onibus/telegram_handlers.py:199-224`
**Issue:** Depois de `query.answer()` sem texto, o handler retorna silenciosamente quando uma data sintaticamente vÃ¡lida Ã© impossÃ­vel ou a pÃ¡gina excede o conjunto atual. Por exemplo, `h:11:1:1:20260231:0` e `h:11:1:1:20261113:9999` nÃ£o alteram a mensagem e nÃ£o explicam o problema. Os testes verificam somente a ausÃªncia de ediÃ§Ã£o, deixando essa ausÃªncia de resposta passar. O contrato do plano exige resposta segura para callback invÃ¡lido e orientaÃ§Ã£o para refazer a busca quando necessÃ¡rio.
**Fix:** Validar a data antes de confirmar o callback e responder com mensagem em portuguÃªs para data/pÃ¡gina invÃ¡lida; fazer o mesmo para falha de formataÃ§Ã£o. Manter uma Ãºnica confirmaÃ§Ã£o por caminho e testar seu texto, alÃ©m da ausÃªncia de ediÃ§Ã£o indevida.

### WR-02: CabeÃ§alho aceito no fluxo inicial torna Ver horÃ¡rios inoperante

**Classification:** WARNING
**Resolution:** fixed â€” o corte arbitrÃ¡rio de 4000 foi removido; o orÃ§amento usa o rÃ³tulo de pÃ¡gina efetivo e preserva horÃ¡rios e endereÃ§o. IdentificaÃ§Ã£o que realmente nÃ£o cabe gera alerta. Confirmado por `test_cabecalho_longo_que_cabe_abre_lista`, `test_identificacao_excessiva_informa_erro` e a paginaÃ§Ã£o de 1440 horÃ¡rios.
**File:** `onibus/telegram_handlers.py:138-139`
**Issue:** O limite arbitrÃ¡rio de 4000 caracteres do cabeÃ§alho rejeita mensagens que ainda caberiam no limite de 4096. O chamador captura o ValueError e retorna sem explicaÃ§Ã£o. ReproduÃ§Ã£o com `ConsultaSaidas` de linha 11, nome Circular e endereÃ§o de 3950 caracteres: artigo de seleÃ§Ã£o tem 3993 caracteres, prÃ³ximas saÃ­das 4021, mas `_paginas_horarios` lanÃ§a ValueError. O usuÃ¡rio consegue chegar ao botÃ£o e o clique nÃ£o produz efeito, embora essa identificaÃ§Ã£o mais uma lista curta caiba em uma mensagem. A entrada nÃ£o Ã© limitada pelo parser/publicador a um tamanho menor.
**Fix:** Calcular o orÃ§amento pelo cabeÃ§alho e rodapÃ© efetivamente produzidos, em vez de rejeitar todo cabeÃ§alho acima de 4000; reservar espaÃ§o para pelo menos um horÃ¡rio. Quando nem a identificaÃ§Ã£o mÃ­nima couber, responder explicitamente e preservar a aÃ§Ã£o Voltar. Adicionar teste de fronteira que atravesse o fluxo inicial e abra a lista completa.

---

RevisÃ£o sem alteraÃ§Ãµes de implementaÃ§Ã£o ou commits. As reproduÃ§Ãµes utilizaram objetos em memÃ³ria e banco temporÃ¡rio.
