# Fase 3 — Consulta do dia seguinte — Pesquisa

**Data:** 2026-11-16  
**Domínio:** Calendário de operação e navegação inline do Telegram  
**Confiança:** Alta para os fluxos locais verificados

<user_constraints>
## User Constraints (from CONTEXT.md)

### Decisões

- **D-01.** Quando houver horários publicados para amanhã, usar a mensagem “As linhas do onibus <numero - nome> estão encerradas no dia de hoje. Elas voltam a circular a partir de <horário> de amanhã.” O horário é a primeira saída de amanhã no ponto selecionado, conforme o calendário daquela data.
- **D-02.** Exibir o botão **Ver horários de amanhã** quando as saídas de hoje terminarem. Se a primeira saída de amanhã estiver indisponível, informar a indisponibilidade em vez de preencher o horário. A falta de dados de hoje recebe o aviso de indisponibilidade já previsto na Fase 2.
- **D-03.** Mostrar a lista completa de amanhã separadamente, identificando a data e o tipo de dia, com a paginação já usada em **Ver horários**.
- **D-04.** O botão **Voltar** na lista de amanhã abre a escolha de endereço da mesma linha.

### Fases posteriores

- Alertas por viagem pertencem à Fase 4. A revisão geral das mensagens pertence à Fase 6.
</user_constraints>

## Resumo

O fluxo existente de lista completa já aceita data explícita e conserva essa data em cada página. Recomenda-se criar **Ver horários de amanhã** com o mesmo esquema de callback, indicando a data seguinte em Brasília, e reutilizar a navegação de volta da lista completa. Evidência literal: `datetime.strptime(campos[3], "%Y%m%d").replace(tzinfo=BRT)` e `f"h:{numero}:{revisao}:{posicao}:{campos[3]}:{indice}"`. [VERIFIED: onibus/telegram_handlers.py:224-256]

A resposta inicial precisa da primeira saída do dia seguinte apenas quando a consulta de hoje indicar encerramento. Obtenha os dois resultados no mesmo snapshot ao atender a seleção do ponto e use a coleção completa de amanhã para incluir inclusive uma saída às 00:00. Evidência literal do filtro atual: `if datetime.combine(local.date(), time.fromisoformat(valor), tzinfo=BRT) > local` e `todos_horarios=publicados`. [VERIFIED: onibus/core.py:251-267] [VERIFIED: onibus/telegram_handlers.py:183-198]

## Architectural Responsibility Map

| Capacidade | Responsável principal | Apoio |
|---|---|---|
| Determinar dia e calendário de operação | Domínio Python | Catálogo local de feriados |
| Carregar listas da mesma revisão | Adaptador Telegram no backend | Transação SQLite existente |
| Gerar aviso, callback datado, páginas e retorno | Adaptador Telegram no backend | Mensagem inline como superfície de interação |

## Project Constraints (from AGENTS.md)

- Evoluir a base Python/SQLite preservando linhas existentes, integridade dos horários obrigatórios e a relação entre horários e endereços.
- Trabalhar no horário de Brasília e usar dados publicados pela origem.
- Preservar a interação em português no Telegram, com linha antes do endereço.
- Usar snake_case, funções anotadas, parâmetros SQL vinculados e gerenciamento explícito da conexão. Manter efeitos externos atrás dos pontos de entrada já existentes.
- Manter as alterações em um fluxo GSD.

<phase_requirements>
## Phase Requirements

| ID | Requisito | Aplicação |
|---|---|---|
| TIME-05 | Consultar os horários de amanhã usando a data e o calendário correspondentes, sem misturá-los às próximas saídas de hoje. | Calcular a próxima data civil em Brasília e alimentar o callback existente de lista completa. |
| BOT-06 | Quando as saídas de hoje terminarem, o usuário recebe aviso e a opção Ver horários de amanhã. | Aplicar a mensagem definida no contexto à consulta encerrada. Manter o botão quando faltar o calendário de amanhã e apresentar indisponibilidade. |
</phase_requirements>

## Standard Stack

Preservar a infraestrutura existente. O manifesto declara literalmente `python-telegram-bot[job-queue]==22.8` e `tzdata==2026.6`. O ambiente de teste informou `Python 3.11.9`. A proposta não requer dependências adicionais, alterações no banco ou novos contratos de publicação. [VERIFIED: requirements.txt:1-4] [VERIFIED: .venv/Scripts/python.exe --version]

## Architecture Patterns

1. **Data civil.** Converter o relógio para Brasília antes de extrair a data e somar um dia. Usar a data calculada para consultar o calendário, inclusive em viradas de mês e ano. Evidência literal: `BRT = ZoneInfo("America/Sao_Paulo")`, `local = agora.astimezone(BRT)` e `feriados = feriados_em(local.date())`. [VERIFIED: onibus/core.py:19-21] [VERIFIED: onibus/core.py:226-241]
2. **Identidade e revisão.** Estender a consulta inicial preservando contrato dos chamadores existentes ou criar um invólucro de apresentação com o mesmo carregamento transacional. O segundo resultado deve usar a mesma revisão da primeira consulta. Evidência literal: `conn.execute("BEGIN")` e `if pontos is None or pontos["revisao"] != revisao or not pontos[f"ponto{posicao}"]:`. [VERIFIED: onibus/telegram_handlers.py:183-198]
3. **Estados.** Oferecer amanhã quando hoje tiver terminado. Se amanhã estiver indisponível, usar a resposta de indisponibilidade da lista, preservando a data solicitada. Evidência literal de estados: `"indisponivel"`, `"disponivel" if futuros else "encerrado"`. [VERIFIED: onibus/core.py:245-267]
4. **Callback datado.** Gerar o botão amanhã com o modelo já usado pelo botão de lista, fornecendo amanhã como a data marcada. Manter a data absoluta quando a mensagem for aberta após a meia-noite ou ao paginar. Evidência literal: `f"h:{numero}:{revisao}:{posicao}:{consulta.data:%Y%m%d}:0"` e `f"h:{numero}:{revisao}:{posicao}:{campos[3]}:{indice}"`. [VERIFIED: onibus/telegram_handlers.py:129-134,224-256]
5. **Lista e retorno.** Reaproveitar a composição do cabeçalho, tamanho de página e botões da lista completa. Evidência literal: `_HORARIOS_POR_PAGINA = 28`, `limite = 4096 - len(cabecalho) - len(rotulo)` e `InlineKeyboardButton("Voltar", callback_data=f"b:{numero}:{revisao}")`. [VERIFIED: onibus/telegram_handlers.py:17-21,137-171,248-256]

## Don't Hand-Roll

| Problema | Reutilização |
|---|---|
| Escolher o calendário para amanhã | Consultar o mesmo domínio que já escolhe o calendário para a data local |
| Abrir e paginar listas com data | Usar o callback de lista com data explícita |
| Retornar aos pontos | Usar o callback já empregado por Voltar |

## Common Pitfalls

- Somar o dia no fuso do relógio recebido pode escolher a data errada quando o relógio estiver em UTC perto da virada em Brasília. Converter primeiro.
- O primeiro horário publicado pode ser 00:00. Usar a coleção completa de amanhã evita descartá-lo pelo filtro estrito de saídas futuras.
- A mensagem inicial e o botão precisam usar a mesma data. Preservar essa data durante callbacks de paginação.
- Reabrir uma conexão para o horário anunciado pode misturar revisões durante uma publicação concorrente. Manter o snapshot já empregado na consulta do ponto.
- Feriado tem precedência sobre dia da semana no seletor atual. Efeito verificável no ramo `"domingos_feriados" if feriados`. [VERIFIED: onibus/core.py:234-240]

## Validation Architecture

A linha de base passou com 65 testes em 4,701 s. Evidência literal: `Ran 65 tests in 4.701s` e `OK`. [VERIFIED: .venv/Scripts/python.exe -m unittest discover -s tests -q]

| Nível | Comando |
|---|---|
| Foco em calendário | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_schedules.py -v` |
| Foco nos callbacks | `.venv/Scripts/python.exe -m unittest discover -s tests -p test_telegram_handlers.py -v` |
| Regressão | `.venv/Scripts/python.exe -m unittest discover -s tests -v` |

| ID | Cobertura a acrescentar |
|---|---|
| TIME-05 | Sexta→sábado, sábado→domingo, véspera→feriado em dia útil, relógio UTC em data distinta de Brasília e primeiro horário às 00:00. |
| TIME-05 | Ao clicar depois de meia-noite, manter a data do botão e da paginação. Verificar a lista completa, identificação de data e calendário e retorno aos endereços. |
| BOT-06 | Hoje encerrado com amanhã publicado e sem calendário amanhã. Dias com saídas futuras ou calendário de hoje indisponível continuam com as respostas já previstas. |

Os testes existentes usam banco temporário, relógio injetado e mocks assíncronos. Evidência literal: `class TelegramHandlersTests(unittest.IsolatedAsyncioTestCase):`, `self.temp_dir = tempfile.TemporaryDirectory()` e `callback = SimpleNamespace(data=data, answer=AsyncMock(), edit_message_text=AsyncMock())`. [VERIFIED: tests/test_telegram_handlers.py:17-52] Usar o mesmo arquivo para ampliar cobertura. Nenhum requisito de infraestrutura foi identificado para Wave 0.

## Security Domain

Para os callbacks, aplicar validação de formato completo, limites já previstos para campos e posição, data válida, índice dentro da lista e revisão atual antes de ler ou exibir dados. Evidência literal: `_HORARIOS_RE.fullmatch(data)`, `if pagina >= len(paginas):` e `pontos["revisao"] != revisao`. [VERIFIED: onibus/telegram_handlers.py:189-250] A proposta preserva controles da aplicação e não amplia autenticação ou criptografia.

## Sources

- Regras do usuário: contexto, roadmap e requisitos locais da Fase 3.
- Implementação atual: `onibus/core.py` e `onibus/telegram_handlers.py`.
- Testes e ambiente: `tests/test_schedules.py`, `tests/test_telegram_handlers.py` e execução do unittest.
