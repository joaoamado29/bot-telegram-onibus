# Pitfalls Research

**Domain:** Scraping de horários de ônibus com consulta e alertas no Telegram
**Researched:** 2026-11-13
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Implementar o parser sem uma página real de referência

**What goes wrong:** O coletor aceita menus, avisos ou listas não relacionadas como horários, ou mistura endereços com calendários diferentes.

**Why it happens:** A estrutura `h2`/`li` foi indicada pelo usuário e não comprova, isoladamente, a associação entre pontos, viagens e calendários. Durante a pesquisa, o usuário corrigiu `SOURCE_URL` em `scraping.py` para `https://tonoponto.com/itinerario-horarios-de-onibus/ce-fortaleza-etufor/`; o antigo placeholder deixou de ser bloqueio. A validação detalhada de HTML é responsabilidade da pesquisa de arquitetura e dos testes do parser.

**How to avoid:** Obter URL válida do catálogo e amostras representativas de páginas detalhadas; salvar fixtures públicas com diferentes quantidades de pontos e tipos de dia. Selecionar os contêineres de calendário e ponto antes dos elementos internos. Validar contagens e formato dos horários antes da gravação. Ausência de dados extraídos deve ser distinguida de ausência real de serviço.

**Warning signs:** Todos os pontos recebem os mesmos horários; texto de navegação aparece como endereço; resposta HTTP bem-sucedida produz zero horários sem diagnóstico.

**Phase to address:** Primeira fase de contrato de origem e scraping. Não declarar o parser validado sem as amostras.

### Pitfall 2: Associar viagens de pontos diferentes pela posição nas listas

**What goes wrong:** O terceiro horário do ponto 1 é combinado com o terceiro horário do ponto 2 sem evidência de que pertencem à mesma viagem; linhas com listas de tamanhos diferentes perdem dados silenciosamente.

**Why it happens:** A forma ampla solicitada, com `horario_ponto1` a `horario_ponto5`, favorece um `zip` entre listas independentes. A existência de tabelas amplas não comprova correspondência entre viagens.

**How to avoid:** Preservar as duas tabelas solicitadas e suas colunas, mas definir explicitamente a unidade de cada registro e a chave que liga horários ao conjunto de endereços. Identidade de linha, calendário, sentido e grupo de pontos devem entrar no contrato quando existirem na origem. Somente montar uma linha por viagem se o HTML comprovar essa associação; se não comprovar, levar a incompatibilidade à discussão do esquema antes da implementação.

**Warning signs:** `zip` descarta o fim da maior lista; número da linha é usado como chave única de todas as viagens; endereços de ida e volta são fundidos.

**Phase to address:** Modelagem e persistência, depois da inspeção do HTML e antes das migrações. GTFS [S6] é referência conceitual para separar viagem, parada e serviço, não exigência de adotar esse formato.

### Pitfall 3: Usar NOT NULL como garantia de horário preenchido

**What goes wrong:** `horario_ponto1` e `horario_ponto2` recebem `''` ou espaços, cumprindo uma restrição de nulidade sem cumprir a exigência do usuário. Uma FK declarada também pode não ser fiscalizada na conexão.

**Why it happens:** Nulidade, string vazia e validade de horário são condições diferentes; SQLite exige habilitação explícita de foreign keys por conexão [S1].

**How to avoid:** Validar e normalizar horários na fronteira do parser; rejeitar valores obrigatórios ausentes, vazios ou inválidos antes da gravação, com diagnóstico identificando linha/calendário. Usar NOT NULL e CHECK adequado ao formato escolhido, além de `PRAGMA foreign_keys=ON` antes de iniciar a transação. A chave referenciada precisa ser PK ou UNIQUE compatível. Testar tentativa de inserir referência inexistente.

**Warning signs:** Inserções com endereço inexistente passam; `NULL` é trocado por string vazia apenas para permitir importação; linhas incompletas substituem dados válidos.

**Phase to address:** Persistência e migração. A regra dos dois horários obrigatórios está confirmada; a política para dados incompatíveis precisa ser explícita.

### Pitfall 4: Confundir horário de parede, data de serviço e calendário

**What goes wrong:** Uma consulta em Brasília usa a data UTC do servidor; sábado recebe horários úteis; amanhã reutiliza o calendário de hoje. Em feriados locais, o cálculo por dia da semana sozinho fornece respostas erradas.

**Why it happens:** Comparar strings de hora sem data ou usar `datetime.now()` sem fuso. Calendário semanal e exceções por data são conceitos distintos [S6].

**How to avoid:** Centralizar relógio e resolução de calendário; usar datetime com fuso `America/Sao_Paulo` e obter a data local antes de escolher o serviço. Resolver novamente o calendário para amanhã. Definir município e fonte das exceções; não tratar ponto facultativo automaticamente como feriado de transporte. A zona IANA não contém feriados. Disponibilizar `tzdata` no Windows se não houver base IANA do sistema [S2].

**Warning signs:** Resultado muda conforme o fuso do servidor; testes usam apenas segunda-feira ao meio-dia; botão de amanhã mostra os mesmos dados sem recalcular o serviço.

**Phase to address:** Motor de consultas e calendário, antes dos handlers do bot. Testes devem incluir virada de dia, sexta/sábado, sábado/domingo e feriado configurado.

### Pitfall 5: Criar alertas apenas em memória e assumir recuperação automática

**What goes wrong:** Reiniciar o processo elimina lembretes, ou recriar tarefas duplica avisos. Retomar tarefas vencidas pode enviar uma sequência de contagens antigas depois da saída.

**Why it happens:** Persistência da conversa é confundida com persistência dos jobs. A API BasePersistence documenta estados de bot, usuário, chat e conversa; recuperação de agendamento precisa de desenho próprio [S4]. APScheduler tem políticas explícitas para execuções perdidas e coalescência [S5].

**How to avoid:** Recomenda-se persistir intenção do alerta, chat, viagem/data, antecedência, status e instante devido; reconstruir tarefas futuras com identificador estável na inicialização. Registrar entregas para minimizar duplicações e definir política para interrupções. A recuperação após reinício é recomendação a confirmar, não promessa já aprovada. Uma falha entre envio e marcação não permite prometer entrega exatamente uma vez sem suporte externo.

**Warning signs:** Teste só funciona sem reiniciar; dois cliques em notificar geram cadeias idênticas; bot reenvia avisos de viagens encerradas.

**Phase to address:** Fase de alertas e verificação operacional, antes de considerar as notificações prontas.

### Pitfall 6: Agendar repetição de cinco minutos sem ancorar na viagem

**What goes wrong:** Agendar ao clicar desloca os alertas em relação à antecedência escolhida. A mensagem final não coincide com a saída; parâmetros de hora sem data podem agendar amanhã inadvertidamente.

**Why it happens:** Uma tarefa repetida simples não representa necessariamente a sequência aprovada. JobQueue assume UTC para datas/horas sem fuso e trata certos parâmetros `time` como hoje ou amanhã [S3].

**How to avoid:** Calcular instantes absolutos a partir da saída selecionada e da antecedência. Para 12h/10 minutos: 11h50, 11h55 e 12h. Calcular minutos restantes pelo relógio atual, encerrar na saída e agendar a mensagem final explicitamente. Definir com o usuário antecedências como 7 minutos (sugestão: 11h53, 11h58 e 12h) e pedidos cujo início já passou. Não afirmar suporte a essas bordas antes da decisão.

**Warning signs:** Contagem fica negativa; mensagem final depende de intervalo divisível por cinco; mudar de ponto altera silenciosamente uma viagem já escolhida.

**Phase to address:** Contrato e implementação dos alertas, com relógio controlado nos testes.

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inserir horários apenas se novos, copiando `INSERT OR IGNORE` atual | Reaproveitar `scraping.py` | Horários antigos permanecem publicados | Somente carga inicial claramente identificada |
| Gravar cada ponto e horário em commits separados | Implementação direta | Consulta observa importação parcial | Não para publicar atualização de uma linha |
| Assumir catálogo e bot sempre executados na raiz | Manter `DB_PATH` relativo | Serviço abre banco diferente | Somente execução manual documentada |
| Usar uma instância de bot sem persistência de alerta | Menos infraestrutura | Reinício perde lembretes | Protótipo com limitação explícita, mediante decisão |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| URLs coletadas | Buscar host+caminho sem esquema; aceitar qualquer destino de `urljoin` | Reconstruir HTTPS e validar esquema/domínio após resolver; Python alerta que URL absoluta pode substituir a base [S8] |
| SQLite | Achar que FK vale apenas por aparecer no CREATE TABLE | Ativar e testar FK em toda conexão [S1] |
| JobQueue | Datas sem fuso e expectativa de primeira repetição imediata | Datas completas com fuso; a documentação descreve limites de `first=0` [S3] |
| Telegram | Reenviar sem limite após 429 | Respeitar retry_after e controlar fila; tratar bloqueio pelo usuário como falha permanente [S7] |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Rodar `requests.get` síncrono no handler | Bot para de responder durante coleta | Coleta desacoplada; handlers leem banco | Uma única requisição lenta já afeta a experiência |
| Todos os alertas disparam na mesma saída | 429 e avisos atrasados | Fila e limites de envio | FAQ orienta aproximadamente 30 mensagens/s no broadcast gratuito e evitar mais de uma/s por chat [S7] |
| Reinício reproduz todos os intervalos vencidos | Rajada de avisos obsoletos | Política de execução perdida e expiração | Qualquer indisponibilidade atravessando vários intervalos [S5] |

Não há benchmark local ou volume contratado de usuários; os limites acima são sinais de desenho, não estimativa de capacidade medida.

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Registrar token Telegram ou URL da API com token | Controle do bot por terceiros | Configurar fora do código e redigir logs |
| Aceitar URL absoluta externa no HTML | Coletor acessa destino não previsto | Lista de origem permitida e validação após redirecionamento |
| Confiar no callback sem conferir usuário e viagem | Usuário aciona seleção antiga ou de outro contexto | Validar chat, estado atual e referência persistida |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Completar três resultados com saídas de amanhã | Passageiro interpreta saída como sendo hoje | Mostrar somente as disponíveis de hoje; oferecer amanhã separadamente |
| Mostrar ponto3 ausente como botão vazio | Seleção sem horário utilizável | Exibir somente endereços válidos vinculados à linha |
| Silenciar fonte indisponível como fim de serviço | Usuário recebe conclusão falsa | Distinguir falha de dados e horários encerrados |
| Apresentar tabela publicada como localização real | Expectativa de previsão GPS | Informar que são horários publicados, sem prometer rastreamento |

## "Looks Done But Isn't" Checklist

- [ ] **Scraping:** fixtures de origem válida, calendários e grupos de pontos preservados.
- [ ] **Banco:** horários obrigatórios rejeitam vazio; FK inválida falha; atualização não expõe dados parciais.
- [ ] **Consulta:** testes para 0, 1, 2 e 3+ saídas, virada do dia e calendário de amanhã.
- [ ] **Alertas:** sequência 10/5/saída verificada; antecedência não múltipla de cinco definida; término sem contagem negativa.
- [ ] **Operação:** reinício, clique repetido, falha de envio e usuário bloqueando o bot têm comportamento definido.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Parser mistura calendários | HIGH | Suspender publicação, preservar último conjunto válido, corrigir fixtures e reimportar |
| FK não fiscalizada | MEDIUM | Auditar órfãos, corrigir relações e habilitar conexões antes de nova importação |
| Avisos duplicados | MEDIUM | Suspender jobs duplicados, reconciliar intenções ativas e adicionar chave estável |
| Fonte fora do ar | LOW | Preservar última coleta válida e indicar estado; nova tentativa limitada |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| URL inválida e seletores não comprovados | Origem e coleta detalhada | Inspeção de amostras reais e testes de parser |
| Correspondência inventada entre viagens | Modelo de dados | Fixture com listas desiguais não gera associações falsas |
| Horários obrigatórios vazios/FK inativa | Persistência | Inserções inválidas rejeitadas e integridade conferida |
| Calendário/fuso/data incorretos | Consulta de horários | Matriz temporal com amanhã e exceções |
| Estado de conversa misturado | Interação Telegram | Dois usuários navegam sem afetar suas seleções |
| Jobs perdidos, duplicados ou vencidos | Alertas | Reinício simulado e sequência ancorada na saída |
| Limites de envio e coleta bloqueante | Verificação operacional | Falhas transitórias simuladas sem travar a navegação |

## Sources

As fases acima são tópicos sugeridos para o roadmap, não numeração aprovada. Confiança MEDIUM obtida pelo seam `classify-confidence --provider websearch --verified`; documentação oficial sustenta mecanismos, enquanto decisões locais e HTML continuam pendentes.

- [S1: SQLite — Foreign Key Support](https://www.sqlite.org/foreignkeys.html).
- [S2: Python — zoneinfo](https://docs.python.org/3/library/zoneinfo.html).
- [S3: python-telegram-bot — JobQueue](https://docs.python-telegram-bot.org/en/stable/telegram.ext.jobqueue.html).
- [S4: python-telegram-bot — BasePersistence](https://docs.python-telegram-bot.org/en/stable/telegram.ext.basepersistence.html).
- [S5: APScheduler 3.x — User guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html).
- [S6: GTFS — Schedule Reference](https://gtfs.org/documentation/schedule/reference/) — referência conceitual de serviço, exceções e paradas; não evidencia a estrutura do Tonoponto.
- [S7: Telegram — Bots FAQ](https://core.telegram.org/bots/faq).
- [S8: Python — urllib.parse](https://docs.python.org/3/library/urllib.parse.html).
- Evidência local: `.planning/PROJECT.md`, `.planning/config.json` e `scraping.py`.

---
*Pitfalls research for: Bot Telegram Ônibus*
*Researched: 2026-11-13*
