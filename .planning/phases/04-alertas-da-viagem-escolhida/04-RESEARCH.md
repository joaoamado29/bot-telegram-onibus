# Fase 4 — Alertas da viagem escolhida — Pesquisa

**Data:** 2026-11-16  
**Confiança:** Alta para os contratos locais e da fila. A entrega no aplicativo requer aceite.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Decisões

- **D-01.** Oferecer os atalhos **10 min**, **15 min**, **20 min** e **30 min**. Mostrar somente os que permitem enviar o primeiro aviso antes da saída. Após o primeiro aviso, enviar a contagem a cada cinco minutos até a mensagem final, usando os textos aprovados nos requisitos.
- **D-02.** Se a viagem ainda estiver no futuro e nenhum atalho couber, oferecer **Só no horário da saída** e informar “Está em cima da hora. Posso avisar no horário da saída.” Essa escolha agenda apenas a mensagem final.
- **D-03.** Manter um alerta ativo por passageiro. Ao tentar agendar outra viagem, oferecer **Substituir alerta**. Manter o alerta atual até que a substituição seja confirmada e a nova viagem possa ser agendada. Navegar pelo bot e tocar novamente em um botão não deve duplicar alertas nem afetar outros passageiros.
- **D-04.** Confirmar um agendamento bem-sucedido com “🔔 Alertas ativados para a linha <Número - Nome>.” Para uma antecedência, acrescentar “Você receberá avisos antes da saída.” Na modalidade final, usar “Você receberá um aviso no horário da saída.”

### Escopo posterior

Recuperação após reinício e cancelamento avulso pertencem à Fase 5.
</user_constraints>

## Resumo

Adicionar **Notificar** às próximas saídas. A mensagem inline fornece a identidade de quem clicou, mas a API entrega `inline_message_id` em vez de uma mensagem convencional. Encaminhar o clique a um `/start` parametrizado no chat privado e continuar ali a escolha de saída, antecedência e confirmação. O Telegram documenta a abertura de `t.me/<bot>?start=<parâmetro>` pela resposta ao callback e exige que o usuário inicie a conversa para o bot enviar mensagens privadas. [CITED: https://core.telegram.org/bots/api#callbackquery] [CITED: https://core.telegram.org/bots/api#answercallbackquery] [CITED: https://core.telegram.org/bots/features#deep-linking] [CITED: https://core.telegram.org/bots#how-are-bots-different-from-users]

Usar um agendador em memória por aplicação com `JobQueue.run_once` e uma versão por alerta. Preservar os jobs antigos até confirmar a criação de toda a nova sequência. Manter o destino privado, a saída e a antecedência no próprio alerta para que a navegação subsequente fique independente. [CITED: https://docs.python-telegram-bot.org/en/v22.8/telegram.ext.jobqueue.html#telegram.ext.JobQueue.run_once]

## Architectural Responsibility Map

| Responsabilidade | Componente | Reuso |
|---|---|---|
| Exibir Notificar e encaminhar ao privado | Handlers Telegram | Rota já registrada em `application.add_handler(CallbackQueryHandler(ponto_callback))`. [VERIFIED: onibus/telegram_handlers.py:24-35] |
| Validar linha, ponto, calendário e horários | Consulta do catálogo SQLite | `proximas_saidas` usa `local = agora.astimezone(BRT)`, comparação estrita e `[:3]`. [VERIFIED: onibus/core.py:226-263] |
| Calcular instantes, substituir e concluir | Serviço de alertas em memória por aplicação | Usar datetimes cientes de fuso e objetos Job da fila instalada. [CITED: https://docs.python-telegram-bot.org/en/v22.8/telegram.ext.jobqueue.html#telegram.ext.JobQueue.run_once] |
| Entregar mensagens | Fila e Bot API | Enviar pelo `chat_id` privado observado no `/start` e armazenado no alerta. [CITED: https://core.telegram.org/bots/api#sendmessage] |

## Standard Stack

- A dependência declarada é `python-telegram-bot[job-queue]==22.8`. O import local confirmou PTB 22.8 e APScheduler 3.11.3. [VERIFIED: requirements.txt:1-4 e probe de importação no venv]
- Reusar a instalação atual. O coletor já agenda com `job_queue.run_once(self._job_inicial, when=1.0, name="coleta_inicial_bootstrap")`. [VERIFIED: onibus/refresh.py:43-56]
- O catálogo já usa callbacks separados `p:`, `h:` e `b:`. Adicionar rotas de alerta com prefixo próprio e ordem de registro que não deixe o handler genérico consumir os callbacks novos. [VERIFIED: onibus/telegram_handlers.py:15-35,229-245]

## Architecture Patterns

### Seleção e envio no privado

1. Acrescentar **Notificar** à resposta da consulta com saídas futuras. Ligar o clique a uma intenção curta e temporária, armazenando identidade de quem clicou, linha, revisão, ponto, data e o conjunto de saídas exibidas. Para manter a correspondência com a tela, carregar a data e os valores apresentados no callback de entrada ou referenciá-los por uma chave opaca. Limitar o payload de callback a 64 bytes e o parâmetro `start` a 64 caracteres do alfabeto permitido. [CITED: https://core.telegram.org/bots/api#inlinekeyboardbutton] [CITED: https://core.telegram.org/bots/features#deep-linking]
2. Responder ao clique com o link privado. Em `/start` parametrizado, confirmar chat privado e dono da intenção. O fluxo normal já responde a `/start` com `switch_inline_query_current_chat=""`, que deve seguir funcionando. Usar a conversa privada também para escolha e substituição, para que essas transições nunca editem uma mensagem compartilhada. [VERIFIED: onibus/telegram_handlers.py:38-50] [CITED: https://core.telegram.org/bots/api#answercallbackquery]
3. Em cada etapa, confirmar revisão, ponto e data e intersectar a seleção com as partidas originalmente exibidas que continuam futuras. Um horário que passou não pode ser trocado automaticamente pelo próximo. Revalidar tempo e opções ao confirmar, inclusive ao abrir um botão compartilhado ou antigo. A leitura atual já fixa revisão e consulta no mesmo snapshot com `conn.execute("BEGIN")`. [VERIFIED: onibus/telegram_handlers.py:203-226]

### Sequência e substituição

- Calcular `saida - timedelta(minutes=n)` para a antecedência escolhida e decrementar cinco minutos até o último valor positivo. Acrescentar a saída uma vez. Filtrar atalhos comparando o instante completo, inclusive segundos, com o relógio de Brasília. A igualdade pode ser aceita como aviso imediato no instante exato. Para final avulso, gerar apenas a saída. [Recomendação derivada de D-01 e D-02]
- Agendar cada evento por `run_once(callback, when=instante_com_fuso, data=evento, chat_id=destino, user_id=dono)`. Guardar os handles retornados. Usar identidade própria de alerta para separar callbacks atrasados da viagem ativa. Empregar a fila existente em vez de loops com sleep ou intervalos dependentes do horário real de execução. [CITED: https://docs.python-telegram-bot.org/en/v22.8/telegram.ext.jobqueue.html#telegram.ext.JobQueue.run_once]
- Modelar a substituição como confirmação vinculada à versão ativa que o usuário viu. Sem `await` entre a validação final de estado e a troca de registro, criar os jobs novos, cancelar os jobs novos que já foram criados se a fila falhar, publicar o novo registro após sucesso e desarmar os jobs antigos. A função de envio confere a versão ativa antes de enviar. Uma confirmação já consumida é idempotente. Confirmação obsoleta nunca substitui uma viagem diferente da que o usuário viu. Uma mensagem cujo envio já começou pode completar enquanto a troca ocorre. [Recomendação derivada de D-03]
- Remover o estado ativo quando o job final concluir, inclusive se o Telegram rejeitar a entrega. Vincular a limpeza à mesma versão para impedir que o final antigo remova um alerta recém-ativado. Evitar enviar contagens vencidas após o horário de saída. Usar uma tolerância de atraso limitada para que um atraso normal da fila não suprima todos os avisos. [Recomendação derivada de ALERT-02 e ALERT-04]
- Guardar data, hora, linha, ponto, destino e antecedência como dados independentes dos handles. Essa separação permite à Fase 5 persistir dados e reconstruir jobs. A Fase 4 mantém os alertas somente com o processo ativo. [Decisão de escopo de 04-CONTEXT.md]

## Project Constraints (from AGENTS.md)

Seguir o GSD para edições, preservar SQLite e linhas existentes e manter a interface em português. Usar o horário de Brasília. Manter anotações de tipo, nomes em snake_case, consultas parametrizadas e efeitos externos por pontos de entrada explícitos. [VERIFIED: AGENTS.md, Constraints, Conventions e GSD Workflow Enforcement fornecidos no contexto do projeto]

<phase_requirements>
## Phase Requirements

| ID | Cobertura de planejamento |
|---|---|
| BOT-03 | Notificar ao lado de Ver horários e Voltar no fluxo de próximas saídas. |
| BOT-07 | Configuração privada, identidade do clique validada e estado indexado por passageiro. |
| ALERT-01 | Escolha de saída e substituição explícita e atômica. |
| ALERT-02 | Primeiro horário e intervalos ancorados na partida, com texto aprovado. |
| ALERT-03 | Atalhos de 10, 15, 20 e 30 minutos filtrados e alternativa de aviso final. |
| ALERT-04 | Mensagem final única e liberação do estado de alerta ativo. |

Fonte de todos os IDs e seus comportamentos. [VERIFIED: .planning/REQUIREMENTS.md:27-40]
</phase_requirements>

## Validation Architecture

Usar o venv Python e `unittest`. O projeto já exercita handlers com banco de dados temporário e relógio injetado. Simular a fila para verificar datetimes, dados, handles removidos e mensagens sem esperar minutos reais. [VERIFIED: tests/test_telegram_handlers.py:64-78]

| Requisitos | Testes a planejar |
|---|---|
| BOT-03, BOT-07 | Notificar na resposta normal, sem chat em callback inline, /start parametrizado privado de dono correto, rejeitar outro usuário, navegação normal preservada. |
| ALERT-01, BOT-07 | Duplo clique e clique obsoleto, confirmar substituição com sucesso, falhar parcialmente na criação da nova fila e manter a viagem anterior, isolar dois passageiros. |
| ALERT-02, ALERT-03 | Saída às 12h com 10 minutos gera 11h50 e 11h55. Testar 15, 20 e 30, limite com segundos, queda abaixo de dez e atraso entre tela e confirmação. |
| ALERT-04 | Final às 12h uma vez e limpeza do estado. Job anterior que dispara após a troca permanece inerte. |

Comando focado `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v`. Suíte `.venv/Scripts/python.exe -m unittest discover -s tests -p test_*.py -v`. Usar ao menos um teste em entrada real do handler e agendamento simulado como primeira fatia. Reservar aceite real para confirmar o redirecionamento ao privado e o recebimento da mensagem no aplicativo.

## Security Domain

- Identidade e isolamento de autorização. Usar a identidade do update Telegram e o chat privado validado. Vincular o identificador da intenção ao dono, à validade e à revisão. Garantir limpeza de intenções vencidas. [CITED: https://core.telegram.org/bots/api#callbackquery]
- Validação. Tratar dados de botões como entrada não confiável. Validar formatos, tamanho, data, existência da viagem e atalho elegível. A API alerta que o callback pode conter dados ausentes dos botões atuais da mensagem. [CITED: https://core.telegram.org/bots/api#callbackquery]
- Segredo e contexto. Manter tokens reais e mensagens privadas fora dos testes e dos logs. Exercitar o envio por mock e reservar a integração ao procedimento de aceite existente. [Recomendação]

## Sources

- [Telegram Bot API — CallbackQuery](https://core.telegram.org/bots/api#callbackquery)
- [Telegram Bot API — answerCallbackQuery](https://core.telegram.org/bots/api#answercallbackquery)
- [Telegram — Deep Linking](https://core.telegram.org/bots/features#deep-linking)
- [python-telegram-bot v22.8 — JobQueue](https://docs.python-telegram-bot.org/en/v22.8/telegram.ext.jobqueue.html)
