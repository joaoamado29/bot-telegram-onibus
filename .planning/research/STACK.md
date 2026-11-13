# Stack Research

**Domain:** Coleta de tabelas de ônibus e bot Telegram com alertas programados
**Researched:** 2026-11-13
**Confidence:** MEDIUM

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | Manter a linha 3.11, atualizando para patch suportado; ambiente observado 3.11.9 | Aplicação e serviços | Preserva a aplicação existente e atende ao requisito Python 3.10+ do PTB; não exige migração de linguagem. |
| python-telegram-bot | 22.8, com extra `job-queue` | Handlers, botões, polling e agendamento | Versão estável observada no PyPI e documentação oficial; interface assíncrona e componentes para o fluxo linha → ponto → horário. [S1] |
| SQLite via `sqlite3` | Biblioteca embarcada no Python; verificar `sqlite3.sqlite_version` na implementação | Dados de linhas, horários, pontos e estado durável dos alertas | Reaproveita `onibus.sqlite3`; não é necessário servidor de banco para a escala inicial. Habilitar FK explicitamente por conexão. [S5] |
| `datetime` e `zoneinfo` | Biblioteca padrão Python 3.11 | Datas locais e instantes dos alertas | Usar `ZoneInfo("America/Sao_Paulo")` para o horário de Brasília; não depender do fuso do host. [S4] |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.34.2, candidato baseado no ambiente mapeado e página PyPI dessa versão | Download de HTML | Manter no coletor separado; requisições com timeout, validação HTTP e domínio permitido. [S6] |
| beautifulsoup4 | 4.15.0, release observada no PyPI | Extração de seções, endereços e listas de horários | Manter `html.parser` inicialmente; validar relação estrutural entre `h2`, listas e calendário com fixtures reais. [S7, S8] |
| APScheduler | `>=3.10.4,<3.12.0`, resolvido pelo extra do PTB | Backend de `JobQueue` | Deixar o extra selecionar versão compatível; não instalar APScheduler 4 em paralelo por suposição de compatibilidade. [S1] |
| tzdata | 2026.6 | Base IANA disponível no Windows | Declarar explicitamente para desenvolvimento/execução multiplataforma. [S4, S9] |
| Calendário local explícito | Módulo próprio, sem dependência externa obrigatória inicialmente | Dias úteis, sábado, domingo/feriado e exceções da operação | Preferir regras publicadas pelo operador e lista de exceções auditável; biblioteca de feriados sozinha não prova que a empresa opera a tabela de domingo. |

Os pins acima são candidatos para um arquivo de dependências reproduzível, não uma afirmação de instalação validada. Não houve instalação nem teste conjunto de resolução nesta pesquisa. `requirements.txt` hoje contém apenas limites mínimos de requests e Beautiful Soup. A página geral do Requests não expôs claramente o número da release no texto extraído; verificar metadata do índice e resolução do pin antes de implementar.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `venv` e pip | Ambiente isolado e resolução | Preservar o fluxo existente; registrar versões diretas e transitivas resolvidas. |
| `unittest` / `unittest.mock` | Testes de parser, calendário, consultas e alertas | Biblioteca padrão suficiente no início; relógio injetável e banco temporário evitam depender de Telegram ou site ao testar. |
| Fixtures HTML | Contrato da origem | Conservar amostras representativas por calendário e número de pontos; conferir resultados esperados independentemente do parser. |

## Installation

Comandos propostos, não executados nesta pesquisa:

```powershell
python -m pip install "python-telegram-bot[job-queue]==22.8" "tzdata==2026.6"
python -m pip install "requests==2.34.2" "beautifulsoup4==4.15.0"
python -m unittest discover -s tests
```

Antes de congelar a resolução, validar Python mínimo, importações, inicialização de `JobQueue` e disponibilidade do fuso. Registrar a versão SQLite fornecida pelo runtime; não instalar um pacote chamado `sqlite3` pelo pip.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| PTB + `JobQueue` | Outro framework Telegram | Apenas se surgir necessidade concreta que PTB não atenda; a escolha atual cobre conversação e temporizadores. |
| SQLite com estado de domínio dos alertas | PostgreSQL e fila externa | Múltiplas instâncias, volume medido ou coordenação distribuída justificarem a complexidade. |
| Requests em coletor separado | Cliente HTTP assíncrono | Coleta passar a integrar o event loop; não reescrever o coletor existente apenas porque o bot é assíncrono. |
| Beautiful Soup + HTML recebido | Navegador automatizado | Só após comprovar que dados necessários dependem de execução JavaScript e não estão no HTML. |
| Polling em uma instância | Webhook HTTPS | Infraestrutura de hospedagem exigir endpoint público e gestão de certificados; não é pré-requisito do MVP. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Exemplos PTB antigos com callbacks síncronos de versões anteriores à 20 | API atual é assíncrona | Exemplos e documentação 22.8. [S1] |
| `time.sleep` ou chamadas requests demoradas dentro de handlers async | Bloqueiam o atendimento e a execução pontual de jobs | Coletor fora do fluxo de consulta; para I/O legado inevitável, `asyncio.to_thread` com conexões criadas na thread de execução. [S10] |
| Persistência da conversa como garantia de persistência dos jobs | PTB distingue esses mecanismos | Persistir intenção e situação do alerta em SQLite e reconstituir jobs pendentes no startup. [S3] |
| Instalar todos os extras do PTB | Recursos não necessários ampliam dependências | Começar com `job-queue`; adicionar limitador apenas com necessidade observada. |
| Inserir valor artificial em `horario_ponto1/2` para cumprir obrigatoriedade | Produz dado falso e consulta enganosa | Validar e rejeitar/quarentenar registros incompletos; decidir política no planejamento. |

## Stack Patterns by Variant

**Coleta e consulta:**
- Manter coleta como comando independente e gravar snapshot validado em transação.
- Bot consulta dados locais; falha da origem não deve apagar o último conjunto válido.
- `scraping.py` define `SOURCE_URL` como `https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/`, catálogo de Fortaleza/ETUFOR. A URL foi conferida novamente após correção do usuário; a validação dos seletores das páginas detalhadas depende da inspeção do HTML real.
- Links persistidos por `_normalize_link` excluem o esquema. Reconstruir HTTPS e validar host antes de buscar páginas detalhadas.

**Conversação e concorrência:**
- `ConversationHandler` é adequado para linha → ponto → ações; configurar `concurrent_updates(False)` conforme a documentação. Paralelismo do workflow GSD é independente dessa opção do bot. [S2]
- Identificar usuário/chat e seleção atual sem compartilhar mutações entre conversas.

**Alertas:**
- Recomenda-se SQLite como fonte durável da assinatura da viagem; `JobQueue` executa os disparos em memória.
- Armazenar `chat_id`, viagem/data, ponto, antecedência, próximo disparo e estado; este armazenamento é adicional às duas tabelas de domínio solicitadas e precisa entrar nos requisitos, não deve ser introduzido silenciosamente.
- Agendar instantes absolutos conscientes de fuso. Exemplo confirmado: saída 12h, antecedência 10, avisos 11h50 e 11h55 e mensagem final 12h.
- Definir política para antecedência não múltipla de cinco e recuperação após downtime antes de implementar. A mensagem final deve ter job explícito ou regra própria para não depender de arredondamento.
- Uma instância ativa é a hipótese inicial. Persistir deduplicação reduz reenvio, mas envio Telegram e commit local não formam transação atômica; não prometer entrega exatamente uma vez.

**Esquema solicitado:**
- Preservar tabela de horários com `numero`, `nome`, `horario_ponto1..5`, sendo os dois primeiros obrigatórios, e tabela de endereços com `numero`, `nome`, `ponto1..5`.
- Acrescentar identificador de conjunto/linha/calendário e FK a chave pai primária/única, conforme definição futura da cardinalidade; `numero` sozinho não identifica viagens nem calendários.
- `NOT NULL` não impede texto vazio; a validação deve rejeitar ambos. Usar um horário escalar por célula e várias linhas por conjunto de viagens é candidato, condicionado a comprovar correspondência entre listas da origem.
- Se o site publicar listas independentes por ponto, não alinhar por índice sem evidência; fechar esse contrato com amostras antes do schema definitivo.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| PTB 22.8 | Python >=3.10 | Runtime local 3.11 atende ao mínimo publicado. [S1] |
| PTB 22.8 `[job-queue]` | APScheduler >=3.10.4,<3.12.0 | Faixa declarada; usar resolução do extra. [S1] |
| `zoneinfo` Python 3.11 | tzdata 2026.6 | Fallback IANA para Windows; validar carregamento do identificador na instalação. [S4, S9] |
| Requests + Beautiful Soup | Uso síncrono separado de PTB | Compatibilidade arquitetural proposta, ainda sem teste integrado. |
| SQLite FK | Chave pai PRIMARY KEY/UNIQUE; PRAGMA por conexão | Ativar antes de abrir transação de escrita e verificar integridade após migração. [S5] |

## Sources

Confiança atribuída pelo seam `query classify-confidence --provider websearch --verified`: **MEDIUM**. Fatos foram verificados em documentação oficial/maintainers; recomendações de desenho são inferências para este projeto. Context7 e CLI `ctx7` não estavam disponíveis, então foi utilizado acesso web às fontes primárias.

- **[S1]** [PTB no PyPI](https://pypi.org/project/python-telegram-bot/) — release 22.8, Python mínimo e dependências opcionais; publicação observada 2026-06-12.
- **[S2]** [ConversationHandler 22.8](https://docs.python-telegram-bot.org/en/stable/telegram.ext.conversationhandler.html) — processamento sequencial de updates.
- **[S3]** [Persistência PTB](https://github.com/python-telegram-bot/python-telegram-bot/wiki/Making-your-bot-persistent) e [JobQueue 22.8](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html) — distinção de estado persistente e jobs; API run_once/run_repeating. Wiki editada em 2023, conferida junto da API atual.
- **[S4]** [Python zoneinfo](https://docs.python.org/3/library/zoneinfo.html) — dados IANA e dependência tzdata em Windows; API verificada, sem adotar a versão do interpretador exibida pelo alias `/3/`.
- **[S5]** [SQLite Foreign Key Support](https://www.sqlite.org/foreignkeys.html) — ativação e requisitos das chaves estrangeiras.
- **[S6]** [Requests no PyPI](https://pypi.org/project/requests/2.34.2/) — biblioteca e suporte Python; pin sujeito a resolução validada.
- **[S7]** [Beautiful Soup no PyPI](https://pypi.org/project/beautifulsoup4/) — release 4.15.0 observada, publicada em 2026-06-07.
- **[S8]** [Beautiful Soup docs](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) — navegação e seleção estrutural; documentação exibiu 4.14.3 enquanto PyPI exibiu 4.15.0, portanto confirmar mudanças por testes de fixtures.
- **[S9]** [tzdata no PyPI](https://pypi.org/project/tzdata/) — release 2026.6 observada, publicada em 2026-10-28.
- **[S10]** [Python asyncio.to_thread](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.to_thread) — execução de I/O bloqueante fora do loop.

---
*Stack research for: Bot Telegram Ônibus*
*Researched: 2026-11-13*
