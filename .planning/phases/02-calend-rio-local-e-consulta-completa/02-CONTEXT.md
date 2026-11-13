# Phase 2: Calendário local e consulta completa - Context

**Gathered:** 2026-11-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Selecionar automaticamente o calendário de operação aplicável à data local, incluindo feriados nacionais, do Ceará e de Fortaleza; permitir consultar a lista completa de horários do ponto escolhido; e voltar à seleção de pontos da mesma linha. A fase deve distinguir calendário/dados indisponíveis de um calendário válido sem saídas futuras.

</domain>

<decisions>
## Implementation Decisions

### Aplicação do calendário de feriados
- **D-01:** Considerar feriados nacionais, estaduais do Ceará e municipais de Fortaleza. Ponto facultativo não conta como feriado.
- **D-02:** Qualquer feriado reconhecido usa o calendário `domingos_feriados`, mesmo quando cai em sábado ou domingo.
- **D-03:** Quando a consulta for em feriado, a resposta deve mostrar o nome do feriado e a data.
- **D-04:** Se não houver dados ou calendário publicado para a data, informar indisponibilidade; não substituir por outro calendário nem dizer que as saídas terminaram.

### Consulta e navegação no Telegram
- **D-05:** “Ver horários” mostra todos os horários do ponto selecionado, preservando a identificação do ponto e do tipo de dia.
- **D-06:** “Voltar” retorna à escolha dos endereços da mesma linha, sem reiniciar o fluxo.
- **D-07:** A resposta diferencia calendário indisponível de saídas futuras esgotadas no dia.

### the agent's Discretion
- Escolher fontes oficiais verificáveis e a forma de manter a lista de feriados atualizada, sem incluir pontos facultativos.
- Escolher o formato de armazenamento e a implementação de calendário, mantendo o fuso `America/Sao_Paulo` como referência.
- Ajustar a apresentação completa para os limites de mensagem do Telegram, preservando todos os horários e permitindo a navegação definida acima.

</decisions>

<canonical_refs>
## Canonical References

### Escopo e requisitos
- `.planning/ROADMAP.md` — objetivo, fronteiras e critérios de sucesso da fase 2.
- `.planning/REQUIREMENTS.md` — requisitos TIME-02, TIME-04, BOT-04 e BOT-05.
- `.planning/PROJECT.md` — decisões aprovadas sobre calendário local, feriados e fluxo do Telegram.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `onibus/core.py`: `ConsultaSaidas`, `proximas_saidas`, `carregar_pontos` e acesso SQLite podem sustentar a consulta completa e a escolha do calendário.
- `onibus/telegram_handlers.py`: `formato_saidas`, `ponto_callback`, `_consultar` e `build_application` são os pontos de extensão para resposta completa e navegação.

### Established Patterns
- O banco é SQLite e as conexões curtas são abertas por `conectar` e fechadas com `contextlib.closing`.
- Horários são separados por calendário e por ponto; listas pertencem ao endereço selecionado.
- Handlers Telegram são assíncronos; consultas SQLite executadas pelos handlers usam `asyncio.to_thread`.
- O calendário atual em `proximas_saidas` distingue dias úteis, sábados e domingos/feriados pelo dia da semana; ainda não reconhece feriados civis.

### Integration Points
- A seleção de calendário conecta-se à consulta temporal em `onibus/core.py`.
- A visualização completa e o botão Voltar conectam-se ao callback de ponto em `onibus/telegram_handlers.py`.
- As respostas de dados ausentes e de dia encerrado são formatadas por `formato_saidas`.

</code_context>

<specifics>
## Specific Ideas

- A resposta de feriado identifica explicitamente o nome do feriado e a data consultada.
- O calendário de feriados prevalece sobre sábado ou domingo para qualquer feriado reconhecido.
- O fluxo Ver horários/Voltar deve manter a linha e o ponto selecionados.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-Calendário local e consulta completa*
*Context gathered: 2026-11-13*
