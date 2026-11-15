---
phase: 02-calend-rio-local-e-consulta-completa
reviewed: 2026-11-15
depth: standard
files_reviewed: 2
files_reviewed_list:
  - onibus/telegram_handlers.py
  - tests/test_telegram_handlers.py
incremental_plan: "02-03"
historical_scope: "A revisão inicial cobriu holidays.py, core.py, telegram_handlers.py, test_schedules.py, test_telegram_handlers.py e README.md; achados resolvidos preservados abaixo."
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
  necessity: 0
resolved_findings: [CR-01, WR-01, WR-02]
resolved_count: 3
status: clean
---

# Fase 02: revisão de código

## Summary

Revisão standard da árvore atual e reavaliação das correções: **zero findings abertos, três resolvidos**. A transação explícita mantém revisão e horários no mesmo snapshot; callbacks inválidos recebem uma única resposta explicativa; o orçamento de paginação usa o cabeçalho e rótulo reais. Os 16 testes dos handlers passaram nesta reavaliação, incluindo as quatro regressões adicionadas para os achados. Não foram encontradas regressões significativas nas correções. Os achados originais abaixo permanecem como histórico, todos encerrados.

## Narrative Findings (AI reviewer)

### Revisão incremental do plano 02-03

Nenhum novo achado comprovado no diff de `onibus/telegram_handlers.py` e `tests/test_telegram_handlers.py`. O helper `_botao_buscar_outra_linha` em `telegram_handlers.py:52` constrói uma ação inline com consulta vazia; os três pontos de construção do teclado a reutilizam, sem acrescentar callback nem estado mutável. `_voltar` reaproveita o artigo, portanto também recebe a ação. O comportamento do parâmetro vazio foi conferido na documentação da biblioteca instalada. A busca continua entrando por `inline_query` e `buscar_sugestoes`, com validações e parâmetros SQL existentes.

Foram executados os 17 testes dos handlers nesta revisão (0.783s, exit 0), incluindo ação única nos pontos, retorno, próximas saídas, indisponibilidade, encerramento e cada página dos 1.440 horários. As asserções conferem consulta vazia e ausência de `callback_data`; o ciclo Voltar e a preservação de data continuam exercitados. Não foram introduzidos novos achados de necessidade.

**T-02-05:** mitigação presente: busca inline existente reutilizada, sem nova entrada de callback nem acesso ao banco. **BOT-04/BOT-05:** cobertura preservada e ampliada pelo teste `test_buscar_outra_linha_em_pontos_consultas_e_retorno` e pelas asserções em `test_lista_extensa_pagina_sem_perdas`. A interação real do cliente Telegram ainda requer confirmação humana; esta revisão não a declara executada.

Os três achados históricos a seguir continuam resolvidos e não representam achados abertos do plano 02-03.

## Critical Issues

### CR-01: Validação da revisão e leitura de horários não compartilham um snapshot

**Classification:** BLOCKER
**Resolution:** fixed — `BEGIN` antes de ler a revisão preserva o snapshot até fechar a conexão. Confirmado por `test_consulta_mantem_snapshot_durante_publicacao`, com publicação concorrente em WAL sem trocar Terminal A pelos novos dados.
**File:** `onibus/telegram_handlers.py:176-179`
**Issue:** `_consultar` lê a revisão em um SELECT e depois chama `proximas_saidas`, que lê novamente os pontos e horários. A conexão não inicia uma transação de leitura; no sqlite3 utilizado, o SELECT isolado não mantém um snapshot entre esses comandos. A atualização semanal pode publicar uma nova revisão entre a validação e a consulta, fazendo um botão antigo mostrar outro endereço e horários. A nova ação `h` reutiliza essa fronteira sem proteção, contrariando a garantia de rejeitar revisão obsoleta antes de exibir dados. Reprodução determinística, sem alterar arquivos: publicar revisão 1 com Terminal A/12:00; intercalar publicação da revisão 2 com Terminal NOVO/13:00 imediatamente antes da chamada real a `proximas_saidas`; `_consultar(db,11,1,1,agora)` retorna Terminal NOVO e 13:00 em vez de recusar ou manter a revisão 1.
**Fix:** Iniciar explicitamente uma transação de leitura antes do primeiro SELECT e manter a validação de revisão, pontos e horários dentro do mesmo snapshot, fechando-a antes de editar a mensagem. Alternativamente, carregar revisão/endereço/coleção por uma única consulta SQL e validar a revisão do próprio resultado. Acrescentar teste determinístico com publicação intercalada.

## Warnings

### WR-01: Datas e páginas inválidas são confirmadas sem mensagem de erro

**Classification:** WARNING
**Resolution:** fixed — os caminhos de data/página inválida retornam alerta em português sem confirmação vazia prévia. Confirmado por `test_data_e_pagina_invalidas_explicam_erro`.
**File:** `onibus/telegram_handlers.py:199-224`
**Issue:** Depois de `query.answer()` sem texto, o handler retorna silenciosamente quando uma data sintaticamente válida é impossível ou a página excede o conjunto atual. Por exemplo, `h:11:1:1:20260231:0` e `h:11:1:1:20261113:9999` não alteram a mensagem e não explicam o problema. Os testes verificam somente a ausência de edição, deixando essa ausência de resposta passar. O contrato do plano exige resposta segura para callback inválido e orientação para refazer a busca quando necessário.
**Fix:** Validar a data antes de confirmar o callback e responder com mensagem em português para data/página inválida; fazer o mesmo para falha de formatação. Manter uma única confirmação por caminho e testar seu texto, além da ausência de edição indevida.

### WR-02: Cabeçalho aceito no fluxo inicial torna Ver horários inoperante

**Classification:** WARNING
**Resolution:** fixed — o corte arbitrário de 4000 foi removido; o orçamento usa o rótulo de página efetivo e preserva horários e endereço. Identificação que realmente não cabe gera alerta. Confirmado por `test_cabecalho_longo_que_cabe_abre_lista`, `test_identificacao_excessiva_informa_erro` e a paginação de 1440 horários.
**File:** `onibus/telegram_handlers.py:138-139`
**Issue:** O limite arbitrário de 4000 caracteres do cabeçalho rejeita mensagens que ainda caberiam no limite de 4096. O chamador captura o ValueError e retorna sem explicação. Reprodução com `ConsultaSaidas` de linha 11, nome Circular e endereço de 3950 caracteres: artigo de seleção tem 3993 caracteres, próximas saídas 4021, mas `_paginas_horarios` lança ValueError. O usuário consegue chegar ao botão e o clique não produz efeito, embora essa identificação mais uma lista curta caiba em uma mensagem. A entrada não é limitada pelo parser/publicador a um tamanho menor.
**Fix:** Calcular o orçamento pelo cabeçalho e rodapé efetivamente produzidos, em vez de rejeitar todo cabeçalho acima de 4000; reservar espaço para pelo menos um horário. Quando nem a identificação mínima couber, responder explicitamente e preservar a ação Voltar. Adicionar teste de fronteira que atravesse o fluxo inicial e abra a lista completa.

---

Revisão sem alterações de implementação ou commits. As reproduções utilizaram objetos em memória e banco temporário.
