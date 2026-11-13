# Architecture Research

**Domain:** Coleta de tabelas de ônibus e bot Telegram com consulta e alertas
**Researched:** 2026-11-13
**Confidence:** MEDIUM — documentação oficial e três páginas reais consultadas; amostra não cobre todas as linhas

## Standard Architecture

### System Overview

Recomenda-se um monólito Python modular, com coleta executada separadamente do atendimento Telegram e SQLite compartilhado por repositórios de acesso. São recomendações de implementação, ainda sujeitas ao planejamento interativo; o escopo confirmado está em `.planning/PROJECT.md`.

```text
Catálogo e páginas da origem
  -> coletor HTTP -> parser puro -> validação -> atualização transacional SQLite

Telegram -> handlers de conversa -> serviço de consulta -> SQLite
                                -> serviço de alertas -> SQLite
                                                     -> JobQueue -> Telegram

Inicialização -> recuperação de alertas pendentes -> JobQueue
Relógio + calendário -> consulta e serviço de alertas
```

**Origem validada:** `scraping.py` configura `https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/`. O catálogo retornou 379 links `a.horLink` na inspeção. A ferramenta web recebeu HTTP 403, mas o coletor Python existente obteve as páginas com sucesso após autorização de rede. Nenhum registro foi inserido ou alterado no banco nessa inspeção.

### Evidência das páginas de horários

O HTML das linhas [004](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-004-messejana-papicu-cambeba-tj/), [011](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-011-circular-i/) e [012](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-012-circular-ii/) confirma a sequência `h2` para ponto, `p.title_p` para calendário e `ul.listaHorarios > li` para horários. Cada página amostrada possui dois pontos. A 004 publica apenas dias úteis, com 26 e 27 horários respectivamente. A 011 tem 33/26/16 horários por ponto para dias úteis/sábados/domingos e feriados; a 012 tem 34/23/16. Existem `li.adInList` de publicidade dentro das listas: contar todo `li` como horário introduz dados inválidos.

Os pontos da 004 são terminais; na 011/012 há também um título com cruzamentos de vias. Portanto, o rótulo de ponto deve preservar o texto da fonte, sem exigir formato de endereço postal. A diferença de contagens na 004 demonstra que a posição de um horário em uma lista não é uma chave de viagem comum aos dois pontos. A amostra não permite afirmar que todas as 379 linhas têm dois pontos, nem inferir operação de fim de semana quando a página não publica esse calendário.

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| Configuração | Localização absoluta do banco, origem permitida, timezone e token fornecido no ambiente | Módulo compartilhado sem segredos em código |
| Coletor | Ler links existentes, reconstruir URLs válidas e buscar páginas com limites | Evolução do fluxo de `scraping.py`, fora de handlers |
| Parser | Produzir blocos de calendário, endereços e coleções de horários | Funções puras Beautiful Soup com fixtures |
| Validador | Impedir importação inconsistente ou incompleta | Regras de domínio antes da transação |
| Repositórios | SQL parametrizado, migrações e integridade | `sqlite3`, conexões curtas por operação |
| Calendário e relógio | Resolver data local, tipo de dia e horários conscientes de fuso | Serviço injetável e testável |
| Consulta | Linhas, pontos, todos os horários e até três futuros de hoje | Funções sem dependência Telegram |
| Conversa | `/start`, escolha de linha, endereço e ações | Handlers e estado por usuário/chat |
| Alertas | Salvar a viagem escolhida e derivar instantes de envio | Estado durável + tarefas identificadas |
| Entrega | Enviar mensagens e registrar resultado | Adaptador Telegram e política de repetição |

## Recommended Project Structure

```text
scraping.py                  # Entrada existente de coleta
consulta.py                  # Entrada existente de consulta no terminal
bot.py                       # Nova entrada Telegram, sem lógica de domínio
onibus/
  config.py                  # Configuração compartilhada
  models.py                  # Tipos de intercâmbio
  storage.py                 # Conexões, migrações, repositórios
  scraping.py                # Coleta detalhada e parser
  calendar.py                # Tipo de serviço por data
  schedules.py               # Consultas e comparação temporal
  reminders.py               # Alertas e recuperação
  telegram_handlers.py       # Conversa e apresentação
tests/
  fixtures/                  # Exemplos de HTML obtidos de fonte validada
  test_scraping.py
  test_schedules.py
  test_reminders.py
```

### Structure Rationale

- `scraping.py` e `consulta.py` continuam utilizáveis como entradas; a extração de lógica compartilhada ocorre quando necessária à extensão.
- `onibus/` evita que o bot dependa de uma entrada CLI e impede duplicação das regras de consulta.
- `tests/` concentra provas do relacionamento entre ponto/calendário/horário e dos limites de data.
- Caminhos são sugestões de organização; não representam arquivos já implementados.

## Architectural Patterns

### Pattern 1: Coleção validada antes da publicação

**What:** Buscar e interpretar uma linha inteira antes de atualizar sua versão publicada.
**When to use:** Atualização dos horários e endereços da mesma linha.
**Trade-offs:** Usa uma pequena área temporária em memória, mas evita que o bot leia metade de uma atualização.

**Example:**

```python
blocks = parse_schedule_page(html)
validated = validate_schedule_blocks(blocks)
repository.replace_line_schedule(numero, validated)
```

O repositório deve trocar endereços e horários na mesma transação, preservando o conjunto anterior quando o parser falhar. Não confundir uma página bloqueada ou selector ausente com uma tabela legitimamente vazia. A política de atualização é uma recomendação nova: o coletor existente apenas ignora linhas já cadastradas.

### Pattern 2: Relacionamento explícito entre as duas tabelas pedidas

**What:** Preservar `horarios(numero, nome, horario_ponto1..horario_ponto5)` e `enderecos(numero, nome, ponto1..ponto5)`, acrescentando identidades e calendário necessários à integridade.
**When to use:** Persistência das tabelas detalhadas.
**Trade-offs:** A forma de cinco colunas atende ao pedido; exige um adaptador para consultas por ponto e um limite explícito quando a fonte apresentar mais de cinco posições.

Recomendações para definir na fase de dados:

1. `enderecos.id` como chave estável do conjunto de pontos; `horarios.enderecos_id` como FK direta. Ambos mantêm `numero` e `nome` solicitados e o número se relaciona ao catálogo `linhas`.
2. Separar conjuntos por sentido/variante caso a fonte tenha mais de um para a mesma linha. `numero` sozinho não identifica um grupo de horários.
3. Adicionar um discriminador de calendário a `horarios`; uma linha pode ter várias tabelas conforme o dia. Não criar apenas uma coluna global por número que sobrescreva sábado ao importar dias úteis.
4. `horario_ponto1` e `horario_ponto2` precisam de `NOT NULL` e validação de conteúdo: string vazia ou coleção vazia também viola o requisito. Pontos 3–5 ausentes não devem receber horários inventados.
5. Habilitar `PRAGMA foreign_keys = ON` em cada conexão antes da transação. A chave referenciada deve ser primária ou única. Isso também permite testar rejeição de órfãos. [SQLite — foreign keys](https://www.sqlite.org/foreignkeys.html)

**Cardinalidade recomendada após a inspeção:** cada registro de `horarios` deve representar um calendário do conjunto de pontos, com uma coleção de horários por coluna, por exemplo JSON validado. As listas reais são independentes e a linha 004 tem contagens diferentes entre pontos. Essa proposta preserva as duas tabelas solicitadas sem fabricar alinhamentos entre viagens; a representação das coleções ainda exige confirmação no planejamento. Não usar uma linha de banco por índice das listas. O serviço de consulta pode converter a coleção do ponto escolhido em horários tipados em memória. Se futuramente for necessária uma linha por viagem, será preciso obter uma fonte que comprove essa correspondência.

### Pattern 3: Relógio injetável e data de serviço explícita

**What:** Receber `now` no serviço e resolver o calendário para a data da consulta.
**When to use:** Próximas saídas, amanhã e criação de alertas.
**Trade-offs:** Um pouco mais de passagem de parâmetros permite testes determinísticos.

Use `ZoneInfo("America/Sao_Paulo")`, não o fuso do computador nem uma hora sem data. `zoneinfo` usa dados IANA do sistema ou `tzdata`; a dependência de dados de fuso precisa ser assegurada no Windows. [Python — zoneinfo](https://docs.python.org/3/library/zoneinfo.html)

Exemplo conceitual: resolver calendário de `now.date()`, combinar cada horário com essa data no fuso configurado, ordenar e selecionar até três instantes futuros. Se houver um ou dois, mostrar os existentes; se não houver, retornar estado de fim do dia e oferecer amanhã, sem incluir amanhã silenciosamente. A inclusão de uma partida exatamente no instante da consulta exige definição na fase de consulta.

O calendário deve aceitar exceções por data para feriados e operação especial. Fonte dos feriados e localidade permanecem pendentes; documentação de biblioteca não comprova a política de operação da linha.

### Pattern 4: Alertas persistidos, agendador como executor

**What:** Armazenar a intenção do usuário antes de agendar mensagens; reconstruir tarefas pendentes ao iniciar o processo.
**When to use:** Notificação selecionada para uma viagem específica.
**Trade-offs:** Exige uma tabela operacional adicional, proposta para aprovação; evita tratar memória do processo como fonte durável.

Persistir, como recomendação, `reminder_id`, usuário/chat, linha, ponto, instante absoluto da viagem, antecedência, status e eventos de entrega. A tabela operacional não substitui as duas tabelas de domínio solicitadas. A recuperação após reinício não foi confirmada pelo usuário e deve ser explicitada como requisito antes da implementação.

Gerar os instantes a partir da saída: saída menos antecedência; incrementos de cinco minutos enquanto anteriores à saída; evento final no horário da saída. Agendar datas completas conscientes de fuso, nunca apenas `datetime.time`, que pode cair no dia seguinte. O `JobQueue.run_once` aceita instantes específicos; callbacks são assíncronos. [PTB — JobQueue](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html)

Usar identidade única de evento, como `(reminder_id, scheduled_at, event_kind)`, para evitar agendamento duplicado. Persistência de conversa em PTB é uma interface distinta; não assumir que salvar `user_data` salva a agenda da aplicação. [PTB — BasePersistence](https://docs.python-telegram-bot.org/en/stable/telegram.ext.basepersistence.html)

Não prometer entrega exatamente uma vez: uma queda entre o envio aceito pelo Telegram e a gravação de sucesso deixa uma janela de duplicação. Definir política de repetição e eventos atrasados. Uma recomendação conservadora é pular contagens vencidas e recuperar apenas eventos futuros; isso requer aceite do comportamento esperado após indisponibilidade.

## Data Flow

### Request Flow

1. `/start` abre a escolha de linha; a busca/lista consulta o catálogo local.
2. A linha selecionada fornece apenas seus endereços; cada ação usa um identificador validado.
3. O ponto selecionado chama o serviço de consulta com relógio local atual e data de serviço.
4. A resposta apresenta saídas e as ações confirmadas: notificar, ver horários e voltar.
5. Notificar escolhe uma viagem, recebe minutos, revalida que ela ainda é futura e salva a intenção.
6. Cada execução verifica status e instante da viagem, entrega a mensagem e encerra no evento final.

### State Management

- Estado de navegação: usuário/chat, linha e ponto selecionados, etapa de escolha de alerta.
- Estado de domínio: catálogo, endereços, calendários e horários em SQLite.
- Estado operacional proposto: lembretes e eventos pendentes em SQLite.
- Configurar processamento sequencial de updates ao usar `ConversationHandler`: essa é a recomendação explícita da documentação. Paralelismo dos planos de desenvolvimento não significa concorrência ilimitada nos handlers. [PTB — ConversationHandler](https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html)

### Key Data Flows

- **Coleta:** link armazenado sem esquema -> URL HTTPS validada -> página -> blocos -> validação -> commit atômico.
- **Atualização:** falha de coleta preserva a versão válida anterior e registra falha; horário desconhecido não vira ausência de ônibus.
- **Consulta:** endereço + data -> calendário -> coleção do ponto -> horários ordenados -> resultado explícito.
- **Amanhã:** resolver novamente o calendário da próxima data, especialmente na transição sexta/sábado ou véspera de feriado.
- **Reinício proposto:** ler lembretes ativos -> descartar/expirar o que a política determinar -> recriar eventos futuros por identidade.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Uso inicial | Um processo bot, coleta em tarefa separada e SQLite com operações curtas; medir comportamento real |
| Muitos alertas simultâneos | Limitar fila de entrega, tratar rate limits e medir atraso; um único dono do agendamento |
| Necessidade de várias réplicas | Introduzir coordenação de entrega e avaliar banco servidor antes de iniciar múltiplos schedulers |

### Scaling Priorities

1. **First bottleneck:** Coleta síncrona dentro do loop assíncrono atrasa todos os usuários e alertas. Executar coleta em comando/processo separado; se houver chamada sob demanda, delegar I/O bloqueante com isolamento de conexões. `asyncio.to_thread` é o mecanismo padrão disponível para I/O bloqueante. [Python — asyncio](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.to_thread)
2. **Second bottleneck:** Muitas mensagens na mesma janela exigem fila e tratamento de respostas de limite. Não inferir capacidade por quantidade de usuários cadastrados; medir mensagens por segundo e atraso efetivo. [Telegram Bot API](https://core.telegram.org/bots/api)

## Anti-Patterns

### Anti-Pattern 1: Achatar todos os `li` da página

**What people do:** Capturar todo texto de listas e associar por índice aos títulos `h2`.
**Why it's wrong:** Pode misturar navegação, calendários e direções; comprimentos diferentes não garantem correspondência de viagens.
**Do this instead:** Percorrer `h2`, `p.title_p` e `ul.listaHorarios` em ordem, preservando ponto e calendário correntes, e aceitar apenas itens com horário válido. Fixar exemplos reais em testes antes de ampliar para todo o catálogo.

### Anti-Pattern 2: Relacionar tabelas apenas por nome

**What people do:** Juntar nome ou número sem identificar calendário e conjunto de pontos.
**Why it's wrong:** O nome é metadado mutável, e o número pode conter vários blocos.
**Do this instead:** Definir identidade de conjunto e FK explícita, mantendo as colunas pedidas como dados do domínio.

### Anti-Pattern 3: Dormir dentro do handler

**What people do:** Manter um `sleep` de minutos na conversa ou executar requests síncrono no callback.
**Why it's wrong:** Prende processamento e mistura navegação com ciclo de vida da viagem.
**Do this instead:** Handler grava intenção e retorna; jobs executam eventos independentes com data completa.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Origem de horários | HTTP com timeout, domínio permitido e validação de conteúdo | Catálogo e três páginas reais validados com o coletor existente |
| Telegram | Adaptador PTB; polling inicial é suficiente como proposta operacional | Token via ambiente, sem envio real na pesquisa |
| Calendário de feriados | Provedor injetável por data e localidade | Fonte e regras operacionais precisam ser confirmadas |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Parser -> repositório | Estruturas validadas | Sem gravação durante parsing |
| Handler -> consulta | Parâmetros tipados e resultados de domínio | Sem scraping na navegação |
| Alertas -> entrega | Evento com identificador e instante | Registro de status separado da conversa |
| Repositório -> SQLite | SQL parametrizado e transações curtas | FK habilitada em todas as conexões |

## Build Order and Open Decisions

1. Capturar fixtures das estruturas reais observadas e ampliar a amostra para linhas com outros números de pontos ou calendários ausentes.
2. Definir cardinalidade das duas tabelas, migração e política de atualização; provar integridade e consulta por ponto.
3. Implementar relógio/calendário e consultas de hoje/amanhã com testes de borda.
4. Entregar o fluxo Telegram linha -> endereço -> próximos horários e navegação.
5. Adicionar seleção de viagem, antecedência, entrega a cada cinco minutos e finalização.
6. Validar recuperação operacional, indisponibilidade e atualização dos dados conforme os requisitos que forem aprovados.

Antes de fechar requisitos, decidir: localidade e calendários excepcionais, representação da coleção de horários, dados obrigatórios ausentes, antecedência não múltipla de cinco, criação de alerta após o primeiro instante e recuperação após reinício. Calendário ausente deve produzir indisponibilidade explícita, não reaproveitar dias úteis automaticamente. Não é necessário reescrever o catálogo existente nem introduzir servidor HTTP próprio para realizar a primeira consulta Telegram.

## Sources

- [PTB ConversationHandler](https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html) — comportamento de conversa e processamento de updates.
- [PTB JobQueue](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html) — agendamento e fuso dos instantes.
- [PTB BasePersistence](https://docs.python-telegram-bot.org/en/stable/telegram.ext.basepersistence.html) — contrato de persistência da biblioteca.
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html) — habilitação e chave referenciada.
- [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html) — dados IANA e fallback `tzdata`.
- [Python asyncio](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.to_thread) — I/O bloqueante fora do event loop.
- [Telegram Bot API](https://core.telegram.org/bots/api) — interface de bot e erros de entrega.
- [Catálogo ETUFOR Fortaleza](https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/) — 379 links observados.
- [Página da linha 004](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-004-messejana-papicu-cambeba-tj/) — dois pontos com contagens diferentes e somente dias úteis na amostra.
- [Página da linha 011](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-011-circular-i/) e [linha 012](https://tonoponto.com/itinerario-horarios-de-onibus/ce-etufor-012-circular-ii/) — três calendários por ponto e publicidade intercalada.
- Evidências locais: `scraping.py`, `.planning/PROJECT.md`, `.planning/codebase/ARCHITECTURE.md`.

As páginas oficiais foram consultadas diretamente em 2026-11-13. A documentação estável PTB exibiu 22.8. O seam `research-plan` sugeriu Context7, mas não há ferramenta Context7 nem CLI `ctx7` disponível; a pesquisa usou páginas oficiais via web. A classificação de confiança do seam para `websearch --verified` retornou MEDIUM. As páginas Tonoponto foram lidas usando `scraping.fetch_page` e Beautiful Soup, sem executar `main()` ou gravar dados. A ferramenta web retornou 403 para o catálogo; o acesso Python autorizado funcionou. As observações são retrato de três linhas e não garantia de estrutura uniforme de todo o catálogo.

---
*Architecture research for: Bot Telegram Ônibus*
*Researched: 2026-11-13*
