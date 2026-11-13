# Phase 1: Primeiras consultas no Telegram - Context

**Gathered:** 2026-11-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Entregar coleta detalhada e persistência reais, escolha de linha e endereço pelo Telegram e consulta de até três próximas saídas do dia em Brasília. Abrange DATA-01 a DATA-06, TIME-01, TIME-03, BOT-01 e BOT-02. Feriados completos, consulta de amanhã e alertas permanecem nas fases previstas no roadmap.
</domain>

<decisions>
## Implementation Decisions

### Escolha da linha
- **D-01:** Buscar por número ou parte do nome, mostrando sugestões no formato `123 - Papicu/Rua Doidinho da Silva`.
- **D-02:** Usar sugestões inline do Telegram enquanto o usuário digita `@NomeDoBot 12` ou `@NomeDoBot papicu`, em vez de exigir o envio de cada termo como mensagem na conversa.
- **D-03:** Ao selecionar a sugestão, mostrar diretamente os endereços daquela linha; escolher o endereço consulta os próximos horários, sem uma etapa intermediária de resumo.
- **D-04:** Ignorar acentos e diferenças entre maiúsculas e minúsculas: `joao` encontra `São João`.
- **D-05:** Apresentar dez resultados por página e carregar mais ao rolar.

### Atualização dos dados
- **D-06:** Coletar todo domingo às 01h no fuso `America/Sao_Paulo`.
- **D-07:** Se uma linha falhar, manter seus últimos dados válidos e tentar novamente mais tarde.
- **D-08:** Após uma coleta válida, substituir o conjunto antigo pelo novo, removendo horários que desapareceram da origem; não apenas acumular horários.
- **D-09:** Rejeitar a atualização de uma linha quando a primeira ou segunda coleção obrigatória estiver vazia; preservar os últimos dados válidos e continuar as demais linhas.
- **D-10:** Fazer coleta inicial automática quando ainda não houver horários no banco; depois seguir a atualização semanal.

### Decisões anteriores preservadas
- **D-11:** Manter as duas tabelas solicitadas, com até cinco endereços e cinco coleções independentes de horários separadas por calendário, relacionadas por chave estrangeira. As duas primeiras coleções são obrigatórias.
- **D-12:** Não parear horários de pontos diferentes pelo índice. Preservar listas com tamanhos diferentes e descartar publicidade presente entre os itens de horários.
- **D-13:** Retornar somente as saídas de hoje disponíveis, até três, em ordem; mostrar uma ou duas se não houver três, sem completar com amanhã.

### Detalhes a resolver na pesquisa e no planejamento
Não houve delegação explícita de preferências adicionais. Identidade das tabelas, serialização das coleções, estratégia de retry e seus limites são detalhes técnicos a propor respeitando as decisões acima.

Validar como a seleção inline exibe os endereços e consulta o ponto dentro do Telegram, incluindo o uso em conversa privada iniciada por `/start`, callback e identificadores estáveis. Não presumir que todo resultado inline produza uma atualização de seleção recebida pelo bot; documentar a configuração necessária. Não substituir a experiência inline aprovada por busca via mensagem sem revisão.
</decisions>

<canonical_refs>
## Canonical References

### Escopo e decisões aprovadas
- `.planning/PROJECT.md` — contexto do produto e decisões globais.
- `.planning/REQUIREMENTS.md` — requisitos aprovados e rastreabilidade.
- `.planning/ROADMAP.md` — fronteira e critérios de sucesso da fase 1.
- `.planning/config.json` — fluxo interativo, modelos herdados e execução paralela.

### Evidência e recomendações
- `.planning/research/ARCHITECTURE.md` — inspeção real de pontos, calendários, anúncios e listas com 26/27 horários.
- `.planning/research/STACK.md` — recomendações de integração Telegram e stack existente.
- `.planning/research/SUMMARY.md` — síntese de riscos e decisões aprovadas posteriormente no projeto.
- `.planning/codebase/ARCHITECTURE.md` — fluxo atual de coleta e consulta.
- `.planning/codebase/INTEGRATIONS.md` — origem e contratos de integração atuais.

### Código existente
- `scraping.py` — catálogo, HTTP, parsing e persistência atuais.
- `consulta.py` — leitura e apresentação de linhas.

Nenhum SPEC ou ADR externo foi indicado pelo usuário nesta discussão.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scraping.py:fetch_page` — obtenção de HTML com timeout e validação HTTP.
- `scraping.py:extract_linhas` e `parse_horlink` — catálogo usado para buscar as páginas detalhadas.
- `consulta.py:listar_linhas` — leitura inicial do catálogo para sugestões.

### Established Patterns
- Funções tipadas, dataclasses imutáveis, SQL parametrizado e funções executáveis protegidas por `__main__`.
- `insert_if_new` usa `INSERT OR IGNORE`; esse comportamento não implementa a substituição de horários aprovada.
- Links atuais guardam host e caminho sem esquema; reconstruir e validar antes de buscar detalhes.
- `DB_PATH` é relativo ao diretório de execução; o agendamento precisa usar uma localização consistente.

### Integration Points
- Preservar o catálogo `linhas` em SQLite ao acrescentar as tabelas detalhadas.
- Separar a coleta síncrona do atendimento Telegram para não bloquear a busca e as consultas.
- Ainda não há handlers, configuração de token nem agendador no código do produto.
</code_context>

<specifics>
## Specific Ideas

- Digitar `12` sugere linhas com números correspondentes; digitar `papicu` sugere nomes correspondentes.
- Exemplo visual aprovado: `123 - Papicu/Rua Doidinho da Silva`.
- Horário semanal aprovado: domingo, 01:00, horário de Brasília.
- Ranking entre resultados, entrada inline vazia, rótulos dos endereços e limite exato no minuto atual não foram discutidos; propor padrões coerentes no planejamento sem tratá-los como decisões do usuário.
</specifics>

<deferred>
## Deferred Ideas

Nenhuma nova capacidade fora de escopo foi solicitada. Feriados, navegação completa, amanhã e alertas continuam nas fases 2 a 5 conforme o roadmap.
</deferred>

---
*Phase: 01-primeiras-consultas-no-telegram*
*Context gathered: 2026-11-13*
