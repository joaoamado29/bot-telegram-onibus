# Feature Research

**Domain:** Consulta de horários de ônibus e alertas pelo Telegram
**Researched:** 2026-11-13
**Confidence:** MEDIUM

## Feature Landscape

O escopo confirmado vem de `.planning/PROJECT.md` e das respostas do usuário. As fontes externas verificam capacidades da plataforma e padrões de calendário; não comprovam a estrutura atual do Tonoponto nem transformam sugestões em requisitos aprovados. A confiança MEDIUM segue `classify-confidence --provider websearch --verified`.

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `/start` e escolha de linha | Entrada explícita no fluxo confirmado | LOW | CONFIRMADO. Telegram oferece comandos, teclados de resposta e botões [S1]. |
| Endereços da linha selecionada | Passageiro precisa identificar onde embarcar | MEDIUM | CONFIRMADO. Usar o endereço visível e uma identidade interna; nomes iguais não garantem que sejam o mesmo ponto. |
| Próximos três horários | Principal resposta esperada após escolher o ponto | MEDIUM | CONFIRMADO. Ordenar apenas horários elegíveis do ponto e da data; não inventar três resultados quando restarem menos. |
| Calendário automático e horário de Brasília | A mesma linha pode operar diferente conforme o dia | HIGH | CONFIRMADO. Dias úteis, sábados e domingos/feriados; fonte e abrangência dos feriados ainda pendentes. |
| Ver todos os horários | Permite planejar além das três próximas saídas | LOW | CONFIRMADO. Preservar linha, ponto e data na apresentação. |
| Voltar para os endereços | Evita reiniciar toda a consulta ao escolher outro ponto | LOW | CONFIRMADO. Manter a linha selecionada. |
| Aviso de término e opção de amanhã | Não deixar o usuário sem orientação após a última saída | MEDIUM | CONFIRMADO. Amanhã deve usar seu próprio calendário. |
| Seleção de saída e antecedência em minutos | Associa o lembrete à viagem pretendida | MEDIUM | CONFIRMADO. Precisam ser definidos limites e validação do valor informado. |
| Alertas em intervalos de cinco minutos | Comportamento pedido pelo usuário | HIGH | CONFIRMADO. Mensagem: `Faltam {minutos_faltantes} para o onibus!`; exemplo aprovado de 12h: 11h50 e 11h55. |
| Mensagem final e encerramento | Define fim do acompanhamento daquela viagem | MEDIUM | CONFIRMADO. `Está no horário do ônibus!` na saída. |
| Dados de ponto e horário corretamente associados | Um horário de outro ponto invalida a consulta | HIGH | CONFIRMADO. Validar extração e correspondência antes da interface; não alinhar listas por índice sem evidência do HTML. |
| Horários obrigatórios dos pontos 1 e 2 | Restrição expressa de integridade | MEDIUM | CONFIRMADO. A política para rejeitar/informar páginas incompletas deve ser fechada no planejamento. |
| Estado isolado por passageiro | Consultas simultâneas não podem misturar escolhas | MEDIUM | RECOMENDAÇÃO TÉCNICA para cumprir o fluxo multiusuário; não exige cadastro separado. |
| Mensagens para dados indisponíveis ou entradas inválidas | Evita confundir falha de coleta com fim do serviço | MEDIUM | RECOMENDAÇÃO a incluir na validação do escopo. |

O Telegram recomenda interações estruturadas por comandos e teclados para tarefas previsíveis [S2]. Botões inline são adequados às ações contextuais; callbacks devem receber resposta da aplicação para encerrar o indicador de espera [S3]. Essa recomendação não substitui a necessidade de aceitar a forma de escolha da linha prevista no produto.

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Cancelar um alerta ativo | Permite desistir da viagem sem continuar recebendo mensagens | MEDIUM | SUGESTÃO, NÃO APROVADA. Recomendada para validação de v1. |
| Recuperar alertas após reinício | Mantém a intenção do passageiro durante interrupções do bot | HIGH | POLÍTICA PENDENTE, NÃO APROVADA. Persistência e regras para avisos vencidos precisam ser decididas. |
| Favoritos de linha e ponto | Reduz passos em consultas repetidas | MEDIUM | OPCIONAL, não consta do escopo confirmado. |
| Data da última atualização dos dados | Ajuda a entender a atualidade dos horários | LOW | OPCIONAL; útil se a coleta não ocorrer em toda consulta. |
| Busca textual e paginação para listas longas | Facilita encontrar uma linha no catálogo | MEDIUM | RECOMENDAÇÃO DE UX dependente do tamanho real da lista; não exige Mini App. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Mostrar previsão GPS como se viesse do scraping | Aparente precisão de chegada | A fonte planejada contém horários publicados, sem telemetria confirmada | Exibir horários programados; rastreamento está explicitamente fora do escopo. |
| Pesquisar todas as linhas por endereço como primeira etapa | Reduzir a escolha da linha | Contraria o fluxo aprovado e exige resolver identidade de pontos entre linhas | Escolher linha e depois endereço, como confirmado. |
| Recorrência diária automática dos alertas | Conveniência em deslocamentos repetidos | O escopo encerra os lembretes na viagem selecionada | Um acompanhamento por viagem; recorrência fica fora do escopo atual. |
| Substituir horários ausentes por estimativas | Preencher resultados e manter a interface cheia | Introduz informação não coletada e pode indicar uma viagem inexistente | Informar indisponibilidade ou mostrar apenas saídas válidas. |
| Exigir conta com senha além do Telegram | Parecer uma aplicação completa | Acrescenta atrito sem necessidade confirmada | Associar conversa ao identificador do Telegram; sem novo cadastro proposto. |
| Adotar uma Mini App antes de validar o fluxo | Interface visual extensa | Aumenta a superfície de implementação para uma navegação simples | Começar com mensagens e teclados nativos [S1]. |

## Feature Dependencies

```text
Coleta do catálogo -> Coleta das páginas de cada linha
Coleta detalhada -> Endereços e horários relacionados e validados
Dados validados + Calendário por data + Relógio BRT -> Próximas saídas
/start -> Escolha da linha -> Escolha do endereço -> Próximas saídas
Próximas saídas -> Seleção da viagem -> Antecedência -> Alertas -> Mensagem final
Fim das saídas de hoje -> Opção de amanhã -> Calendário de amanhã
Dados validados -> Ver todos os horários do ponto
```

### Dependency Notes

- O calendário depende de exceções por data, além da rotina semanal. GTFS formaliza essa distinção em `calendar.txt` e `calendar_dates.txt` [S4]; trata-se de referência conceitual, não de obrigação de adotar GTFS ou de evidência de um feed local.
- A classificação genérica de feriado não garante que a operação real siga a tabela de domingo. O produto pede essa seleção; confirmar a regra da fonte e a localidade é necessário antes de prometê-la.
- A API de agendamento permite eventos únicos e repetidos, mas horários sem fuso podem assumir UTC [S5]. A aceitação deve testar a data completa em BRT, especialmente perto da meia-noite.
- Recuperação após reinício e cancelamento são capacidades adicionais a validar; não tratá-las como escopo confirmado apenas por serem tecnicamente recomendáveis.

## MVP Definition

### Launch With (v1)

Proposta baseada no que já foi confirmado, sujeita à aprovação dos requisitos:

- [ ] Extrair endereços e horários por linha e calendário, preservando as duas tabelas relacionadas solicitadas.
- [ ] Validar horários obrigatórios dos pontos 1 e 2; não publicar dados incompletos como se estivessem válidos.
- [ ] Consultar no Telegram: iniciar, escolher linha, escolher endereço e apresentar até três próximas saídas disponíveis.
- [ ] Selecionar automaticamente calendário e horário BRT.
- [ ] Oferecer ver todos os horários e voltar à escolha do endereço.
- [ ] Informar fim do dia e permitir visualizar amanhã.
- [ ] Selecionar uma viagem e antecedência; emitir avisos de cinco em cinco minutos e encerrar com a mensagem final.

### Add After Validation (v1.x)

- [ ] Favoritos — considerar após observar consultas repetidas.
- [ ] Indicador de atualização — considerar quando a política de atualização estiver definida.
- [ ] Melhorias de busca/paginação — ajustar após avaliar volume e uso real das listas.

### Future Consideration (v2+)

- [ ] Alertas recorrentes por dia da semana — fora do escopo atual; nova decisão de produto.
- [ ] Múltiplas fontes ou cidades — exigem identidade de linhas e calendário por origem.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Extração e integridade dos horários e endereços | HIGH | HIGH | P1 |
| Calendário e consultas temporais BRT | HIGH | MEDIUM | P1 |
| Fluxo linha -> ponto -> próximas saídas | HIGH | MEDIUM | P1 |
| Ver todos, voltar e amanhã | HIGH | LOW | P1 |
| Alertas e mensagem final | HIGH | HIGH | P1 |
| Cancelar alerta | HIGH | MEDIUM | P2, validar escopo |
| Recuperar alertas após reinício | HIGH | HIGH | A decidir antes do lançamento |
| Favoritos | MEDIUM | MEDIUM | P3 |

## Competitor Feature Analysis

Não foi realizada comparação de produtos concorrentes: não há evidência suficiente para atribuir funcionalidades a serviços locais. A referência de produto é o fluxo fornecido pelo usuário; a pesquisa externa verifica plataforma e calendário.

| Feature | Referência oficial | Our Approach |
|---------|--------------------|--------------|
| Navegação previsível | Telegram descreve comandos e teclados [S1, S2] | Linha, endereço e ações explícitas no chat. |
| Exceções do serviço | GTFS diferencia semana regular e exceções de data [S4] | Modelar seleção automática sem perder o calendário da origem. |
| Avisos temporizados | JobQueue oferece agendamentos únicos e repetidos [S5] | Executar a sequência aprovada e finalizar na viagem escolhida. |

## Open Product Decisions

1. **Feriados:** qual município/estado e quais exceções de operação considerar? Quem fornece a fonte de datas e a regra da linha?
2. **Antecedência arbitrária:** aceitar qualquer inteiro positivo ou apenas múltiplos de cinco? Para 12 minutos, a leitura literal sugere 12, 7, 2 e mensagem final, mas isso ainda não foi confirmado.
3. **Ativação tardia:** se o início da antecedência já passou, emitir imediatamente, ajustar o primeiro aviso ou recusar? Recomenda-se explicar o comportamento antes de confirmar o alerta.
4. **Reinícios:** recuperar alertas futuros? Descartar, resumir ou reenviar avisos vencidos? A documentação de agendamento não decide essa política de produto.
5. **Menos de três saídas:** recomenda-se mostrar uma ou duas disponíveis, sem completar com amanhã; confirmar no requisito.
6. **Cancelamento e duplicidade:** oferecer cancelar e impedir múltiplos alertas idênticos? Quantas viagens simultâneas por usuário?
7. **Sem dados:** diferenciar ausência de serviço, falha de coleta e tabela incompleta; definir mensagens e política de preservação dos últimos dados válidos.
8. **Pontos e viagens:** confirmar o significado da linha de horários e como ela corresponde aos cinco endereços; o layout real não foi inspecionado nesta dimensão da pesquisa.

## Sources

- Escopo confirmado: `.planning/PROJECT.md`, conversa de definição do projeto e `.planning/config.json`.
- [S1 — Telegram Bot Features](https://core.telegram.org/bots/features), documentação oficial consultada em 2026-11-13. Confiança MEDIUM conforme classificação do provedor verificado.
- [S2 — Telegram Bot Guidelines](https://core.telegram.org/bots/guidelines), orientação oficial de interação; consultada em 2026-11-13. Confiança MEDIUM.
- [S3 — Telegram Bot API: CallbackQuery](https://core.telegram.org/bots/api#callbackquery), obrigação de responder callbacks; consultada em 2026-11-13. Confiança MEDIUM.
- [S4 — GTFS Schedule Reference: calendar_dates.txt](https://gtfs.org/documentation/schedule/reference/#calendar_datestxt), calendário de serviço e exceções; consultada em 2026-11-13. Confiança MEDIUM.
- [S5 — python-telegram-bot JobQueue](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html), documentação estável consultada em 2026-11-13, exibindo v22.8. Confiança MEDIUM. Não comprova persistência automática de lembretes nem garantia de entrega ao passageiro.

---
*Feature research for: Bot Telegram Ônibus*
*Researched: 2026-11-13*
